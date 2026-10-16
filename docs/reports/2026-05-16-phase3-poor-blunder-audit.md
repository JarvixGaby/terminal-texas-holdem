# Phase 3 Stage 3.3 Poor/Blunder Audit

Date: 2026-05-16

## Summary

Stage 3.3 is complete as an evidence and audit-pipeline slice. The benchmark artifacts now emit sanitized `poor_blunder_samples` for low-grade decisions, each with a public context payload and an initial taxonomy classification. This is deliberately additive measurement work: no AI policy tuning, benchmark-threshold weakening, public API work, or platform scope was introduced.

## Artifacts reviewed / generated

- Audit benchmark artifact: `docs/reports/2026-05-16-phase3-poor-blunder-audit-benchmark.json`
- Audit benchmark progress artifact: `docs/reports/2026-05-16-phase3-poor-blunder-audit-benchmark.progress.json`
- Audit benchmark gate evaluation: `docs/reports/2026-05-16-phase3-poor-blunder-audit-benchmark-evaluation.json`
- Baseline reference: `docs/reports/2026-05-16-phase3-profile-calibration-reduced-benchmark.json`
- Full-primary reference: `docs/reports/2026-05-13-phase3-primary-benchmark-gate-after-preflop-fold-calibration.json`

The saved Stage 3.1 and Stage 3.2 artifacts contained grade distributions and transcript samples, but did not expose decision-level poor/blunder context. Stage 3.3 therefore adds a focused, sanitized audit payload to new benchmark reports.

## Implementation note

`ai_system_evaluator.py` now includes `poor_blunder_samples` in each single-seed run report. Each sample includes only public/safe fields:

- hand number
- player name and profile label
- street/phase
- public board available at that phase
- action, amount, score, grade
- sanitized risk tags
- taxonomy classification
- available public numeric context such as pot/to-call/equity/pot-odds when present

The payload intentionally excludes hidden deck order, raw hole-card fields, unsafe seed/private internals, and hidden/private risk-tag strings. A regression test injects forbidden fields and private-card tokens into a synthetic decision record and asserts they do not survive into the audit sample JSON.

## Diagnostic benchmark protocol

The audit artifact uses the same reduced diagnostic execution profile as Stage 3.2:

- seeds: `0..9`
- hands per seed: `100`
- total hands: `1000`
- player count: `4`
- starting chips: `10000`
- AI equity simulations: `5`

The machine-readable gate evaluation status is `FAIL` only because the standard gate evaluator compares artifacts to the canonical primary `10 × 500` protocol. This is expected for a reduced diagnostic audit artifact and is not interpreted as a poker-quality failure.

## Poor/blunder sample distribution

From `57` sanitized samples across `1000` hands and `4445` actions:

| Class | Samples | Interpretation |
|---|---:|---|
| Pot-odds call mistake | 33 | Largest class. Mostly `negative_pot_odds_call`; concentrated in calling-station behavior but present across public postflop/preflop calls. |
| Overfold | 21 | Second-largest class. Mostly nit profile folds; this aligns with Stage 3.2 evidence that some profiles are low-participation/tighter than target bands. |
| Low-equity bluff | 3 | Smaller class. Mostly high-risk bluff/raise spots, currently lower priority than call/overfold patterns. |

By profile:

| Profile | Samples |
|---|---:|
| calling_station | 27 |
| nit | 23 |
| loose_aggressive | 5 |
| tight_aggressive | 2 |

By grade:

| Grade | Samples |
|---|---:|
| poor | 51 |
| blunder | 6 |

By street:

| Street | Samples |
|---|---:|
| preflop | 38 |
| flop | 10 |
| river | 6 |
| turn | 3 |

## Representative sanitized examples

```json
{
  "hand_number": 8,
  "player_name": "AI-4",
  "profile": "calling_station",
  "phase": "preflop",
  "action": "call",
  "amount": 27,
  "grade": "blunder",
  "score": 15.0,
  "classification": "pot-odds call mistake",
  "risk_tags": ["negative_pot_odds_call"],
  "public_board": []
}
```

```json
{
  "hand_number": 4,
  "player_name": "AI-1",
  "profile": "nit",
  "phase": "preflop",
  "action": "fold",
  "amount": 0,
  "grade": "poor",
  "score": 30.0,
  "classification": "overfold",
  "risk_tags": ["overfold"],
  "public_board": []
}
```

```json
{
  "hand_number": 52,
  "player_name": "AI-3",
  "profile": "loose_aggressive",
  "phase": "preflop",
  "action": "raise",
  "amount": 27,
  "grade": "poor",
  "score": 30.0,
  "classification": "low-equity bluff",
  "risk_tags": ["high_risk_bluff"],
  "public_board": []
}
```

## Top recurring error classes

1. **Pot-odds call mistakes** — likely a mix of AI policy and evaluator calibration. Because this class is driven by `negative_pot_odds_call`, it should be split next into clear negative-EV call spots vs evaluator false positives where profile stickiness is intended.
2. **Overfold** — likely policy/style calibration, especially for nit and low-participation archetypes. It should not be tuned globally until the regression target names profile, position/street, and hand-strength/public-board context.
3. **Low-equity bluff** — currently low count. Keep as a lower-priority watch item unless repeated in future primary artifacts or associated with large-pot/river blunders.

## Recommended next slices

Do not tune broadly. Convert findings into these named future slices only after Stage 3.4 safety gates are in place:

1. **Pot-odds call audit split**
   - Regression target: a synthetic poor/blunder sample with `negative_pot_odds_call` must classify as `pot-odds call mistake`.
   - Follow-up: sample enough raw public context to distinguish true call mistakes from evaluator false positives.

2. **Nit overfold regression matrix**
   - Regression target: obvious profitable/preventable overfolds should be classified and counted without weakening nit style identity.
   - Follow-up: separate style fidelity from poker quality so tightening target bands does not hide poor decisions.

3. **High-risk bluff watchlist**
   - Regression target: keep `high_risk_bluff` classified as `low-equity bluff` and monitor count in future reduced/full-primary runs.
   - Follow-up: defer policy tuning unless it becomes frequent or high-impact.

## Verification

Commands run:

```bash
python3 -m pytest -q tests/test_ai_system_evaluator.py::test_poor_blunder_audit_samples_include_classification_without_private_state
python3 -m pytest -q tests/test_ai_system_evaluator.py::test_poor_blunder_audit_classifies_negative_pot_odds_calls
python3 -m pytest -q tests/test_ai_system_evaluator.py
```

Observed focused result before final-suite validation:

```text
21 passed in 3.42s
```

Final full-suite validation after documentation/index updates:

```text
269 passed in 31.70s
```

Markdown index path validation:

```text
indexed paths ok
```

## Stage 3.4 handoff

Stage 3.4 should promote safety from sample-level checks to an explicit public/private safety gate. The immediate target is not to tune AI policy, but to define and test public transcript/audit schema invariants for fold-only, showdown, all-in, side-pot, and early-winner hands.
