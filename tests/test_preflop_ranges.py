from dataclasses import replace

import pytest

from texas_holdem.ai.advanced_ai_engine import AdvancedAIEngine, PositionRangeManager
from texas_holdem.ai.ai_profiles import ARCHETYPE_PROFILES, get_archetype_profile
from texas_holdem.ai.preflop_ranges import PREFLOP_RANGES, get_preflop_range
from texas_holdem.engine.card import Card, Rank, Suit


def test_range_tables_cover_profiles_positions_and_valid_hands():
    ranks = '23456789TJQKA'
    valid = {a + b + suffix for i, a in enumerate(ranks) for b in ranks[:i + 1]
             for suffix in ([''] if a == b else ['s', 'o'])}
    assert len(valid) == 169
    assert set(PREFLOP_RANGES) == set(ARCHETYPE_PROFILES)
    for positions in PREFLOP_RANGES.values():
        assert set(positions) == {'UTG', 'UTG+1', 'UTG+2', 'MP', 'LJ', 'HJ', 'CO', 'BTN', 'SB', 'BB'}
        for ranges in positions.values():
            assert set(ranges) == {'enter', 'raise', 'call_raise', 'three_bet'}
            for hands in ranges.values():
                assert hands <= valid
                assert {'AA', 'KK', 'AKs'} <= hands
            assert ranges['raise'] <= ranges['enter']


def test_range_style_position_and_suitedness():
    nit = PREFLOP_RANGES['nit']
    lag = PREFLOP_RANGES['loose_aggressive']
    assert '76s' not in nit['BTN']['enter']
    assert '76s' in lag['BTN']['enter']
    assert '76o' not in lag['BTN']['enter']
    for positions in PREFLOP_RANGES.values():
        assert positions['UTG']['enter'] <= positions['BTN']['enter']
    hand = [Card(Suit.CLUBS, Rank.SIX), Card(Suit.CLUBS, Rank.SEVEN)]
    assert PositionRangeManager.hand_to_notation(hand) == '76s'


def test_custom_profile_falls_back_and_tables_are_immutable():
    profile = get_archetype_profile('nit')
    assert get_preflop_range(replace(profile, vpip_target=.5), 'BTN') is None
    assert get_preflop_range(profile, 'unknown') == PREFLOP_RANGES['nit']['MP']
    with pytest.raises(TypeError):
        PREFLOP_RANGES['nit']['BTN']['enter'] = frozenset()


@pytest.mark.parametrize('name', list(ARCHETYPE_PROFILES))
def test_trash_folds_for_price_but_checks_for_free(name):
    engine = AdvancedAIEngine('Bot', archetype_name=name)
    hand = [Card(Suit.CLUBS, Rank.SEVEN), Card(Suit.HEARTS, Rank.TWO)]
    kwargs = dict(hole_cards=hand, position_name='UTG', equity=.1,
                  min_raise=20, pot_size=15, player_chips=1000)
    assert engine._profiled_preflop_decision(current_bet=10, **kwargs) == ('fold', 0)
    assert engine._profiled_preflop_decision(current_bet=0, **kwargs) == ('check', 0)


def test_engine_reads_table_membership(monkeypatch):
    engine = AdvancedAIEngine('Bot', archetype_name='nit')
    monkeypatch.setattr('texas_holdem.ai.advanced_ai_engine.get_preflop_range',
                        lambda *args: {'enter': {'72o'}, 'raise': {'72o'}})
    monkeypatch.setattr('random.random', lambda: 0)
    hand = [Card(Suit.CLUBS, Rank.SEVEN), Card(Suit.HEARTS, Rank.TWO)]
    assert engine._profiled_preflop_decision(
        hand, 'UTG', .5, 10, 20, 15, 1000)[0] == 'raise'


@pytest.mark.parametrize('draw', [False, True])
def test_bluff_action_depends_on_style_and_public_context(monkeypatch, draw):
    monkeypatch.setattr('random.random', lambda: .15)
    def action(name, position=True, opponents=('Villain',), danger=0):
        engine = AdvancedAIEngine('Bot', archetype_name=name)
        return engine._handle_no_bet_scenario(
            .20, .1, position, draw, 100, 1000, 20,
            {'danger_level': danger}, list(opponents), 'turn', [])[0]
    assert action('nit') == 'check'
    assert action('calling_station') == 'check'
    assert action('maniac') == 'raise'
    assert action('maniac', opponents=('A', 'B', 'C'), danger=6) == 'check'
    if not draw:
        assert action('maniac', position=False) == 'check'
