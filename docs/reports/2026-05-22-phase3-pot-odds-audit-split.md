# Phase 3 Pot-Odds Call Audit Split

Date: 2026-05-22

## Summary

This slice continues after the Stage 3.5 evaluation-agent loop. It implements the coordinator-approved first follow-up: split `pot-odds call mistake` poor/blunder audit samples using only public benchmark evidence.

No AI policy tuning was performed. No benchmark thresholds were weakened. No online/API/WebSocket/auth/platform surface was added.

## What changed

`ai_system_evaluator.py` now enriches poor/blunder audit samples classified as `pot-odds call mistake` with:

- `audit_split`
- `audit_basis`
- `equity_edge` when public equity and pot-odds evidence is available

The split values are:

| `audit_split` | Meaning |
|---|---|
| `true_negative_equity_call` | Public evaluator evidence shows equity below pot odds; treat as a likely real strategy/policy error candidate. |
| `evaluator_false_positive_candidate` | Public evaluator evidence shows equity meets/exceeds pot odds despite the negative-pot-odds tag; inspect evaluator calibration before tuning AI policy. |
| `insufficient_public_context` | The audit sample lacks public equity or pot-odds metrics; do not classify as strategy or evaluator error yet. |

The implementation reads equity/pot-odds from either top-level evaluation fields or nested `metrics`, matching current benchmark report shape.

## Focused fixture result

Added focused public-context tests covering:

1. A negative-equity call split as `true_negative_equity_call`.
2. A positive-edge negative-pot-odds tag split as `evaluator_false_positive_candidate`.
3. Nested public `metrics.equity` / `metrics.pot_odds` extraction, matching real benchmark artifacts.

These tests avoid private hole-card/deck dependency.

## Updated reduced diagnostic artifact

Generated:

- `docs/reports/2026-05-22-phase3-pot-odds-audit-split-benchmark.json`
- `docs/reports/2026-05-22-phase3-pot-odds-audit-split-benchmark.progress.json`
- `docs/reports/2026-05-22-phase3-pot-odds-audit-split-benchmark-evaluation.json`

Protocol:

```text
10 seeds × 100 hands
player_count = 4
starting_chips = 10000
ai_equity_simulations = 5
```

Gate status against the explicit reduced protocol:

```text
PASS
```

Key benchmark summary:

| Metric | Result |
|---|---:|
| average decision score mean | 72.7313 |
| average decision score min | 72.1245 |
| average decision score max | 73.1433 |

Poor/blunder sample classes:

| Classification | Count |
|---|---:|
| pot-odds call mistake | 33 |
| overfold | 21 |
| low-equity bluff | 3 |

Pot-odds audit split:

| Split | Count |
|---|---:|
| true_negative_equity_call | 33 |
| evaluator_false_positive_candidate | 0 |
| insufficient_public_context | 0 |

Pot-odds sample concentration by profile:

| Profile | Count |
|---|---:|
| calling_station | 23 |
| nit | 6 |
| tight_aggressive | 2 |
| loose_aggressive | 2 |

## Interpretation

The updated diagnostic artifact indicates that this run's sampled pot-odds call mistakes are currently all supported by public equity-vs-pot-odds evidence rather than being obvious evaluator false positives.

This still does **not** justify broad AI tuning. It narrows the next possible tuning target to a named class: calling-station-heavy negative-equity calls. Any future tuning should add focused regression fixtures and then produce a distinct before/after benchmark artifact.

## Verification

Commands run:

```bash
python3 -m pytest -q tests/test_ai_system_evaluator.py::test_poor_blunder_audit_splits_negative_pot_odds_calls_by_public_equity_edge \
  tests/test_ai_system_evaluator.py::test_poor_blunder_audit_marks_positive_edge_pot_odds_tags_as_evaluator_candidates \
  tests/test_ai_system_evaluator.py::test_poor_blunder_audit_uses_nested_public_metrics_for_pot_odds_split
```

Observed:

```text
3 passed in 0.03s
```

```bash
python3 -m pytest -q tests/test_ai_system_evaluator.py
```

Observed:

```text
26 passed in 4.80s
```

```bash
python3 -m pytest -q
```

Observed:

```text
274 passed in 33.47s
```

```bash
python3 - <<'PY'
from pathlib import Path
missing=[]
text=Path('docs/index.md').read_text()
for token in text.split('`')[1::2]:
    if token.startswith(('docs/','reports/','tests/')) or token.endswith('.py') or token in {'AGENTS.md','CLAUDE.md','README.md'}:
        if token.endswith('/') or '*' in token or '<' in token or ' ' in token:
            continue
        if not Path(token).exists():
            missing.append(token)
if missing:
    raise SystemExit(f'missing indexed paths: {missing}')
print('indexed paths ok')
PY
```

Observed:

```text
indexed paths ok
```

Reduced diagnostic benchmark generation observed:

```text
gate_status PASS
pot_odds_audit_splits {'true_negative_equity_call': 33}
```
