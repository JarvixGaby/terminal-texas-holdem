# Phase 3 AI Evaluation Loop Plan

Date: 2026-05-12

## Goal

Turn the current local built-in AI baseline into a repeatable AI Evaluation Loop for the future AI Poker Arena / Agent Poker Platform.

The immediate objective is not online rooms, WebSocket APIs, auth, accounts, or external-agent runtime implementation. The objective is to make AI strength, style fidelity, legality, variance, and public/private safety measurable enough that future platform work can rely on evidence instead of ad-hoc smoke tests.

## Current Baseline

Fresh post-fix evidence from `docs/reports/2026-05-12-ai-player-evaluation.md` and independent read-only review:

- Full test suite: `247 passed`.
- Focused AI/evaluator/headless/profile/tuning/metrics tests: `121 passed`.
- Fresh 100-hand smoke benchmark:
  - `hands completed`: 100
  - `illegal_action_rate`: 0.0
  - `errors`: `[]`
  - `average_decision_score`: 72.3855
  - `style_separability_score`: 0.2568
  - profile groups: `calling_station`, `loose_aggressive`, `nit`, `tight_aggressive`
- Fresh 3-seed micro benchmark:
  - `illegal_action_rate` mean/max: 0.0
  - `style_separability_score` mean: 0.2907

Interpretation: the AI is now a stable, multi-style local trainer baseline. It is not GTO, solver-validated, real-money-ready, or a mature platform agent benchmark.

## Non-Goals

Phase 3 does not implement:

- Online rooms.
- Public WebSocket/API surfaces.
- Auth/accounts.
- External user-agent execution.
- Real-money gameplay.
- Solver/GTO claims.
- Public leaderboard claims before benchmark gates and privacy contracts are stronger.

## Stage 3.1 — Primary Benchmark Gate

### Objective

Promote current smoke diagnostics into a repeatable primary benchmark gate that can be run before major AI/platform decisions.

### Proposed protocol

Primary protocol:

- `seeds`: 10 deterministic seeds.
- `hands_per_seed`: 500.
- `player_count`: 4.
- `starting_chips`: 10000.
- Built-in AI profile mix must include at least: `nit`, `tight_aggressive`, `loose_aggressive`, `calling_station`.

Diagnostic variants, after primary gate exists:

- Player counts: 2, 4, 6, 9.
- Stack depths: short, normal, deep.
- Optional longer run: 20 seeds × 1000 hands, only when runtime is acceptable.

### Gate checks

A benchmark gate passes only if:

- Every run completes.
- `errors == []` for every run.
- `illegal_action_rate == 0.0` for every run.
- Required aggregate metrics are present.
- Required profile metrics are present for every configured archetype.
- Public transcript samples pass leakage checks.
- Average decision score, poor/blunder rate, and style separability meet explicit threshold values.

Initial threshold proposal:

| Metric | Initial gate | Notes |
|---|---:|---|
| illegal action rate | 0.0 | Hard gate. |
| errors | `[]` | Hard gate. |
| average decision score | >= 70 | Soft threshold; tune after first primary run. |
| poor + blunder share | <= 10% | Soft threshold; also audit high-impact blunders separately. |
| blunder share | <= 1% | Harder warning threshold. |
| style separability score | >= 0.20 | Soft threshold; should increase after profile calibration. |
| transcript unsafe tokens | 0 | Hard gate. |
| folded/non-showdown private-card leaks | 0 | Hard gate. |

### Deliverables

- Machine-readable benchmark artifact under `docs/reports/`.
- Human-readable benchmark gate report under `docs/reports/`.
- Tests or focused checks that verify gate evaluation behavior.
- A small command recipe documented in the report for rerunning the gate.

### Acceptance criteria

- A bounded primary run has been executed or, if runtime is too high, a documented reduced run has been executed with a clear reason.
- Gate result is explicit: pass/fail/warn per metric.
- Any failure produces a concrete follow-up issue/slice, not vague tuning language.

## Stage 3.2 — Profile Calibration Metrics

### Objective

Move from “profiles are different” to “profiles behave close to their intended archetype.”

### Measurements

For each profile, compare observed behavior to target ranges:

- VPIP.
- PFR.
- Aggression factor or aggression frequency.
- Call rate.
- Fold rate.
- C-bet frequency.
- Fold-to-cbet frequency.
- Showdown stickiness.
- Poor/blunder rate.
- Average decision score.

### Analysis outputs

- Target-vs-observed table per profile.
- Distance score per profile.
- Profile confusion matrix: whether behavior statistics are enough to infer the assigned archetype.
- Confidence interval or seed variance for each profile metric.

### Acceptance criteria

- Each supported built-in archetype has a target band and observed benchmark band.
- The report identifies which profiles are under-separated or over-distorted.
- Tuning recommendations separate style fidelity from raw poker quality.

## Stage 3.3 — Poor/Blunder Audit Pipeline

### Objective

Convert evaluator low grades into actionable poker-quality improvement slices.

### Classification taxonomy

Poor/blunder actions should be grouped by spot type:

- Premium preflop fold/passive line.
- Weak preflop defend.
- Pot-odds call mistake.
- River large bet/call mistake.
- Short-stack all-in or min-raise edge case.
- Side-pot/all-in/reopen-action edge case.
- Missed value with strong hand.
- Overfold.
- Low-equity bluff.
- Draw equity/semi-bluff miscalibration.
- Evaluator false positive.

### Deliverables

- Sampled poor/blunder hand audit report.
- Top 3 recurring error classes.
- Regression-test recommendations for obvious or high-impact cases.
- Distinction between AI policy defects and evaluator defects.

### Acceptance criteria

- At least one benchmark artifact can emit or reconstruct enough context to inspect poor/blunder decisions.
- High-impact blunders are prioritized over small evaluator-score improvements.
- No tuning work starts without a named error class and regression target.

## Stage 3.4 — Public/Private Safety Gate

### Objective

Upgrade transcript safety from sample review to a contract gate suitable for future external-agent and online-room surfaces.

### Invariants

Public outputs must never expose:

- Hidden deck order.
- Opponent private hole cards before legal showdown reveal.
- Folded/non-contesting players' private cards.
- Non-showdown private cards.
- Unsafe seed/private internals.
- Private AI reasoning fields that depend on hidden information.

### Deliverables

- Explicit public transcript schema.
- Showdown reveal policy documented and tested.
- Fuzz/snapshot tests over multiple seeds and hand outcomes.
- Safety check integrated into benchmark gate evaluation.

### Acceptance criteria

- Safety gate fails on deliberate leaked tokens/fields.
- Safety gate covers fold-only, showdown, all-in, side-pot, and early-winner hands.
- Public benchmark reports can include transcript samples without manual redaction.

## Stage 3.5 — Evaluation Agent Loop

### Objective

Define repeatable agent roles so benchmark results drive structured iteration.

### Agent roles

1. **Benchmark Agent**
   - Runs configured benchmark protocols.
   - Produces machine-readable artifacts and human summaries.
   - Flags pass/fail/warn gates and outlier seeds.

2. **Poker Quality Reviewer Agent**
   - Reviews poor/blunder samples.
   - Separates real AI mistakes from evaluator false positives.
   - Recommends targeted tuning slices and regression tests.

3. **Safety/Contract Agent**
   - Reviews transcript and snapshot public/private boundaries.
   - Checks future external-agent request/response safety assumptions.
   - Blocks public/platform claims when hidden-state risks remain.

4. **Coordinator**
   - Keeps scope aligned with non-goals.
   - Decides whether findings become tests, tuning tasks, docs, or deferred risks.
   - Verifies changes with focused tests and the smallest relevant benchmark.

### Acceptance criteria

- Each major AI tuning cycle starts with benchmark evidence and ends with updated evidence.
- Agent outputs include commands run, artifacts reviewed, and explicit recommendations.
- Coordinator does not claim AI improvement without pre/post metric comparison.

## Execution Checklist

### Stage 3.1 checklist

- [ ] Inspect existing `ai_system_evaluator.py` benchmark protocol and gate helpers.
- [ ] Decide whether the first primary gate run is full `10 × 500` or reduced due to runtime.
- [ ] Run the primary/reduced benchmark and save a machine-readable artifact.
- [ ] Generate a human-readable benchmark gate report.
- [ ] Verify illegal-action, errors, required metrics, style metrics, and transcript safety gates.
- [ ] Add or update focused tests only if gate behavior needs code support.
- [ ] Update `docs/index.md` with durable report/artifact links.

### Stage 3.2 checklist

- [ ] Read `ai_profiles.py` target fields and current profile metric output.
- [ ] Define target bands for each archetype.
- [ ] Add target-vs-observed profile calibration metrics.
- [ ] Run a calibration benchmark.
- [ ] Write a profile calibration report.

### Stage 3.3 checklist

- [ ] Confirm benchmark artifacts expose enough context for poor/blunder audit without leaking hidden state.
- [ ] Extract poor/blunder samples from a benchmark run.
- [ ] Classify samples using the audit taxonomy.
- [ ] Identify top recurring error classes.
- [ ] Create targeted regression/tuning slices for high-impact issues.

### Stage 3.4 checklist

- [ ] Define public transcript schema and showdown reveal policy.
- [ ] Add safety cases for fold-only, showdown, all-in, side-pot, and early-winner hands.
- [ ] Integrate leakage checks into benchmark gate evaluation.
- [ ] Verify public report samples are safe without manual redaction.

### Stage 3.5 checklist

- [ ] Create a lightweight template for Benchmark Agent outputs.
- [ ] Create a lightweight template for Poker Quality Reviewer outputs.
- [ ] Create a lightweight template for Safety/Contract Agent outputs.
- [ ] Run one full loop on a benchmark artifact and capture the before/after decision.

## Verification

Because this plan is documentation-only, validation consists of:

```bash
test -f docs/plans/2026-05-12-phase3-ai-evaluation-loop-plan.md
python3 - <<'PY'
from pathlib import Path
required = [
    'Primary Benchmark Gate',
    'Profile Calibration Metrics',
    'Poor/Blunder Audit Pipeline',
    'Public/Private Safety Gate',
    'Evaluation Agent Loop',
    'Execution Checklist',
]
text = Path('docs/plans/2026-05-12-phase3-ai-evaluation-loop-plan.md').read_text()
missing = [item for item in required if item not in text]
if missing:
    raise SystemExit(f'missing sections: {missing}')
print('plan ok')
PY
```
