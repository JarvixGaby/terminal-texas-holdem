from texas_holdem.ai.advanced_ai_engine import AdvancedAIEngine
from texas_holdem.engine.card import Card, Rank, Suit


def test_preflop_weak_hand_checks_when_no_call_required():
    engine = AdvancedAIEngine("AI-test")
    weak_hand = [Card(Suit.CLUBS, Rank.TWO), Card(Suit.DIAMONDS, Rank.SEVEN)]

    action, amount = engine._preflop_decision_v2(
        hole_cards=weak_hand,
        position_name="BB",
        equity=0.10,
        current_bet=0,
        min_raise=20,
        pot_size=30,
        player_chips=1000,
        opponents_in_hand=["AI-1", "AI-2"],
    )

    assert (action, amount) == ("check", 0)


def test_profiled_preflop_continues_broadway_at_blind_price_when_random_roll_misses(monkeypatch):
    engine = AdvancedAIEngine("AI-nit", archetype_name="nit")
    broadway_hand = [Card(Suit.CLUBS, Rank.KING), Card(Suit.DIAMONDS, Rank.QUEEN)]
    monkeypatch.setattr("texas_holdem.ai.advanced_ai_engine.random.random", lambda: 0.99)

    action, amount = engine._preflop_decision_v2(
        hole_cards=broadway_hand,
        position_name="BTN",
        equity=0.60,
        current_bet=10,
        min_raise=20,
        pot_size=30,
        player_chips=1000,
        opponents_in_hand=["AI-1", "AI-2"],
    )

    assert action == "call"
    assert amount == 10


def test_profiled_preflop_calls_playable_broadway_facing_raise_when_random_roll_misses(monkeypatch):
    engine = AdvancedAIEngine("AI-tag", archetype_name="tight_aggressive")
    broadway_hand = [Card(Suit.CLUBS, Rank.KING), Card(Suit.DIAMONDS, Rank.QUEEN)]
    monkeypatch.setattr("texas_holdem.ai.advanced_ai_engine.random.random", lambda: 0.99)

    action, amount = engine._preflop_decision_v2(
        hole_cards=broadway_hand,
        position_name="BTN",
        equity=0.60,
        current_bet=30,
        min_raise=60,
        pot_size=90,
        player_chips=1000,
        opponents_in_hand=["AI-1", "AI-2"],
    )

    assert action == "call"
    assert amount == 30


def test_postflop_no_bet_strong_equity_builds_pot_even_when_slowplay_roll_hits(monkeypatch):
    engine = AdvancedAIEngine("AI-value")
    monkeypatch.setattr("texas_holdem.ai.advanced_ai_engine.MixedStrategyDecider.should_slow_play", lambda equity: True)

    action, amount = engine._handle_no_bet_scenario(
        equity=0.90,
        raw_strength=0.90,
        has_position=True,
        has_draw=False,
        pot_size=100,
        player_chips=1000,
        min_raise=20,
        board_texture={"danger_level": 3},
        opponents_in_hand=["AI-1"],
        phase="turn",
        action_history=[],
    )

    assert action == "raise"
    assert amount >= 20


def test_profiled_preflop_folds_non_premium_when_equity_far_below_pot_odds(monkeypatch):
    engine = AdvancedAIEngine("AI-station", archetype_name="calling_station")
    small_pair = [Card(Suit.CLUBS, Rank.SIX), Card(Suit.DIAMONDS, Rank.SIX)]
    monkeypatch.setattr("texas_holdem.ai.advanced_ai_engine.random.random", lambda: 0.0)

    action, amount = engine._preflop_decision_v2(
        hole_cards=small_pair,
        position_name="BB",
        equity=0.0,
        current_bet=10,
        min_raise=20,
        pot_size=15,
        player_chips=1000,
        opponents_in_hand=["AI-1", "AI-2"],
    )

    assert (action, amount) == ("fold", 0)


def test_calling_station_folds_blind_price_preflop_when_equity_below_pot_odds(monkeypatch):
    engine = AdvancedAIEngine("AI-station", archetype_name="calling_station")
    small_pair = [Card(Suit.CLUBS, Rank.SIX), Card(Suit.DIAMONDS, Rank.SIX)]
    monkeypatch.setattr("texas_holdem.ai.advanced_ai_engine.random.random", lambda: 0.0)

    action, amount = engine._preflop_decision_v2(
        hole_cards=small_pair,
        position_name="BB",
        equity=0.20,
        current_bet=10,
        min_raise=20,
        pot_size=20,
        player_chips=1000,
        opponents_in_hand=["AI-1", "AI-2"],
    )

    assert (action, amount) == ("fold", 0)


def test_calling_station_calls_playable_late_position_hand_at_close_blind_price(monkeypatch):
    station = AdvancedAIEngine("AI-station", archetype_name="calling_station")
    nit = AdvancedAIEngine("AI-nit", archetype_name="nit")
    suited_king = [Card(Suit.CLUBS, Rank.KING), Card(Suit.CLUBS, Rank.SIX)]
    monkeypatch.setattr("texas_holdem.ai.advanced_ai_engine.random.random", lambda: 0.0)

    def choose(engine):
        return engine._preflop_decision_v2(
            hole_cards=suited_king,
            position_name="BTN",
            equity=0.35,
            current_bet=10,
            min_raise=20,
            pot_size=15,
            player_chips=1000,
            opponents_in_hand=["AI-1", "AI-2"],
        )

    assert choose(station) == ("call", 10)
    assert choose(nit) == ("fold", 0)


def test_calling_station_completes_small_blind_when_equity_covers_price():
    station = AdvancedAIEngine("AI-station", archetype_name="calling_station")
    nit = AdvancedAIEngine("AI-nit", archetype_name="nit")
    weak_hand = [Card(Suit.CLUBS, Rank.SEVEN), Card(Suit.DIAMONDS, Rank.TWO)]

    def choose(engine, equity):
        return engine._preflop_decision_v2(
            hole_cards=weak_hand,
            position_name="SB",
            equity=equity,
            current_bet=5,
            min_raise=20,
            pot_size=15,
            player_chips=1000,
            opponents_in_hand=["AI-1", "AI-2"],
        )

    assert choose(station, 0.40) == ("call", 5)
    assert choose(nit, 0.40) == ("fold", 0)
    assert choose(station, 0.20) == ("fold", 0)


def test_calling_station_prefers_call_to_reraise_with_strong_postflop_equity(monkeypatch):
    station = AdvancedAIEngine("AI-station", archetype_name="calling_station")
    tag = AdvancedAIEngine("AI-tag", archetype_name="tight_aggressive")
    monkeypatch.setattr(
        "texas_holdem.ai.advanced_ai_engine.MixedStrategyDecider.should_reraise_strong",
        lambda equity: True,
    )

    def choose(engine, equity):
        return engine._handle_facing_bet_scenario(
            equity=equity,
            raw_strength=0.8,
            has_position=True,
            has_draw=False,
            current_bet=50,
            pot_size=100,
            player_chips=1000,
            min_raise=100,
            board_texture={"danger_level": 2},
            opponents_in_hand=["Villain"],
            phase="turn",
            table_current_bet=50,
        )

    assert choose(station, 0.80) == ("call", 50)
    assert choose(tag, 0.80)[0] == "raise"


def test_calling_station_calls_medium_strong_postflop_hand(monkeypatch):
    station = AdvancedAIEngine("AI-station", archetype_name="calling_station")
    monkeypatch.setattr("texas_holdem.ai.advanced_ai_engine.random.random", lambda: 0.0)

    action, amount = station._handle_facing_bet_scenario(
        equity=0.65,
        raw_strength=0.65,
        has_position=True,
        has_draw=False,
        current_bet=40,
        pot_size=100,
        player_chips=1000,
        min_raise=80,
        board_texture={"danger_level": 2},
        opponents_in_hand=["Villain"],
        phase="turn",
    )

    assert (action, amount) == ("call", 40)


def test_calling_station_folds_postflop_air_when_equity_clearly_below_pot_odds(monkeypatch):
    engine = AdvancedAIEngine("AI-station", archetype_name="calling_station")
    monkeypatch.setattr("texas_holdem.ai.advanced_ai_engine.random.random", lambda: 0.99)

    action, amount = engine._handle_facing_bet_scenario(
        equity=0.08,
        raw_strength=0.05,
        has_position=False,
        has_draw=False,
        current_bet=50,
        pot_size=100,
        player_chips=1000,
        min_raise=150,
        board_texture={"danger_level": 2},
        opponents_in_hand=["Villain-1", "Villain-2"],
        phase="flop",
        table_current_bet=50,
        player_current_bet=0,
        action_history=[
            {"phase": "preflop", "player_name": "Villain-1", "action": "raise"},
            {"phase": "flop", "player_name": "Villain-1", "action": "raise"},
        ],
    )

    assert (action, amount) == ("fold", 0)


def test_calling_station_folds_nonpremium_preflop_raise_when_equity_negative_price(monkeypatch):
    engine = AdvancedAIEngine("AI-station", archetype_name="calling_station")
    medium_pair = [Card(Suit.CLUBS, Rank.SIX), Card(Suit.DIAMONDS, Rank.SIX)]
    monkeypatch.setattr("texas_holdem.ai.advanced_ai_engine.random.random", lambda: 0.0)

    action, amount = engine._preflop_decision_v2(
        hole_cards=medium_pair,
        position_name="BB",
        equity=0.20,
        current_bet=22,
        min_raise=44,
        pot_size=42,
        player_chips=1000,
        opponents_in_hand=["AI-1", "AI-2"],
    )

    assert (action, amount) == ("fold", 0)


def test_calling_station_checks_medium_equity_showdown_value(monkeypatch):
    station = AdvancedAIEngine("AI-station", archetype_name="calling_station")
    tag = AdvancedAIEngine("AI-tag", archetype_name="tight_aggressive")
    monkeypatch.setattr("texas_holdem.ai.advanced_ai_engine.random.random", lambda: 0.0)

    monkeypatch.setattr(
        "texas_holdem.ai.advanced_ai_engine.MixedStrategyDecider.get_marginal_action",
        lambda: "thin_value",
    )

    def choose(engine, equity=0.50, phase="turn", history=None):
        return engine._handle_no_bet_scenario(
            equity=equity,
            raw_strength=0.45,
            has_position=True,
            has_draw=False,
            pot_size=100,
            player_chips=1000,
            min_raise=20,
            board_texture={"danger_level": 3},
            opponents_in_hand=["Villain"],
            phase=phase,
            action_history=history or [],
        )

    assert choose(station) == ("check", 0)
    assert choose(station, equity=0.60) == ("check", 0)
    assert choose(tag)[0] == "raise"
    assert choose(station, equity=0.80)[0] == "raise"
    assert choose(station, phase="flop", history=[
        {"phase": "preflop", "player_name": "AI-station", "action": "raise"},
    ])[0] == "raise"
