from dataclasses import dataclass, field
import json
import random

import pytest

from texas_holdem.ai.action_validator import validate_action
from texas_holdem.ai.advanced_ai_engine import ActionLine, AdvancedAIEngine, BetSizingEngine
from texas_holdem.engine.card import Card, Rank, Suit
from texas_holdem.ai.decision_provider import ActionResponse, GameStateSnapshot, VisiblePlayerSnapshot


@dataclass(frozen=True)
class AIScenario:
    name: str
    hole_cards: list[Card]
    community_cards: list[Card]
    phase: str
    amount_to_call: int
    min_raise: int
    pot_size: int
    player_chips: int = 1000
    position: int = 3
    total_players: int = 4
    visible_current_bet: int = 0
    acting_current_bet: int = 0
    action_history: list[dict] = field(default_factory=list)
    seed: int = 0

    @property
    def legal_actions(self) -> list[str]:
        if self.amount_to_call == 0:
            return ["check", "raise", "fold"]
        return ["fold", "call", "raise"]


WEAK_PREFLOP_FREE_CHECK = AIScenario(
    name="weak preflop free check",
    hole_cards=[Card(Suit.CLUBS, Rank.TWO), Card(Suit.DIAMONDS, Rank.SEVEN)],
    community_cards=[],
    phase="preflop",
    amount_to_call=0,
    min_raise=20,
    pot_size=30,
    position=1,
)

WEAK_FLOP_FREE_CHECK = AIScenario(
    name="weak flop free check",
    hole_cards=[Card(Suit.CLUBS, Rank.TWO), Card(Suit.DIAMONDS, Rank.SEVEN)],
    community_cards=[
        Card(Suit.HEARTS, Rank.ACE),
        Card(Suit.SPADES, Rank.KING),
        Card(Suit.CLUBS, Rank.NINE),
    ],
    phase="flop",
    amount_to_call=0,
    min_raise=20,
    pot_size=60,
)

WEAK_TURN_FREE_CHECK = AIScenario(
    name="weak turn free check",
    hole_cards=[Card(Suit.CLUBS, Rank.TWO), Card(Suit.DIAMONDS, Rank.SEVEN)],
    community_cards=[
        Card(Suit.HEARTS, Rank.ACE),
        Card(Suit.SPADES, Rank.KING),
        Card(Suit.CLUBS, Rank.NINE),
        Card(Suit.DIAMONDS, Rank.QUEEN),
    ],
    phase="turn",
    amount_to_call=0,
    min_raise=20,
    pot_size=90,
    seed=1,
)

WEAK_RIVER_FREE_CHECK = AIScenario(
    name="weak river free check",
    hole_cards=[Card(Suit.CLUBS, Rank.TWO), Card(Suit.DIAMONDS, Rank.SEVEN)],
    community_cards=[
        Card(Suit.HEARTS, Rank.ACE),
        Card(Suit.SPADES, Rank.KING),
        Card(Suit.CLUBS, Rank.NINE),
        Card(Suit.DIAMONDS, Rank.QUEEN),
        Card(Suit.HEARTS, Rank.FIVE),
    ],
    phase="river",
    amount_to_call=0,
    min_raise=20,
    pot_size=120,
    seed=2,
)

PREMIUM_PREFLOP_OPEN = AIScenario(
    name="premium preflop open",
    hole_cards=[Card(Suit.SPADES, Rank.ACE), Card(Suit.HEARTS, Rank.ACE)],
    community_cards=[],
    phase="preflop",
    amount_to_call=0,
    min_raise=20,
    pot_size=15,
)

KINGS_PREFLOP_OPEN = AIScenario(
    name="kings preflop open",
    hole_cards=[Card(Suit.SPADES, Rank.KING), Card(Suit.HEARTS, Rank.KING)],
    community_cards=[],
    phase="preflop",
    amount_to_call=0,
    min_raise=20,
    pot_size=15,
)

QUEENS_PREFLOP_OPEN = AIScenario(
    name="queens preflop open",
    hole_cards=[Card(Suit.SPADES, Rank.QUEEN), Card(Suit.HEARTS, Rank.QUEEN)],
    community_cards=[],
    phase="preflop",
    amount_to_call=0,
    min_raise=20,
    pot_size=15,
)

ACE_KING_SUITED_SHORT_STACK_SMALL_RAISE = AIScenario(
    name="ace king suited short stack small raise",
    hole_cards=[Card(Suit.SPADES, Rank.ACE), Card(Suit.SPADES, Rank.KING)],
    community_cards=[],
    phase="preflop",
    amount_to_call=20,
    min_raise=20,
    pot_size=45,
    player_chips=15,
)

QUEENS_SHORT_STACK_SMALL_RAISE = AIScenario(
    name="queens short stack small raise",
    hole_cards=[Card(Suit.SPADES, Rank.QUEEN), Card(Suit.HEARTS, Rank.QUEEN)],
    community_cards=[],
    phase="preflop",
    amount_to_call=20,
    min_raise=20,
    pot_size=45,
    player_chips=15,
    seed=1,
)

STRONG_POSTFLOP_MIN_RAISE_BOUNDARY = AIScenario(
    name="strong postflop min raise boundary",
    hole_cards=[Card(Suit.SPADES, Rank.ACE), Card(Suit.HEARTS, Rank.ACE)],
    community_cards=[
        Card(Suit.CLUBS, Rank.ACE),
        Card(Suit.DIAMONDS, Rank.KING),
        Card(Suit.CLUBS, Rank.NINE),
    ],
    phase="flop",
    amount_to_call=0,
    min_raise=100,
    pot_size=60,
)

STRONG_FLOP_MADE_HAND = AIScenario(
    name="strong flop made hand",
    hole_cards=[Card(Suit.SPADES, Rank.ACE), Card(Suit.HEARTS, Rank.ACE)],
    community_cards=[
        Card(Suit.CLUBS, Rank.ACE),
        Card(Suit.DIAMONDS, Rank.KING),
        Card(Suit.CLUBS, Rank.NINE),
    ],
    phase="flop",
    amount_to_call=40,
    min_raise=120,
    pot_size=100,
    position=3,
    seed=3,
)

WEAK_FLOP_AIR_FACING_BET = AIScenario(
    name="weak flop air facing bet",
    hole_cards=[Card(Suit.SPADES, Rank.TWO), Card(Suit.HEARTS, Rank.SEVEN)],
    community_cards=[
        Card(Suit.CLUBS, Rank.ACE),
        Card(Suit.DIAMONDS, Rank.KING),
        Card(Suit.CLUBS, Rank.NINE),
    ],
    phase="flop",
    amount_to_call=40,
    min_raise=120,
    pot_size=100,
    position=0,
    seed=3,
)

FLOP_NUT_FLUSH_DRAW_FACING_BET = AIScenario(
    name="flop nut flush draw facing bet",
    hole_cards=[Card(Suit.CLUBS, Rank.ACE), Card(Suit.CLUBS, Rank.QUEEN)],
    community_cards=[
        Card(Suit.CLUBS, Rank.TWO),
        Card(Suit.CLUBS, Rank.SEVEN),
        Card(Suit.DIAMONDS, Rank.KING),
    ],
    phase="flop",
    amount_to_call=20,
    min_raise=60,
    pot_size=100,
    position=3,
    seed=2,
)

STRONG_FLOP_BUCKETED_RAISE = AIScenario(
    name="strong flop bucketed raise",
    hole_cards=[Card(Suit.SPADES, Rank.ACE), Card(Suit.HEARTS, Rank.ACE)],
    community_cards=[
        Card(Suit.CLUBS, Rank.ACE),
        Card(Suit.DIAMONDS, Rank.KING),
        Card(Suit.CLUBS, Rank.NINE),
    ],
    phase="flop",
    amount_to_call=40,
    min_raise=120,
    pot_size=200,
    player_chips=1000,
    position=3,
    visible_current_bet=40,
    seed=1,
)

STRONG_FLOP_BUCKETED_RAISE_AFTER_CALLING_STREET_BET = AIScenario(
    name="strong flop bucketed raise after calling street bet",
    hole_cards=[Card(Suit.SPADES, Rank.ACE), Card(Suit.HEARTS, Rank.ACE)],
    community_cards=[
        Card(Suit.CLUBS, Rank.ACE),
        Card(Suit.DIAMONDS, Rank.KING),
        Card(Suit.CLUBS, Rank.NINE),
    ],
    phase="flop",
    amount_to_call=60,
    min_raise=160,
    pot_size=200,
    player_chips=960,
    position=3,
    visible_current_bet=100,
    acting_current_bet=40,
    seed=1,
)

SCENARIOS = [
    WEAK_PREFLOP_FREE_CHECK,
    WEAK_FLOP_FREE_CHECK,
    WEAK_TURN_FREE_CHECK,
    WEAK_RIVER_FREE_CHECK,
    PREMIUM_PREFLOP_OPEN,
    KINGS_PREFLOP_OPEN,
    QUEENS_PREFLOP_OPEN,
    ACE_KING_SUITED_SHORT_STACK_SMALL_RAISE,
    QUEENS_SHORT_STACK_SMALL_RAISE,
    STRONG_POSTFLOP_MIN_RAISE_BOUNDARY,
    STRONG_FLOP_MADE_HAND,
    WEAK_FLOP_AIR_FACING_BET,
    FLOP_NUT_FLUSH_DRAW_FACING_BET,
    STRONG_FLOP_BUCKETED_RAISE,
]

POSTFLOP_FREE_CHECK_SCENARIOS = [
    WEAK_FLOP_FREE_CHECK,
    WEAK_TURN_FREE_CHECK,
    WEAK_RIVER_FREE_CHECK,
]

PREMIUM_NO_RAISE_OPEN_SCENARIOS = [
    PREMIUM_PREFLOP_OPEN,
    KINGS_PREFLOP_OPEN,
    QUEENS_PREFLOP_OPEN,
]

PREMIUM_SMALL_ACTION_SCENARIOS = [
    ACE_KING_SUITED_SHORT_STACK_SMALL_RAISE,
    QUEENS_SHORT_STACK_SMALL_RAISE,
]

ARCHETYPE_PREMIUM_GUARD_ARCHETYPES = [
    "nit",
    "tight_aggressive",
    "loose_aggressive",
    "calling_station",
    "maniac",
    "balanced",
]

ARCHETYPE_PREMIUM_PREFLOP_CONTEXTS = [
    AIScenario(
        name="archetype aces blind action",
        hole_cards=[Card(Suit.SPADES, Rank.ACE), Card(Suit.HEARTS, Rank.ACE)],
        community_cards=[],
        phase="preflop",
        amount_to_call=10,
        min_raise=20,
        pot_size=15,
        position=2,
    ),
    AIScenario(
        name="archetype aces facing raise",
        hole_cards=[Card(Suit.SPADES, Rank.ACE), Card(Suit.HEARTS, Rank.ACE)],
        community_cards=[],
        phase="preflop",
        amount_to_call=30,
        min_raise=60,
        pot_size=45,
        position=2,
    ),
]


def run_scenario(
    scenario: AIScenario,
    archetype_name: str | None = None,
) -> tuple[ActionResponse, GameStateSnapshot]:
    random.seed(scenario.seed)
    if archetype_name is None:
        engine = AdvancedAIEngine("AI")
    else:
        engine = AdvancedAIEngine("AI", archetype_name=archetype_name)
    action, amount = engine.make_decision(
        hole_cards=scenario.hole_cards,
        community_cards=scenario.community_cards,
        current_bet=scenario.amount_to_call,
        min_raise=scenario.min_raise,
        pot_size=scenario.pot_size,
        player_chips=scenario.player_chips,
        position=scenario.position,
        total_players=scenario.total_players,
        opponents_in_hand=["Villain-1", "Villain-2"],
        phase=scenario.phase,
        table_current_bet=scenario.visible_current_bet,
        player_current_bet=scenario.acting_current_bet,
        action_history=scenario.action_history,
    )
    response = ActionResponse(action=action, amount=amount)
    snapshot = GameStateSnapshot(
        game_id="scenario",
        hand_id=scenario.name,
        phase=scenario.phase,
        player_name="AI",
        position=scenario.position,
        hole_cards=[str(card) for card in scenario.hole_cards],
        community_cards=[str(card) for card in scenario.community_cards],
        pot_size=scenario.pot_size,
        current_bet=scenario.visible_current_bet,
        amount_to_call=scenario.amount_to_call,
        player_chips=scenario.player_chips,
        visible_players=[
            VisiblePlayerSnapshot(
                "AI",
                scenario.player_chips,
                scenario.acting_current_bet,
                False,
                False,
                scenario.position,
            ),
            VisiblePlayerSnapshot("Villain-1", 1000, scenario.visible_current_bet, False, False, 0),
            VisiblePlayerSnapshot("Villain-2", 1000, scenario.visible_current_bet, False, False, 1),
        ],
        action_history=list(scenario.action_history),
        legal_actions=scenario.legal_actions,
        min_raise=scenario.min_raise,
        dealer_position=0,
        small_blind=5,
        big_blind=10,
    )
    return response, snapshot


ARCHETYPE_PREFLOP_BATCH = [
    AIScenario(
        name="batch aces open",
        hole_cards=[Card(Suit.SPADES, Rank.ACE), Card(Suit.HEARTS, Rank.ACE)],
        community_cards=[],
        phase="preflop",
        amount_to_call=10,
        min_raise=20,
        pot_size=15,
        position=1,
    ),
    AIScenario(
        name="batch ace king suited open",
        hole_cards=[Card(Suit.SPADES, Rank.ACE), Card(Suit.SPADES, Rank.KING)],
        community_cards=[],
        phase="preflop",
        amount_to_call=10,
        min_raise=20,
        pot_size=15,
        position=2,
    ),
    AIScenario(
        name="batch ace queen offsuit open",
        hole_cards=[Card(Suit.SPADES, Rank.ACE), Card(Suit.HEARTS, Rank.QUEEN)],
        community_cards=[],
        phase="preflop",
        amount_to_call=10,
        min_raise=20,
        pot_size=15,
        position=3,
    ),
    AIScenario(
        name="batch king queen suited open",
        hole_cards=[Card(Suit.CLUBS, Rank.KING), Card(Suit.CLUBS, Rank.QUEEN)],
        community_cards=[],
        phase="preflop",
        amount_to_call=10,
        min_raise=20,
        pot_size=15,
        position=3,
    ),
    AIScenario(
        name="batch jack ten suited open",
        hole_cards=[Card(Suit.DIAMONDS, Rank.JACK), Card(Suit.DIAMONDS, Rank.TEN)],
        community_cards=[],
        phase="preflop",
        amount_to_call=10,
        min_raise=20,
        pot_size=15,
        position=3,
    ),
    AIScenario(
        name="batch pair eights open",
        hole_cards=[Card(Suit.SPADES, Rank.EIGHT), Card(Suit.HEARTS, Rank.EIGHT)],
        community_cards=[],
        phase="preflop",
        amount_to_call=10,
        min_raise=20,
        pot_size=15,
        position=2,
    ),
    AIScenario(
        name="batch pair fives open",
        hole_cards=[Card(Suit.SPADES, Rank.FIVE), Card(Suit.HEARTS, Rank.FIVE)],
        community_cards=[],
        phase="preflop",
        amount_to_call=10,
        min_raise=20,
        pot_size=15,
        position=3,
    ),
    AIScenario(
        name="batch ace five suited open",
        hole_cards=[Card(Suit.SPADES, Rank.ACE), Card(Suit.SPADES, Rank.FIVE)],
        community_cards=[],
        phase="preflop",
        amount_to_call=10,
        min_raise=20,
        pot_size=15,
        position=3,
    ),
    AIScenario(
        name="batch seven six suited open",
        hole_cards=[Card(Suit.CLUBS, Rank.SEVEN), Card(Suit.CLUBS, Rank.SIX)],
        community_cards=[],
        phase="preflop",
        amount_to_call=10,
        min_raise=20,
        pot_size=15,
        position=3,
    ),
    AIScenario(
        name="batch queen nine suited open",
        hole_cards=[Card(Suit.HEARTS, Rank.QUEEN), Card(Suit.HEARTS, Rank.NINE)],
        community_cards=[],
        phase="preflop",
        amount_to_call=10,
        min_raise=20,
        pot_size=15,
        position=3,
    ),
    AIScenario(
        name="batch ace two offsuit open",
        hole_cards=[Card(Suit.SPADES, Rank.ACE), Card(Suit.HEARTS, Rank.TWO)],
        community_cards=[],
        phase="preflop",
        amount_to_call=10,
        min_raise=20,
        pot_size=15,
        position=3,
    ),
    AIScenario(
        name="batch seven two offsuit open",
        hole_cards=[Card(Suit.CLUBS, Rank.SEVEN), Card(Suit.DIAMONDS, Rank.TWO)],
        community_cards=[],
        phase="preflop",
        amount_to_call=10,
        min_raise=20,
        pot_size=15,
        position=1,
    ),
]

DRY_FLOP_CBET_OPPORTUNITY = AIScenario(
    name="dry flop cbet opportunity",
    hole_cards=[Card(Suit.SPADES, Rank.ACE), Card(Suit.HEARTS, Rank.QUEEN)],
    community_cards=[
        Card(Suit.CLUBS, Rank.KING),
        Card(Suit.DIAMONDS, Rank.SEVEN),
        Card(Suit.SPADES, Rank.TWO),
    ],
    phase="flop",
    amount_to_call=0,
    min_raise=20,
    pot_size=90,
    position=3,
    action_history=[
        {"phase": "preflop", "player_name": "AI", "action": "raise", "amount": 30},
        {"phase": "preflop", "player_name": "Villain-1", "action": "call", "amount": 30},
    ],
)

WEAK_AIR_FACING_CREDIBLE_CBET = AIScenario(
    name="weak air facing credible cbet",
    hole_cards=[Card(Suit.CLUBS, Rank.THREE), Card(Suit.DIAMONDS, Rank.EIGHT)],
    community_cards=[
        Card(Suit.SPADES, Rank.ACE),
        Card(Suit.HEARTS, Rank.SEVEN),
        Card(Suit.CLUBS, Rank.TWO),
    ],
    phase="flop",
    amount_to_call=45,
    min_raise=135,
    pot_size=90,
    position=1,
    visible_current_bet=45,
    action_history=[
        {"phase": "preflop", "player_name": "Villain-1", "action": "raise", "amount": 30},
        {"phase": "preflop", "player_name": "AI", "action": "call", "amount": 30},
        {"phase": "flop", "player_name": "Villain-1", "action": "raise", "amount": 45},
    ],
)

STRONG_MADE_HAND_FACING_CREDIBLE_CBET = AIScenario(
    name="strong made hand facing credible cbet",
    hole_cards=[Card(Suit.SPADES, Rank.ACE), Card(Suit.HEARTS, Rank.SEVEN)],
    community_cards=[
        Card(Suit.CLUBS, Rank.ACE),
        Card(Suit.DIAMONDS, Rank.SEVEN),
        Card(Suit.SPADES, Rank.TWO),
    ],
    phase="flop",
    amount_to_call=45,
    min_raise=135,
    pot_size=90,
    position=1,
    visible_current_bet=45,
    action_history=WEAK_AIR_FACING_CREDIBLE_CBET.action_history,
)

GOOD_DRAW_FACING_CREDIBLE_CBET = AIScenario(
    name="good draw facing credible cbet",
    hole_cards=[Card(Suit.CLUBS, Rank.ACE), Card(Suit.CLUBS, Rank.QUEEN)],
    community_cards=[
        Card(Suit.CLUBS, Rank.TWO),
        Card(Suit.CLUBS, Rank.SEVEN),
        Card(Suit.DIAMONDS, Rank.KING),
    ],
    phase="flop",
    amount_to_call=30,
    min_raise=90,
    pot_size=90,
    position=1,
    visible_current_bet=30,
    action_history=WEAK_AIR_FACING_CREDIBLE_CBET.action_history,
)


def collect_archetype_preflop_batch(archetype_name: str) -> dict[str, float]:
    counts = {"total": 0, "vpip": 0, "raises": 0, "calls": 0, "illegal": 0}
    for seed_offset in range(6):
        for index, scenario in enumerate(ARCHETYPE_PREFLOP_BATCH):
            scenario_with_seed = AIScenario(
                name=f"{scenario.name} seed {seed_offset}",
                hole_cards=scenario.hole_cards,
                community_cards=scenario.community_cards,
                phase=scenario.phase,
                amount_to_call=scenario.amount_to_call,
                min_raise=scenario.min_raise,
                pot_size=scenario.pot_size,
                player_chips=scenario.player_chips,
                position=scenario.position,
                total_players=scenario.total_players,
                visible_current_bet=scenario.visible_current_bet,
                seed=1000 + seed_offset * 100 + index,
            )
            response, snapshot = run_scenario(scenario_with_seed, archetype_name=archetype_name)
            result = validate_action(snapshot, response)

            counts["total"] += 1
            counts["illegal"] += 0 if result.is_valid else 1
            if response.action in {"call", "raise"}:
                counts["vpip"] += 1
            if response.action == "raise":
                counts["raises"] += 1
            if response.action == "call":
                counts["calls"] += 1

    total = counts["total"]
    return {
        "vpip": counts["vpip"] / total,
        "pfr": counts["raises"] / total,
        "call_rate": counts["calls"] / total,
        "illegal_actions": counts["illegal"],
    }


def collect_flop_actions(scenario: AIScenario, archetype_name: str, seeds: range) -> dict[str, int]:
    counts = {"total": 0, "checks": 0, "raises": 0, "folds": 0, "calls": 0, "illegal": 0}
    for seed in seeds:
        seeded_scenario = AIScenario(
            name=f"{scenario.name} seed {seed}",
            hole_cards=scenario.hole_cards,
            community_cards=scenario.community_cards,
            phase=scenario.phase,
            amount_to_call=scenario.amount_to_call,
            min_raise=scenario.min_raise,
            pot_size=scenario.pot_size,
            player_chips=scenario.player_chips,
            position=scenario.position,
            total_players=scenario.total_players,
            visible_current_bet=scenario.visible_current_bet,
            acting_current_bet=scenario.acting_current_bet,
            action_history=scenario.action_history,
            seed=seed,
        )
        response, snapshot = run_scenario(seeded_scenario, archetype_name=archetype_name)
        result = validate_action(snapshot, response)
        counts["total"] += 1
        counts["illegal"] += 0 if result.is_valid else 1
        if response.action == "check":
            counts["checks"] += 1
        elif response.action == "raise":
            counts["raises"] += 1
        elif response.action == "fold":
            counts["folds"] += 1
        elif response.action == "call":
            counts["calls"] += 1
    return counts


def test_preflop_weak_hand_with_no_call_required_checks_instead_of_folding():
    response, _ = run_scenario(WEAK_PREFLOP_FREE_CHECK)

    assert response.action == "check"
    assert response.amount == 0


@pytest.mark.parametrize(
    "scenario",
    POSTFLOP_FREE_CHECK_SCENARIOS,
    ids=[scenario.name for scenario in POSTFLOP_FREE_CHECK_SCENARIOS],
)
def test_postflop_no_bet_check_available_spots_never_fold(scenario):
    response, snapshot = run_scenario(scenario)
    result = validate_action(snapshot, response)

    assert response.action in {"check", "raise"}
    assert result.is_valid is True, result.reason


def test_premium_preflop_hand_does_not_open_fold():
    response, _ = run_scenario(PREMIUM_PREFLOP_OPEN)

    assert response.action != "fold"


@pytest.mark.parametrize(
    "scenario",
    PREMIUM_NO_RAISE_OPEN_SCENARIOS,
    ids=[scenario.name for scenario in PREMIUM_NO_RAISE_OPEN_SCENARIOS],
)
def test_premium_preflop_pairs_open_raise_when_raising_is_legal(scenario):
    response, snapshot = run_scenario(scenario)
    result = validate_action(snapshot, response)

    assert response.action == "raise"
    assert response.amount >= scenario.min_raise
    assert result.is_valid is True, result.reason


@pytest.mark.parametrize(
    "scenario",
    PREMIUM_SMALL_ACTION_SCENARIOS,
    ids=[scenario.name for scenario in PREMIUM_SMALL_ACTION_SCENARIOS],
)
def test_premium_preflop_hands_facing_small_action_do_not_fold(scenario):
    response, snapshot = run_scenario(scenario)
    result = validate_action(snapshot, response)

    assert response.action in {"call", "raise"}
    assert result.is_valid is True, result.reason


@pytest.mark.parametrize("archetype_name", ARCHETYPE_PREMIUM_GUARD_ARCHETYPES)
@pytest.mark.parametrize(
    "scenario",
    ARCHETYPE_PREMIUM_PREFLOP_CONTEXTS,
    ids=[scenario.name for scenario in ARCHETYPE_PREMIUM_PREFLOP_CONTEXTS],
)
def test_archetype_enabled_premium_preflop_hands_never_fold_common_spots(
    archetype_name,
    scenario,
):
    for seed in range(20):
        seeded_scenario = AIScenario(
            name=f"{scenario.name} seed {seed}",
            hole_cards=scenario.hole_cards,
            community_cards=scenario.community_cards,
            phase=scenario.phase,
            amount_to_call=scenario.amount_to_call,
            min_raise=scenario.min_raise,
            pot_size=scenario.pot_size,
            player_chips=scenario.player_chips,
            position=scenario.position,
            total_players=scenario.total_players,
            visible_current_bet=scenario.visible_current_bet,
            seed=seed,
        )
        response, snapshot = run_scenario(seeded_scenario, archetype_name=archetype_name)
        result = validate_action(snapshot, response)

        assert result.is_valid is True, result.reason
        if scenario.amount_to_call > 0:
            assert response.action in {"call", "raise"}, (
                archetype_name,
                scenario.name,
                seed,
                response,
            )
        else:
            assert response.action in {"check", "raise"}, (
                archetype_name,
                scenario.name,
                seed,
                response,
            )


def test_preflop_archetype_batches_have_distinct_legal_tendencies():
    nit = collect_archetype_preflop_batch("nit")
    tight_aggressive = collect_archetype_preflop_batch("tight_aggressive")
    loose_aggressive = collect_archetype_preflop_batch("loose_aggressive")
    calling_station = collect_archetype_preflop_batch("calling_station")
    maniac = collect_archetype_preflop_batch("maniac")

    assert nit["illegal_actions"] == 0
    assert tight_aggressive["illegal_actions"] == 0
    assert loose_aggressive["illegal_actions"] == 0
    assert calling_station["illegal_actions"] == 0
    assert maniac["illegal_actions"] == 0

    assert nit["vpip"] < tight_aggressive["vpip"]
    assert nit["vpip"] < loose_aggressive["vpip"]
    assert calling_station["call_rate"] > tight_aggressive["call_rate"]
    assert maniac["pfr"] > calling_station["pfr"]
    assert tight_aggressive["pfr"] > calling_station["pfr"]


def test_postflop_hand_strength_distinguishes_strong_flop_made_hand_from_air():
    engine = AdvancedAIEngine("AI-postflop-strength")

    strong_texture = engine._evaluate_hand_strength(
        STRONG_FLOP_MADE_HAND.hole_cards,
        STRONG_FLOP_MADE_HAND.community_cards,
        {"danger_level": 0, "paired": False},
    )
    weak_texture = engine._evaluate_hand_strength(
        WEAK_FLOP_AIR_FACING_BET.hole_cards,
        WEAK_FLOP_AIR_FACING_BET.community_cards,
        {"danger_level": 0, "paired": False},
    )

    assert strong_texture["category"] != "unknown"
    assert strong_texture["showdown_value"] is True
    assert strong_texture["raw_strength"] > weak_texture["raw_strength"]
    assert weak_texture["showdown_value"] is False


@pytest.mark.parametrize(
    "scenario,expected_actions",
    [
        (STRONG_FLOP_MADE_HAND, {"call", "raise"}),
        (WEAK_FLOP_AIR_FACING_BET, {"fold"}),
        (FLOP_NUT_FLUSH_DRAW_FACING_BET, {"call", "raise"}),
    ],
    ids=[
        STRONG_FLOP_MADE_HAND.name,
        WEAK_FLOP_AIR_FACING_BET.name,
        FLOP_NUT_FLUSH_DRAW_FACING_BET.name,
    ],
)
def test_postflop_policy_uses_made_hand_air_and_draw_strength_legally(
    scenario,
    expected_actions,
):
    response, snapshot = run_scenario(scenario)
    result = validate_action(snapshot, response)

    assert response.action in expected_actions
    assert result.is_valid is True, result.reason


def test_bet_sizing_engine_exposes_simple_named_buckets():
    assert set(BetSizingEngine.SIZING_BUCKETS) == {
        "small",
        "half-pot",
        "two-thirds-pot",
        "pot-ish",
        "all-in",
    }


@pytest.mark.parametrize(
    "action_line,expected_buckets",
    [
        (ActionLine.VALUE_BET, {"two-thirds-pot", "pot-ish"}),
        (ActionLine.THIN_VALUE, {"small", "half-pot"}),
        (ActionLine.SEMI_BLUFF, {"half-pot", "two-thirds-pot"}),
        (ActionLine.BLUFF, {"small", "half-pot"}),
    ],
)
def test_postflop_action_lines_map_to_plausible_sizing_buckets(
    action_line,
    expected_buckets,
):
    random.seed(18)

    amount = BetSizingEngine.calculate_bet_size(
        pot_size=300,
        player_chips=1000,
        action_line=action_line,
        board_texture={"danger_level": 3},
    )
    legal_bucket_amounts = {
        int(300 * BetSizingEngine.SIZING_BUCKETS[bucket])
        for bucket in expected_buckets
    }

    assert amount in legal_bucket_amounts


def test_postflop_facing_bet_raise_uses_legal_bucketed_total_amount():
    response, snapshot = run_scenario(STRONG_FLOP_BUCKETED_RAISE)
    result = validate_action(snapshot, response)

    assert response.action == "raise"
    assert result.is_valid is True, result.reason
    assert STRONG_FLOP_BUCKETED_RAISE.min_raise <= response.amount <= STRONG_FLOP_BUCKETED_RAISE.player_chips
    assert response.amount in {
        STRONG_FLOP_BUCKETED_RAISE.visible_current_bet
        + int(STRONG_FLOP_BUCKETED_RAISE.pot_size * BetSizingEngine.SIZING_BUCKETS["two-thirds-pot"]),
        STRONG_FLOP_BUCKETED_RAISE.visible_current_bet
        + int(STRONG_FLOP_BUCKETED_RAISE.pot_size * BetSizingEngine.SIZING_BUCKETS["pot-ish"]),
        STRONG_FLOP_BUCKETED_RAISE.player_chips,
    }


def test_postflop_facing_bet_raise_after_committed_chips_uses_target_total_semantics():
    response, snapshot = run_scenario(STRONG_FLOP_BUCKETED_RAISE_AFTER_CALLING_STREET_BET)
    result = validate_action(snapshot, response)

    bucket_target_totals = {
        snapshot.current_bet
        + int(
            STRONG_FLOP_BUCKETED_RAISE_AFTER_CALLING_STREET_BET.pot_size
            * BetSizingEngine.SIZING_BUCKETS["two-thirds-pot"]
        ),
        snapshot.current_bet
        + int(
            STRONG_FLOP_BUCKETED_RAISE_AFTER_CALLING_STREET_BET.pot_size
            * BetSizingEngine.SIZING_BUCKETS["pot-ish"]
        ),
    }
    amount_to_call_targets = {
        STRONG_FLOP_BUCKETED_RAISE_AFTER_CALLING_STREET_BET.amount_to_call
        + int(
            STRONG_FLOP_BUCKETED_RAISE_AFTER_CALLING_STREET_BET.pot_size
            * BetSizingEngine.SIZING_BUCKETS["two-thirds-pot"]
        ),
        STRONG_FLOP_BUCKETED_RAISE_AFTER_CALLING_STREET_BET.amount_to_call
        + int(
            STRONG_FLOP_BUCKETED_RAISE_AFTER_CALLING_STREET_BET.pot_size
            * BetSizingEngine.SIZING_BUCKETS["pot-ish"]
        ),
    }

    assert response.action == "raise"
    assert result.is_valid is True, result.reason
    assert response.amount in bucket_target_totals
    assert response.amount not in amount_to_call_targets


def test_tag_and_lag_preflop_aggressors_sometimes_cbet_dry_flops_but_not_always():
    tag = collect_flop_actions(DRY_FLOP_CBET_OPPORTUNITY, "tight_aggressive", range(40))
    lag = collect_flop_actions(DRY_FLOP_CBET_OPPORTUNITY, "loose_aggressive", range(40))

    assert tag["illegal"] == 0
    assert lag["illegal"] == 0
    assert 0 < tag["raises"] < tag["total"]
    assert 0 < lag["raises"] < lag["total"]


def test_calling_station_cbets_less_often_than_aggressive_profiles_on_same_dry_flop_batch():
    tag = collect_flop_actions(DRY_FLOP_CBET_OPPORTUNITY, "tight_aggressive", range(50))
    lag = collect_flop_actions(DRY_FLOP_CBET_OPPORTUNITY, "loose_aggressive", range(50))
    station = collect_flop_actions(DRY_FLOP_CBET_OPPORTUNITY, "calling_station", range(50))

    assert station["illegal"] == 0
    assert station["raises"] < tag["raises"]
    assert station["raises"] < lag["raises"]


def test_weak_defender_air_facing_credible_cbet_can_fold_by_profile_tendency():
    tag = collect_flop_actions(WEAK_AIR_FACING_CREDIBLE_CBET, "tight_aggressive", range(40))
    station = collect_flop_actions(WEAK_AIR_FACING_CREDIBLE_CBET, "calling_station", range(40))

    assert tag["illegal"] == 0
    assert station["illegal"] == 0
    assert tag["folds"] > 0
    assert station["folds"] < tag["folds"]


@pytest.mark.parametrize(
    "scenario",
    [
        STRONG_MADE_HAND_FACING_CREDIBLE_CBET,
        GOOD_DRAW_FACING_CREDIBLE_CBET,
    ],
    ids=[
        STRONG_MADE_HAND_FACING_CREDIBLE_CBET.name,
        GOOD_DRAW_FACING_CREDIBLE_CBET.name,
    ],
)
def test_strong_made_hands_and_good_draws_do_not_fold_to_credible_cbet(scenario):
    for archetype_name in ["nit", "tight_aggressive", "calling_station"]:
        actions = collect_flop_actions(scenario, archetype_name, range(20))

        assert actions["illegal"] == 0
        assert actions["folds"] == 0


def test_advanced_ai_engine_records_json_safe_cbet_explanation_without_changing_decision():
    action = None
    amount = None
    engine = None
    for seed in range(40):
        random.seed(seed)
        engine = AdvancedAIEngine("AI", archetype_name="tight_aggressive")
        action, amount = engine.make_decision(
            hole_cards=DRY_FLOP_CBET_OPPORTUNITY.hole_cards,
            community_cards=DRY_FLOP_CBET_OPPORTUNITY.community_cards,
            current_bet=DRY_FLOP_CBET_OPPORTUNITY.amount_to_call,
            min_raise=DRY_FLOP_CBET_OPPORTUNITY.min_raise,
            pot_size=DRY_FLOP_CBET_OPPORTUNITY.pot_size,
            player_chips=DRY_FLOP_CBET_OPPORTUNITY.player_chips,
            position=DRY_FLOP_CBET_OPPORTUNITY.position,
            total_players=DRY_FLOP_CBET_OPPORTUNITY.total_players,
            opponents_in_hand=["Villain-1", "Villain-2"],
            phase=DRY_FLOP_CBET_OPPORTUNITY.phase,
            table_current_bet=DRY_FLOP_CBET_OPPORTUNITY.visible_current_bet,
            player_current_bet=DRY_FLOP_CBET_OPPORTUNITY.acting_current_bet,
            action_history=DRY_FLOP_CBET_OPPORTUNITY.action_history,
        )
        if action == "raise":
            break

    assert engine is not None
    explanation = engine.last_decision_explanation
    serialized = json.dumps(explanation)

    assert action == "raise"
    assert amount > 0
    assert "c-bet" in explanation["tags"]
    assert explanation["factors"]["phase"] == "flop"
    assert "Card" not in serialized
    assert "deck" not in serialized.lower()
    assert "hole_cards" not in serialized.lower()
    assert "opponent_hole_cards" not in serialized.lower()


def test_advanced_ai_engine_records_fold_to_cbet_explanation_when_that_tendency_drives_fold():
    action = None
    amount = None
    engine = None
    for seed in range(40):
        random.seed(seed)
        engine = AdvancedAIEngine("AI", archetype_name="tight_aggressive")
        action, amount = engine.make_decision(
            hole_cards=WEAK_AIR_FACING_CREDIBLE_CBET.hole_cards,
            community_cards=WEAK_AIR_FACING_CREDIBLE_CBET.community_cards,
            current_bet=WEAK_AIR_FACING_CREDIBLE_CBET.amount_to_call,
            min_raise=WEAK_AIR_FACING_CREDIBLE_CBET.min_raise,
            pot_size=WEAK_AIR_FACING_CREDIBLE_CBET.pot_size,
            player_chips=WEAK_AIR_FACING_CREDIBLE_CBET.player_chips,
            position=WEAK_AIR_FACING_CREDIBLE_CBET.position,
            total_players=WEAK_AIR_FACING_CREDIBLE_CBET.total_players,
            opponents_in_hand=["Villain-1", "Villain-2"],
            phase=WEAK_AIR_FACING_CREDIBLE_CBET.phase,
            table_current_bet=WEAK_AIR_FACING_CREDIBLE_CBET.visible_current_bet,
            player_current_bet=WEAK_AIR_FACING_CREDIBLE_CBET.acting_current_bet,
            action_history=WEAK_AIR_FACING_CREDIBLE_CBET.action_history,
        )
        if action == "fold":
            break

    assert action == "fold"
    assert amount == 0
    assert engine is not None
    assert "fold-to-cbet" in engine.last_decision_explanation["tags"]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=[scenario.name for scenario in SCENARIOS])
def test_every_scenario_action_passes_action_validator_boundary(scenario):
    response, snapshot = run_scenario(scenario)

    result = validate_action(snapshot, response)

    assert result.is_valid is True, result.reason
