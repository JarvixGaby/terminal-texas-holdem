"""SB-relative seat names and full-ring range roles, independent of hand state."""

# Names are a display convention; range roles are based on seats before BTN.
_EARLY_SEATS = {
    2: (), 3: (), 4: ('CO',), 5: ('HJ', 'CO'),
    6: ('UTG', 'HJ', 'CO'),
    7: ('UTG', 'LJ', 'HJ', 'CO'),
    8: ('UTG', 'MP', 'LJ', 'HJ', 'CO'),
    9: ('UTG', 'UTG+1', 'MP', 'LJ', 'HJ', 'CO'),
    10: ('UTG', 'UTG+1', 'UTG+2', 'MP', 'LJ', 'HJ', 'CO'),
}
FULL_RING_ROLES = _EARLY_SEATS[10]
POSITION_BONUSES = {
    'UTG': -.05, 'UTG+1': -.035, 'UTG+2': -.02, 'MP': 0.0,
    'LJ': .015, 'HJ': .03, 'CO': .05, 'BTN': .08, 'SB': -.03, 'BB': .02,
}


def seat_names(total_players):
    if total_players < 2:
        raise ValueError('At least two players are required')
    if total_players == 2:
        return ('BTN', 'BB')
    early = _EARLY_SEATS.get(total_players)
    if early is None:
        # Larger custom tables retain unique names and cap early ranges at UTG.
        extra = total_players - 10
        early = ('UTG',) + tuple(f'UTG+{i}' for i in range(1, extra + 3)) + FULL_RING_ROLES[3:]
    return ('SB', 'BB') + early + ('BTN',)


def range_position(position, total_players=None):
    """Map a named seat to its role by distance to BTN (six-seat UTG => LJ)."""
    if total_players is None or position in {'SB', 'BB', 'BTN'}:
        return position
    early = seat_names(total_players)[2:-1]
    if position not in early:
        return position
    remaining = len(early) - early.index(position)
    return FULL_RING_ROLES[max(0, len(FULL_RING_ROLES) - remaining)]
