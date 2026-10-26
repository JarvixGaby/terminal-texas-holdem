import json

import pytest

from texas_holdem.engine.card import Card, Rank, Suit
from texas_holdem.ai.decision_evaluator import DecisionContext
import texas_holdem.engine.game as game_module
from texas_holdem.engine.game import TexasHoldemGame
from texas_holdem.history.game_history import GameHistoryManager
from texas_holdem.engine.player import AIPlayer, HumanPlayer


def test_record_action_stores_and_exposes_decision_evaluation(tmp_path):
    manager = GameHistoryManager(str(tmp_path / "history.json"))
    manager.start_new_game_record(["Hero", "Villain"], 5, 10, 0)
    manager.start_new_phase("preflop", [], 30, 10)

    evaluation = {
        "grade": "good",
        "score": 80.0,
        "recommended_action": "call",
        "reasoning": "Call is supported.",
        "risk_tags": [],
        "metrics": {"equity": 0.45, "pot_odds": 0.25},
    }
    manager.record_action("Hero", "call", 10, 100, 90, decision_evaluation=evaluation)

    action_obj = manager.current_game_record.phases[-1].actions[-1]
    assert action_obj.decision_evaluation == evaluation

    record = manager.get_current_game_record()
    action_dict = record["phases"][0]["actions"][0]
    assert action_dict["decision_evaluation"] == evaluation


def test_loading_old_history_without_decision_evaluation_sets_none(tmp_path):
    history_file = tmp_path / "old_history.json"
    old_record = {
        "game_id": "old-1",
        "timestamp": 1.0,
        "date_time": "2026-01-01 00:00:00",
        "players": ["Hero", "Villain"],
        "small_blind": 5,
        "big_blind": 10,
        "dealer_position": 0,
        "phases": [
            {
                "phase": "preflop",
                "community_cards": [],
                "pot_size": 15,
                "current_bet": 10,
                "actions": [
                    {
                        "player_name": "Hero",
                        "action": "fold",
                        "amount": 0,
                        "chips_before": 100,
                        "chips_after": 100,
                        "timestamp": 2.0,
                    }
                ],
            }
        ],
        "final_hands": [],
        "total_pot": 15,
        "winner_names": ["Villain"],
        "duration_seconds": 3.0,
    }
    history_file.write_text(json.dumps([old_record]), encoding="utf-8")

    loaded = GameHistoryManager(str(history_file))._load_all_games()

    assert len(loaded) == 1
    assert loaded[0].phases[0].actions[0].decision_evaluation is None


def test_build_decision_context_contains_expected_fields_and_calculated_values(monkeypatch):
    hero = HumanPlayer("Hero", chips=90)
    villain = AIPlayer("Villain", chips=100)
    hero.hand = [Card(Suit.SPADES, Rank.ACE), Card(Suit.HEARTS, Rank.KING)]
    villain.hand = [Card(Suit.CLUBS, Rank.TWO), Card(Suit.DIAMONDS, Rank.SEVEN)]
    hero.current_bet = 10

    game = TexasHoldemGame([hero, villain], small_blind=5, big_blind=10)
    game.active_players = [hero, villain]
    game.current_game_id = "game-ctx"
    game.game_phase = "flop"
    game.community_cards = [
        Card(Suit.SPADES, Rank.TWO),
        Card(Suit.HEARTS, Rank.THREE),
        Card(Suit.CLUBS, Rank.FOUR),
    ]
    game.pot = 40
    game.current_bet = 20
    monkeypatch.setattr(game, "_estimate_player_equity", lambda player: 0.55)

    context = game._build_decision_context(
        hero,
        action="call",
        amount=10,
        amount_to_call=10,
        legal_actions=game._get_legal_actions(hero, amount_to_call=10),
        min_raise=30,
    )

    assert isinstance(context, DecisionContext)
    assert context.game_id == "game-ctx"
    assert context.player_name == "Hero"
    assert context.phase == "flop"
    assert context.position == "0"
    assert context.hole_cards == ["A♠", "K♥"]
    assert context.community_cards == ["2♠", "3♥", "4♣"]
    assert context.pot_size == 40
    assert context.current_bet == 20
    assert context.amount_to_call == 10
    assert context.player_chips == 90
    assert context.legal_actions == ["call", "raise", "fold"]
    assert context.action_taken == "call"
    assert context.amount == 10
    assert context.estimated_equity == 0.55
    assert context.pot_odds == pytest.approx(10 / 50)
    assert context.opponent_count == 1
    assert context.min_raise == 30


def test_record_processed_action_passes_decision_evaluation_to_history(monkeypatch):
    hero = HumanPlayer("Hero", chips=100)
    villain = AIPlayer("Villain", chips=100)
    game = TexasHoldemGame([hero, villain], small_blind=5, big_blind=10)
    game.active_players = [hero, villain]
    game.current_bet = 10
    game.pot = 30

    evaluation = {"grade": "good", "score": 80.0, "recommended_action": "call"}
    monkeypatch.setattr(game, "_evaluate_player_decision", lambda *args, **kwargs: evaluation)
    recorded = []

    def fake_record_action(*args, **kwargs):
        recorded.append((args, kwargs))

    game.history_manager.record_action = fake_record_action
    game._record_processed_action(hero, "call", 10, chips_before=100, amount_to_call=10)

    assert recorded == [(("Hero", "call", 10, 100, 100), {"decision_evaluation": evaluation})]


def test_record_processed_action_evaluates_pre_action_snapshot_after_mutation(monkeypatch):
    hero = HumanPlayer("Hero", chips=90)
    villain = AIPlayer("Villain", chips=100)
    game = TexasHoldemGame([hero, villain], small_blind=5, big_blind=10)
    game.active_players = [hero, villain]
    game.current_game_id = "snapshot-game"
    game.current_bet = 10
    game.pot = 40  # post-call mutated pot

    captured_contexts = []

    def fake_evaluate(context):
        captured_contexts.append(context)
        return {"grade": "good", "score": 80.0, "recommended_action": "call"}

    monkeypatch.setattr(game, "_estimate_player_equity", lambda player: 0.5)
    monkeypatch.setattr(game_module, "evaluate_decision", fake_evaluate)
    game.history_manager.record_action = lambda *args, **kwargs: None

    game._record_processed_action(
        hero,
        "call",
        10,
        chips_before=100,
        amount_to_call=10,
        legal_actions=["fold", "call", "raise"],
        min_raise=20,
        decision_pot_size=30,
        decision_player_chips=100,
        decision_current_bet=10,
    )

    assert len(captured_contexts) == 1
    context = captured_contexts[0]
    assert context.pot_size == 30
    assert context.player_chips == 100
    assert context.current_bet == 10
    assert context.pot_odds == pytest.approx(10 / 40)


def test_human_feedback_emits_compact_trainer_hint_but_ai_feedback_does_not():
    human = HumanPlayer("Hero", chips=100)
    ai = AIPlayer("Bot", chips=100)
    game = TexasHoldemGame([human, ai], small_blind=5, big_blind=10)
    events = []
    game.subscribe_to_events(events.append)
    evaluation = {
        "grade": "good",
        "score": 80.0,
        "recommended_action": "call",
        "reasoning": "Call is supported because estimated equity meets pot odds.",
    }

    game._show_decision_feedback(human, evaluation)
    feedback_events = [event for event in events if event.type == "decision_feedback_displayed"]
    assert len(feedback_events) == 1
    event = feedback_events[0]
    message = event.public_payload["message"]
    assert "训练提示" in message
    assert "决策反馈" not in message
    assert "GTO" not in message
    assert "correct" not in message.lower()
    assert "good" in message
    assert "80" in message
    assert event.private_payload_by_player == {}
    assert "hole" not in repr(event.to_dict()).lower()

    game._show_decision_feedback(ai, evaluation)
    assert len([event for event in events if event.type == "decision_feedback_displayed"]) == 1
