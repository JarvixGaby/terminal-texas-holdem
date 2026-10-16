# Phase 3 Profile Calibration Target Bands

Date: 2026-05-16

## Scope

This report documents Phase 3 Stage 3.2: explicit target-band calibration for the built-in AI archetype profiles.

Boundary: this slice adds measurement and reporting only. It does not tune AI policy, change benchmark gate thresholds, change public/private state schemas, or implement online/API/WebSocket/auth/platform work.

## What changed

`ai_system_evaluator.py` now emits additive profile calibration fields in AI evaluation reports:

- `profile_calibration`
- `profile_calibration_status`
- `profile_calibration_distance`

These fields are additive. Existing fields such as `profile_metrics`, `weakest_profile`, `style_separability_score`, `vpip_spread`, `pfr_spread`, `aggression_spread`, and `call_rate_spread` are preserved.

Multi-seed benchmark summaries now also include `profile_calibration_distance` mean/std/min/max so calibration drift can be tracked across seeds.

## Target bands

Initial Stage 3.2 bands are intentionally diagnostic. They convert the existing archetype intent into observed metric ranges, but they are not yet benchmark pass/fail gates.

| Profile | Metric | Target band |
|---|---|---:|
| nit | VPIP | 0.08–0.18 |
| nit | PFR | 0.00–0.10 |
| nit | Aggression factor | 0.00–1.20 |
| nit | Call rate | 0.10–0.35 |
| nit | Fold rate | 0.35–0.90 |
| nit | Showdown rate | 0.00–0.35 |
| nit | Poor/blunder rate | 0.00–0.10 |
| nit | Average decision score | 60–100 |
| tight_aggressive | VPIP | 0.16–0.28 |
| tight_aggressive | PFR | 0.12–0.24 |
| tight_aggressive | Aggression factor | 0.80–3.50 |
| tight_aggressive | Call rate | 0.12–0.45 |
| tight_aggressive | Fold rate | 0.20–0.70 |
| tight_aggressive | Showdown rate | 0.05–0.45 |
| tight_aggressive | Poor/blunder rate | 0.00–0.10 |
| tight_aggressive | Average decision score | 60–100 |
| loose_aggressive | VPIP | 0.28–0.45 |
| loose_aggressive | PFR | 0.20–0.34 |
| loose_aggressive | Aggression factor | 1.20–5.00 |
| loose_aggressive | Call rate | 0.15–0.45 |
| loose_aggressive | Fold rate | 0.15–0.65 |
| loose_aggressive | Showdown rate | 0.08–0.55 |
| loose_aggressive | Poor/blunder rate | 0.00–0.10 |
| loose_aggressive | Average decision score | 60–100 |
| calling_station | VPIP | 0.30–0.50 |
| calling_station | PFR | 0.00–0.16 |
| calling_station | Aggression factor | 0.00–1.20 |
| calling_station | Call rate | 0.45–1.00 |
| calling_station | Fold rate | 0.00–0.35 |
| calling_station | Showdown rate | 0.15–0.75 |
| calling_station | Poor/blunder rate | 0.00–0.10 |
| calling_station | Average decision score | 60–100 |

## Reduced calibration benchmark

A bounded diagnostic benchmark was run with progress artifacts enabled:

```bash
python3 - <<'PY'
from ai_system_evaluator import benchmark_ai_system_multi_seed, evaluate_benchmark_gates
import json
from pathlib import Path
artifact_path = Path('docs/reports/2026-05-16-phase3-profile-calibration-reduced-benchmark.json')
progress_path = Path('docs/reports/2026-05-16-phase3-profile-calibration-reduced-benchmark.progress.json')
eval_path = Path('docs/reports/2026-05-16-phase3-profile-calibration-reduced-benchmark-evaluation.json')
artifact = benchmark_ai_system_multi_seed(
    seeds=list(range(10)),
    hands_per_seed=100,
    player_count=4,
    starting_chips=10000,
    output_path=str(artifact_path),
    progress_path=str(progress_path),
    ai_equity_simulations=5,
)
gate = evaluate_benchmark_gates(
    artifact,
    expected_protocol={
        'seeds': list(range(10)),
        'hands_per_seed': 100,
        'player_count': 4,
        'starting_chips': 10000,
    },
)
eval_path.write_text(json.dumps(gate, ensure_ascii=False, indent=2), encoding='utf-8')
PY
```

Artifacts:

- `docs/reports/2026-05-16-phase3-profile-calibration-reduced-benchmark.json`
- `docs/reports/2026-05-16-phase3-profile-calibration-reduced-benchmark.progress.json`
- `docs/reports/2026-05-16-phase3-profile-calibration-reduced-benchmark-evaluation.json`

Gate status for the reduced diagnostic protocol:

```text
PASS
```

Calibration status across seeds:

```text
10 / 10 runs: WARN
```

Mean profile calibration distance:

```text
0.0784549
```

## Target-vs-observed summary

Observed values below are mean/min/max across the reduced `10 seeds × 100 hands` diagnostic benchmark.

| Profile | Metric | Target | Mean | Min | Max | WARN runs |
|---|---|---:|---:|---:|---:|---:|
| nit | VPIP | 0.08–0.18 | 0.0600 | 0.0300 | 0.0800 | 7 |
| nit | PFR | 0.00–0.10 | 0.0307 | 0.0000 | 0.0500 | 0 |
| nit | Aggression factor | 0.00–1.20 | 1.7200 | 0.8667 | 2.6667 | 8 |
| nit | Call rate | 0.10–0.35 | 0.0865 | 0.0337 | 0.1250 | 8 |
| nit | Fold rate | 0.35–0.90 | 0.7057 | 0.6230 | 0.8315 | 0 |
| tight_aggressive | VPIP | 0.16–0.28 | 0.0930 | 0.0600 | 0.1400 | 10 |
| tight_aggressive | PFR | 0.12–0.24 | 0.0530 | 0.0300 | 0.0700 | 10 |
| tight_aggressive | Aggression factor | 0.80–3.50 | 2.9768 | 1.5714 | 5.5455 | 3 |
| tight_aggressive | Call rate | 0.12–0.45 | 0.0666 | 0.0306 | 0.0965 | 10 |
| loose_aggressive | VPIP | 0.28–0.45 | 0.1550 | 0.0900 | 0.1900 | 10 |
| loose_aggressive | PFR | 0.20–0.34 | 0.1330 | 0.0600 | 0.1700 | 10 |
| loose_aggressive | Aggression factor | 1.20–5.00 | 4.1953 | 2.0000 | 7.5000 | 2 |
| loose_aggressive | Call rate | 0.15–0.45 | 0.0691 | 0.0288 | 0.1083 | 10 |
| calling_station | VPIP | 0.30–0.50 | 0.2113 | 0.1300 | 0.3333 | 8 |
| calling_station | PFR | 0.00–0.16 | 0.0154 | 0.0000 | 0.0600 | 0 |
| calling_station | Aggression factor | 0.00–1.20 | 0.9849 | 0.5000 | 2.5000 | 2 |
| calling_station | Call rate | 0.45–1.00 | 0.2303 | 0.1538 | 0.4348 | 10 |
| calling_station | Fold rate | 0.00–0.35 | 0.4745 | 0.2609 | 0.6410 | 8 |

## Interpretation

The reduced benchmark confirms that the measurement surface works and that the existing primary gate remains clean under the reduced protocol. The calibration layer also exposes a useful distinction that style separability alone hides:

1. The AI profiles are distinguishable enough for the existing separability gate.
2. But several profiles are globally tighter/lower-participation than their target bands imply.
3. Calling station behavior is not sticky/cally enough by observed call-rate and fold-rate bands.
4. Tight-aggressive and loose-aggressive profiles under-hit VPIP/PFR bands in this reduced diagnostic.
5. Poker-quality bands are healthy in this diagnostic: poor/blunder and average decision score remain inside target bands.

This should be treated as evidence for future tuning slices, not as a reason to weaken calibration bands immediately.

## Why a full primary rerun was not required for this slice

The canonical `10 seeds × 500 hands` primary benchmark was already clean `PASS` after preflop-fold calibration. This slice only adds additive calibration fields and a reduced diagnostic artifact; it does not change AI policy, legality, transcript safety, or gate thresholds.

A full primary rerun with the new fields is useful before claiming Stage 3.2 as a long-run stable baseline, but it is not required before starting the next evidence-gathering slice. If future work tunes AI policy to reduce calibration WARNs, that tuning must be validated with focused tests, related tests, full suite, and an appropriate pre/post benchmark comparison.

## Verification

RED tests were added first and failed on missing profile calibration fields:

```text
2 failed: KeyError: 'profile_calibration_status' / 'profile_calibration'
```

Focused GREEN validation:

```bash
python3 -m pytest -q tests/test_ai_system_evaluator.py::test_profile_calibration_reports_target_band_distance_and_status tests/test_ai_system_evaluator.py::test_profile_calibration_is_empty_without_known_profile_metrics
```

Result:

```text
2 passed
```

Summary regression validation for multi-seed calibration distance:

```bash
python3 -m pytest -q tests/test_ai_system_evaluator.py::test_multi_seed_benchmark_reports_mean_std_min_max tests/test_ai_system_evaluator.py::test_profile_calibration_reports_target_band_distance_and_status tests/test_ai_system_evaluator.py::test_profile_calibration_is_empty_without_known_profile_metrics
```

Result:

```text
3 passed
```

Focused related validation:

```bash
python3 -m pytest -q tests/test_ai_system_evaluator.py tests/test_ai_profiles.py
```

Result:

```text
24 passed in 9.04s
```

Final validation is recorded in the active plan after full suite and markdown/index checks complete.

## Recommended next work

1. Start Phase 3 Stage 3.3 poor/blunder audit from saved benchmark artifacts.
2. Treat calibration WARNs as tuning candidates only after classifying whether the issue is AI policy, evaluator calibration, or benchmark variance.
3. Keep online/API/WebSocket/auth/platform work deferred until the evaluation loop remains stable over repeated evidence cycles.
