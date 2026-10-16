# -*- coding: utf-8 -*-
"""Non-throwing action validation and normalization for decision providers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from decision_provider import ActionResponse, GameStateSnapshot


@dataclass
class ValidatedAction:
    action: str
    amount: int
    is_valid: bool
    reason: str
    original_action: Any
    original_amount: Any


def validate_action(snapshot: GameStateSnapshot, response: ActionResponse) -> ValidatedAction:
    """Validate and normalize an action response, falling back safely on all bad input."""
    try:
        original_action = response.action
        original_amount = response.amount
        action = str(response.action).strip().lower()
        amount = _safe_int(response.amount, default=0)
        legal_actions = set(snapshot.legal_actions or [])

        if action not in legal_actions:
            return _fallback(snapshot, original_action, original_amount, f"illegal action: {original_action}")

        if action == "check":
            if snapshot.amount_to_call > 0:
                return _fallback(snapshot, original_action, original_amount, "check illegal when facing a bet")
            return ValidatedAction("check", 0, True, "ok", original_action, original_amount)

        if action == "fold":
            return ValidatedAction("fold", 0, True, "ok", original_action, original_amount)

        if action == "call":
            normalized = min(max(snapshot.player_chips, 0), max(snapshot.amount_to_call, 0))
            reason = "short stack all-in call" if normalized < snapshot.amount_to_call else "normalized to amount_to_call"
            return ValidatedAction("call", normalized, True, reason, original_action, original_amount)

        if action == "raise":
            max_total_bet = max(snapshot.player_chips, 0) + _acting_player_current_bet(snapshot)
            if amount < snapshot.min_raise:
                if amount == max_total_bet and amount > snapshot.current_bet:
                    return ValidatedAction("raise", amount, True, "short stack all-in raise below min_raise", original_action, original_amount)
                return _fallback(snapshot, original_action, original_amount, f"raise below min_raise {snapshot.min_raise}")
            if amount > max_total_bet:
                return _fallback(snapshot, original_action, original_amount, "raise amount exceeds player chips")
            return ValidatedAction("raise", amount, True, "ok", original_action, original_amount)

        if action == "all-in":
            if snapshot.player_chips <= 0:
                return _fallback(snapshot, original_action, original_amount, "all-in requires positive chips")
            return ValidatedAction("all-in", snapshot.player_chips, True, "ok", original_action, original_amount)

        return _fallback(snapshot, original_action, original_amount, f"unsupported action: {action}")
    except Exception as exc:
        return _fallback(snapshot, getattr(response, "action", None), getattr(response, "amount", None), f"validation exception: {exc}")


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _acting_player_current_bet(snapshot: GameStateSnapshot) -> int:
    for player in snapshot.visible_players or []:
        if player.name == snapshot.player_name:
            return max(_safe_int(player.current_bet, default=0), 0)
    return 0


def _fallback(snapshot: GameStateSnapshot, original_action: Any, original_amount: Any, reason: str) -> ValidatedAction:
    action = "check" if "check" in (snapshot.legal_actions or []) else "fold"
    return ValidatedAction(action, 0, False, reason, original_action, original_amount)
