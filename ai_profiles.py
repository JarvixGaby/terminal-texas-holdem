# -*- coding: utf-8 -*-
"""Static AI archetype profiles for selectable built-in opponent personas.

These profiles describe intended AI tendencies. They are intentionally separate
from observed opponent models such as ``advanced_ai_engine.OpponentProfile``.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, Mapping, Tuple


DEFAULT_ARCHETYPE_NAME = "balanced"


@dataclass(frozen=True)
class AIArchetypeProfile:
    """Immutable target tendencies for a built-in AI opponent archetype."""

    name: str
    vpip_target: float
    pfr_target: float
    aggression_bias: float
    call_bias: float
    bluff_frequency: float
    three_bet_frequency: float
    cbet_frequency: float
    fold_to_cbet_bias: float
    showdown_stickiness: float
    sizing_bias: float

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name is required")

        for field_name in _RANGED_FLOAT_FIELDS:
            value = getattr(self, field_name)
            if not isinstance(value, (int, float)):
                raise ValueError(f"{field_name} must be numeric")
            if not 0.0 <= float(value) <= 1.0:
                raise ValueError(f"{field_name} must be between 0.0 and 1.0")

        if self.pfr_target > self.vpip_target:
            raise ValueError("pfr_target cannot exceed vpip_target")

    def to_dict(self) -> Dict[str, object]:
        """Return a JSON-compatible representation."""
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "AIArchetypeProfile":
        """Build a profile from a JSON-compatible mapping."""
        return cls(
            name=str(payload["name"]),
            vpip_target=float(payload["vpip_target"]),
            pfr_target=float(payload["pfr_target"]),
            aggression_bias=float(payload["aggression_bias"]),
            call_bias=float(payload["call_bias"]),
            bluff_frequency=float(payload["bluff_frequency"]),
            three_bet_frequency=float(payload["three_bet_frequency"]),
            cbet_frequency=float(payload["cbet_frequency"]),
            fold_to_cbet_bias=float(payload["fold_to_cbet_bias"]),
            showdown_stickiness=float(payload["showdown_stickiness"]),
            sizing_bias=float(payload["sizing_bias"]),
        )


_RANGED_FLOAT_FIELDS: Tuple[str, ...] = (
    "vpip_target",
    "pfr_target",
    "aggression_bias",
    "call_bias",
    "bluff_frequency",
    "three_bet_frequency",
    "cbet_frequency",
    "fold_to_cbet_bias",
    "showdown_stickiness",
    "sizing_bias",
)


_PROFILE_SEQUENCE: Tuple[AIArchetypeProfile, ...] = (
    AIArchetypeProfile(
        name="nit",
        vpip_target=0.13,
        pfr_target=0.09,
        aggression_bias=0.42,
        call_bias=0.22,
        bluff_frequency=0.04,
        three_bet_frequency=0.03,
        cbet_frequency=0.48,
        fold_to_cbet_bias=0.68,
        showdown_stickiness=0.28,
        sizing_bias=0.44,
    ),
    AIArchetypeProfile(
        name="tight_aggressive",
        vpip_target=0.22,
        pfr_target=0.18,
        aggression_bias=0.68,
        call_bias=0.36,
        bluff_frequency=0.11,
        three_bet_frequency=0.07,
        cbet_frequency=0.62,
        fold_to_cbet_bias=0.46,
        showdown_stickiness=0.42,
        sizing_bias=0.56,
    ),
    AIArchetypeProfile(
        name="loose_aggressive",
        vpip_target=0.34,
        pfr_target=0.26,
        aggression_bias=0.78,
        call_bias=0.44,
        bluff_frequency=0.18,
        three_bet_frequency=0.10,
        cbet_frequency=0.68,
        fold_to_cbet_bias=0.38,
        showdown_stickiness=0.48,
        sizing_bias=0.64,
    ),
    AIArchetypeProfile(
        name="calling_station",
        vpip_target=0.38,
        pfr_target=0.10,
        aggression_bias=0.24,
        call_bias=0.82,
        bluff_frequency=0.04,
        three_bet_frequency=0.02,
        cbet_frequency=0.32,
        fold_to_cbet_bias=0.18,
        showdown_stickiness=0.82,
        sizing_bias=0.40,
    ),
    AIArchetypeProfile(
        name="maniac",
        vpip_target=0.50,
        pfr_target=0.38,
        aggression_bias=0.92,
        call_bias=0.58,
        bluff_frequency=0.30,
        three_bet_frequency=0.16,
        cbet_frequency=0.76,
        fold_to_cbet_bias=0.24,
        showdown_stickiness=0.62,
        sizing_bias=0.80,
    ),
    AIArchetypeProfile(
        name="balanced",
        vpip_target=0.26,
        pfr_target=0.18,
        aggression_bias=0.55,
        call_bias=0.50,
        bluff_frequency=0.10,
        three_bet_frequency=0.06,
        cbet_frequency=0.56,
        fold_to_cbet_bias=0.48,
        showdown_stickiness=0.50,
        sizing_bias=0.52,
    ),
)


ARCHETYPE_PROFILES: Dict[str, AIArchetypeProfile] = {
    profile.name: profile for profile in _PROFILE_SEQUENCE
}


def list_archetype_names() -> list[str]:
    """Return archetype names in the configured display/assignment order."""
    return [profile.name for profile in _PROFILE_SEQUENCE]


def get_archetype_profile(name: str = DEFAULT_ARCHETYPE_NAME) -> AIArchetypeProfile:
    """Return the immutable profile for a known archetype name."""
    try:
        return ARCHETYPE_PROFILES[name]
    except KeyError as exc:
        valid_names = ", ".join(list_archetype_names())
        raise ValueError(f"unknown AI archetype profile {name!r}; expected one of: {valid_names}") from exc
