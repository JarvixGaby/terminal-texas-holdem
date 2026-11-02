"""Editable starting-hand ranges for built-in personas, not solver charts.

The JSON lists canonical pairs, suited (s), and offsuit (o) hands separately.
Membership permits an action; price, stack and mixed-strategy checks still apply.
Custom profiles retain the engine's parameter-based fallback.
"""

import json
from pathlib import Path
from types import MappingProxyType

from texas_holdem.ai.ai_profiles import ARCHETYPE_PROFILES


_payload = json.loads(Path(__file__).with_suffix('.json').read_text())
PREFLOP_RANGES = MappingProxyType({
    name: MappingProxyType({
        position: MappingProxyType({action: frozenset(hands.split())
                                    for action, hands in ranges.items()})
        for position, ranges in positions.items()
    })
    for name, positions in _payload.items()
})
del _payload


def get_preflop_range(profile, position):
    """Return immutable action sets, or None for a custom profile."""
    if ARCHETYPE_PROFILES.get(profile.name) != profile:
        return None
    positions = PREFLOP_RANGES[profile.name]
    return positions.get(position, positions['MP'])
