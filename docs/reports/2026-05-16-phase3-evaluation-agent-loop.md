# Phase 3 Stage 3.5 Evaluation Agent Loop

Date: 2026-05-16

## Summary

Stage 3.5 defines reusable role templates for the AI evaluation loop and runs one complete evidence loop over an existing Phase 3 benchmark artifact. The loop produced a coordination decision without changing AI policy, benchmark thresholds, online/platform scope, public APIs, auth, or external-agent runtime behavior.

## Durable template

- `docs/evaluation-agent-loop-templates.md`

The template defines four outputs:

1. Benchmark Agent
2. Poker Quality Reviewer
3. Safety/Contract Agent
4. Coordinator Decision

Every role must list artifacts reviewed, commands run, and non-goals preserved.

## Artifact reviewed for this loop

- Benchmark artifact: `docs/reports/2026-05-16-phase3-poor-blunder-audit-benchmark.json`
- Gate evaluation: `docs/reports/2026-05-16-phase3-poor-blunder-audit-benchmark-evaluation.json`
- Stage 3.3 report: `docs/reports/2026-05-16-phase3-poor-blunder-audit.md`
- Stage 3.4 report: `docs/reports/2026-05-16-phase3-public-private-safety-gate.md`

## Benchmark Agent Output

**Protocol:**

- seeds: `0..9`
- hands per seed: `100`
- player count: `4`
- starting chips: `10000`
- AI equity simulations: `5`

**Gate status:**

- Reduced diagnostic artifact.
- Canonical gate evaluation status: `FAIL` because the artifact is `10 × 100`, not the primary `10 × 500` protocol.
- Expected deviations:
  - `benchmark_metadata` fails primary protocol check.
  - `completion` fails primary `hands_played == 500` check.

This is an expected protocol mismatch, not a runtime/legal/poker-quality regression.

**Key metrics from the reduced diagnostic:**

- illegal action rate: mean `0.0`, max `0.0`
- average decision score: mean `72.7313`, min `72.1245`, max `73.1433`
- style separability: mean `0.2917`, min `0.2083`, max `0.4165`
- poor/blunder audit sample count: `57`

**Recommended next action:** pass the artifact for review as diagnostic evidence; do not use it as the canonical primary gate result.

## Poker Quality Reviewer Output

**Poor/blunder samples:** `57`

**Top classes:**

1. Pot-odds call mistake — `33` samples — needs split into true policy mistakes vs evaluator calibration/intentional calling-station stickiness.
2. Overfold — `21` samples — likely style/policy calibration risk, especially for low-participation profiles.
3. Low-equity bluff — `3` samples — low-frequency watch item.

**Profile concentration:**

- calling_station: `27`
- nit: `23`
- loose_aggressive: `5`
- tight_aggressive: `2`

**Regression targets before tuning:**

- Keep `negative_pot_odds_call` classified as `pot-odds call mistake`.
- Add future public-context split for real bad calls vs evaluator false positives before policy changes.
- Keep overfold analysis profile-specific; do not erase nit identity globally.
- Keep high-risk bluff count as a watchlist until frequency/high-impact evidence increases.

## Safety/Contract Agent Output

**Safety checks reviewed:**

- Stage 3.4 transcript schema metadata exists.
- Stage 3.4 showdown reveal policy exists.
- Transcript sample gate checks remain active.
- Poor/blunder audit sample gate checks now reject forbidden private-state tokens.

**Forbidden-token scan over this loop's artifact:** no forbidden tokens found in transcript samples or poor/blunder samples.

**Blocked claims/surfaces:**

- No public leaderboard claims from reduced diagnostics.
- No external-agent API surface until the safety gate remains stable over primary/repeated runs.
- No solver/GTO or real-money claims.

## Coordinator Decision

**Decision:** Phase 3 evidence loop is now complete enough to mark Stage 3.5 done as a process/template slice.

**Rationale:**

- Benchmark Agent separated expected reduced-protocol gate failure from actual quality/runtime failure.
- Poker Quality Reviewer converted low grades into named evidence classes and future regression targets.
- Safety/Contract Agent confirmed safety metadata and gate integration, and found no forbidden-token leakage in the reviewed artifact.
- No AI improvement claim was made because no tuning was performed and no pre/post tuning artifact was generated.

**Allowed next future slice:**

If AI tuning resumes later, start with a pot-odds call audit split using a focused public-context fixture and a before/after benchmark artifact. Do not tune during the evaluation-loop template stage.

## Verification

Focused template/report validation:

```bash
test -f docs/evaluation-agent-loop-templates.md
test -f docs/reports/2026-05-16-phase3-evaluation-agent-loop.md
```

Final Phase 3 validation:

```bash
test -f docs/evaluation-agent-loop-templates.md && test -f docs/reports/2026-05-16-phase3-evaluation-agent-loop.md && python3 -m pytest -q
python3 - <<'PY'
from pathlib import Path
text=Path('docs/index.md').read_text()
missing=[]
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
272 passed in 31.68s
indexed paths ok
```
