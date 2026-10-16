# Phase 3 Primary Benchmark Gate Follow-up

Date: 2026-05-13

## Scope

This follow-up completes the `docs/active_plan.md` item to make the full primary AI benchmark gate runnable with a practical execution strategy while preserving the canonical primary target.

Boundary: this remains evaluation-loop hardening only. No online room, WebSocket/API, auth/account, external-agent runtime, real-money, or solver/GTO work was implemented.

## Root cause of the 600-second timeout

The previous full primary benchmark attempted the canonical protocol:

- `seeds`: `[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]`
- `hands_per_seed`: `500`
- `player_count`: `4`
- `starting_chips`: `10000`

Profiling a 10-hand run showed the runtime was dominated by per-decision Monte Carlo equity simulation:

```text
advanced_ai_engine.py -> optimized_odds_calculator.AIEquityCalculator.get_equity(...)
```

At the runtime default of 500 equity rollouts per AI decision, a 50-hand sample took about `19.7s`, making the full `10 × 500` gate too close to or beyond a 600-second interactive budget.

## Practical execution strategy

The canonical primary gate remains `10 seeds × 500 hands`; the execution profile is now configurable separately from the protocol:

- `AIEquityCalculator(simulation_count=...)` accepts a rollout count.
- `run_ai_only_simulation(..., ai_equity_simulations=...)` can inject a benchmark-specific equity calculator.
- `evaluate_ai_system(...)`, `benchmark_ai_system(...)`, and `benchmark_ai_system_multi_seed(...)` propagate the setting.
- `benchmark_ai_system_multi_seed(...)` defaults to `ai_equity_simulations=5` so the full primary protocol can complete in a practical local run.
- Passing `ai_equity_simulations=None` preserves the runtime AI default behavior of 500 rollouts.

This keeps scope explicit: reduced diagnostics are still distinct from the canonical primary benchmark, and the full primary run declares the benchmark execution profile in the artifact metadata.

## Commands and validation

Focused regression validation after the code changes:

```bash
python3 -m pytest -q tests/test_ai_system_evaluator.py tests/test_headless_simulation.py
```

Result:

```text
27 passed in 15.90s
```

Full primary gate generation:

```bash
python3 - <<'PY'
from ai_system_evaluator import benchmark_ai_system_multi_seed, evaluate_benchmark_gates
import json, time

output_path='docs/reports/2026-05-13-phase3-primary-benchmark-gate.json'
gate_output_path='docs/reports/2026-05-13-phase3-primary-benchmark-gate-evaluation.json'
start=time.perf_counter()
artifact = benchmark_ai_system_multi_seed(output_path=output_path)
gate = evaluate_benchmark_gates(artifact)
with open(gate_output_path, 'w', encoding='utf-8') as f:
    json.dump(gate, f, ensure_ascii=False, indent=2)
print(round(time.perf_counter() - start, 2), gate['status'])
PY
```

Result:

```text
407.60 seconds, WARN
```

Artifacts:

- `docs/reports/2026-05-13-phase3-primary-benchmark-gate.json`
- `docs/reports/2026-05-13-phase3-primary-benchmark-gate-evaluation.json`

## Gate result

Machine gate status:

```text
WARN
```

Hard gates all passed:

| Check | Status |
|---|---|
| benchmark metadata | PASS |
| multi-seed summary | PASS |
| completion | PASS |
| runtime errors | PASS |
| action coverage | PASS |
| illegal action rate | PASS |
| required metrics | PASS |
| transcript availability | PASS |
| transcript safety | PASS |
| profile coverage | PASS |
| JSON safety | PASS |

Soft quality gates with warnings:

| Check | Status | Observed |
|---|---|---|
| average decision score | WARN | seed 0 scored `69.6395`, below `70.0` |
| poor+blunder rate | WARN | seed 5 had `164 / 1582 = 10.37%`, above `10%` |
| blunder rate | WARN | seed 2 had `28 / 2280 = 1.23%`, above `1%` |

Interpretation: the canonical full primary protocol is now runnable and produced a machine-readable artifact. It is not a clean PASS yet; it is a valid full-primary WARN that should drive the next tuning/audit stage.

## Metrics summary

Full benchmark summary over `10 seeds × 500 hands`:

| Metric | Mean | Std | Min | Max | Gate read |
|---|---:|---:|---:|---:|---|
| hands played | 500.0000 | 0.0000 | 500.0000 | 500.0000 | PASS completion |
| total actions | 1895.6000 | 310.5966 | 1581.0000 | 2466.0000 | PASS coverage |
| illegal action rate | 0.0000 | 0.0000 | 0.0000 | 0.0000 | PASS hard gate |
| average decision score | 69.6765 | 0.5704 | 68.6346 | 70.5434 | WARN soft gate |
| style separability score | 0.3073 | 0.0205 | 0.2826 | 0.3477 | PASS soft gate |
| VPIP spread | 0.1671 | 0.0178 | 0.1320 | 0.1980 | Informational |
| PFR spread | 0.1116 | 0.0156 | 0.0860 | 0.1439 | Informational |
| aggression spread | 3.9970 | 1.6091 | 2.0840 | 6.9596 | Informational |
| call-rate spread | 0.1692 | 0.0271 | 0.1270 | 0.2168 | Informational |
| largest stack share | 0.6265 | 0.1715 | 0.3861 | 0.9618 | Informational |
| bustout rate | 0.3500 | 0.1225 | 0.2500 | 0.5000 | Informational |
| stack gini | 0.5338 | 0.1156 | 0.3210 | 0.7309 | Informational |

## Per-seed summary

| Seed | Actions | Avg decision score | Style separability | Illegal action rate | Errors |
|---:|---:|---:|---:|---:|---|
| 0 | 1581 | 69.639 | 0.330 | 0.0 | `[]` |
| 1 | 1643 | 69.702 | 0.326 | 0.0 | `[]` |
| 2 | 2280 | 69.985 | 0.303 | 0.0 | `[]` |
| 3 | 1774 | 69.789 | 0.316 | 0.0 | `[]` |
| 4 | 1888 | 69.804 | 0.291 | 0.0 | `[]` |
| 5 | 1582 | 68.635 | 0.348 | 0.0 | `[]` |
| 6 | 2466 | 70.543 | 0.289 | 0.0 | `[]` |
| 7 | 1752 | 70.468 | 0.283 | 0.0 | `[]` |
| 8 | 1699 | 69.099 | 0.295 | 0.0 | `[]` |
| 9 | 2291 | 69.101 | 0.292 | 0.0 | `[]` |

## Next stage

Recommended next work:

1. Audit seed 5 poor/blunder decisions and seed 2 blunders using transcript/action records.
2. Tune obvious poor/blunder cases without weakening legality or profile separability.
3. Re-run the full primary gate after tuning and require no hard failures, then drive soft warnings toward PASS.
4. Consider adding progress output or incremental artifact writing for long benchmark runs so future interactive runs are easier to monitor.
