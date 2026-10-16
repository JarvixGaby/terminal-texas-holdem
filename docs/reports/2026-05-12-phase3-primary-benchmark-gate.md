# Phase 3 Primary Benchmark Gate Report

Date: 2026-05-12

## Scope

This report executes Phase 3 Stage 3.1 from `docs/plans/2026-05-12-phase3-ai-evaluation-loop-plan.md`: establish the first repeatable AI benchmark gate for the local Texas Hold'em AI baseline.

Boundary: this is evaluation-loop hardening only. No online room, WebSocket/API, auth/account, external-agent runtime, real-money, or solver/GTO work was implemented.

## Commands Run

### 1. Inspect existing benchmark protocol

```bash
python3 - <<'PY'
from ai_system_evaluator import BENCHMARK_GATE_PROTOCOL
print(BENCHMARK_GATE_PROTOCOL)
PY
```

Result:

```text
{'seeds': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], 'hands_per_seed': 500, 'player_count': 4, 'starting_chips': 10000}
```

### 2. Attempt full primary protocol

Attempted the existing primary protocol: `10 seeds × 500 hands`, `player_count=4`, `starting_chips=10000`.

```bash
python3 - <<'PY'
from ai_system_evaluator import benchmark_ai_system_multi_seed, BENCHMARK_GATE_PROTOCOL, evaluate_benchmark_gates
...
PY
```

Result: timed out at 600 seconds before writing an artifact.

Conclusion: the full primary gate is the correct target protocol, but it is too slow for the current interactive execution budget. Per the Phase 3 plan, this run was reduced and documented rather than silently changing the primary protocol.

### 3. Run reduced bounded benchmark gate

Reduced protocol used for this first Stage 3.1 artifact:

- `seeds`: `[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]`
- `hands_per_seed`: 100
- `player_count`: 4
- `starting_chips`: 10000

Artifact:

- `docs/reports/2026-05-12-phase3-reduced-benchmark-gate.json`

Machine gate evaluation artifact:

- `docs/reports/2026-05-12-phase3-reduced-benchmark-gate-evaluation.json`

### 4. Regression and suite validation

After adding explicit reduced-protocol support and Phase 3 threshold/profile checks to `evaluate_benchmark_gates(...)`:

```bash
python3 -m pytest -q tests/test_ai_system_evaluator.py::test_benchmark_gate_evaluation_accepts_explicit_reduced_protocol
```

Result: `1 passed in 0.02s`.

```bash
python3 -m pytest -q tests/test_ai_system_evaluator.py
```

Result: `17 passed in 2.64s`.

```bash
python3 -m pytest -q tests/test_ai_system_evaluator.py tests/test_headless_simulation.py tests/test_ai_metrics.py
```

Result: `33 passed in 11.76s`.

```bash
python3 -m pytest -q
```

Result: `250 passed in 30.96s`.

## Gate Result

### Machine gate status

After adding explicit expected-protocol support and Phase 3 threshold checks to `evaluate_benchmark_gates(...)`, the reduced diagnostic gate was evaluated against its declared `10 × 100` scope and returned:

```text
WARN
```

Important distinction: this is a **reduced diagnostic gate warning**, not a full primary `10 × 500` gate result. The full primary protocol still timed out in the current interactive execution budget. The warning is caused by one seed falling slightly below the soft average-decision-score threshold; all hard legality, error, metric coverage, profile coverage, transcript, and JSON checks passed.

| Check | Status | Meaning |
|---|---|---|
| benchmark metadata | PASS | Artifact metadata matches declared reduced protocol. |
| multi-seed summary | PASS | Required summary rollups present. |
| completion | PASS | Every run completed 100 hands. |
| runtime errors | PASS | Every run had `errors == []`. |
| action coverage | PASS | Every run had `total_actions > 0`. |
| illegal action rate | PASS | Every run had `illegal_action_rate == 0.0`. |
| required metrics | PASS | Required top-level metrics present. |
| transcript availability | PASS | Transcript samples available for completed runs. |
| transcript safety | PASS | No forbidden private/deck/hidden-state tokens in transcript text. |
| profile coverage | PASS | Every run includes `nit`, `tight_aggressive`, `loose_aggressive`, and `calling_station`. |
| average decision score | WARN | Seed 6 scored `69.8753`, slightly below soft threshold `70.0`. |
| style separability score | PASS | Every run had `style_separability_score >= 0.20`. |
| poor+blunder rate | PASS | Every run stayed below `10%`. |
| blunder rate | PASS | Every run stayed below `1%`. |
| JSON safety | PASS | Artifact is JSON-serializable. |

### Phase 3 reduced-run health verdict

For this reduced Stage 3.1 run:

```text
WARN as reduced diagnostic / NOT a full-primary pass
```

Reason:

- It is not a full `10 × 500` primary gate.
- Within its declared `10 × 100` scope, hard legality, errors, metric completeness, profile coverage, transcript token safety, and JSON safety passed.
- One seed missed the soft average decision score threshold by `0.1247` points.

## Metrics Summary

Reduced benchmark summary over 10 seeds × 100 hands:

| Metric | Mean | Std | Min | Max | Gate read |
|---|---:|---:|---:|---:|---|
| hands played | 100.0000 | 0.0000 | 100.0000 | 100.0000 | Reduced run only |
| total actions | 483.7000 | 62.0452 | 361.0000 | 544.0000 | PASS coverage |
| illegal action rate | 0.0000 | 0.0000 | 0.0000 | 0.0000 | PASS hard gate |
| average decision score | 71.2092 | 0.9042 | 69.8753 | 72.4388 | WARN: mean >= 70, one seed below 70 |
| style separability score | 0.3043 | 0.0300 | 0.2568 | 0.3508 | PASS reduced threshold >= 0.20 |
| VPIP spread | 0.1688 | 0.0486 | 0.0673 | 0.2300 | Informational |
| PFR spread | 0.1250 | 0.0225 | 0.0900 | 0.1600 | Informational |
| aggression spread | 3.7008 | 2.0089 | 1.1682 | 7.9333 | Informational |
| call-rate spread | 0.1761 | 0.0437 | 0.0946 | 0.2305 | Informational |
| largest stack share | 0.4232 | 0.0588 | 0.3536 | 0.5593 | Informational |
| bustout rate | 0.0500 | 0.1000 | 0.0000 | 0.2500 | Informational |
| stack gini | 0.2799 | 0.0872 | 0.1339 | 0.4283 | Informational |

## Per-Seed Summary

| Seed | Actions | Avg decision score | Illegal action rate | Style separability | Errors |
|---:|---:|---:|---:|---:|---|
| 0 | 524 | 72.385 | 0.0 | 0.257 | `[]` |
| 1 | 505 | 70.762 | 0.0 | 0.322 | `[]` |
| 2 | 427 | 70.105 | 0.0 | 0.260 | `[]` |
| 3 | 391 | 71.151 | 0.0 | 0.271 | `[]` |
| 4 | 524 | 71.288 | 0.0 | 0.351 | `[]` |
| 5 | 522 | 71.264 | 0.0 | 0.323 | `[]` |
| 6 | 361 | 69.875 | 0.0 | 0.306 | `[]` |
| 7 | 508 | 70.413 | 0.0 | 0.324 | `[]` |
| 8 | 544 | 72.408 | 0.0 | 0.303 | `[]` |
| 9 | 531 | 72.439 | 0.0 | 0.325 | `[]` |

## Grade Distribution

Across 4,837 evaluated actions:

| Grade | Count | Share |
|---|---:|---:|
| excellent | 245 | 5.07% |
| good | 4,110 | 84.97% |
| questionable | 167 | 3.45% |
| poor | 301 | 6.22% |
| blunder | 14 | 0.29% |

Combined poor+blunder share:

```text
315 / 4837 = 6.51%
```

Initial Phase 3 threshold read:

- poor+blunder share <= 10%: PASS.
- blunder share <= 1%: PASS.

## Profile Coverage and Style Metrics

Every reduced benchmark run included the expected four profile groups:

- `calling_station`
- `loose_aggressive`
- `nit`
- `tight_aggressive`

Average observed profile behavior across 10 seeds:

| Profile | VPIP | PFR | Aggression factor | Call rate | Fold rate | Poor/blunder rate | Avg decision score |
|---|---:|---:|---:|---:|---:|---:|---:|
| calling_station | 0.2038 | 0.0250 | 0.8614 | 0.2125 | 0.4622 | 0.0833 | 71.0578 |
| loose_aggressive | 0.1610 | 0.1380 | 3.1954 | 0.0898 | 0.5225 | 0.0517 | 71.9443 |
| nit | 0.0420 | 0.0200 | 2.1531 | 0.0547 | 0.7676 | 0.0727 | 70.3800 |
| tight_aggressive | 0.0890 | 0.0650 | 2.7464 | 0.0752 | 0.6129 | 0.0576 | 71.3302 |

Interpretation:

- Style separation is consistently non-zero and above the initial reduced-run threshold.
- Calling station has the highest call rate and low aggression, matching directionally.
- Loose aggressive has high PFR and high aggression, matching directionally.
- Nit has the lowest VPIP/PFR and highest fold rate, matching directionally.
- Tight aggressive sits between nit and loose aggressive, matching directionally.
- This is still not full profile calibration; Stage 3.2 should compare observed values to explicit target bands.

## Transcript/Public-State Safety

The reduced run passed the existing machine transcript checks:

- transcript samples available for completed runs;
- no forbidden text tokens detected: `deck`, `hole_cards`, `opponent_hole_cards`, `private_ai_internals`, `unsafe_seed`;
- JSON artifact is serializable.

Limitations:

- This is token/schema-level safety, not a full semantic proof of no hidden-state leakage.
- Stage 3.4 should add stronger outcome-specific safety cases for fold-only, showdown, all-in, side-pot, and early-winner hands.

## Findings

### What passed in the reduced gate

- 10 deterministic seeds completed at 100 hands each.
- Every run had `errors == []`.
- Every run had `illegal_action_rate == 0.0`.
- Required metrics were present.
- Transcript sample availability passed.
- Transcript forbidden-token safety passed.
- JSON serialization passed.
- Profile groups were present and style separability was consistently non-zero.
- Poor+blunder and blunder shares are below initial thresholds.

### What did not pass

- Full primary protocol did not complete within 600 seconds.
- Reduced diagnostic gate now evaluates against its declared `10 × 100` protocol; it returns `WARN`, not `FAIL`, because one seed had average decision score slightly below the soft threshold (`seed=6`, `69.8753`).
- If the same reduced artifact is evaluated without an explicit reduced `expected_protocol`, the default full-primary gate should still reject it. That preserves the canonical `10 × 500` primary target.

## Follow-Up Slices

### Must-fix / next Stage 3.1 slice

- Investigate full `10 × 500` runtime. Options:
  - optimize benchmark runtime;
  - run as a background/overnight job;
  - make the primary protocol configurable while preserving the canonical target.

### Completed during this Stage 3.1 pass

- Added explicit expected-protocol support to `evaluate_benchmark_gates(...)`, so reduced diagnostic runs can be evaluated against their declared scope without being mislabeled as failed full-primary gates.
- Added machine-readable Phase 3 checks for required profile coverage and soft quality thresholds: average decision score, style separability, poor+blunder share, and blunder share.
- Added regression coverage: `tests/test_ai_system_evaluator.py::test_benchmark_gate_evaluation_accepts_explicit_reduced_protocol`, `tests/test_ai_system_evaluator.py::test_benchmark_gate_evaluation_warns_for_quality_thresholds`, and `tests/test_ai_system_evaluator.py::test_benchmark_gate_evaluation_fails_when_required_profiles_are_missing`.

### Should-improve

- Preserve low-grade decision samples for Stage 3.3 poor/blunder audit.
- Decide whether the soft average-score warning should be based on every seed, mean score, or confidence interval once more benchmark evidence exists.

### Later

- Move transcript safety beyond token checks into outcome-aware contract tests.
- Add profile target bands and target-vs-observed calibration in Stage 3.2.
- Run diagnostic variants with 2, 6, and 9 players after primary 4-player gate is stable.

## Non-Claims

This report does not claim:

- GTO correctness.
- Solver validation.
- Real-money readiness.
- Online-platform certification.
- Full public/private safety certification.
- Full primary gate pass, because the full `10 × 500` protocol timed out in the current execution budget.
