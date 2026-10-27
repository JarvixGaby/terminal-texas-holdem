import json
from dataclasses import FrozenInstanceError

import pytest

from texas_holdem.ai.advanced_ai_engine import AdvancedAIEngine
from texas_holdem.engine.card import Card, Rank, Suit
from texas_holdem.engine.player import AIPlayer
from texas_holdem.ai.ai_profiles import (
    AIArchetypeProfile,
    ARCHETYPE_PROFILES,
    DEFAULT_ARCHETYPE_NAME,
    get_archetype_profile,
    list_archetype_names,
)


def test_defines_expected_ai_archetype_profiles():
    assert list_archetype_names() == [
        "nit",
        "tight_aggressive",
        "loose_aggressive",
        "calling_station",
        "maniac",
        "balanced",
    ]
    assert set(ARCHETYPE_PROFILES) == set(list_archetype_names())
    assert DEFAULT_ARCHETYPE_NAME == "balanced"


def test_profile_round_trips_through_json_compatible_dict():
    profile = get_archetype_profile("tight_aggressive")

    payload = profile.to_dict()
    encoded = json.dumps(payload)
    decoded = json.loads(encoded)

    assert AIArchetypeProfile.from_dict(decoded) == profile
    assert decoded == {
        "name": "tight_aggressive",
        "vpip_target": 0.22,
        "pfr_target": 0.18,
        "aggression_bias": 0.68,
        "call_bias": 0.36,
        "bluff_frequency": 0.11,
        "three_bet_frequency": 0.07,
        "cbet_frequency": 0.62,
        "fold_to_cbet_bias": 0.46,
        "showdown_stickiness": 0.42,
        "sizing_bias": 0.56,
    }


def test_profiles_are_immutable_and_range_validated():
    profile = get_archetype_profile("balanced")

    with pytest.raises(FrozenInstanceError):
        profile.vpip_target = 0.99

    with pytest.raises(ValueError, match="vpip_target"):
        AIArchetypeProfile(
            name="invalid",
            vpip_target=1.01,
            pfr_target=0.2,
            aggression_bias=0.5,
            call_bias=0.5,
            bluff_frequency=0.1,
            three_bet_frequency=0.05,
            cbet_frequency=0.5,
            fold_to_cbet_bias=0.5,
            showdown_stickiness=0.5,
            sizing_bias=0.5,
        )

    with pytest.raises(ValueError, match="pfr_target"):
        AIArchetypeProfile(
            name="invalid",
            vpip_target=0.2,
            pfr_target=0.3,
            aggression_bias=0.5,
            call_bias=0.5,
            bluff_frequency=0.1,
            three_bet_frequency=0.05,
            cbet_frequency=0.5,
            fold_to_cbet_bias=0.5,
            showdown_stickiness=0.5,
            sizing_bias=0.5,
        )


def test_default_engine_construction_remains_compatible_without_profile_selection():
    engine = AdvancedAIEngine("AI-test")

    assert engine.player_name == "AI-test"
    assert engine.skill_level == "advanced"


def test_computer_player_uses_selected_archetype_and_refreshes_reused_name():
    from texas_holdem.ai.advanced_ai_engine import advanced_ai_manager

    original = dict(advanced_ai_manager.engines)
    try:
        advanced_ai_manager.engines.clear()
        player = AIPlayer("Companion", archetype_name="loose_aggressive")
        assert player.archetype_name == "loose_aggressive"
        assert advanced_ai_manager.get_engine(player.name, player.archetype_name).archetype_profile.name == "loose_aggressive"

        replacement = advanced_ai_manager.get_engine(player.name, "tight_aggressive")
        assert replacement.archetype_profile.name == "tight_aggressive"
        assert advanced_ai_manager.get_engine(player.name, "tight_aggressive") is replacement
    finally:
        advanced_ai_manager.engines = original


def test_terminal_companions_get_distinct_play_styles(monkeypatch):
    import main

    monkeypatch.setattr(main, "log_user_action", lambda *args: None)
    monkeypatch.setattr(main, "log_game_event", lambda *args: None)
    players = main.EnhancedTexasHoldemUI.__new__(main.EnhancedTexasHoldemUI).create_players(
        {"player_name": "Human", "initial_chips": 1000, "ai_count": 5}
    )
    assert [player.archetype_name for player in players[1:]] == [
        "balanced", "loose_aggressive", "calling_station",
        "tight_aggressive", "maniac",
    ]


def test_terminal_game_supports_ten_total_players(monkeypatch):
    import main
    from texas_holdem.engine.game import TexasHoldemGame

    monkeypatch.setattr(main, "log_user_action", lambda *args: None)
    monkeypatch.setattr(main, "log_game_event", lambda *args: None)
    players = main.EnhancedTexasHoldemUI.__new__(main.EnhancedTexasHoldemUI).create_players(
        {"player_name": "Human", "initial_chips": 1000, "ai_count": 9}
    )

    assert len(players) == 10
    assert len({player.name for player in players}) == 10
    assert players[-1].name == "Jemini 2"
    assert players[7].archetype_name == "balanced"
    assert isinstance(TexasHoldemGame(players), TexasHoldemGame)

    with pytest.raises(ValueError, match="2-10"):
        TexasHoldemGame([AIPlayer(f"Extra-{index}") for index in range(11)])


def test_terminal_player_creation_rejects_more_than_nine_computer_opponents():
    import main

    ui = main.EnhancedTexasHoldemUI.__new__(main.EnhancedTexasHoldemUI)
    with pytest.raises(ValueError, match="1-9"):
        ui.create_players({"player_name": "Human", "initial_chips": 1000, "ai_count": 10})


def test_companion_styles_take_distinct_preflop_lines_with_same_public_price(monkeypatch):
    monkeypatch.setattr("random.random", lambda: 0.0)
    hole_cards = [Card(Suit.CLUBS, Rank.SEVEN), Card(Suit.CLUBS, Rank.SIX)]
    actions = {}
    for profile in ("nit", "tight_aggressive", "loose_aggressive", "calling_station", "maniac"):
        engine = AdvancedAIEngine("Companion", archetype_name=profile)
        actions[profile] = engine._profiled_preflop_decision(
            hole_cards, "BTN", equity=0.5, current_bet=10,
            min_raise=20, pot_size=15, player_chips=1000,
        )[0]

    assert actions == {
        "nit": "fold", "tight_aggressive": "fold",
        "loose_aggressive": "call", "calling_station": "call", "maniac": "raise",
    }


def test_game_history_records_actual_companion_profiles(tmp_path):
    from texas_holdem.engine.game import TexasHoldemGame
    from texas_holdem.history.game_history import GameHistoryManager

    players = [
        AIPlayer("Alice", archetype_name="balanced"),
        AIPlayer("Bob", archetype_name="loose_aggressive"),
    ]
    game = TexasHoldemGame(players)
    game.history_manager = GameHistoryManager(str(tmp_path / "history.json"))
    game.history_manager.start_new_game_record([player.name for player in players], 5, 10, 0)
    game._record_ai_styles()

    assert game.history_manager.current_game_record.ai_styles == {
        "Alice": "balanced", "Bob": "loose_aggressive",
    }
