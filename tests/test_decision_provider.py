from dataclasses import asdict
import json
import random

from texas_holdem.ai.action_validator import validate_action
from texas_holdem.ai.advanced_ai_engine import advanced_ai_manager
from texas_holdem.engine.card import Card, Rank, Suit
from texas_holdem.ai.decision_provider import (
    ActionResponse,
    BuiltInAIDecisionProvider,
    GameStateSnapshot,
    HumanCliDecisionProvider,
    VisiblePlayerSnapshot,
)
from texas_holdem.ai.agent_state_contract import external_agent_state_from_snapshot
from texas_holdem.engine.player import AIPlayer


def make_snapshot(**overrides):
    data = dict(
        game_id="g1",
        hand_id="h1",
        phase="preflop",
        player_name="AI-1",
        position=0,
        hole_cards=["A♠", "K♠"],
        community_cards=[],
        pot_size=15,
        current_bet=10,
        amount_to_call=5,
        player_chips=100,
        visible_players=[
            VisiblePlayerSnapshot("AI-1", 100, 5, False, False, 0),
            VisiblePlayerSnapshot("AI-2", 100, 10, False, False, 1),
        ],
        action_history=[{"player_name": "AI-2", "action": "raise", "amount": 10}],
        legal_actions=["fold", "call", "raise"],
        min_raise=20,
        dealer_position=0,
        small_blind=5,
        big_blind=10,
    )
    data.update(overrides)
    return GameStateSnapshot(**data)


def test_action_response_metadata_is_not_shared():
    first = ActionResponse("check")
    second = ActionResponse("fold")
    first.metadata["x"] = 1
    assert second.metadata == {}


def test_action_response_metadata_can_carry_json_explanation_without_shared_defaults():
    first = ActionResponse(
        "call",
        10,
        metadata={
            "ai_explanation": {
                "schema_version": 1,
                "summary": "Calling because the price is plausible.",
                "tags": ["pot-odds"],
                "factors": {"phase": "flop", "facing_bet": True},
            }
        },
    )
    second = ActionResponse("check")

    serialized = asdict(first)

    assert serialized["metadata"]["ai_explanation"]["tags"] == ["pot-odds"]
    assert second.metadata == {}
    json.dumps(serialized)


def test_snapshot_serializes_without_hidden_cards_or_deck():
    snapshot = make_snapshot()
    serialized = asdict(snapshot)
    assert serialized["hole_cards"] == ["A♠", "K♠"]
    assert "deck" not in serialized
    assert "opponent_hole_cards" not in str(serialized).lower()
    assert all("hand" not in player for player in serialized["visible_players"])


def test_external_agent_state_serialization_is_seat_scoped_and_public_safe():
    snapshot = make_snapshot(
        player_name="Hero",
        hole_cards=["A♠", "K♠"],
        community_cards=["2♣", "7♦", "Q♥"],
        visible_players=[
            VisiblePlayerSnapshot("Hero", 100, 5, False, False, 0),
            VisiblePlayerSnapshot("Villain", 120, 10, False, False, 1),
        ],
        action_history=[
            {
                "phase": "preflop",
                "player_name": "Villain",
                "action": "raise",
                "amount": 10,
                "opponent_hole_cards": ["2♠", "2♥"],
                "deck": ["3♣", "4♣"],
                "unsafe_seed": 12345,
                "private_ai_internals": {"range": "hidden"},
            }
        ],
    )

    serialized = external_agent_state_from_snapshot(snapshot).to_dict()
    serialized_text = json.dumps(serialized, ensure_ascii=False).lower()

    assert serialized["private_hole_cards"] == ("A♠", "K♠")
    assert [player["name"] for player in serialized["public_players"]] == ["Hero", "Villain"]
    assert all("hand" not in player and "hole" not in player for player in serialized["public_players"])
    assert "2♠" not in serialized_text
    assert "2♥" not in serialized_text
    assert "deck" not in serialized_text
    assert "unsafe_seed" not in serialized_text
    assert "private_ai_internals" not in serialized_text



def test_builtin_ai_provider_wraps_existing_make_decision():
    class StubAI(AIPlayer):
        def __init__(self):
            super().__init__("AI-1", chips=100)
            self.hand = [Card(Suit.SPADES, Rank.ACE), Card(Suit.SPADES, Rank.KING)]
            self.calls = []

        def make_decision(self, **kwargs):
            self.calls.append(kwargs)
            return "call", 5

    ai = StubAI()
    response = BuiltInAIDecisionProvider(ai).decide(make_snapshot())
    assert response.action == "call"
    assert response.amount == 5
    assert response.error is None
    assert ai.calls[0]["current_bet"] == 5
    assert ai.calls[0]["table_current_bet"] == 10
    assert ai.calls[0]["player_current_bet"] == 5
    assert ai.calls[0]["action_history"] == [{"player_name": "AI-2", "action": "raise", "amount": 10}]
    assert ai.calls[0]["min_raise"] == 20
    assert ai.calls[0]["pot_size"] == 15


def test_builtin_ai_provider_adds_public_safe_json_explanation_without_changing_decision():
    class StubAI(AIPlayer):
        def __init__(self):
            super().__init__("AI-1", chips=100)
            self.hand = [Card(Suit.SPADES, Rank.ACE), Card(Suit.SPADES, Rank.KING)]

        def make_decision(self, **kwargs):
            return "call", 5

    response = BuiltInAIDecisionProvider(StubAI()).decide(make_snapshot())
    explanation = response.metadata["ai_explanation"]
    serialized = asdict(response)
    serialized_text = json.dumps(serialized)

    assert response.action == "call"
    assert response.amount == 5
    assert explanation["schema_version"] == 1
    assert "pot-odds" in explanation["tags"]
    assert explanation["factors"]["phase"] == "preflop"
    assert "Card" not in serialized_text
    assert "deck" not in serialized_text.lower()
    assert "opponent_hole_cards" not in serialized_text.lower()
    assert "hole_cards" not in serialized_text.lower()


def test_builtin_ai_receives_position_relative_to_rotating_blinds():
    class StubAI(AIPlayer):
        def __init__(self):
            super().__init__("AI-1")
            self.positions = []

        def make_decision(self, **kwargs):
            self.positions.append(kwargs["position"])
            return "fold", 0

    ai = StubAI()
    provider = BuiltInAIDecisionProvider(ai)
    seats = [VisiblePlayerSnapshot(f"AI-{i + 1}", 100, 0, False, False, i)
             for i in range(4)]
    for dealer, expected in [(0, 3), (1, 2), (2, 1), (3, 0)]:
        provider.decide(make_snapshot(
            visible_players=seats, position=0, dealer_position=dealer,
        ))
        assert ai.positions[-1] == expected


def test_heads_up_position_maps_button_small_blind_and_big_blind():
    from texas_holdem.ai.advanced_ai_engine import PositionRangeManager

    assert PositionRangeManager.get_position_name(0, 2) == "BTN"
    assert PositionRangeManager.get_position_name(1, 2) == "BB"


def test_builtin_ai_provider_uses_engine_explanation_when_ai_exposes_one():
    class StubAI(AIPlayer):
        def __init__(self):
            super().__init__("AI-1", chips=100)
            self.last_decision_metadata = {
                "schema_version": 1,
                "summary": "Continuation bet on a favorable flop.",
                "tags": ["c-bet"],
                "factors": {"phase": "flop"},
            }

        def make_decision(self, **kwargs):
            return "raise", 45

    response = BuiltInAIDecisionProvider(StubAI()).decide(
        make_snapshot(
            phase="flop",
            amount_to_call=0,
            current_bet=0,
            legal_actions=["check", "raise", "fold"],
            action_history=[
                {"phase": "preflop", "player_name": "AI-1", "action": "raise", "amount": 30}
            ],
        )
    )

    assert response.action == "raise"
    assert response.amount == 45
    assert response.metadata["ai_explanation"]["tags"] == ["c-bet"]


def test_builtin_ai_provider_live_ai_player_carries_advanced_engine_explanation_json_safely():
    random.seed(0)
    advanced_ai_manager.engines.pop("AI-1", None)
    ai = AIPlayer("AI-1", chips=1000)
    ai.hand = [Card(Suit.SPADES, Rank.ACE), Card(Suit.HEARTS, Rank.QUEEN)]
    flop = [
        Card(Suit.CLUBS, Rank.KING),
        Card(Suit.DIAMONDS, Rank.SEVEN),
        Card(Suit.SPADES, Rank.TWO),
    ]
    snapshot = make_snapshot(
        phase="flop",
        hole_cards=[str(card) for card in ai.hand],
        community_cards=[str(card) for card in flop],
        pot_size=90,
        current_bet=0,
        amount_to_call=0,
        player_chips=ai.chips,
        position=3,
        visible_players=[
            VisiblePlayerSnapshot("AI-1", ai.chips, 0, False, False, 3),
            VisiblePlayerSnapshot("Villain-1", 1000, 0, False, False, 0),
            VisiblePlayerSnapshot("Villain-2", 1000, 0, False, False, 1),
        ],
        action_history=[
            {"phase": "preflop", "player_name": "AI-1", "action": "raise", "amount": 30},
            {"phase": "preflop", "player_name": "Villain-1", "action": "call", "amount": 30},
        ],
        legal_actions=["check", "raise", "fold"],
        min_raise=20,
    )

    response = BuiltInAIDecisionProvider(
        ai,
        community_cards_provider=lambda: flop,
    ).decide(snapshot)
    explanation = response.metadata["ai_explanation"]
    serialized_text = json.dumps(asdict(response))

    assert validate_action(snapshot, response).is_valid is True
    assert response.raw_response == (response.action, response.amount)
    assert response.action in snapshot.legal_actions
    assert isinstance(response.amount, int)
    assert response.error is None
    assert ai.last_decision_metadata is not None
    assert explanation["source"] == "AdvancedAIEngine"
    assert explanation == ai.last_decision_metadata
    assert explanation["factors"]["phase"] == "flop"
    assert "Card" not in serialized_text
    assert "hole_cards" not in serialized_text.lower()
    assert "opponent_hole_cards" not in serialized_text.lower()
    assert "deck" not in serialized_text.lower()


def test_builtin_ai_provider_can_use_live_card_objects_for_internal_ai_adapter():
    class StubAI(AIPlayer):
        def __init__(self):
            super().__init__("AI-1", chips=100)
            self.seen_community_cards = None

        def make_decision(self, **kwargs):
            self.seen_community_cards = kwargs["community_cards"]
            return "check", 0

    flop = [Card(Suit.HEARTS, Rank.TWO), Card(Suit.CLUBS, Rank.THREE), Card(Suit.DIAMONDS, Rank.FOUR)]
    ai = StubAI()
    response = BuiltInAIDecisionProvider(ai, community_cards_provider=lambda: flop).decide(
        make_snapshot(amount_to_call=0, legal_actions=["check", "raise", "fold"], community_cards=[str(card) for card in flop])
    )

    assert response.action == "check"
    assert ai.seen_community_cards == flop


def test_builtin_ai_provider_safe_fallback_on_exception_prefers_check():
    class BrokenAI(AIPlayer):
        def make_decision(self, **kwargs):
            raise RuntimeError("boom")

    response = BuiltInAIDecisionProvider(BrokenAI("AI-1", 100)).decide(
        make_snapshot(amount_to_call=0, legal_actions=["check", "raise", "fold"])
    )
    assert response.action == "check"
    assert response.amount == 0
    assert response.error is not None
    assert response.metadata["fallback"] is True


def test_builtin_ai_provider_safe_fallback_on_illegal_action():
    class BadAI(AIPlayer):
        def make_decision(self, **kwargs):
            return "dance", 99

    response = BuiltInAIDecisionProvider(BadAI("AI-1", 100)).decide(make_snapshot())
    assert response.action == "fold"
    assert response.amount == 0
    assert response.error is not None
    assert response.metadata["fallback"] is True


def test_human_cli_provider_reads_action_and_raise_amount():
    prompts = []
    answers = iter(["raise", "30"])
    provider = HumanCliDecisionProvider(input_fn=lambda prompt="": (prompts.append(prompt), next(answers))[1], print_fn=lambda *args, **kwargs: None)
    response = provider.decide(make_snapshot())
    assert response.action == "raise"
    assert response.amount == 30
    assert any("fold" in prompt and "raise" in prompt for prompt in prompts)
