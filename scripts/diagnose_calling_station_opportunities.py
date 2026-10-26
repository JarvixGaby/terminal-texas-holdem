"""Observe calling-station action opportunities without changing AI policy or metrics."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from texas_holdem.ai.advanced_ai_engine import AdvancedAIEngine
from texas_holdem.analytics.ai_system_evaluator import summarize_ai_evaluations
from texas_holdem.analytics.headless_simulation import run_ai_only_simulation


def _price_margin_bucket(margin: float) -> str:
    if margin < -0.10:
        return "<-10pp"
    if margin < 0:
        return "-10..0pp"
    if margin < 0.10:
        return "0..+10pp"
    return ">=+10pp"


def diagnose(seeds: list[int], hands_per_seed: int, rollouts: int) -> dict:
    original_equity = AdvancedAIEngine._get_monte_carlo_equity
    original_decision = AdvancedAIEngine.make_decision
    trace: list[dict] = []

    def traced_equity(self, *args, **kwargs):
        equity = original_equity(self, *args, **kwargs)
        self._station_diagnostic_equity = equity
        return equity

    def traced_decision(self, *args, **kwargs):
        action, amount = original_decision(self, *args, **kwargs)
        if self.archetype_profile is not None and self.archetype_profile.name == "calling_station":
            cost = kwargs["current_bet"]
            pot = kwargs["pot_size"]
            trace.append({
                "phase": kwargs["phase"],
                "cost": cost,
                "price": cost / (pot + cost) if cost > 0 and pot + cost > 0 else 0.0,
                "equity": self._station_diagnostic_equity,
                "action": action,
            })
        return action, amount

    AdvancedAIEngine._get_monte_carlo_equity = traced_equity
    AdvancedAIEngine.make_decision = traced_decision
    runs = []
    try:
        for seed in seeds:
            trace.clear()
            simulation = run_ai_only_simulation(
                num_hands=hands_per_seed,
                player_count=4,
                starting_chips=10000,
                seed=seed,
                ai_equity_simulations=rollouts,
            )
            station_names = {
                name for name, profile in simulation.player_profiles.items()
                if profile == "calling_station"
            }
            actual = [
                action
                for hand in simulation.hand_summaries
                for action in hand["action_records"]
                if action["player_name"] in station_names
            ]
            if len(trace) != len(actual):
                raise RuntimeError(f"seed {seed}: {len(trace)} decisions != {len(actual)} recorded actions")
            if any(decision["action"] != action["action"] for decision, action in zip(trace, actual)):
                raise RuntimeError(f"seed {seed}: decision and recorded action differ")
            if simulation.errors or simulation.hands_completed != hands_per_seed:
                raise RuntimeError(
                    f"seed {seed}: completed {simulation.hands_completed}/{hands_per_seed}; "
                    f"errors={simulation.errors}"
                )

            evaluation = summarize_ai_evaluations(simulation)
            station = evaluation.to_dict()["profile_metrics"]["calling_station"]
            counts = Counter(
                (item["phase"], "facing" if item["cost"] > 0 else "free", item["action"])
                for item in trace
            )
            margins = Counter(
                (item["phase"], item["action"], _price_margin_bucket(item["equity"] - item["price"]))
                for item in trace if item["cost"] > 0
            )
            run = {
                "seed": seed,
                "hands_completed": simulation.hands_completed,
                "errors": simulation.errors,
                "illegal_action_rate": evaluation.illegal_action_rate,
                "station_actions": len(trace),
                "station_call_rate": station["call_rate"],
                "counts": [
                    {"phase": phase, "opportunity": opportunity, "action": action, "count": count}
                    for (phase, opportunity, action), count in sorted(counts.items())
                ],
                "facing_price_margin": [
                    {"phase": phase, "action": action, "estimated_equity_minus_price": bucket, "count": count}
                    for (phase, action, bucket), count in sorted(margins.items())
                ],
            }
            runs.append(run)
            print(f"seed {seed}: {simulation.hands_completed} hands, {len(trace)} station actions", flush=True)
    finally:
        AdvancedAIEngine._get_monte_carlo_equity = original_equity
        AdvancedAIEngine.make_decision = original_decision

    return {
        "protocol": {
            "seeds": seeds,
            "hands_per_seed": hands_per_seed,
            "player_count": 4,
            "starting_chips": 10000,
            "ai_equity_simulations": rollouts,
        },
        "runs": runs,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2])
    parser.add_argument("--hands-per-seed", type=int, default=100)
    parser.add_argument("--rollouts", type=int, default=500)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.seeds or args.hands_per_seed <= 0 or args.rollouts <= 0:
        parser.error("seeds must be nonempty; hands and rollouts must be positive")
    result = diagnose(args.seeds, args.hands_per_seed, args.rollouts)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
