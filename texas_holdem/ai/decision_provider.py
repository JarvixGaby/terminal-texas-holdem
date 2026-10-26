# -*- coding: utf-8 -*-
"""Decision provider abstractions for poker action selection."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from texas_holdem.engine.player import AIPlayer


@dataclass
class VisiblePlayerSnapshot:
    name: str
    chips: int
    current_bet: int
    is_folded: bool
    is_all_in: bool
    position: int


@dataclass
class GameStateSnapshot:
    game_id: str
    hand_id: str
    phase: str
    player_name: str
    position: int
    hole_cards: List[str]
    community_cards: List[str]
    pot_size: int
    current_bet: int
    amount_to_call: int
    player_chips: int
    visible_players: List[VisiblePlayerSnapshot]
    action_history: List[Dict[str, Any]]
    legal_actions: List[str]
    min_raise: int
    dealer_position: int
    small_blind: int
    big_blind: int


@dataclass
class ActionResponse:
    action: Any
    amount: Any = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    raw_response: Any = None
    error: Optional[str] = None


class DecisionProvider(ABC):
    @abstractmethod
    def decide(self, state: GameStateSnapshot) -> ActionResponse:
        """Return an action response for the supplied public decision snapshot."""


class BuiltInAIDecisionProvider(DecisionProvider):
    """Adapter around the existing AIPlayer.make_decision API."""

    def __init__(self, ai_player: AIPlayer, community_cards_provider: Optional[Callable[[], List[Any]]] = None):
        self.ai_player = ai_player
        self.community_cards_provider = community_cards_provider

    def decide(self, state: GameStateSnapshot) -> ActionResponse:
        try:
            opponents = [
                player.name for player in state.visible_players
                if player.name != state.player_name and not player.is_folded
            ]
            community_cards = self.community_cards_provider() if self.community_cards_provider else state.community_cards
            raw = self.ai_player.make_decision(
                current_bet=state.amount_to_call,
                min_raise=state.min_raise,
                pot_size=state.pot_size,
                community_cards=community_cards,
                position=self._ai_position(state),
                total_players=len(state.visible_players),
                opponents_in_hand=opponents,
                table_current_bet=state.current_bet,
                player_current_bet=self._acting_player_current_bet(state),
                action_history=state.action_history,
            )
            action, amount = raw
            if action not in state.legal_actions:
                return self._fallback(state, f"illegal action from AI: {action}", raw_response=raw)
            return ActionResponse(
                action=action,
                amount=amount,
                metadata={
                    "ai_explanation": self._decision_explanation(state, action, amount)
                },
                raw_response=raw,
            )
        except Exception as exc:  # never let provider failure break the game loop
            return self._fallback(state, str(exc), raw_response=None)

    def _fallback(self, state: GameStateSnapshot, error: str, raw_response: Any = None) -> ActionResponse:
        action = "check" if "check" in state.legal_actions else "fold"
        return ActionResponse(
            action=action,
            amount=0,
            metadata={"fallback": True, "provider": self.__class__.__name__},
            raw_response=raw_response,
            error=error,
        )

    def _acting_player_current_bet(self, state: GameStateSnapshot) -> int:
        for player in state.visible_players or []:
            if player.name == state.player_name:
                try:
                    return max(int(player.current_bet), 0)
                except (TypeError, ValueError):
                    return 0
        return 0

    @staticmethod
    def _ai_position(state: GameStateSnapshot) -> int:
        """Translate the public seat index into the AI range manager's SB-first order."""
        player_count = len(state.visible_players)
        if player_count < 2:
            return state.position
        small_blind_seat = (
            state.dealer_position if player_count == 2
            else (state.dealer_position + 1) % player_count
        )
        return (state.position - small_blind_seat) % player_count

    def _decision_explanation(
        self,
        state: GameStateSnapshot,
        action: str,
        amount: Any,
    ) -> Dict[str, Any]:
        engine_explanation = self._json_safe_dict(
            getattr(self.ai_player, "last_decision_metadata", None)
        )
        if engine_explanation:
            return engine_explanation

        tags = self._public_explanation_tags(state, action)
        return {
            "schema_version": 1,
            "source": self.__class__.__name__,
            "summary": self._public_explanation_summary(action, tags),
            "tags": tags,
            "factors": {
                "phase": state.phase,
                "action": action,
                "amount": self._safe_int(amount),
                "facing_bet": state.amount_to_call > 0,
                "pot_odds": round(
                    state.amount_to_call / (state.pot_size + state.amount_to_call),
                    3,
                )
                if state.amount_to_call > 0 and state.pot_size + state.amount_to_call > 0
                else None,
            },
        }

    def _public_explanation_tags(self, state: GameStateSnapshot, action: str) -> List[str]:
        tags: List[str] = []
        if self._is_flop_cbet_opportunity(state) and action == "raise":
            tags.append("c-bet")
        if self._is_facing_flop_cbet(state):
            tags.append("fold-to-cbet" if action == "fold" else "continue-vs-cbet")
        if state.amount_to_call > 0 and action == "call":
            tags.append("pot-odds")
        if action == "raise" and "c-bet" not in tags:
            tags.append("pressure")
        if action == "check":
            tags.append("pot-control")
        if action == "fold" and "fold-to-cbet" not in tags:
            tags.append("fold")
        return tags or [action]

    def _public_explanation_summary(self, action: str, tags: List[str]) -> str:
        if "c-bet" in tags:
            return "Continuation bet with prior initiative."
        if "fold-to-cbet" in tags:
            return "Folding to flop continuation pressure."
        if "pot-odds" in tags:
            return "Continuing because the call price looks plausible."
        if "pressure" in tags:
            return "Applying pressure with a raise."
        if action == "check":
            return "Keeping the pot controlled when checking is available."
        if action == "fold":
            return "Declining the continue price."
        return "Using the built-in AI's selected action."

    def _last_preflop_aggressor(self, action_history: List[Dict[str, Any]]) -> Optional[str]:
        aggressor = None
        for item in action_history or []:
            if item.get("phase") == "preflop" and item.get("action") in {"raise", "bet"}:
                aggressor = item.get("player_name")
        return aggressor

    def _is_flop_cbet_opportunity(self, state: GameStateSnapshot) -> bool:
        if state.phase != "flop":
            return False
        if any(item.get("phase") == "flop" for item in state.action_history or []):
            return False
        return self._last_preflop_aggressor(state.action_history) == state.player_name

    def _is_facing_flop_cbet(self, state: GameStateSnapshot) -> bool:
        if state.phase != "flop":
            return False
        preflop_aggressor = self._last_preflop_aggressor(state.action_history)
        if not preflop_aggressor or preflop_aggressor == state.player_name:
            return False
        flop_aggressors = [
            item.get("player_name")
            for item in state.action_history or []
            if item.get("phase") == "flop" and item.get("action") in {"raise", "bet"}
        ]
        return bool(flop_aggressors) and flop_aggressors[0] == preflop_aggressor

    def _safe_int(self, value: Any) -> int:
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0

    def _json_safe_dict(self, value: Any) -> Dict[str, Any]:
        if not isinstance(value, dict):
            return {}
        safe = self._json_safe_value(value)
        return safe if isinstance(safe, dict) else {}

    def _json_safe_value(self, value: Any) -> Any:
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, list):
            return [self._json_safe_value(item) for item in value]
        if isinstance(value, dict):
            return {
                str(key): self._json_safe_value(item)
                for key, item in value.items()
                if key not in {"hole_cards", "opponent_hole_cards", "deck"}
            }
        return str(value)


class HumanCliDecisionProvider(DecisionProvider):
    """Simple CLI provider with injected IO functions to keep it testable."""

    def __init__(self, input_fn: Callable[[str], str] = input, print_fn: Callable[..., None] = print):
        self.input_fn = input_fn
        self.print_fn = print_fn

    def decide(self, state: GameStateSnapshot) -> ActionResponse:
        legal = list(state.legal_actions)
        self.print_fn(f"{state.player_name} legal actions: {', '.join(legal)}")
        while True:
            action = self.input_fn(f"Choose action ({'/'.join(legal)}): ").strip().lower()
            if action in legal:
                break
            self.print_fn("Invalid action, please try again.")

        amount = 0
        if action in ("raise", "all-in"):
            while True:
                raw_amount = self.input_fn("Amount: ").strip()
                try:
                    amount = int(raw_amount)
                    break
                except (TypeError, ValueError):
                    self.print_fn("Invalid amount, please enter an integer.")
        return ActionResponse(action=action, amount=amount, metadata={"provider": self.__class__.__name__})
