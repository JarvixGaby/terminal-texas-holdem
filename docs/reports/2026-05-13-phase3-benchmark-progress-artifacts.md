# Phase 3 Benchmark Progress Artifacts

Date: 2026-05-13

## Scope

This report documents a small Phase 3 benchmark runner improvement: long multi-seed benchmark runs can now write an optional incremental progress artifact after each completed seed.

Boundary: this change does not alter AI strategy, evaluator scoring, gate thresholds, online/API/WebSocket/auth behavior, or the default benchmark output format when progress writing is not requested.

## Problem

The primary Phase 3 benchmark (`10 seeds × 500 hands`) can take several minutes. Before this change, no machine-readable artifact was written until all seeds completed. If a run was interrupted or appeared idle, the operator had no durable progress signal beyond process status.

## Change

`benchmark_ai_system_multi_seed(...)` now accepts an optional parameter:

```python
progress_path: Optional[str] = None
```

When omitted, behavior is unchanged.

When provided, the runner writes JSON to `progress_path` after each seed and once more at completion. The progress artifact contains:

- `status`: `running` or `completed`
- `benchmark`: the same benchmark metadata used by the final artifact
- `completed_seeds`
- `completed_seed_count`
- `total_seed_count`
- `summary`: current partial summary while running, final summary when completed
- `runs`: completed per-seed reports so far
- `updated_at`

This allows a long benchmark process to be inspected safely while it is still running.

## Verification

### Focused RED/GREEN test

Added:

```text
test_multi_seed_benchmark_writes_progress_after_each_seed
```

The test monkeypatches `evaluate_ai_system(...)` and checks that the progress artifact exists before the next seed starts, proving that progress is written incrementally rather than only at final completion.

Focused validation:

```bash
python3 -m pytest -q tests/test_ai_system_evaluator.py::test_multi_seed_benchmark_writes_progress_after_each_seed tests/test_ai_system_evaluator.py::test_multi_seed_benchmark_reports_mean_std_min_max
```

Result:

```text
2 passed in 0.03s
```

### Related tests

```bash
python3 -m pytest -q tests/test_ai_system_evaluator.py tests/test_headless_simulation.py tests/test_decision_evaluator.py
```

Result:

```text
61 passed in 13.11s
```

### Smoke benchmark

A small live benchmark smoke test wrote both final and progress artifacts using:

```python
benchmark_ai_system_multi_seed(
    seeds=[0, 1],
    hands_per_seed=5,
    player_count=4,
    starting_chips=10000,
    output_path="docs/reports/_phase3-progress-smoke-output.json",
    progress_path="docs/reports/_phase3-progress-smoke-progress.json",
    ai_equity_simulations=2,
)
```

Observed result:

```json
{
  "output_runs": 2,
  "progress_status": "completed",
  "completed_seeds": [0, 1],
  "summary_matches": true,
  "runs_match": true
}
```

Temporary smoke artifacts were removed after verification.

### Full suite

```bash
python3 -m pytest -q
```

Result:

```text
257 passed in 30.57s
```

## How to use for future long runs

Example:

```python
from ai_system_evaluator import benchmark_ai_system_multi_seed, evaluate_benchmark_gates

artifact = benchmark_ai_system_multi_seed(
    output_path="docs/reports/phase3-primary.json",
    progress_path="docs/reports/phase3-primary.progress.json",
)
gate = evaluate_benchmark_gates(artifact)
```

While the benchmark is still running, inspect progress with:

```bash
python3 - <<'PY'
import json
from pathlib import Path
p = Path('docs/reports/phase3-primary.progress.json')
data = json.loads(p.read_text())
print(data['status'], data['completed_seed_count'], '/', data['total_seed_count'])
print(data['completed_seeds'])
print(data['summary'].get('average_decision_score'))
PY
```

## Effect validation for evaluator/AI tuning

For future Phase 3 tuning, success should be validated with all of the following, not with a single benchmark average:

1. Focused regression tests for the exact behavior being changed.
2. Related evaluator/headless/benchmark tests.
3. Full test suite.
4. Full or reduced benchmark gate depending on change size.
5. Pre/post artifact comparison covering:
   - gate status
   - illegal action rate
   - average decision score mean/min
   - poor+blunder rate
   - blunder rate
   - style separability score
   - transcript safety
6. Representative example audit when a soft gate moves significantly.

The preflop-fold calibration validated this way: the post-calibration primary artifact moved from `WARN` to `PASS`, poor+blunder fell from `8.08%` to `1.13%`, blunder fell from `0.99%` to `0.12%`, illegal action rate remained `0.0`, and style separability stayed within gate.

## Next recommended work

1. Add explicit AI profile target bands so style quality is judged by intended archetype behavior, not only broad separability spread.
2. Keep progress artifacts enabled for long primary gate reruns.
3. Continue poor/blunder audit only with focused regressions and pre/post artifact comparisons.
