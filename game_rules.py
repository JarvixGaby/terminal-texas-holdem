# -*- coding: utf-8 -*-
"""Rule and stack-depth configuration for supported Hold'em games."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class BettingStructure(str, Enum):
    NO_LIMIT = "no_limit"


@dataclass(frozen=True)
class BlindStructure:
    small_blind: int
    big_blind: int

    def validate(self) -> None:
        if self.small_blind <= 0:
            raise ValueError("small blind must be positive")
        if self.big_blind <= self.small_blind:
            raise ValueError("big blind must be greater than small blind")


@dataclass(frozen=True)
class StackProfile:
    name: str
    big_blinds: Optional[int] = None
    custom_chips: Optional[int] = None

    def starting_chips_for(self, big_blind: int) -> int:
        if self.custom_chips is not None:
            return self.custom_chips
        if self.big_blinds is None:
            raise ValueError("stack profile requires big_blinds or custom_chips")
        return self.big_blinds * big_blind


@dataclass(frozen=True)
class GameRules:
    variant: str
    betting_structure: BettingStructure
    small_blind: int
    big_blind: int
    starting_chips: int
    stack_profile: str
    allow_short_all_in: bool = True
    max_raises_per_street: Optional[int] = None


BLIND_PRESETS = {
    "5/10": BlindStructure(5, 10),
    "10/20": BlindStructure(10, 20),
}

STACK_PROFILES = {
    "short": StackProfile("short", 20),
    "standard": StackProfile("standard", 50),
    "deep": StackProfile("deep", 100),
}


def create_rules(
    blind_structure: BlindStructure,
    stack_profile: StackProfile,
) -> GameRules:
    blind_structure.validate()
    starting_chips = stack_profile.starting_chips_for(blind_structure.big_blind)
    if starting_chips <= 0:
        raise ValueError("starting chips must be positive")

    return GameRules(
        variant="texas_holdem",
        betting_structure=BettingStructure.NO_LIMIT,
        small_blind=blind_structure.small_blind,
        big_blind=blind_structure.big_blind,
        starting_chips=starting_chips,
        stack_profile=stack_profile.name,
        allow_short_all_in=True,
        max_raises_per_street=None,
    )
