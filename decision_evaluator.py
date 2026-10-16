"""Rule-based poker decision evaluator.

This module contains a small MVP evaluator for grading poker actions.  It is
intentionally deterministic and conservative so it can be used by higher-level
features without depending on the game engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DecisionContext:
    game_id: str = ""
    hand_id: str = ""
    player_name: str = ""
    phase: str = "preflop"
    position: str = ""
    hole_cards: list[str] = field(default_factory=list)
    community_cards: list[str] = field(default_factory=list)
    pot_size: int = 0
    current_bet: int = 0
    amount_to_call: int = 0
    player_chips: int = 0
    legal_actions: list[str] = field(default_factory=list)
    action_taken: str = ""
    amount: int = 0
    estimated_equity: float | None = None
    pot_odds: float | None = None
    opponent_count: int = 1
    min_raise: int = 0


@dataclass
class DecisionEvaluation:
    grade: str
    score: float
    recommended_action: str
    reasoning: str
    risk_tags: list[str] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)


def calculate_pot_odds(pot_size: int, amount_to_call: int) -> float:
    """Return call price divided by final pot, or 0 when checking is free."""
    if amount_to_call <= 0 or pot_size < 0:
        return 0.0
    denominator = pot_size + amount_to_call
    if denominator <= 0:
        return 0.0
    return amount_to_call / denominator


def evaluate_decision(context: DecisionContext) -> DecisionEvaluation:
    """Evaluate a poker decision using simple rule-based heuristics."""
    action = _normalize_action(context.action_taken)
    legal_actions = [_normalize_action(legal_action) for legal_action in context.legal_actions]
    equity = context.estimated_equity
    pot_odds = (
        context.pot_odds
        if context.pot_odds is not None
        else calculate_pot_odds(context.pot_size, context.amount_to_call)
    )
    equity_edge = equity - pot_odds if equity is not None else None
    metrics = _build_metrics(equity, pot_odds, equity_edge)

    if action and legal_actions and not _is_action_legal(action, legal_actions, context):
        return DecisionEvaluation(
            grade="blunder",
            score=5.0,
            recommended_action=_best_legal_action(context, pot_odds),
            reasoning=(
                f"Illegal action: {context.action_taken!r} is not one of "
                f"{context.legal_actions}."
            ),
            risk_tags=["illegal_action"],
            metrics=metrics,
        )

    if (
        action == "raise"
        and context.min_raise > 0
        and context.amount < context.min_raise
        and not _is_short_stack_all_in_raise(context)
    ):
        return DecisionEvaluation(
            grade="blunder",
            score=5.0,
            recommended_action=_best_non_raise_action(context, pot_odds),
            reasoning=(
                f"Illegal raise amount: {context.amount} is below the minimum "
                f"raise of {context.min_raise}."
            ),
            risk_tags=["illegal_raise_amount"],
            metrics=metrics,
        )

    if _is_low_equity_large_raise(context, action, equity):
        return DecisionEvaluation(
            grade="poor",
            score=30.0,
            recommended_action="fold" if "fold" in legal_actions else _best_non_raise_action(context, pot_odds),
            reasoning="Low equity combined with an all-in or large raise is a high-risk bluff.",
            risk_tags=["high_risk_bluff"],
            metrics=metrics,
        )

    if _is_missed_value(context, action, legal_actions, equity, pot_odds):
        return DecisionEvaluation(
            grade="questionable",
            score=60.0,
            recommended_action="raise",
            reasoning="Very strong equity should usually build the pot when raising is legal.",
            risk_tags=["missed_value"],
            metrics=metrics,
        )

    if context.amount_to_call > 0 and _has_poor_preflop_playability(context):
        if action == "call":
            return DecisionEvaluation(
                grade="questionable",
                score=55.0,
                recommended_action="fold",
                reasoning=(
                    "Preflop call has poor playability/realization; raw equity alone "
                    "does not justify continuing with this offsuit disconnected hand."
                ),
                risk_tags=["poor_preflop_playability"],
                metrics=metrics,
            )
        if action == "fold":
            return DecisionEvaluation(
                grade="good",
                score=75.0,
                recommended_action="fold",
                reasoning=(
                    "Fold is preferred because this preflop hand has poor "
                    "playability/realization despite the raw pot-odds estimate."
                ),
                risk_tags=["poor_preflop_playability"],
                metrics=metrics,
            )

    if context.amount_to_call > 0 and equity is not None:
        if action == "fold" and not _can_trust_raw_equity_for_fold_overfold(context):
            return DecisionEvaluation(
                grade="good",
                score=70.0,
                recommended_action="fold",
                reasoning="Preflop fold is not penalized from noisy raw equity alone for this non-premium hand.",
                risk_tags=["preflop_raw_equity_uncertain"],
                metrics=metrics,
            )

        if action == "call":
            if not _can_trust_raw_equity_for_call_pot_odds(context):
                return DecisionEvaluation(
                    grade="good",
                    score=75.0,
                    recommended_action="call",
                    reasoning="Preflop call with a strong hand is not penalized from noisy raw equity alone.",
                    risk_tags=["preflop_raw_equity_uncertain"],
                    metrics=metrics,
                )
            if equity < pot_odds - 0.15:
                return DecisionEvaluation(
                    grade="blunder",
                    score=15.0,
                    recommended_action="fold" if "fold" in legal_actions else _best_legal_action(context, pot_odds),
                    reasoning="Called with equity far below the pot odds required to continue.",
                    risk_tags=["negative_pot_odds_call"],
                    metrics=metrics,
                )
            if equity < pot_odds:
                return DecisionEvaluation(
                    grade="poor",
                    score=35.0,
                    recommended_action="fold" if "fold" in legal_actions else _best_legal_action(context, pot_odds),
                    reasoning="Called without enough equity to meet the offered pot odds.",
                    risk_tags=["negative_pot_odds_call"],
                    metrics=metrics,
                )
            if equity >= pot_odds + 0.20:
                grade = "excellent"
                score = 90.0
            else:
                grade = "good"
                score = 80.0
            return DecisionEvaluation(
                grade=grade,
                score=score,
                recommended_action="call",
                reasoning="Call is supported because estimated equity meets or exceeds pot odds.",
                metrics=metrics,
            )

        if action == "fold" and equity > pot_odds + 0.20 and _can_trust_raw_equity_for_fold_overfold(context):
            return DecisionEvaluation(
                grade="poor",
                score=30.0,
                recommended_action="call" if "call" in legal_actions else _best_legal_action(context, pot_odds),
                reasoning="Folded despite equity being far above the price offered by pot odds.",
                risk_tags=["overfold"],
                metrics=metrics,
            )

    return _default_evaluation(context, action, legal_actions, equity, pot_odds, metrics)


def _normalize_action(action: str) -> str:
    normalized = action.strip().lower().replace("_", "-")
    if normalized in {"allin", "all-in"}:
        return "all-in"
    return normalized


def _is_action_legal(action: str, legal_actions: list[str], context: DecisionContext) -> bool:
    if action in legal_actions:
        return True
    return (
        action == "all-in"
        and "raise" in legal_actions
        and context.player_chips > 0
        and context.amount >= context.player_chips
    )


def _is_short_stack_all_in_raise(context: DecisionContext) -> bool:
    """Return True when a below-min raise is exactly the actor's all-in total."""
    if context.player_chips <= 0:
        return False
    already_committed = max(context.current_bet - context.amount_to_call, 0)
    all_in_total = already_committed + context.player_chips
    return context.amount == all_in_total


def _build_metrics(
    equity: float | None,
    pot_odds: float,
    equity_edge: float | None,
) -> dict[str, Any]:
    return {
        "equity": equity,
        "pot_odds": pot_odds,
        "equity_edge": equity_edge,
    }


def _has_poor_preflop_playability(context: DecisionContext) -> bool:
    if context.phase.lower() != "preflop" or context.community_cards:
        return False
    hand_key = _preflop_hand_key(context.hole_cards)
    if not hand_key or hand_key.endswith("s") or len(hand_key) == 2:
        return False

    ranks = hand_key[:-1]
    if len(ranks) != 2:
        return False
    high = _rank_value(ranks[0])
    low = _rank_value(ranks[1])
    if high == 0 or low == 0:
        return False

    is_broadwayish = high >= 12 and low >= 10
    is_ace_with_playable_kicker = high == 14 and low >= 10
    is_connected = high - low <= 2
    return not (is_broadwayish or is_ace_with_playable_kicker or is_connected)


def _can_trust_raw_equity_for_fold_overfold(context: DecisionContext) -> bool:
    """Avoid over-penalizing preflop folds from noisy raw equity alone.

    Low-rollout benchmark equity estimates can make weak suited or speculative
    preflop hands look far ahead of pot odds.  Treat preflop folds as clear
    overfolds only when no hole-card shape is available or the hand is strong
    enough that folding is obviously bad independent of noisy raw equity.
    """
    if context.phase.lower() != "preflop" or context.community_cards:
        return True
    hand_key = _preflop_hand_key(context.hole_cards)
    if not hand_key:
        return True
    return _is_strong_preflop_hand(hand_key)


def _can_trust_raw_equity_for_call_pot_odds(context: DecisionContext) -> bool:
    """Avoid flagging strong preflop calls from low-rollout raw equity alone."""
    if context.phase.lower() != "preflop" or context.community_cards:
        return True
    hand_key = _preflop_hand_key(context.hole_cards)
    if not hand_key:
        return True
    return not _is_strong_preflop_hand(hand_key)


def _is_strong_preflop_hand(hand_key: str) -> bool:
    if len(hand_key) == 2:
        rank = _rank_value(hand_key[0])
        return rank >= 10
    ranks = hand_key[:-1]
    if len(ranks) != 2:
        return False
    high = _rank_value(ranks[0])
    low = _rank_value(ranks[1])
    if high == 14 and low >= 10:
        return True
    if high >= 12 and low >= 11:
        return True
    return False


def _preflop_hand_key(hole_cards: list[str]) -> str:
    if len(hole_cards) != 2:
        return ""
    parsed = [_parse_card(card) for card in hole_cards]
    if any(rank == "" for rank, _suit in parsed):
        return ""
    parsed.sort(key=lambda card: _rank_value(card[0]), reverse=True)
    high_rank, high_suit = parsed[0]
    low_rank, low_suit = parsed[1]
    if high_rank == low_rank:
        return f"{high_rank}{low_rank}"
    suffix = "s" if high_suit and high_suit == low_suit else "o"
    return f"{high_rank}{low_rank}{suffix}"


def _parse_card(card: str) -> tuple[str, str]:
    stripped = str(card).strip()
    if not stripped:
        return "", ""
    rank = "10" if stripped.startswith("10") else stripped[0].upper()
    if rank == "10":
        rank = "T"
        suit = stripped[2:]
    else:
        suit = stripped[1:]
    if _rank_value(rank) == 0:
        return "", ""
    return rank, suit


def _rank_value(rank: str) -> int:
    return {
        "A": 14,
        "K": 13,
        "Q": 12,
        "J": 11,
        "T": 10,
        "9": 9,
        "8": 8,
        "7": 7,
        "6": 6,
        "5": 5,
        "4": 4,
        "3": 3,
        "2": 2,
    }.get(rank, 0)


def _best_legal_action(context: DecisionContext, pot_odds: float) -> str:
    legal_actions = [_normalize_action(action) for action in context.legal_actions]
    equity = context.estimated_equity

    if not legal_actions:
        return "unknown"
    if equity is not None and context.amount_to_call > 0:
        if equity >= pot_odds and "call" in legal_actions:
            return "call"
        if "fold" in legal_actions:
            return "fold"
    if "check" in legal_actions:
        return "check"
    if "call" in legal_actions:
        return "call"
    if "fold" in legal_actions:
        return "fold"
    return legal_actions[0]


def _best_non_raise_action(context: DecisionContext, pot_odds: float) -> str:
    legal_actions = [_normalize_action(action) for action in context.legal_actions if _normalize_action(action) not in {"raise", "all-in"}]
    if not legal_actions:
        return "unknown"
    adjusted_context = DecisionContext(
        amount_to_call=context.amount_to_call,
        legal_actions=legal_actions,
        estimated_equity=context.estimated_equity,
    )
    return _best_legal_action(adjusted_context, pot_odds)


def _is_low_equity_large_raise(
    context: DecisionContext,
    action: str,
    equity: float | None,
) -> bool:
    if action not in {"raise", "all-in"}:
        return False
    if equity is None or equity >= 0.20:
        return False
    is_all_in = context.player_chips > 0 and context.amount >= context.player_chips
    is_large_raise = context.pot_size > 0 and context.amount >= context.pot_size
    return is_all_in or is_large_raise


def _is_missed_value(
    context: DecisionContext,
    action: str,
    legal_actions: list[str],
    equity: float | None,
    pot_odds: float,
) -> bool:
    if equity is None or equity < 0.75 or "raise" not in legal_actions:
        return False
    if action == "check" and context.amount_to_call <= 0:
        return True
    if action == "call":
        return True
    return False


def _default_evaluation(
    context: DecisionContext,
    action: str,
    legal_actions: list[str],
    equity: float | None,
    pot_odds: float,
    metrics: dict[str, Any],
) -> DecisionEvaluation:
    if action in {"check", "call"}:
        grade = "good"
        score = 75.0
        reasoning = "Action is reasonable under the available rule-based checks."
    elif action == "fold":
        grade = "good"
        score = 70.0
        reasoning = "Fold is not contradicted by the available equity and pot-odds checks."
    elif action == "raise":
        grade = "good" if equity is None or equity >= 0.35 else "questionable"
        score = 75.0 if grade == "good" else 55.0
        reasoning = "Raise is legal and not flagged by the risk rules."
    else:
        grade = "questionable"
        score = 50.0
        reasoning = "No specific rule matched this decision."

    return DecisionEvaluation(
        grade=grade,
        score=score,
        recommended_action=_best_legal_action(context, pot_odds),
        reasoning=reasoning,
        metrics=metrics,
    )
