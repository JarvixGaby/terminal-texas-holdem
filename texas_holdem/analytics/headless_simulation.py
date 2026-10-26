# -*- coding: utf-8 -*-
"""Headless AI-only simulation helpers."""

from __future__ import annotations

import contextlib
import copy
import io
import os
import random
import tempfile
import threading
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Dict, List, Mapping, Sequence

from texas_holdem.ai.decision_provider import ActionResponse, DecisionProvider, GameStateSnapshot
from texas_holdem.engine.game import TexasHoldemGame
from texas_holdem.engine.game_rules import MAX_PLAYERS, MIN_PLAYERS
from texas_holdem.history.game_history import GameRecord, GameHistoryManager
from texas_holdem.engine.player import AIPlayer


_simulation_lock = threading.RLock()


def _serialize_simulation(run):
    """Keep local runs from swapping shared AI/style globals concurrently."""
    @wraps(run)
    def guarded(*args, **kwargs):
        with _simulation_lock:
            return run(*args, **kwargs)
    return guarded


@dataclass
class SimulationResult:
    hands_requested: int
    hands_completed: int
    errors: List[str] = field(default_factory=list)
    final_stacks: Dict[str, int] = field(default_factory=dict)
    total_actions: int = 0
    hand_summaries: List[Dict[str, Any]] = field(default_factory=list)
    engine_events: List[Dict[str, Any]] = field(default_factory=list)
    event_type_counts: Counter[str] = field(default_factory=Counter)
    event_types_by_hand_id: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(list))
    player_profiles: Dict[str, str] = field(default_factory=dict)


@dataclass
class ActionSequenceFixtureResult:
    hands_completed: int = 0
    errors: List[str] = field(default_factory=list)
    action_records: List[Dict[str, Any]] = field(default_factory=list)
    engine_events: List[Dict[str, Any]] = field(default_factory=list)
    final_stacks: Dict[str, int] = field(default_factory=dict)
    winner_names: List[str] = field(default_factory=list)
    provider_call_counts: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hands_completed": self.hands_completed,
            "errors": list(self.errors),
            "action_records": _public_safe_value(self.action_records),
            "engine_events": _public_safe_value(self.engine_events),
            "final_stacks": dict(self.final_stacks),
            "winner_names": list(self.winner_names),
            "provider_call_counts": dict(self.provider_call_counts),
        }


class ScriptedDecisionProvider(DecisionProvider):
    """Local-only deterministic provider for headless action fixture tests."""

    def __init__(self, responses: Sequence[ActionResponse]):
        self.responses = list(responses)
        self.call_count = 0

    def decide(self, state: GameStateSnapshot) -> ActionResponse:
        self.call_count += 1
        if self.responses:
            return self.responses.pop(0)
        if state.amount_to_call > 0 and "call" in state.legal_actions:
            return ActionResponse("call", state.amount_to_call, metadata={"scripted_default": True})
        if "check" in state.legal_actions:
            return ActionResponse("check", 0, metadata={"scripted_default": True})
        return ActionResponse("fold", 0, metadata={"scripted_default": True})


@_serialize_simulation
def run_action_sequence_fixture(
    scripted_responses: Mapping[str, Sequence[ActionResponse] | ScriptedDecisionProvider],
    player_count: int = 2,
    starting_chips: int = 100,
    small_blind: int = 5,
    big_blind: int = 10,
    collect_events: bool = False,
    seed: int | None = None,
    suppress_output: bool = True,
) -> ActionSequenceFixtureResult:
    """Run one local hand using scripted providers through the real validator path."""
    result = ActionSequenceFixtureResult()
    if player_count < MIN_PLAYERS or player_count > MAX_PLAYERS:
        result.errors.append(f"player_count must be between {MIN_PLAYERS} and {MAX_PLAYERS}")
        return result

    import texas_holdem.training.player_styles as player_styles
    import texas_holdem.ai.smart_ai_system as smart_ai_system
    import texas_holdem.ai.advanced_ai_engine as advanced_ai_engine
    import texas_holdem.ai.optimized_odds_calculator as optimized_odds_calculator  # noqa: F401 - preload before seeding for deterministic runs

    original_random_state = random.getstate()
    if seed is not None:
        random.seed(seed)

    players = [AIPlayer(f"AI-{idx + 1}", starting_chips) for idx in range(player_count)]
    game = TexasHoldemGame(players, small_blind=small_blind, big_blind=big_blind)
    game.assistant_enabled = False
    game.ai_action_delay_seconds = 0

    providers: Dict[str, ScriptedDecisionProvider] = {}
    for player in players:
        configured = scripted_responses.get(player.name, [])
        provider = (
            configured
            if isinstance(configured, ScriptedDecisionProvider)
            else ScriptedDecisionProvider(configured)
        )
        providers[player.name] = provider
        game.set_decision_provider(player.name, provider)

    if collect_events:
        def collect_event(event):
            result.engine_events.append(_public_safe_value(event.to_dict()))

        game.subscribe_to_events(collect_event)

    history_fd, history_path = tempfile.mkstemp(prefix="texas_action_fixture_", suffix=".json")
    stats_fd, stats_path = tempfile.mkstemp(prefix="texas_action_fixture_stats_", suffix=".json")
    os.close(history_fd)
    os.close(stats_fd)
    for temp_path in (history_path, stats_path):
        try:
            os.remove(temp_path)
        except OSError:
            pass
    game.history_manager = GameHistoryManager(history_file=history_path)

    original_stats_file = player_styles.player_style_analyzer.stats_file
    original_player_stats = copy.deepcopy(player_styles.player_style_analyzer.player_stats)
    original_style_cache = copy.deepcopy(player_styles.player_style_analyzer.style_cache)
    original_smart_ai_engines = dict(smart_ai_system.ai_engine_manager.engines)
    original_advanced_ai_engines = dict(advanced_ai_engine.advanced_ai_manager.engines)
    original_ai_equity_calculator = optimized_odds_calculator._ai_equity_calculator
    original_odds_calculator = optimized_odds_calculator._odds_calculator
    player_styles.player_style_analyzer.stats_file = stats_path
    player_styles.player_style_analyzer.player_stats = {}
    player_styles.player_style_analyzer.style_cache = {}
    smart_ai_system.ai_engine_manager.engines = {}
    advanced_ai_engine.advanced_ai_manager.engines = {}
    optimized_odds_calculator._ai_equity_calculator = None
    optimized_odds_calculator._odds_calculator = None

    try:
        stream = io.StringIO()
        output_context = contextlib.redirect_stdout(stream) if suppress_output else contextlib.nullcontext()
        with output_context:
            played = game.play_hand()
        if played or game.current_game_id is not None:
            result.hands_completed = 1
            record = game.history_manager.get_game_by_id(game.current_game_id)
            if record is not None:
                result.action_records = _summarize_fixture_actions(record)
                result.winner_names = list(record.winner_names)
    except Exception as exc:
        result.errors.append(str(exc))
    finally:
        random.setstate(original_random_state)
        player_styles.player_style_analyzer.stats_file = original_stats_file
        player_styles.player_style_analyzer.player_stats = original_player_stats
        player_styles.player_style_analyzer.style_cache = original_style_cache
        smart_ai_system.ai_engine_manager.engines = original_smart_ai_engines
        advanced_ai_engine.advanced_ai_manager.engines = original_advanced_ai_engines
        optimized_odds_calculator._ai_equity_calculator = original_ai_equity_calculator
        optimized_odds_calculator._odds_calculator = original_odds_calculator
        for temp_path in (history_path, stats_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass

    result.final_stacks = {player.name: player.chips for player in players}
    result.provider_call_counts = {
        player_name: provider.call_count
        for player_name, provider in providers.items()
    }
    return result


@_serialize_simulation
def run_ai_only_simulation(
    num_hands: int = 5,
    player_count: int = 4,
    starting_chips: int = 1000,
    small_blind: int = 5,
    big_blind: int = 10,
    suppress_output: bool = True,
    collect_events: bool = False,
    seed: int | None = None,
    ai_equity_simulations: int | None = None,
) -> SimulationResult:
    result = SimulationResult(hands_requested=num_hands, hands_completed=0)
    if num_hands <= 0:
        return result
    if player_count < MIN_PLAYERS or player_count > MAX_PLAYERS:
        result.errors.append(f"player_count must be between {MIN_PLAYERS} and {MAX_PLAYERS}")
        return result

    import texas_holdem.training.player_styles as player_styles
    import texas_holdem.ai.smart_ai_system as smart_ai_system
    import texas_holdem.ai.advanced_ai_engine as advanced_ai_engine
    import texas_holdem.ai.optimized_odds_calculator as optimized_odds_calculator  # noqa: F401 - preload before seeding for deterministic runs

    original_random_state = random.getstate()
    if seed is not None:
        random.seed(seed)

    players = [AIPlayer(f"AI-{idx + 1}", starting_chips) for idx in range(player_count)]
    game = TexasHoldemGame(players, small_blind=small_blind, big_blind=big_blind)
    game.assistant_enabled = False
    game.ai_action_delay_seconds = 0
    if collect_events:
        def collect_event(event):
            event_dict = event.to_dict()
            result.engine_events.append(event_dict)
            event_type = event_dict.get("type")
            if event_type:
                result.event_type_counts[event_type] += 1
            hand_id = event_dict.get("hand_id")
            if hand_id and event_type:
                result.event_types_by_hand_id[hand_id].append(event_type)

        game.subscribe_to_events(collect_event)

    history_fd, history_path = tempfile.mkstemp(prefix="texas_headless_", suffix=".json")
    stats_fd, stats_path = tempfile.mkstemp(prefix="texas_headless_stats_", suffix=".json")
    os.close(history_fd)
    os.close(stats_fd)
    for temp_path in (history_path, stats_path):
        try:
            os.remove(temp_path)
        except OSError:
            pass
    game.history_manager = GameHistoryManager(history_file=history_path)

    original_stats_file = player_styles.player_style_analyzer.stats_file
    original_player_stats = copy.deepcopy(player_styles.player_style_analyzer.player_stats)
    original_style_cache = copy.deepcopy(player_styles.player_style_analyzer.style_cache)
    original_smart_ai_engines = dict(smart_ai_system.ai_engine_manager.engines)
    original_advanced_ai_engines = dict(advanced_ai_engine.advanced_ai_manager.engines)
    original_ai_equity_calculator = optimized_odds_calculator._ai_equity_calculator
    original_odds_calculator = optimized_odds_calculator._odds_calculator
    player_styles.player_style_analyzer.stats_file = stats_path
    player_styles.player_style_analyzer.player_stats = {}
    player_styles.player_style_analyzer.style_cache = {}
    smart_ai_system.ai_engine_manager.engines = {}
    advanced_ai_engine.advanced_ai_manager.engines = {}
    optimized_odds_calculator._ai_equity_calculator = (
        optimized_odds_calculator.AIEquityCalculator(simulation_count=ai_equity_simulations)
        if ai_equity_simulations is not None
        else None
    )
    optimized_odds_calculator._odds_calculator = None

    from texas_holdem.ai.advanced_ai_engine import AdvancedAIEngine
    from texas_holdem.ai.ai_profiles import list_archetype_names

    profile_names = list_archetype_names()
    result.player_profiles = {
        player.name: profile_names[index % len(profile_names)]
        for index, player in enumerate(players)
    }
    game._headless_player_profiles = dict(result.player_profiles)
    advanced_ai_engine.advanced_ai_manager.engines = {
        player.name: AdvancedAIEngine(player.name, archetype_name=result.player_profiles[player.name])
        for player in players
    }

    try:
        stream = io.StringIO()
        output_context = contextlib.redirect_stdout(stream) if suppress_output else contextlib.nullcontext()
        with output_context:
            for hand_index in range(num_hands):
                if len([p for p in players if p.chips > 0]) < 2:
                    break
                try:
                    game.dealer_position %= len([p for p in players if p.chips > 0])
                    played = game.play_hand()
                    if not played and game.current_game_id is None:
                        break
                    record = game.history_manager.get_game_by_id(game.current_game_id)
                    summary = _summarize_record(hand_index + 1, record, game)
                    result.hands_completed += 1
                    result.hand_summaries.append(summary)
                except Exception as exc:
                    result.errors.append(f"hand {hand_index + 1}: {exc}")
                    break
    finally:
        random.setstate(original_random_state)
        player_styles.player_style_analyzer.stats_file = original_stats_file
        player_styles.player_style_analyzer.player_stats = original_player_stats
        player_styles.player_style_analyzer.style_cache = original_style_cache
        smart_ai_system.ai_engine_manager.engines = original_smart_ai_engines
        advanced_ai_engine.advanced_ai_manager.engines = original_advanced_ai_engines
        optimized_odds_calculator._ai_equity_calculator = original_ai_equity_calculator
        optimized_odds_calculator._odds_calculator = original_odds_calculator
        for temp_path in (history_path, stats_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass

    result.final_stacks = {player.name: player.chips for player in players}
    result.total_actions = sum(summary.get("actions", 0) for summary in result.hand_summaries)
    return result


def _summarize_fixture_actions(record: GameRecord) -> List[Dict[str, Any]]:
    actions: List[Dict[str, Any]] = []
    for phase in record.phases:
        for action in phase.actions:
            metadata = _public_safe_value(action.action_metadata or {})
            actions.append({
                "phase": phase.phase,
                "player_name": action.player_name,
                "action": action.action,
                "amount": action.amount,
                "chips_before": action.chips_before,
                "chips_after": action.chips_after,
                "validation": {
                    "action": metadata.get("validated_action"),
                    "amount": metadata.get("validated_amount"),
                    "is_valid": metadata.get("is_valid"),
                    "reason": metadata.get("validation_reason"),
                    "original_action": metadata.get("raw_action"),
                    "original_amount": metadata.get("raw_amount"),
                },
                "provider_metadata": metadata.get("provider_metadata", {}),
                "provider_error": metadata.get("provider_error"),
            })
    return actions


def _summarize_record(hand_index: int, record: GameRecord, game: TexasHoldemGame) -> Dict[str, Any]:
    if record is None:
        return {
            "hand_index": hand_index,
            "game_id": game.current_game_id,
            "actions": 0,
            "action_records": [],
            "winner_names": [],
            "total_pot": game.pot,
            "decision_evaluations": [],
            "final_hands": [],
            "outcome_metadata": {},
            "ai_styles": getattr(game, "_headless_player_profiles", {}) or {},
        }

    decision_evaluations: List[Dict[str, Any]] = []
    action_records: List[Dict[str, Any]] = []
    phase_boards: Dict[str, List[str]] = {}
    action_count = 0
    for phase in record.phases:
        phase_boards[phase.phase] = list(phase.community_cards)
        action_count += len(phase.actions)
        for action in phase.actions:
            action_record = {
                "phase": phase.phase,
                "player_name": action.player_name,
                "action": action.action,
                "amount": action.amount,
                "chips_before": action.chips_before,
                "chips_after": action.chips_after,
                "decision_evaluation": action.decision_evaluation,
            }
            action_records.append(action_record)
            if action.decision_evaluation:
                decision_evaluations.append(action.decision_evaluation)

    ai_styles = dict(getattr(record, "ai_styles", {}) or {})
    if not ai_styles:
        ai_styles = {
            player.name: (getattr(game, "_headless_player_profiles", {}) or {}).get(
                player.name,
                getattr(player, "ai_mode", "unknown"),
            )
            for player in getattr(game, "players", [])
            if getattr(player, "player_type", "") == "ai"
        }

    return {
        "hand_index": hand_index,
        "game_id": record.game_id,
        "actions": action_count,
        "action_records": action_records,
        "winner_names": list(record.winner_names),
        "total_pot": record.total_pot,
        "phase_boards": phase_boards,
        "decision_evaluations": decision_evaluations,
        "final_hands": [
            {
                "player_name": hand.player_name,
                "hole_cards": list(hand.hole_cards),
                "final_chips": hand.final_chips,
                "is_winner": hand.is_winner,
                "hand_rank": hand.hand_rank,
                "winnings": hand.winnings,
            }
            for hand in record.final_hands
        ],
        "outcome_metadata": dict(getattr(record, "outcome_metadata", {}) or {}),
        "ai_styles": ai_styles,
    }


def _count_actions(game: TexasHoldemGame) -> int:
    record = game.history_manager.current_game_record
    if not record:
        return 0
    return sum(len(phase.actions) for phase in record.phases)


_FORBIDDEN_PUBLIC_RESULT_KEYS = {
    "deck",
    "opponent_hole_cards",
    "private_ai_internals",
}


def _public_safe_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, list):
        return [_public_safe_value(item) for item in value]
    if isinstance(value, tuple):
        return [_public_safe_value(item) for item in value]
    if isinstance(value, dict):
        return {
            str(key): _public_safe_value(item)
            for key, item in value.items()
            if str(key).lower() not in _FORBIDDEN_PUBLIC_RESULT_KEYS
        }
    return str(value)
