# -*- coding: utf-8 -*-
"""MVP evaluator for end-to-end AI system behavior."""

from __future__ import annotations

import json
import statistics
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from headless_simulation import run_ai_only_simulation

BENCHMARK_GATE_VERSION = "phase2.2"
BENCHMARK_GATE_PROTOCOL = {
    "seeds": list(range(10)),
    "hands_per_seed": 500,
    "player_count": 4,
    "starting_chips": 10000,
}
_REQUIRED_RUN_METRICS = {
    "hands_played",
    "total_actions",
    "illegal_action_rate",
    "average_decision_score",
    "grade_distribution",
    "final_stacks",
    "errors",
    "player_metrics",
    "profile_metrics",
    "weakest_profile",
    "style_separability_score",
    "vpip_spread",
    "pfr_spread",
    "aggression_spread",
    "call_rate_spread",
    "largest_stack_share",
    "bustout_rate",
    "hands_until_first_bust",
    "stack_gini",
    "transcript_samples",
    "benchmark",
}
_REQUIRED_SUMMARY_METRICS = {
    "total_actions",
    "illegal_action_rate",
    "average_decision_score",
}
_FORBIDDEN_TRANSCRIPT_TOKENS = (
    "deck",
    "hole_cards",
    "opponent_hole_cards",
    "private_ai_internals",
    "unsafe_seed",
)
_PUBLIC_TRANSCRIPT_SCHEMA = {
    "version": "phase3.4-public-transcript-v1",
    "sample_fields": ["hand_number", "text", "flags"],
    "allowed_private_cards": "only legally revealed showdown contestants",
    "forbidden_fields": list(_FORBIDDEN_TRANSCRIPT_TOKENS),
}
_SHOWDOWN_REVEAL_POLICY = {
    "showdown": "reveal only players who legally reached showdown",
    "non_showdown": "do not reveal any private hole cards",
    "folded_players": "never reveal folded/non-contesting players' private cards",
}
_REQUIRED_PROFILE_METRICS = {
    "nit",
    "tight_aggressive",
    "loose_aggressive",
    "calling_station",
}
_AVERAGE_DECISION_SCORE_WARN_THRESHOLD = 70.0
_STYLE_SEPARABILITY_WARN_THRESHOLD = 0.20
_POOR_BLUNDER_RATE_WARN_THRESHOLD = 0.10
_BLUNDER_RATE_WARN_THRESHOLD = 0.01
_PROFILE_CALIBRATION_TARGET_BANDS: Dict[str, Dict[str, tuple[float, float]]] = {
    "nit": {
        "vpip": (0.08, 0.18),
        "pfr": (0.00, 0.10),
        "aggression_factor": (0.00, 1.20),
        "call_rate": (0.10, 0.35),
        "fold_rate": (0.35, 0.90),
        "showdown_rate": (0.00, 0.35),
        "poor_blunder_rate": (0.00, 0.10),
        "average_decision_score": (60.0, 100.0),
    },
    "tight_aggressive": {
        "vpip": (0.16, 0.28),
        "pfr": (0.12, 0.24),
        "aggression_factor": (0.80, 3.50),
        "call_rate": (0.12, 0.45),
        "fold_rate": (0.20, 0.70),
        "showdown_rate": (0.05, 0.45),
        "poor_blunder_rate": (0.00, 0.10),
        "average_decision_score": (60.0, 100.0),
    },
    "loose_aggressive": {
        "vpip": (0.28, 0.45),
        "pfr": (0.20, 0.34),
        "aggression_factor": (1.20, 5.00),
        "call_rate": (0.15, 0.45),
        "fold_rate": (0.15, 0.65),
        "showdown_rate": (0.08, 0.55),
        "poor_blunder_rate": (0.00, 0.10),
        "average_decision_score": (60.0, 100.0),
    },
    "calling_station": {
        "vpip": (0.30, 0.50),
        "pfr": (0.00, 0.16),
        "aggression_factor": (0.00, 1.20),
        "call_rate": (0.45, 1.00),
        "fold_rate": (0.00, 0.35),
        "showdown_rate": (0.15, 0.75),
        "poor_blunder_rate": (0.00, 0.10),
        "average_decision_score": (60.0, 100.0),
    },
}


@dataclass
class PlayerPokerMetrics:
    hands_played: int = 0
    actions: int = 0
    vpip: float = 0.0
    pfr: float = 0.0
    aggression_factor: float = 0.0
    call_rate: float = 0.0
    fold_rate: float = 0.0
    showdown_rate: float = 0.0
    win_rate: float = 0.0
    poor_blunder_rate: float = 0.0
    average_decision_score: float = 0.0
    preflop_vpip_hands: int = 0
    preflop_raise_hands: int = 0
    preflop_opportunities: int = 0
    aggressive_actions: int = 0
    call_actions: int = 0
    fold_actions: int = 0
    showdown_hands: int = 0
    won_hands: int = 0
    poor_blunder_actions: int = 0


@dataclass
class ProfilePokerMetrics:
    player_count: int = 0
    hands_played: int = 0
    actions: int = 0
    vpip: float = 0.0
    pfr: float = 0.0
    aggression_factor: float = 0.0
    call_rate: float = 0.0
    fold_rate: float = 0.0
    showdown_rate: float = 0.0
    win_rate: float = 0.0
    poor_blunder_rate: float = 0.0
    average_decision_score: float = 0.0
    aggressive_actions: int = 0
    call_actions: int = 0


@dataclass
class AISystemEvaluationReport:
    hands_played: int
    total_actions: int
    illegal_action_rate: float
    average_decision_score: float
    grade_distribution: Dict[str, int] = field(default_factory=dict)
    final_stacks: Dict[str, int] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    player_metrics: Dict[str, PlayerPokerMetrics] = field(default_factory=dict)
    profile_metrics: Dict[str, ProfilePokerMetrics] = field(default_factory=dict)
    weakest_profile: str = "unknown"
    style_separability_score: float = 0.0
    vpip_spread: float = 0.0
    pfr_spread: float = 0.0
    aggression_spread: float = 0.0
    call_rate_spread: float = 0.0
    largest_stack_share: float = 0.0
    bustout_rate: float = 0.0
    hands_until_first_bust: Optional[int] = None
    stack_gini: float = 0.0
    profile_calibration: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    profile_calibration_status: str = "NOT_RUN"
    profile_calibration_distance: float = 0.0
    poor_blunder_samples: List[Dict[str, Any]] = field(default_factory=list)
    public_transcript_schema: Dict[str, Any] = field(default_factory=lambda: dict(_PUBLIC_TRANSCRIPT_SCHEMA))
    showdown_reveal_policy: Dict[str, str] = field(default_factory=lambda: dict(_SHOWDOWN_REVEAL_POLICY))
    transcript_samples: List[Dict[str, Any]] = field(default_factory=list)
    benchmark: Dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        data = asdict(self)
        data["hands"] = self.hands_played
        data["actions"] = self.total_actions
        return data


def evaluate_ai_system(num_hands: int = 10, player_count: int = 4,
                       starting_chips: int = 1000,
                       seed: Optional[int] = None,
                       ai_equity_simulations: Optional[int] = None) -> AISystemEvaluationReport:
    if num_hands <= 0:
        return AISystemEvaluationReport(
            hands_played=0,
            total_actions=0,
            illegal_action_rate=0,
            average_decision_score=0,
            grade_distribution={},
            final_stacks={},
            errors=[],
        )

    simulation = run_ai_only_simulation(
        num_hands=num_hands,
        player_count=player_count,
        starting_chips=starting_chips,
        seed=seed,
        ai_equity_simulations=ai_equity_simulations,
    )
    return summarize_ai_evaluations(simulation)


def summarize_ai_evaluations(simulation) -> AISystemEvaluationReport:
    scores: List[float] = []
    grade_distribution: Dict[str, int] = {}
    illegal_actions = 0
    player_metrics = _calculate_player_metrics(simulation)
    profile_metrics, weakest_profile = _calculate_profile_metrics(simulation, player_metrics)
    separability_metrics = _calculate_style_separability_metrics(profile_metrics)
    calibration_metrics = _calculate_profile_calibration(profile_metrics)
    stack_metrics = _calculate_stack_concentration_metrics(simulation)
    poor_blunder_samples = _build_poor_blunder_samples(simulation)
    transcript_samples = _build_transcript_samples(simulation)

    for summary in simulation.hand_summaries:
        for evaluation in summary.get("decision_evaluations", []) or []:
            if not evaluation:
                continue
            try:
                scores.append(float(evaluation.get("score", 0)))
            except (TypeError, ValueError):
                pass
            grade = evaluation.get("grade")
            if grade:
                grade_distribution[grade] = grade_distribution.get(grade, 0) + 1
            risk_tags = set(evaluation.get("risk_tags", []) or [])
            if (
                evaluation.get("is_legal") is False
                or evaluation.get("illegal") is True
                or "illegal_action" in risk_tags
                or "illegal_raise_amount" in risk_tags
            ):
                illegal_actions += 1

    total_actions = simulation.total_actions
    average_score = sum(scores) / len(scores) if scores else 0
    illegal_rate = illegal_actions / total_actions if total_actions else 0

    return AISystemEvaluationReport(
        hands_played=simulation.hands_completed,
        total_actions=total_actions,
        illegal_action_rate=illegal_rate,
        average_decision_score=average_score,
        grade_distribution=grade_distribution,
        final_stacks=simulation.final_stacks,
        errors=simulation.errors,
        player_metrics=player_metrics,
        profile_metrics=profile_metrics,
        weakest_profile=weakest_profile,
        **separability_metrics,
        **stack_metrics,
        **calibration_metrics,
        poor_blunder_samples=poor_blunder_samples,
        transcript_samples=transcript_samples,
    )


def _calculate_player_metrics(simulation) -> Dict[str, PlayerPokerMetrics]:
    player_names = set(getattr(simulation, "final_stacks", {}) or {})
    for summary in simulation.hand_summaries:
        for action in summary.get("action_records", []) or []:
            player_name = action.get("player_name")
            if player_name:
                player_names.add(player_name)
        for player_hand in summary.get("final_hands", []) or []:
            player_name = player_hand.get("player_name")
            if player_name:
                player_names.add(player_name)
        for winner in summary.get("winner_names", []) or []:
            player_names.add(winner)

    metrics = {player_name: PlayerPokerMetrics() for player_name in sorted(player_names)}
    score_totals = {player_name: 0.0 for player_name in metrics}
    score_counts = {player_name: 0 for player_name in metrics}

    for summary in simulation.hand_summaries:
        active_this_hand = _players_in_hand(summary, metrics)
        for player_name in active_this_hand:
            metrics[player_name].hands_played += 1

        preflop_vpip = set()
        preflop_raises = set()
        outcome_metadata = summary.get("outcome_metadata") or {}
        has_blind_metadata = bool(outcome_metadata.get("blind_positions") or outcome_metadata.get("forced_blinds"))
        if has_blind_metadata:
            preflop_opportunity_players = set(active_this_hand)
        else:
            preflop_opportunity_players = set()
        final_hand_players = {hand.get("player_name") for hand in summary.get("final_hands", []) or [] if hand.get("player_name")}
        if "went_to_showdown" in outcome_metadata:
            showdown_players = final_hand_players if outcome_metadata.get("went_to_showdown") is True else set()
        else:
            showdown_players = final_hand_players
        winners = set(summary.get("winner_names", []) or [])

        for player_name in showdown_players:
            metrics.setdefault(player_name, PlayerPokerMetrics()).showdown_hands += 1
        for player_name in winners:
            metrics.setdefault(player_name, PlayerPokerMetrics()).won_hands += 1

        for action_record in summary.get("action_records", []) or []:
            player_name = action_record.get("player_name")
            if not player_name:
                continue
            metric = metrics.setdefault(player_name, PlayerPokerMetrics())
            action = str(action_record.get("action", "")).lower()
            phase = action_record.get("phase")
            metric.actions += 1

            if phase == "preflop" and action in {"call", "raise", "all-in"}:
                preflop_vpip.add(player_name)
            if phase == "preflop" and action == "raise":
                preflop_raises.add(player_name)
            if action in {"raise", "bet", "all-in"}:
                metric.aggressive_actions += 1
            if action == "call":
                metric.call_actions += 1
            if action == "fold":
                metric.fold_actions += 1

            evaluation = action_record.get("decision_evaluation") or {}
            if evaluation:
                grade = str(evaluation.get("grade", "")).lower()
                if grade in {"poor", "blunder"}:
                    metric.poor_blunder_actions += 1
                try:
                    score_totals[player_name] = score_totals.get(player_name, 0.0) + float(evaluation.get("score", 0))
                    score_counts[player_name] = score_counts.get(player_name, 0) + 1
                except (TypeError, ValueError):
                    pass

        for player_name in preflop_vpip:
            metrics[player_name].preflop_vpip_hands += 1
        for player_name in preflop_raises:
            metrics[player_name].preflop_raise_hands += 1
        for player_name in preflop_opportunity_players:
            metrics[player_name].preflop_opportunities += 1

    for player_name, metric in metrics.items():
        vpip_denominator = metric.preflop_opportunities if metric.preflop_opportunities else metric.hands_played
        metric.vpip = metric.preflop_vpip_hands / vpip_denominator if vpip_denominator else 0.0
        metric.pfr = metric.preflop_raise_hands / vpip_denominator if vpip_denominator else 0.0
        metric.aggression_factor = metric.aggressive_actions / metric.call_actions if metric.call_actions else float(metric.aggressive_actions)
        metric.call_rate = metric.call_actions / metric.actions if metric.actions else 0.0
        metric.fold_rate = metric.fold_actions / metric.actions if metric.actions else 0.0
        metric.showdown_rate = metric.showdown_hands / metric.hands_played if metric.hands_played else 0.0
        metric.win_rate = metric.won_hands / metric.hands_played if metric.hands_played else 0.0
        metric.poor_blunder_rate = metric.poor_blunder_actions / metric.actions if metric.actions else 0.0
        metric.average_decision_score = score_totals.get(player_name, 0.0) / score_counts.get(player_name, 1) if score_counts.get(player_name, 0) else 0.0
    return metrics


def _calculate_profile_metrics(simulation, player_metrics: Dict[str, PlayerPokerMetrics]) -> tuple[Dict[str, ProfilePokerMetrics], str]:
    player_profiles = _collect_player_profiles(simulation)
    grouped: Dict[str, List[PlayerPokerMetrics]] = {}
    for player_name, metric in player_metrics.items():
        profile = player_profiles.get(player_name, "unknown") or "unknown"
        grouped.setdefault(profile, []).append(metric)

    profile_metrics: Dict[str, ProfilePokerMetrics] = {}
    for profile, metrics in grouped.items():
        aggregate = ProfilePokerMetrics(player_count=len(metrics))
        aggregate.hands_played = sum(metric.hands_played for metric in metrics)
        aggregate.actions = sum(metric.actions for metric in metrics)
        aggregate.aggressive_actions = sum(metric.aggressive_actions for metric in metrics)
        aggregate.call_actions = sum(metric.call_actions for metric in metrics)
        aggregate.vpip = _weighted_average(metrics, "vpip", "preflop_opportunities", fallback_weight="hands_played")
        aggregate.pfr = _weighted_average(metrics, "pfr", "preflop_opportunities", fallback_weight="hands_played")
        aggregate.aggression_factor = aggregate.aggressive_actions / aggregate.call_actions if aggregate.call_actions else float(aggregate.aggressive_actions)
        aggregate.call_rate = aggregate.call_actions / aggregate.actions if aggregate.actions else 0.0
        aggregate.fold_rate = _weighted_average(metrics, "fold_rate", "actions")
        aggregate.showdown_rate = _weighted_average(metrics, "showdown_rate", "hands_played")
        aggregate.win_rate = _weighted_average(metrics, "win_rate", "hands_played")
        aggregate.poor_blunder_rate = _weighted_average(metrics, "poor_blunder_rate", "actions")
        aggregate.average_decision_score = _weighted_average(metrics, "average_decision_score", "actions")
        profile_metrics[profile] = aggregate

    weakest_profile = "unknown"
    if profile_metrics:
        weakest_profile = max(
            profile_metrics,
            key=lambda profile: (
                profile_metrics[profile].poor_blunder_rate,
                -profile_metrics[profile].win_rate,
                profile_metrics[profile].fold_rate,
                -profile_metrics[profile].average_decision_score,
            ),
        )
    return profile_metrics, weakest_profile


def _calculate_style_separability_metrics(profile_metrics: Dict[str, ProfilePokerMetrics]) -> Dict[str, float]:
    if len(profile_metrics) < 2:
        return {
            "style_separability_score": 0.0,
            "vpip_spread": 0.0,
            "pfr_spread": 0.0,
            "aggression_spread": 0.0,
            "call_rate_spread": 0.0,
        }

    vpip_spread = _metric_spread(profile_metrics, "vpip")
    pfr_spread = _metric_spread(profile_metrics, "pfr")
    aggression_spread = _metric_spread(profile_metrics, "aggression_factor")
    call_rate_spread = _metric_spread(profile_metrics, "call_rate")
    normalized_aggression_spread = aggression_spread / (1 + aggression_spread) if aggression_spread else 0.0
    style_separability_score = (
        vpip_spread + pfr_spread + normalized_aggression_spread + call_rate_spread
    ) / 4
    return {
        "style_separability_score": style_separability_score,
        "vpip_spread": vpip_spread,
        "pfr_spread": pfr_spread,
        "aggression_spread": aggression_spread,
        "call_rate_spread": call_rate_spread,
    }


def _calculate_profile_calibration(profile_metrics: Dict[str, ProfilePokerMetrics]) -> Dict[str, object]:
    calibration: Dict[str, Dict[str, Any]] = {}
    distances: List[float] = []
    for profile_name, target_bands in _PROFILE_CALIBRATION_TARGET_BANDS.items():
        observed = profile_metrics.get(profile_name)
        if observed is None:
            continue
        metric_results: Dict[str, Dict[str, object]] = {}
        profile_distances: List[float] = []
        for metric_name, (target_min, target_max) in target_bands.items():
            observed_value = float(getattr(observed, metric_name, 0.0) or 0.0)
            distance = _distance_outside_band(observed_value, target_min, target_max)
            status = "PASS" if distance == 0.0 else "WARN"
            metric_results[metric_name] = {
                "observed": round(observed_value, 6),
                "target_min": target_min,
                "target_max": target_max,
                "status": status,
                "distance": distance,
            }
            profile_distances.append(distance)
            distances.append(distance)
        profile_status = "PASS" if all(result["status"] == "PASS" for result in metric_results.values()) else "WARN"
        calibration[profile_name] = {
            "status": profile_status,
            "distance": round(sum(profile_distances) / len(profile_distances), 6) if profile_distances else 0.0,
            "metrics": metric_results,
        }

    if not calibration:
        return {
            "profile_calibration": {},
            "profile_calibration_status": "NOT_RUN",
            "profile_calibration_distance": 0.0,
        }

    return {
        "profile_calibration": calibration,
        "profile_calibration_status": "PASS" if all(item["status"] == "PASS" for item in calibration.values()) else "WARN",
        "profile_calibration_distance": round(sum(distances) / len(distances), 6) if distances else 0.0,
    }


def _distance_outside_band(value: float, target_min: float, target_max: float) -> float:
    if value < target_min:
        return round(target_min - value, 6)
    if value > target_max:
        return round(value - target_max, 6)
    return 0.0


def _calculate_stack_concentration_metrics(simulation) -> Dict[str, object]:
    final_stacks = dict(getattr(simulation, "final_stacks", {}) or {})
    stacks = [max(int(chips), 0) for chips in final_stacks.values()]
    total_chips = sum(stacks)
    player_count = len(stacks)

    largest_stack_share = max(stacks) / total_chips if total_chips and stacks else 0.0
    bustout_rate = sum(1 for chips in stacks if chips <= 0) / player_count if player_count else 0.0
    stack_gini = _calculate_gini(stacks)
    hands_until_first_bust = _hands_until_first_bust(getattr(simulation, "hand_summaries", []) or [])

    return {
        "largest_stack_share": largest_stack_share,
        "bustout_rate": bustout_rate,
        "hands_until_first_bust": hands_until_first_bust,
        "stack_gini": stack_gini,
    }


def _hands_until_first_bust(hand_summaries: List[Dict]) -> Optional[int]:
    for index, summary in enumerate(hand_summaries, start=1):
        final_chips_by_player = _final_chips_from_summary(summary)
        if any(chips <= 0 for chips in final_chips_by_player.values()):
            return index
    return None


def _final_chips_from_summary(summary: Dict) -> Dict[str, int]:
    chips_by_player: Dict[str, int] = {}
    for final_hand in summary.get("final_hands", []) or []:
        player_name = final_hand.get("player_name")
        if player_name and "final_chips" in final_hand:
            try:
                chips_by_player[player_name] = int(final_hand.get("final_chips") or 0)
            except (TypeError, ValueError):
                pass
    for action_record in summary.get("action_records", []) or []:
        player_name = action_record.get("player_name")
        if player_name and player_name not in chips_by_player and "chips_after" in action_record:
            try:
                chips_by_player[player_name] = int(action_record.get("chips_after") or 0)
            except (TypeError, ValueError):
                pass
    return chips_by_player


def _calculate_gini(values: List[int]) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(max(value, 0) for value in values)
    total = sum(sorted_values)
    if total <= 0:
        return 0.0
    count = len(sorted_values)
    weighted_sum = sum((2 * index - count - 1) * value for index, value in enumerate(sorted_values, start=1))
    return weighted_sum / (count * total)


def _build_transcript_samples(simulation, sample_count: int = 3) -> List[Dict[str, Any]]:
    samples: List[Dict[str, Any]] = []
    for summary in (getattr(simulation, "hand_summaries", []) or [])[:sample_count]:
        sample = _build_hand_transcript_sample(summary)
        if sample:
            samples.append(sample)
    return samples


def _build_poor_blunder_samples(simulation, sample_count: int = 25) -> List[Dict[str, Any]]:
    samples: List[Dict[str, Any]] = []
    for summary in getattr(simulation, "hand_summaries", []) or []:
        profiles = summary.get("ai_styles") or {}
        for action_record in summary.get("action_records", []) or []:
            evaluation = action_record.get("decision_evaluation") or {}
            grade = str(evaluation.get("grade", "")).lower()
            if grade not in {"poor", "blunder"}:
                continue
            player_name = action_record.get("player_name") or "unknown"
            classification = _classify_poor_blunder(action_record, evaluation)
            equity = _evaluation_metric(evaluation, "equity")
            pot_odds = _evaluation_metric(evaluation, "pot_odds")
            sample = {
                "hand_number": summary.get("hand_index") or summary.get("hand_number") or 0,
                "player_name": player_name,
                "profile": profiles.get(player_name, "unknown"),
                "phase": action_record.get("phase") or "unknown",
                "action": action_record.get("action") or "unknown",
                "amount": action_record.get("amount"),
                "grade": grade,
                "score": evaluation.get("score"),
                "classification": classification,
                "risk_tags": _public_risk_tags(evaluation.get("risk_tags") or []),
                "public_board": _public_board_for_phase(summary, action_record.get("phase")),
                "pot": action_record.get("pot"),
                "to_call": action_record.get("to_call"),
                "equity": equity,
                "pot_odds": pot_odds,
            }
            sample.update(_pot_odds_audit_split(classification, equity, pot_odds))
            samples.append({key: value for key, value in sample.items() if value is not None})
            if len(samples) >= sample_count:
                return samples
    return samples


def _evaluation_metric(evaluation: Dict[str, Any], name: str) -> Any:
    if name in evaluation:
        return evaluation.get(name)
    metrics_value = evaluation.get("metrics")
    metrics = metrics_value if isinstance(metrics_value, dict) else {}
    return metrics.get(name)


def _pot_odds_audit_split(classification: str, equity_value: Any, pot_odds_value: Any) -> Dict[str, Any]:
    if classification != "pot-odds call mistake":
        return {}
    if equity_value is None or pot_odds_value is None:
        return {
            "audit_split": "insufficient_public_context",
            "audit_basis": "missing_public_equity_or_pot_odds",
        }
    try:
        equity = float(equity_value)
        pot_odds = float(pot_odds_value)
    except (TypeError, ValueError):
        return {
            "audit_split": "insufficient_public_context",
            "audit_basis": "missing_public_equity_or_pot_odds",
        }

    equity_edge = round(equity - pot_odds, 4)
    if equity_edge < 0:
        split = "true_negative_equity_call"
    else:
        split = "evaluator_false_positive_candidate"
    return {
        "audit_split": split,
        "audit_basis": "public_equity_vs_pot_odds",
        "equity_edge": equity_edge,
    }


def _classify_poor_blunder(action_record: Dict[str, Any], evaluation: Dict[str, Any]) -> str:
    risk_tags = set(_public_risk_tags(evaluation.get("risk_tags") or []))
    action = str(action_record.get("action") or "").lower()
    phase = str(action_record.get("phase") or "").lower()
    if "overfold" in risk_tags or action == "fold":
        return "overfold"
    if "pot_odds" in risk_tags or "bad_call" in risk_tags or "negative_pot_odds_call" in risk_tags:
        return "pot-odds call mistake"
    if "low_equity_bluff" in risk_tags or "high_risk_bluff" in risk_tags or (action in {"bet", "raise", "all-in"} and "bluff" in risk_tags):
        return "low-equity bluff"
    if phase == "preflop" and action in {"call", "raise", "all-in"}:
        return "weak preflop defend"
    if phase == "river" and action in {"call", "bet", "raise", "all-in"}:
        return "river large bet/call mistake"
    if "missed_value" in risk_tags:
        return "missed value with strong hand"
    if "draw" in risk_tags or "semi_bluff" in risk_tags:
        return "draw equity/semi-bluff miscalibration"
    if "evaluator_false_positive" in risk_tags:
        return "evaluator false positive"
    return "unclassified"


def _public_risk_tags(risk_tags: List[Any]) -> List[str]:
    public_tags = []
    for tag in risk_tags:
        text = str(tag)
        lowered = text.lower()
        if any(token in lowered for token in ("hole", "card", "deck", "private", "hidden", "seed")):
            continue
        public_tags.append(text)
    return public_tags


def _public_board_for_phase(summary: Dict[str, Any], phase: Any) -> List[str]:
    phase_boards = _phase_boards(summary)
    phase_text = str(phase or "")
    street_order = ["preflop", "flop", "turn", "river"]
    if phase_text not in street_order:
        return []
    board: List[str] = []
    for street in street_order[: street_order.index(phase_text) + 1]:
        board = phase_boards.get(street, board)
    return [str(card) for card in board]


def _build_hand_transcript_sample(summary: Dict[str, Any]) -> Dict[str, Any]:
    hand_number = summary.get("hand_index") or summary.get("hand_number") or 0
    lines = [f"Hand {hand_number}"]
    phase_boards = _phase_boards(summary)

    for phase in ("preflop", "flop", "turn", "river"):
        board = phase_boards.get(phase)
        if board:
            lines.append(f"{phase} board: {' '.join(str(card) for card in board)}")
        actions = [
            _format_action(action_record)
            for action_record in summary.get("action_records", []) or []
            if action_record.get("phase") == phase
        ]
        if actions:
            lines.append(f"{phase}: {'; '.join(actions)}")

    outcome_metadata = summary.get("outcome_metadata") or {}
    winner_names = [str(winner) for winner in summary.get("winner_names", []) or []]
    winner_text = ", ".join(winner_names) if winner_names else "no listed winner"
    total_pot = summary.get("total_pot", 0)
    winner_reason = outcome_metadata.get("winner_reason") or "unknown"
    lines.append(f"result: {winner_text} won {total_pot} by {winner_reason}")

    if outcome_metadata.get("went_to_showdown") is True:
        revealed_hands = _format_showdown_reveals(
            summary.get("final_hands", []) or [],
            folded_players=_folded_players(summary),
        )
        if revealed_hands:
            lines.append(f"showdown: {revealed_hands}")

    flags = _transcript_flags(summary)
    return {
        "hand_number": hand_number,
        "text": " | ".join(lines),
        "flags": flags,
    }


def _phase_boards(summary: Dict[str, Any]) -> Dict[str, List[str]]:
    boards = {
        str(phase): [str(card) for card in cards]
        for phase, cards in (summary.get("phase_boards") or {}).items()
    }
    for action_record in summary.get("action_records", []) or []:
        phase = action_record.get("phase")
        cards = action_record.get("community_cards")
        if phase and cards and phase not in boards:
            boards[str(phase)] = [str(card) for card in cards]
    return boards


def _format_action(action_record: Dict[str, Any]) -> str:
    player_name = action_record.get("player_name") or "unknown"
    action = str(action_record.get("action") or "unknown")
    amount = action_record.get("amount")
    if amount in (None, 0):
        return f"{player_name} {action}"
    return f"{player_name} {action} {amount}"


def _format_showdown_reveals(final_hands: List[Dict[str, Any]], folded_players: Optional[set[str]] = None) -> str:
    folded_players = folded_players or set()
    reveals = []
    for final_hand in final_hands:
        player_name = final_hand.get("player_name")
        hole_cards = final_hand.get("hole_cards") or []
        if not player_name or not hole_cards or player_name in folded_players:
            continue
        hand_rank = final_hand.get("hand_rank")
        reveal = f"{player_name} [{' '.join(str(card) for card in hole_cards)}]"
        if hand_rank:
            reveal = f"{reveal} {hand_rank}"
        reveals.append(reveal)
    return "; ".join(reveals)


def _folded_players(summary: Dict[str, Any]) -> set[str]:
    return {
        str(action_record.get("player_name"))
        for action_record in summary.get("action_records", []) or []
        if action_record.get("player_name") and str(action_record.get("action", "")).lower() == "fold"
    }


def _transcript_flags(summary: Dict[str, Any]) -> List[str]:
    flags = []
    preflop_aggressor = None
    for action_record in summary.get("action_records", []) or []:
        if action_record.get("phase") == "preflop" and action_record.get("action") in {"raise", "bet", "all-in"}:
            preflop_aggressor = action_record.get("player_name")

    cbet_seen = False
    for action_record in summary.get("action_records", []) or []:
        if action_record.get("phase") != "flop":
            continue
        action = action_record.get("action")
        player_name = action_record.get("player_name")
        if not cbet_seen and preflop_aggressor and player_name == preflop_aggressor and action in {"bet", "raise", "all-in"}:
            flags.append("c-bet")
            cbet_seen = True
            continue
        if cbet_seen and action == "fold":
            flags.append("fold-to-cbet")
            break

    return flags or ["no-obvious-issue"]


def _metric_spread(profile_metrics: Dict[str, ProfilePokerMetrics], attr: str) -> float:
    values = [getattr(metric, attr, 0.0) for metric in profile_metrics.values()]
    return max(values) - min(values) if values else 0.0


def _collect_player_profiles(simulation) -> Dict[str, str]:
    profiles = dict(getattr(simulation, "player_profiles", {}) or {})
    for summary in getattr(simulation, "hand_summaries", []) or []:
        for player_name, profile in (summary.get("ai_styles") or {}).items():
            if player_name and profile:
                profiles[player_name] = profile
    return profiles


def _weighted_average(metrics: List[PlayerPokerMetrics], value_attr: str, weight_attr: str,
                      fallback_weight: Optional[str] = None) -> float:
    total_weight = 0
    weighted_sum = 0.0
    for metric in metrics:
        weight = getattr(metric, weight_attr, 0)
        if not weight and fallback_weight:
            weight = getattr(metric, fallback_weight, 0)
        total_weight += weight
        weighted_sum += getattr(metric, value_attr, 0.0) * weight
    return weighted_sum / total_weight if total_weight else 0.0

def _players_in_hand(summary: Dict, metrics: Dict[str, PlayerPokerMetrics]) -> set:
    players = set()
    for action in summary.get("action_records", []) or []:
        player_name = action.get("player_name")
        if player_name:
            players.add(player_name)
    for player_hand in summary.get("final_hands", []) or []:
        player_name = player_hand.get("player_name")
        if player_name:
            players.add(player_name)
    for winner in summary.get("winner_names", []) or []:
        players.add(winner)
    return players


def evaluate_benchmark_gates(
    artifact: Optional[Dict[str, Any]],
    expected_protocol: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Evaluate a multi-seed benchmark artifact against benchmark gate criteria.

    The default expected protocol is the full primary gate. Callers may pass an
    explicit reduced protocol for bounded diagnostic runs so those runs are
    evaluated against their declared scope instead of being mislabeled as a
    failed full-primary gate.
    """
    protocol = dict(expected_protocol or BENCHMARK_GATE_PROTOCOL)
    checks: List[Dict[str, Any]] = []
    if not isinstance(artifact, dict):
        return _gate_result(
            "NOT_RUN",
            [_gate_check("artifact", "NOT_RUN", "readable JSON object", type(artifact).__name__)],
            protocol,
        )

    benchmark = artifact.get("benchmark") if isinstance(artifact.get("benchmark"), dict) else {}
    runs = artifact.get("runs") if isinstance(artifact.get("runs"), list) else []
    summary = artifact.get("summary") if isinstance(artifact.get("summary"), dict) else {}

    checks.append(_check_benchmark_metadata(benchmark, runs, protocol))
    checks.append(_check_summary_metrics(summary))
    checks.extend(_check_runs(runs, protocol))
    checks.extend(_check_phase3_quality_thresholds(runs))
    checks.append(_check_json_serializable(artifact))

    if any(check["status"] == "FAIL" for check in checks):
        status = "FAIL"
    elif any(check["status"] == "NOT_RUN" for check in checks):
        status = "NOT_RUN"
    elif any(check["status"] == "WARN" for check in checks):
        status = "WARN"
    else:
        status = "PASS"
    return _gate_result(status, checks, protocol)


def _gate_result(status: str, checks: List[Dict[str, Any]], protocol: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "gate_version": BENCHMARK_GATE_VERSION,
        "status": status,
        "protocol": dict(protocol),
        "checks": checks,
    }


def _gate_check(name: str, status: str, threshold: str, observed: Any) -> Dict[str, Any]:
    return {
        "name": name,
        "status": status,
        "threshold": threshold,
        "observed": observed,
    }


def _check_benchmark_metadata(benchmark: Dict[str, Any], runs: List[Dict[str, Any]], protocol: Dict[str, Any]) -> Dict[str, Any]:
    observed = {key: benchmark.get(key) for key in protocol}
    observed["run_count"] = len(runs)
    protocol_matches = all(benchmark.get(key) == expected for key, expected in protocol.items())
    run_count_matches = len(runs) == len(protocol["seeds"])
    has_timestamp = bool(benchmark.get("generated_at"))
    status = "PASS" if protocol_matches and run_count_matches and has_timestamp else "FAIL"
    return _gate_check("benchmark_metadata", status, "declared benchmark protocol", observed)


def _check_summary_metrics(summary: Dict[str, Any]) -> Dict[str, Any]:
    missing = []
    for metric in sorted(_REQUIRED_SUMMARY_METRICS):
        rollup = summary.get(metric)
        if not isinstance(rollup, dict) or not {"mean", "std", "min", "max"}.issubset(rollup):
            missing.append(metric)
    status = "PASS" if not missing else "FAIL"
    return _gate_check("multi_seed_summary", status, "mean/std/min/max for required numeric metrics", missing or "complete")


def _check_runs(runs: List[Dict[str, Any]], protocol: Dict[str, Any]) -> List[Dict[str, Any]]:
    hands_per_seed = protocol["hands_per_seed"]
    return [
        _aggregate_run_check("completion", f"each run hands_played == {hands_per_seed}", _completion_failure(runs, protocol)),
        _aggregate_run_check("runtime_errors", "every run errors == []", _runtime_error_failure(runs)),
        _aggregate_run_check("action_coverage", "every run total_actions > 0", _action_coverage_failure(runs)),
        _aggregate_run_check("illegal_action_rate", "every run illegal_action_rate == 0.0", _illegal_action_failure(runs)),
        _aggregate_run_check("required_metrics", "every run includes required top-level metrics", _required_metric_failure(runs)),
        _aggregate_run_check("transcript_availability", "1 <= len(transcript_samples) <= 3 for completed runs", _transcript_availability_failure(runs)),
        _aggregate_run_check("transcript_safety", "no private/deck/hidden-state tokens in transcript text", _transcript_safety_failure(runs)),
        _aggregate_run_check("profile_coverage", "every run includes required built-in archetype profile metrics", _profile_coverage_failure(runs)),
    ]


def _check_phase3_quality_thresholds(runs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        _threshold_run_check(
            "average_decision_score",
            "every run average_decision_score >= 70.0",
            _numeric_threshold_failure(runs, "average_decision_score", _AVERAGE_DECISION_SCORE_WARN_THRESHOLD),
        ),
        _threshold_run_check(
            "style_separability_score",
            "every run style_separability_score >= 0.20",
            _numeric_threshold_failure(runs, "style_separability_score", _STYLE_SEPARABILITY_WARN_THRESHOLD),
        ),
        _threshold_run_check(
            "poor_blunder_rate",
            "every run poor+blunder share <= 10%",
            _grade_share_threshold_failure(runs, {"poor", "blunder"}, _POOR_BLUNDER_RATE_WARN_THRESHOLD),
        ),
        _threshold_run_check(
            "blunder_rate",
            "every run blunder share <= 1%",
            _grade_share_threshold_failure(runs, {"blunder"}, _BLUNDER_RATE_WARN_THRESHOLD),
        ),
    ]


def _aggregate_run_check(name: str, threshold: str, failure: Optional[Any]) -> Dict[str, Any]:
    return _gate_check(name, "FAIL" if failure else "PASS", threshold, failure or "ok")


def _threshold_run_check(name: str, threshold: str, failure: Optional[Any]) -> Dict[str, Any]:
    return _gate_check(name, "WARN" if failure else "PASS", threshold, failure or "ok")


def _completion_failure(runs: List[Dict[str, Any]], protocol: Dict[str, Any]) -> Optional[Any]:
    for run in runs:
        if run.get("hands_played") != protocol["hands_per_seed"]:
            return {"seed": run.get("seed"), "hands_played": run.get("hands_played")}
    return None


def _runtime_error_failure(runs: List[Dict[str, Any]]) -> Optional[Any]:
    for run in runs:
        if run.get("errors"):
            return {"seed": run.get("seed"), "errors": run.get("errors")}
    return None


def _action_coverage_failure(runs: List[Dict[str, Any]]) -> Optional[Any]:
    for run in runs:
        if not isinstance(run.get("total_actions"), (int, float)) or run.get("total_actions", 0) <= 0:
            return {"seed": run.get("seed"), "total_actions": run.get("total_actions")}
    return None


def _illegal_action_failure(runs: List[Dict[str, Any]]) -> Optional[Any]:
    for run in runs:
        if run.get("illegal_action_rate") != 0.0:
            return {"seed": run.get("seed"), "illegal_action_rate": run.get("illegal_action_rate")}
    return None


def _required_metric_failure(runs: List[Dict[str, Any]]) -> Optional[Any]:
    for run in runs:
        missing = sorted(_REQUIRED_RUN_METRICS - set(run))
        if missing:
            return {"seed": run.get("seed"), "missing": missing}
    return None


def _transcript_availability_failure(runs: List[Dict[str, Any]]) -> Optional[Any]:
    for run in runs:
        samples = run.get("transcript_samples") or []
        if run.get("hands_played", 0) > 0 and not (1 <= len(samples) <= 3):
            return {"seed": run.get("seed"), "sample_count": len(samples)}
    return None


def _transcript_safety_failure(runs: List[Dict[str, Any]]) -> Optional[str]:
    for run in runs:
        for sample in run.get("transcript_samples") or []:
            text = str(sample.get("text", "")).lower()
            for token in _FORBIDDEN_TRANSCRIPT_TOKENS:
                if token in text:
                    return f"forbidden token: {token}"
        audit_payload = json.dumps(run.get("poor_blunder_samples") or [], ensure_ascii=False).lower()
        for token in _FORBIDDEN_TRANSCRIPT_TOKENS:
            if token in audit_payload:
                return f"forbidden token in poor_blunder_samples: {token}"
    return None


def _profile_coverage_failure(runs: List[Dict[str, Any]]) -> Optional[Any]:
    for run in runs:
        profiles = set((run.get("profile_metrics") or {}).keys())
        missing = sorted(_REQUIRED_PROFILE_METRICS - profiles)
        if missing:
            return {"seed": run.get("seed"), "missing_profiles": missing}
    return None


def _numeric_threshold_failure(runs: List[Dict[str, Any]], metric: str, minimum: float) -> Optional[Any]:
    for run in runs:
        try:
            value = float(run.get(metric, 0.0) or 0.0)
        except (TypeError, ValueError):
            value = 0.0
        if value < minimum:
            return {"seed": run.get("seed"), metric: value}
    return None


def _grade_share_threshold_failure(runs: List[Dict[str, Any]], grades: set[str], maximum: float) -> Optional[Any]:
    for run in runs:
        distribution = run.get("grade_distribution") or {}
        total = sum(int(count or 0) for count in distribution.values())
        count = sum(int(distribution.get(grade, 0) or 0) for grade in grades)
        share = count / total if total else 0.0
        if share > maximum:
            return {"seed": run.get("seed"), "share": share, "count": count, "total": total}
    return None


def _check_json_serializable(artifact: Dict[str, Any]) -> Dict[str, Any]:
    try:
        json.dumps(artifact, ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        return _gate_check("json_safety", "FAIL", "standard JSON serializable artifact", str(exc))
    return _gate_check("json_safety", "PASS", "standard JSON serializable artifact", "ok")


def benchmark_ai_system(num_hands: int = 1000, player_count: int = 4,
                        output_path: Optional[str] = None,
                        starting_chips: int = 1000,
                        seed: Optional[int] = None,
                        ai_equity_simulations: Optional[int] = None) -> AISystemEvaluationReport:
    report = evaluate_ai_system(
        num_hands=num_hands,
        player_count=player_count,
        starting_chips=starting_chips,
        seed=seed,
        ai_equity_simulations=ai_equity_simulations,
    )
    report.benchmark = {
        "hands_requested": num_hands,
        "player_count": player_count,
        "starting_chips": starting_chips,
        "seed": seed,
        "ai_equity_simulations": ai_equity_simulations,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def benchmark_ai_system_multi_seed(
    seeds: Optional[List[int]] = None,
    hands_per_seed: int = 500,
    player_count: int = 4,
    output_path: Optional[str] = None,
    starting_chips: int = 10000,
    ai_equity_simulations: Optional[int] = 5,
    progress_path: Optional[str] = None,
) -> Dict[str, object]:
    """Run the AI benchmark across multiple deterministic seeds and summarize variance.

    The canonical primary gate remains 10 seeds × 500 hands.  Multi-seed
    benchmark runs default to fewer equity rollouts per AI decision so the full
    gate can finish in a practical local/CI window; pass ``None`` to use the
    runtime AI default of 500 equity rollouts.
    """
    selected_seeds = list(range(10)) if seeds is None else list(seeds)
    runs = []
    benchmark_metadata = {
        "hands_per_seed": hands_per_seed,
        "player_count": player_count,
        "starting_chips": starting_chips,
        "seeds": selected_seeds,
        "ai_equity_simulations": ai_equity_simulations,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    for seed in selected_seeds:
        report = evaluate_ai_system(
            num_hands=hands_per_seed,
            player_count=player_count,
            starting_chips=starting_chips,
            seed=seed,
            ai_equity_simulations=ai_equity_simulations,
        )
        run_data = report.to_dict()
        run_data["seed"] = seed
        runs.append(run_data)
        if progress_path:
            _write_multi_seed_progress(
                progress_path=progress_path,
                benchmark_metadata=benchmark_metadata,
                runs=runs,
                selected_seeds=selected_seeds,
                status="running",
            )

    multi_seed_report: Dict[str, object] = {
        "benchmark": benchmark_metadata,
        "summary": _summarize_seed_runs(runs),
        "runs": runs,
    }
    if progress_path:
        _write_multi_seed_progress(
            progress_path=progress_path,
            benchmark_metadata=benchmark_metadata,
            runs=runs,
            selected_seeds=selected_seeds,
            status="completed",
            summary=multi_seed_report["summary"],
        )
    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(multi_seed_report, ensure_ascii=False, indent=2), encoding="utf-8")
    return multi_seed_report


def _write_multi_seed_progress(
    progress_path: str,
    benchmark_metadata: Dict[str, object],
    runs: List[Dict[str, object]],
    selected_seeds: List[int],
    status: str,
    summary: Optional[Dict[str, Dict[str, float]]] = None,
) -> None:
    """Write an incremental multi-seed benchmark progress artifact."""
    path = Path(progress_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    progress_summary = summary if summary is not None else _summarize_seed_runs(runs)
    progress_artifact: Dict[str, object] = {
        "status": status,
        "benchmark": benchmark_metadata,
        "completed_seeds": [run["seed"] for run in runs],
        "completed_seed_count": len(runs),
        "total_seed_count": len(selected_seeds),
        "summary": progress_summary,
        "runs": runs,
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    path.write_text(json.dumps(progress_artifact, ensure_ascii=False, indent=2), encoding="utf-8")


def _summarize_seed_runs(runs: List[Dict[str, object]]) -> Dict[str, Dict[str, float]]:
    numeric_metrics = [
        "hands_played",
        "total_actions",
        "illegal_action_rate",
        "average_decision_score",
        "style_separability_score",
        "vpip_spread",
        "pfr_spread",
        "aggression_spread",
        "call_rate_spread",
        "largest_stack_share",
        "bustout_rate",
        "stack_gini",
        "profile_calibration_distance",
    ]
    return {
        metric: _mean_std_min_max([float(run.get(metric, 0.0) or 0.0) for run in runs])
        for metric in numeric_metrics
    }


def _mean_std_min_max(values: List[float]) -> Dict[str, float]:
    if not values:
        return {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0}
    return {
        "mean": statistics.fmean(values),
        "std": statistics.pstdev(values),
        "min": min(values),
        "max": max(values),
    }
