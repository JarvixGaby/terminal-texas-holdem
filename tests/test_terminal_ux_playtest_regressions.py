"""Regressions found during the eight-player terminal playtest."""

from types import SimpleNamespace

from texas_holdem.ai.decision_evaluator import DecisionContext, evaluate_decision
from texas_holdem.engine.card import Card, Rank, Suit
from texas_holdem.engine.game import TexasHoldemGame
from texas_holdem.engine.player import AIPlayer, HumanPlayer
from texas_holdem.training.realtime_assistant import RealtimeAssistant
from texas_holdem.ui import localization


def test_short_stack_call_uses_payable_amount(monkeypatch, capsys):
    human = HumanPlayer("Human", 30)
    game = TexasHoldemGame([human, AIPlayer("AI", 500)])
    prompts = []
    monkeypatch.setattr("builtins.input", lambda prompt: prompts.append(prompt) or "y")

    game._show_call_amount(human, 50)
    assert game._confirm_action("call", 50, human) == ("call", 30)
    assert "可跟注: 30" in capsys.readouterr().out
    assert "全押跟注 30" in prompts[0]
    assert "下注差额 50" in prompts[0]


def test_short_stack_advice_and_feedback_use_same_call_price(monkeypatch, capsys):
    human = HumanPlayer("Human", 184)
    villain = AIPlayer("AI", 500)
    game = TexasHoldemGame([human, villain])
    game.active_players = [human, villain]
    game.current_game_id = "hand-1"
    game.game_phase = "river"
    game.pot = 618
    game.current_bet = 247
    human.hand = [Card(Suit.CLUBS, Rank.THREE), Card(Suit.HEARTS, Rank.TWO)]
    game.community_cards = [
        Card(Suit.DIAMONDS, Rank.JACK), Card(Suit.CLUBS, Rank.ACE),
        Card(Suit.HEARTS, Rank.FIVE), Card(Suit.DIAMONDS, Rank.ACE),
        Card(Suit.CLUBS, Rank.TEN),
    ]
    monkeypatch.setattr(game, "_estimate_player_equity", lambda player: 0.05)

    game._show_realtime_assistance(human, 247)
    context = game._build_decision_context(
        human, "call", 184, 247, ["call", "fold"], 494,
    )

    assert "弃牌" in capsys.readouterr().out
    assert context.amount_to_call == 184
    assert context.pot_odds == 184 / (618 + 184)
    assert evaluate_decision(context).recommended_action == "fold"


def test_river_does_not_show_draw_outs():
    assistant = RealtimeAssistant()
    cards = [
        Card(Suit.DIAMONDS, Rank.EIGHT), Card(Suit.DIAMONDS, Rank.THREE),
        Card(Suit.CLUBS, Rank.FOUR), Card(Suit.HEARTS, Rank.FIVE),
        Card(Suit.SPADES, Rank.SIX), Card(Suit.CLUBS, Rank.SEVEN),
        Card(Suit.HEARTS, Rank.KING),
    ]

    analysis = assistant.analyze(
        hole_cards=cards[:2], community_cards=cards[2:],
        pot_size=100, bet_to_call=20, player_chips=200,
    )

    assert analysis.total_outs == 0
    assert "outs" not in assistant.format_compact(analysis)


def test_completed_hand_record_is_available_for_immediate_review(monkeypatch):
    human = HumanPlayer("Human", 500)
    game = TexasHoldemGame([human, AIPlayer("AI", 500)])
    game.active_players = list(game.players)
    game._completed_replay_record = {"players": ["Human", "AI"], "phases": []}
    monkeypatch.setattr(game.history_manager, "get_current_game_record", lambda: None)
    monkeypatch.setattr(game, "_get_hand_coach", lambda: None)
    reviewed = []

    class Analyzer:
        def analyze_hand(self, record, player_name):
            reviewed.append((record, player_name))
            return SimpleNamespace(overall_score=80)

    monkeypatch.setattr(
        "texas_holdem.history.instant_replay.get_replay_analyzer",
        lambda: Analyzer(),
    )
    monkeypatch.setattr("builtins.input", lambda prompt: reviewed.append(prompt) or "n")

    game._show_instant_replay([], ["AI"])

    assert reviewed[0][1] == "Human"
    assert any("是否查看本局复盘" in item for item in reviewed if isinstance(item, str))
    assert game._completed_replay_record is None


def test_good_raise_feedback_recommends_raise():
    evaluation = evaluate_decision(DecisionContext(
        action_taken="raise", amount=20, amount_to_call=10, min_raise=20,
        player_chips=500, pot_size=30, estimated_equity=0.50,
        legal_actions=["fold", "call", "raise"],
    ))
    assert evaluation.grade == "good"
    assert evaluation.recommended_action == "raise"


def test_english_hand_description_does_not_mix_languages():
    with localization.terminal_language("en"):
        assert localization.translate("两对 (J 和 6)") == "Two pair (J and 6)"
        assert localization.translate("赔率:满足(需25%)") == "Pot odds met (need 25%)"
        assert localization.translate("赔率门槛:40%") == "Pot odds threshold: 40%"


def test_compact_advice_shows_threshold_when_raw_equity_and_recommendation_differ():
    assistant = RealtimeAssistant()
    cards = [Card(Suit.CLUBS, Rank.KING), Card(Suit.SPADES, Rank.QUEEN)]
    analysis = assistant.analyze(
        hole_cards=cards, community_cards=[], pot_size=15,
        bet_to_call=10, player_chips=500, equity_override=0.34,
    )
    from texas_holdem.training.realtime_assistant import SuggestedAction
    analysis.suggested_action = SuggestedAction.CALL
    compact = assistant.format_compact(analysis)
    assert "赔率门槛:40%" in compact
    assert "赔率:不足" not in compact
