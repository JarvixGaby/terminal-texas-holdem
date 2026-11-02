"""Strong-hand short-stack decisions must survive the real action pipeline."""

import pytest

from texas_holdem.ai.action_validator import validate_action
from texas_holdem.ai.advanced_ai_engine import AdvancedAIEngine, advanced_ai_manager
from texas_holdem.ai.ai_profiles import list_archetype_names
from texas_holdem.ai.decision_provider import (
    BuiltInAIDecisionProvider, GameStateSnapshot, VisiblePlayerSnapshot,
)
from texas_holdem.ai.optimized_odds_calculator import AIEquityCalculator
from texas_holdem.engine.betting_rules import NoLimitBettingRules
from texas_holdem.engine.card import Card, Rank, Suit
from texas_holdem.engine.player import AIPlayer


def make_river_spot(monkeypatch, profile, chips, invested=0, royal=False):
    if royal:
        hand = [Card(Suit.HEARTS, Rank.ACE), Card(Suit.HEARTS, Rank.KING)]
        board = [Card(Suit.HEARTS, Rank.QUEEN), Card(Suit.HEARTS, Rank.JACK),
                 Card(Suit.HEARTS, Rank.TEN), Card(Suit.CLUBS, Rank.TWO),
                 Card(Suit.DIAMONDS, Rank.THREE)]
    else:
        hand = [Card(Suit.CLUBS, Rank.KING), Card(Suit.DIAMONDS, Rank.QUEEN)]
        board = [Card(Suit.HEARTS, Rank.KING), Card(Suit.DIAMONDS, Rank.NINE),
                 Card(Suit.HEARTS, Rank.SEVEN), Card(Suit.SPADES, Rank.FIVE),
                 Card(Suit.CLUBS, Rank.TWO)]
    ai = AIPlayer('Hero', chips, archetype_name=profile)
    ai.hand = hand
    engine = AdvancedAIEngine('Hero', archetype_name=profile)
    monkeypatch.setattr(advanced_ai_manager, 'engines', {'Hero': engine})
    rules = NoLimitBettingRules(big_blind=10)
    snapshot = GameStateSnapshot(
        game_id='short-stack-test', hand_id='river-hand', phase='river',
        player_name='Hero', position=0,
        hole_cards=[str(card) for card in hand],
        community_cards=[str(card) for card in board],
        pot_size=300, current_bet=100, amount_to_call=100 - invested,
        player_chips=chips,
        visible_players=[
            VisiblePlayerSnapshot('Hero', chips, invested, False, False, 0),
            VisiblePlayerSnapshot('Villain', 1000, 100, False, False, 1),
        ],
        action_history=[{'phase': 'river', 'player_name': 'Villain',
                         'action': 'raise', 'amount': 100}],
        legal_actions=rules.legal_actions(100 - invested, 100, invested, chips, 100),
        min_raise=rules.minimum_raise_total(100, 100),
        dealer_position=0, small_blind=5, big_blind=10,
    )
    return engine, snapshot, BuiltInAIDecisionProvider(ai, lambda: board), hand, board


def assert_live_action(provider, snapshot, action, amount):
    response = provider.decide(snapshot)
    assert response.error is None
    assert not response.metadata.get('fallback')
    assert response.metadata['ai_explanation']['source'] == 'AdvancedAIEngine'
    assert response.raw_response == (action, amount)
    validated = validate_action(snapshot, response)
    assert validated.is_valid, validated.reason
    assert (validated.action, validated.amount) == (action, amount)


@pytest.mark.parametrize('profile', list_archetype_names())
@pytest.mark.parametrize('equity', [.60, .75], ids=['strong', 'very-strong'])
@pytest.mark.parametrize('roll', [0.0, .99], ids=['raise-roll', 'call-roll'])
@pytest.mark.parametrize('invested,chips,expected_call', [
    (0, 50, 50), (0, 100, 100), (40, 50, 50), (40, 60, 60),
])
def test_strong_hand_calls_when_remaining_stack_cannot_raise(
    monkeypatch, profile, equity, roll, invested, chips, expected_call,
):
    engine, snapshot, provider, _, _ = make_river_spot(monkeypatch, profile, chips, invested)
    monkeypatch.setattr(engine, '_get_monte_carlo_equity', lambda *args: equity)
    monkeypatch.setattr('random.random', lambda: roll)
    assert snapshot.legal_actions == ['call', 'fold']
    assert_live_action(provider, snapshot, 'call', expected_call)


@pytest.mark.parametrize('roll', [0.0, .99])
def test_royal_flush_uses_real_equity_and_calls_short_all_in(monkeypatch, roll):
    engine, snapshot, provider, hand, board = make_river_spot(
        monkeypatch, 'tight_aggressive', 50, royal=True,
    )
    # Every sampled opponent loses on this completed board; no equity stub.
    calculator = AIEquityCalculator(simulation_count=32)
    engine._equity_calculator = calculator
    monkeypatch.setattr('random.random', lambda: roll)
    assert_live_action(provider, snapshot, 'call', 50)
    assert calculator.get_equity(hand, board, 1) == 1.0


@pytest.mark.parametrize('equity', [.60, .75])
def test_one_chip_above_table_wager_remains_legal_short_all_in_raise(monkeypatch, equity):
    engine, snapshot, provider, _, _ = make_river_spot(
        monkeypatch, 'tight_aggressive', 61, invested=40,
    )
    monkeypatch.setattr(engine, '_get_monte_carlo_equity', lambda *args: equity)
    monkeypatch.setattr('random.random', lambda: 0)
    assert 'raise' in snapshot.legal_actions
    assert_live_action(provider, snapshot, 'raise', 101)


@pytest.mark.parametrize('profile', list_archetype_names())
def test_weak_short_stack_is_not_forced_to_call_all_in(monkeypatch, profile):
    engine, snapshot, provider, _, _ = make_river_spot(monkeypatch, profile, 50)
    monkeypatch.setattr(engine, '_get_monte_carlo_equity', lambda *args: .10)
    monkeypatch.setattr('random.random', lambda: .99)
    assert_live_action(provider, snapshot, 'fold', 0)


@pytest.mark.parametrize('equity', [.60, .75])
def test_strong_hand_with_chips_behind_calls_only_the_price(monkeypatch, equity):
    engine, snapshot, provider, _, _ = make_river_spot(monkeypatch, 'nit', 250)
    monkeypatch.setattr(engine, '_get_monte_carlo_equity', lambda *args: equity)
    monkeypatch.setattr('random.random', lambda: .99)
    assert_live_action(provider, snapshot, 'call', 100)


@pytest.mark.parametrize('equity', [.60, .75])
def test_empty_stack_does_not_emit_a_zero_chip_call(monkeypatch, equity):
    engine, snapshot, provider, _, _ = make_river_spot(monkeypatch, 'nit', 0)
    monkeypatch.setattr(engine, '_get_monte_carlo_equity', lambda *args: equity)
    monkeypatch.setattr('random.random', lambda: 0)
    assert_live_action(provider, snapshot, 'fold', 0)
