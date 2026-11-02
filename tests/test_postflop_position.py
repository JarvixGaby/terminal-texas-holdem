"""Exercise relative position through the real provider/player/engine chain."""

import pytest

from texas_holdem.ai.advanced_ai_engine import AdvancedAIEngine, advanced_ai_manager
from texas_holdem.ai.decision_provider import (
    BuiltInAIDecisionProvider, GameStateSnapshot, VisiblePlayerSnapshot,
)
from texas_holdem.engine.card import Card, Rank, Suit
from texas_holdem.engine.player import AIPlayer


def cards_for_pressure(draw):
    hand = [Card(Suit.HEARTS, Rank.SEVEN), Card(Suit.HEARTS, Rank.TWO)]
    board = [Card(Suit.HEARTS, Rank.ACE), Card(Suit.HEARTS, Rank.KING),
             Card(Suit.CLUBS, Rank.NINE), Card(Suit.DIAMONDS, Rank.FIVE)]
    if not draw:
        board.append(Card(Suit.DIAMONDS, Rank.THREE))
    return hand, board


@pytest.mark.parametrize('count,dealer,hero,folded,all_in,in_position', [
    pytest.param(6, 3, 3, {0, 1, 2, 5}, set(), True, id='button-vs-small-blind'),
    pytest.param(6, 3, 2, {0, 1, 4, 5}, set(), False, id='cutoff-vs-button'),
    pytest.param(6, 3, 0, {1, 2, 3, 5}, set(), True, id='early-seat-last-after-folds'),
    pytest.param(2, 1, 1, set(), set(), True, id='heads-up-button-small-blind'),
    pytest.param(2, 1, 0, set(), set(), False, id='heads-up-big-blind'),
    pytest.param(6, 3, 2, {0, 1, 5}, {3}, True, id='all-in-button-does-not-act'),
    pytest.param(4, 0, 0, {2, 3}, {1}, False, id='only-all-in-opponent'),
    pytest.param(4, 0, 0, {1, 2, 3}, set(), False, id='no-remaining-opponent'),
])
@pytest.mark.parametrize('draw', [False, True], ids=['pure-bluff', 'semi-bluff'])
@pytest.mark.parametrize('profile', ['maniac', 'nit'])
def test_public_seats_drive_live_pressure_actions(
    monkeypatch, count, dealer, hero, folded, all_in, in_position, draw, profile,
):
    hand, board = cards_for_pressure(draw)
    ai = AIPlayer('Hero', 1000, archetype_name=profile)
    ai.hand = hand
    engine = AdvancedAIEngine('Hero', archetype_name=profile)
    monkeypatch.setattr(advanced_ai_manager, 'engines', {'Hero': engine})
    equity_opponents = []

    def fixed_equity(hole_cards, community_cards, num_opponents):
        equity_opponents.append(num_opponents)
        return .2

    monkeypatch.setattr(engine, '_get_monte_carlo_equity', fixed_equity)
    opponents_in_hand = count - 1 - len(folded)
    has_actionable_opponent = bool(set(range(count)) - {hero} - folded - all_in)
    # Between the maniac's in-position and out-of-position semi-bluff rates,
    # and above either nit rate. All-in players still dilute multiway pressure.
    roll = (.48 if draw else .2) / max(1, opponents_in_hand)
    if not has_actionable_opponent:
        # Even a draw and a low random roll must not pressure all-in players.
        roll = .01
    monkeypatch.setattr('random.random', lambda: roll)
    seats = [
        VisiblePlayerSnapshot(
            'Hero' if seat == hero else f'P{seat}',
            0 if seat in all_in else 1000, 0,
            seat in folded, seat in all_in, seat,
        )
        for seat in range(count)
    ]
    snapshot = GameStateSnapshot(
        game_id='position-test', hand_id='position-hand',
        phase='turn' if draw else 'river', player_name='Hero', position=hero,
        hole_cards=[str(card) for card in hand],
        community_cards=[str(card) for card in board],
        pot_size=100, current_bet=0, amount_to_call=0, player_chips=1000,
        visible_players=seats, action_history=[], legal_actions=['check', 'raise'],
        min_raise=10, dealer_position=dealer, small_blind=5, big_blind=10,
    )
    response = BuiltInAIDecisionProvider(ai, lambda: board).decide(snapshot)

    assert response.error is None
    assert not response.metadata.get('fallback')
    assert response.metadata['ai_explanation']['source'] == 'AdvancedAIEngine'
    assert response.raw_response == (response.action, response.amount)
    assert response.action == ('raise' if in_position and profile == 'maniac' else 'check')
    assert equity_opponents == [max(1, opponents_in_hand)]
    if draw and profile == 'maniac' and not in_position and has_actionable_opponent:
        # Being out of position discounts semi-bluffs rather than disabling them.
        monkeypatch.setattr('random.random', lambda: .3 / opponents_in_hand)
        response = BuiltInAIDecisionProvider(ai, lambda: board).decide(snapshot)
        assert response.error is None
        assert response.metadata['ai_explanation']['source'] == 'AdvancedAIEngine'
        assert response.action == 'raise'


@pytest.mark.parametrize('count,seat,opponents,expected', [
    (6, 5, ['Villain'], 'raise'),
    (6, 4, ['Villain'], 'check'),
    (2, 0, ['Villain'], 'raise'),
    (2, 1, ['Villain'], 'check'),
    (6, 5, [], 'check'),
])
def test_direct_engine_without_public_seats_uses_conservative_button_fallback(
    monkeypatch, count, seat, opponents, expected,
):
    engine = AdvancedAIEngine('Hero', archetype_name='maniac')
    hand, board = cards_for_pressure(False)
    monkeypatch.setattr(engine, '_get_monte_carlo_equity', lambda *args: .2)
    monkeypatch.setattr('random.random', lambda: .2)
    action, _ = engine.make_decision(
        hand, board, 0, 10, 100, 1000, seat, count, opponents,
    )
    assert action == expected


def test_position_context_does_not_change_standard_ai_call(monkeypatch):
    ai = AIPlayer('Hero', 1000)
    ai.ai_mode = 'standard'
    calls = []

    def standard(current_bet, min_raise, pot_size, community_cards,
                 position, total_players, opponents_in_hand):
        calls.append((position, total_players, opponents_in_hand))
        return 'check', 0

    monkeypatch.setattr(ai, '_standard_decision', standard)
    assert ai.make_decision(
        0, 10, 100, position=2, total_players=4, opponents_in_hand=['Villain'],
        postflop_in_position=True, has_actionable_opponent=True,
    ) == ('check', 0)
    assert calls == [(2, 4, ['Villain'])]


@pytest.mark.parametrize('draw', [False, True])
def test_no_actionable_opponent_also_blocks_weak_flop_cbet(monkeypatch, draw):
    hand, board = cards_for_pressure(True)
    if not draw:
        hand = [Card(Suit.SPADES, Rank.SEVEN), Card(Suit.DIAMONDS, Rank.TWO)]
    board = board[:3]
    ai = AIPlayer('Hero', 1000, archetype_name='maniac')
    ai.hand = hand
    engine = AdvancedAIEngine('Hero', archetype_name='maniac')
    monkeypatch.setattr(advanced_ai_manager, 'engines', {'Hero': engine})
    monkeypatch.setattr(engine, '_get_monte_carlo_equity', lambda *args: .2)
    monkeypatch.setattr('random.random', lambda: 0)
    snapshot = GameStateSnapshot(
        game_id='position-test', hand_id='cbet-hand', phase='flop',
        player_name='Hero', position=0,
        hole_cards=[str(card) for card in hand], community_cards=[str(card) for card in board],
        pot_size=100, current_bet=0, amount_to_call=0, player_chips=1000,
        visible_players=[
            VisiblePlayerSnapshot('Hero', 1000, 0, False, False, 0),
            VisiblePlayerSnapshot('Villain', 0, 0, False, True, 1),
        ],
        action_history=[{'phase': 'preflop', 'player_name': 'Hero', 'action': 'raise', 'amount': 50}],
        legal_actions=['check', 'raise'], min_raise=10,
        dealer_position=0, small_blind=5, big_blind=10,
    )
    response = BuiltInAIDecisionProvider(ai, lambda: board).decide(snapshot)
    assert response.error is None
    assert not response.metadata.get('fallback')
    assert response.metadata['ai_explanation']['source'] == 'AdvancedAIEngine'
    assert response.action == 'check'
