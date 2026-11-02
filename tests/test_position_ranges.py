import pytest

from texas_holdem.ai.advanced_ai_engine import AdvancedAIEngine, PositionRangeManager
from texas_holdem.ai.positions import range_position, seat_names
from texas_holdem.ai.preflop_ranges import PREFLOP_RANGES
from texas_holdem.engine.card import Card, Rank, Suit


@pytest.mark.parametrize('count,expected', [
    (2, 'BTN BB'), (3, 'SB BB BTN'), (4, 'SB BB CO BTN'),
    (5, 'SB BB HJ CO BTN'), (6, 'SB BB UTG HJ CO BTN'),
    (7, 'SB BB UTG LJ HJ CO BTN'), (8, 'SB BB UTG MP LJ HJ CO BTN'),
    (9, 'SB BB UTG UTG+1 MP LJ HJ CO BTN'),
    (10, 'SB BB UTG UTG+1 UTG+2 MP LJ HJ CO BTN'),
])
def test_all_seats_map_in_actual_order(count, expected):
    assert [PositionRangeManager.get_position_name(i, count)
            for i in range(count)] == expected.split()


def test_short_table_utg_uses_fewer_players_behind():
    assert range_position('UTG', 6) == 'LJ'
    assert range_position('UTG', 8) == 'UTG+2'
    assert range_position('UTG', 10) == 'UTG'
    for tables in PREFLOP_RANGES.values():
        assert tables['UTG']['enter'] <= tables['LJ']['enter']
    assert PREFLOP_RANGES['nit']['UTG']['enter'] < PREFLOP_RANGES['nit']['LJ']['enter']


@pytest.mark.parametrize('count', range(4, 11))
def test_ranges_widen_toward_button(count):
    roles = [range_position(p, count) for p in seat_names(count)[2:]]
    for tables in PREFLOP_RANGES.values():
        for first, second in zip(roles, roles[1:]):
            for action in ('enter', 'raise', 'call_raise', 'three_bet'):
                assert tables[first][action] <= tables[second][action]


def test_live_engine_passes_table_size_to_range_lookup(monkeypatch):
    engine = AdvancedAIEngine('Bot', archetype_name='nit')
    seen = []
    from texas_holdem.ai.preflop_ranges import get_preflop_range
    def lookup(profile, role):
        seen.append(role)
        return get_preflop_range(profile, role)
    monkeypatch.setattr('texas_holdem.ai.advanced_ai_engine.get_preflop_range', lookup)
    monkeypatch.setattr(engine, '_get_monte_carlo_equity', lambda *args, **kwargs: .5)
    hand = [Card(Suit.CLUBS, Rank.SEVEN), Card(Suit.HEARTS, Rank.TWO)]
    for count in (6, 10):
        engine.make_decision(hand, [], 15, 10, 20, 1000, 2, count,
                             [f'P{i}' for i in range(count - 1)])
    assert seen == ['LJ', 'UTG']


def test_extra_large_custom_table_has_unique_positions():
    names = seat_names(11)
    assert len(names) == len(set(names)) == 11
    assert range_position('UTG+3', 11) == 'UTG+2'
