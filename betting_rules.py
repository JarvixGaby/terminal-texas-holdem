# -*- coding: utf-8 -*-
"""No-Limit Hold'em betting helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class NoLimitBettingRules:
    big_blind: int
    allow_short_all_in: bool = True

    def minimum_bet_total(self, current_bet: int) -> int:
        if current_bet <= 0:
            return self.big_blind
        return current_bet

    def minimum_raise_total(self, current_bet: int, last_full_raise_increment: int) -> int:
        if current_bet <= 0:
            return self.big_blind
        return current_bet + max(last_full_raise_increment, self.big_blind)

    def maximum_raise_total(self, player_current_bet: int, player_chips: int) -> int:
        return max(player_current_bet, 0) + max(player_chips, 0)

    def is_full_raise(
        self,
        target_total: int,
        previous_current_bet: int,
        last_full_raise_increment: int,
    ) -> bool:
        if target_total <= previous_current_bet:
            return False
        increment = target_total - previous_current_bet
        return increment >= max(last_full_raise_increment, self.big_blind)

    def is_raise_legal(
        self,
        target_total: int,
        current_bet: int,
        player_current_bet: int,
        player_chips: int,
        last_full_raise_increment: int,
    ) -> bool:
        max_total = self.maximum_raise_total(player_current_bet, player_chips)
        if target_total > max_total or target_total <= current_bet:
            return False
        if target_total >= self.minimum_raise_total(current_bet, last_full_raise_increment):
            return True
        return self.allow_short_all_in and target_total == max_total

    def legal_actions(
        self,
        amount_to_call: int,
        current_bet: int,
        player_current_bet: int,
        player_chips: int,
        last_full_raise_increment: int,
    ) -> List[str]:
        actions: List[str] = []
        if amount_to_call == 0:
            actions.append("check")
        if amount_to_call > 0 and player_chips > 0:
            actions.append("call")

        max_total = self.maximum_raise_total(player_current_bet, player_chips)
        if self.is_raise_legal(
            target_total=max_total,
            current_bet=current_bet,
            player_current_bet=player_current_bet,
            player_chips=player_chips,
            last_full_raise_increment=last_full_raise_increment,
        ):
            actions.append("raise")

        actions.append("fold")
        return actions
