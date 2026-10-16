# Post-Phase-3 Builder/Hacker Loop Dry Run

Date: 2026-05-25

## Scope

This dry-run applies the refreshed evaluation-agent loop to the Slice 2 report:

- `docs/reports/2026-05-25-post-phase3-remaining-poor-blunder-triage.md`
- `docs/reports/2026-05-22-phase3-calling-station-negative-equity-call-tuning-benchmark.json`

No production code was changed. No AI policy, evaluator scoring, target bands, benchmark thresholds, runtime API, or platform code was changed.

## Refreshed Loop Requirements

The loop now requires all of the following before accepting a policy or evaluator change:

- Fixture-backed target using public decision-time information.
- Public/private safety verdict.
- Artifact evidence and commands run.
- Explicit non-goals preserved.
- Pre/post benchmark comparison plan or result.

## Benchmark Agent Output

**Artifact(s) reviewed:**

- `docs/reports/2026-05-22-phase3-calling-station-negative-equity-call-tuning-benchmark.json`

**Protocol:**

- Reduced diagnostic artifact: 10 seeds x 100 hands.
- Post-tuning artifact for the calling-station negative-equity call loop.

**Gate status:**

- This artifact supports reduced diagnostic claims only.
- It does not support broad AI strength claims.

**Key evidence:**

- Remaining poor/blunder samples: 22.
- Classes: overfold 12; pot-odds call mistake 6; low-equity bluff 4.
- Profiles: nit 12; calling_station 4; loose_aggressive 4; tight_aggressive 2.

**Recommended next action:**

- Defer implementation until at least one public-information fixture is defined.

## Poker Quality Reviewer Output

**Poor/blunder sample count:**

- 22.

**Top classes:**

1. overfold - 12 - needs split.
2. pot-odds call mistake - 6 - watchlist after prior targeted reduction.
3. low-equity bluff - 4 - insufficient public context.

**Representative public examples:**

- Nit preflop fold samples show empty public board, high artifact equity, and overfold risk tags.
- Flop call samples show `true_negative_equity_call` with equity below pot odds.
- Low-equity bluff samples are preflop raises with empty public board and no action-history detail in the sanitized sample.

**Regression targets:**

- Possible future evaluator fixture: nit preflop fold spot reconstructed from public decision state plus acting-seat hand.

**Do not tune yet:**

- Low-equity preflop raises and postflop overfolds lack enough public decision context.
- Remaining negative-equity calls are too sparse after the prior loop to justify immediate policy work.

## Hacker Agent Output

**Attack scope:**

- Benchmark/report exploit and strategy-label exploit.

**Public-information compliance:**

- Used only sanitized artifact fields and the Slice 2 report.
- Did not use hidden deck order, opponent private cards, folded/non-showdown cards, or private AI internals.

**Findings:**

1. "Evaluator label drives policy without fixture"
   - Type: benchmark.
   - Severity: medium.
   - Affected profile(s): nit first, possibly others.
   - Public trigger: overfold label with high artifact equity but no full decision snapshot.
   - Impact: a Builder could over-loosen nit policy based on an evaluator label rather than a verified public spot.
   - Suggested regression target: fixture-backed nit preflop fold evaluator case before evaluator or policy changes.

2. "Sparse residual call samples after successful reduction"
   - Type: strategy.
   - Severity: low.
   - Affected profile(s): mixed.
   - Public trigger: true negative-equity call split persists in six samples.
   - Impact: tempting to overfit a reduced artifact after the main targeted class already fell sharply.
   - Suggested action: watchlist, rerun only if concentration returns.

**Recommended next action:**

- Defer implementation. Add a focused public-information fixture only after reconstructing a representative decision state.

## Safety/Contract Agent Output

**Safety checks:**

- Public transcript/schema changes: none.
- Private-card leak risk from this dry-run: none; no hidden fields were inspected.
- Contract changes: none.
- Runtime/platform surfaces: none.

**Verdict:**

- Safe as documentation/evidence.
- No implementation candidate is approved because no fixture-backed public-information target exists yet.

## Coordinator Decision

**Decision:**

- Defer immediate implementation.

**Rationale:**

- Slice 2 found no shared public policy-tuning pattern. The only plausible near-term work is evaluator calibration for nit preflop overfold labels, but that requires a focused public-information fixture first.

**Allowed next slice:**

- "Nit preflop overfold evaluator fixture design" only if it reconstructs public decision-time state plus acting-seat private hand and defines before/after evaluator expectations without changing benchmark thresholds.

**Explicit non-goals preserved:**

- No online/API/WebSocket/auth.
- No external-agent runtime or SDK.
- No AI policy tuning.
- No evaluator calibration change.
- No benchmark threshold or target-band change.

## Verification

Template role presence command:

```bash
python3 - <<'PY'
from pathlib import Path
text = Path('docs/evaluation-agent-loop-templates.md').read_text()
required = ['Benchmark Agent', 'Poker Quality Reviewer', 'Safety/Contract Agent', 'Coordinator']
missing = [item for item in required if item not in text]
if missing:
    raise SystemExit(f'missing template roles: {missing}')
print('agent loop templates present')
PY
```

Observed output:

```text
agent loop templates present
```
