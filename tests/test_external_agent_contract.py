from dataclasses import FrozenInstanceError

import pytest

from texas_holdem.ai.agent_state_contract import ExternalAgentState, external_agent_state_from_snapshot
from texas_holdem.ai.decision_provider import GameStateSnapshot, VisiblePlayerSnapshot


def make_snapshot():
    return GameStateSnapshot(
        game_id="game-1",
        hand_id="hand-1",
        phase="preflop",
        player_name="Hero",
        position=0,
        hole_cards=["AS", "KD"],
        community_cards=[],
        pot_size=15,
        current_bet=10,
        amount_to_call=5,
        player_chips=95,
        visible_players=[
            VisiblePlayerSnapshot("Hero", 95, 5, False, False, 0),
            VisiblePlayerSnapshot("Villain", 100, 10, False, False, 1),
        ],
        action_history=[{"player_name": "Villain", "action": "raise", "amount": 10}],
        legal_actions=["call", "raise", "fold"],
        min_raise=20,
        dealer_position=0,
        small_blind=5,
        big_blind=10,
    )


def test_external_agent_state_is_immutable_and_serializable():
    state = external_agent_state_from_snapshot(make_snapshot())

    assert isinstance(state, ExternalAgentState)
    assert state.to_dict()["player_name"] == "Hero"
    with pytest.raises(FrozenInstanceError):
        state.player_name = "Other"


def test_external_agent_state_separates_private_hole_cards_from_public_players():
    state = external_agent_state_from_snapshot(make_snapshot())
    serialized_public_players = repr(state.public_players)

    assert state.private_hole_cards == ("AS", "KD")
    assert "AS" not in serialized_public_players
    assert "KD" not in serialized_public_players
    assert state.public_players[1].name == "Villain"
