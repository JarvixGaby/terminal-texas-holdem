# AI Player Evaluation Plan

> **For Hermes:** Use subagent-driven-development skill to execute this plan as a read-mostly evaluation task. Do not change AI behavior in this plan unless a separate implementation plan is approved.

**Goal:** Test current built-in AI player effectiveness in the local Texas Hold'em trainer and produce a concise evidence-backed evaluation of strengths, weaknesses, and next tuning priorities.

**Architecture:** Use existing deterministic scenario tests, existing benchmark/evaluator functions, and a fresh smoke benchmark artifact. Treat this as evaluation, not feature implementation. Preserve Phase 2 public/private and benchmark-gate contracts: reports may summarize public-safe transcript samples and aggregate metrics, but must not expose hidden deck order or non-showdown private cards.

**Tech Stack:** Python 3, pytest, `texas_holdem/analytics/headless_simulation.py`, `texas_holdem/analytics/ai_system_evaluator.py`, existing test files under `tests/`, Markdown report under `docs/reports/`.

---

## Evaluation Questions

1. **Legality / stability:** Do AI decisions avoid illegal actions and game-loop crashes?
2. **Obvious poker sanity:** Do deterministic scenario tests catch and pass important no-brainer spots, such as premium-hand handling and no-bet raise sizing?
3. **Style variety:** Are AI profiles measurably different enough to feel like different opponents?
4. **Benchmark health:** Are aggregate metrics acceptable for a local trainer, without claiming GTO or solver-level correctness?
5. **Transcript safety:** Do public benchmark samples avoid folded/non-showdown private-card leaks?
6. **Player-facing value:** Based on current metrics and samples, would the AI feel useful for terminal trainer practice, and what should be tuned next?

## Acceptance Criteria

The evaluation is complete when a subagent has produced `docs/reports/2026-05-12-ai-player-evaluation.md` containing:

- Commands run and exact pass/fail results.
- Deterministic test summary for AI scenario/profile/tuning/evaluator coverage.
- A fresh benchmark smoke run summary with parameters recorded.
- Key metrics: hands completed, total actions, illegal action rate, average decision score, style separability, VPIP/PFR/aggression/call spreads, stack concentration, bustout rate, transcript sample count.
- A short qualitative read on AI player effectiveness.
- Public/private safety note for transcript samples.
- Recommended next tuning slices, separated into must-fix, should-improve, and later.
- Explicit non-claim: this is not GTO proof, solver validation, real-money readiness, or online-platform certification.

## Task 1: Run focused AI correctness tests

**Objective:** Verify existing focused tests for AI behavior, profiles, tuning, metrics, and evaluator gates.

**Files:**
- Read: `tests/test_ai_scenario_sanity.py`
- Read: `tests/test_ai_profiles.py`
- Read: `tests/test_ai_tuning.py`
- Read: `tests/test_ai_metrics.py`
- Read: `tests/test_ai_system_evaluator.py`
- Report: `docs/reports/2026-05-12-ai-player-evaluation.md`

**Commands:**

```bash
python3 -m pytest -q tests/test_ai_scenario_sanity.py tests/test_ai_profiles.py tests/test_ai_tuning.py tests/test_ai_metrics.py tests/test_ai_system_evaluator.py
```

**Expected:** All tests pass. If any fail, record the failing test names, failure reason, and whether the failure blocks AI evaluation.

## Task 2: Run fresh deterministic smoke benchmark

**Objective:** Generate current evidence for AI player quality without running an expensive full benchmark.

**Command:**

```bash
python3 - <<'PY'
from texas_holdem.analytics.ai_system_evaluator import benchmark_ai_system
report = benchmark_ai_system(
    num_hands=100,
    player_count=4,
    starting_chips=10000,
    seed=0,
)
print(report.to_dict())
PY
```

**Expected:** Benchmark completes, JSON-like output is inspectable, `hands_played > 0`, `total_actions > 0`, `illegal_action_rate == 0.0` if healthy.

**Notes:** If runtime is too long, use 30 hands with the same player count, starting chips, and seed, and record the adjustment.

## Task 3: Run optional multi-seed micro-benchmark

**Objective:** Check variance across seeds cheaply.

**Command:**

```bash
python3 - <<'PY'
from texas_holdem.analytics.ai_system_evaluator import benchmark_ai_system_multi_seed
report = benchmark_ai_system_multi_seed(
    seeds=[0, 1, 2],
    hands_per_seed=30,
    player_count=4,
    starting_chips=10000,
)
print(report)
PY
```

**Expected:** The result includes per-seed runs and summary mean/std/min/max. This is diagnostic only and does not replace Phase 2 primary benchmark gates.

## Task 4: Inspect transcript safety and qualitative samples

**Objective:** Confirm public benchmark samples are usable for human review and do not leak private state.

**Checks:**

- `transcript_samples` exists when hands complete.
- Sample text includes public hand flow: hand number, board after dealt, public actions, result.
- Non-showdown folded cards do not appear.
- No text tokens like `deck`, `opponent_hole_cards`, `private_ai_internals`, or `unsafe_seed` appear.
- Showdown reveals are acceptable only when the transcript states the hand reached showdown.

## Task 5: Write evaluation report

**Objective:** Save the evaluation in a durable report.

**Create:** `docs/reports/2026-05-12-ai-player-evaluation.md`

**Report structure:**

```markdown
# AI Player Evaluation

Date: 2026-05-12

## Scope

## Commands Run

## Automated Test Results

## Smoke Benchmark Parameters

## Metrics Summary

## Transcript Safety Check

## Qualitative Assessment

## Recommended Next Tuning Slices

## Non-Claims
```

**Verification:**

```bash
test -f docs/reports/2026-05-12-ai-player-evaluation.md
rg -n "illegal action|average decision|style separability|Transcript Safety|Non-Claims" docs/reports/2026-05-12-ai-player-evaluation.md
```

## Task 6: Coordinator follow-up

After the subagent returns, Hermes should verify the report exists, read it, optionally update `docs/index.md` if the report is durable enough to keep, and summarize findings to the user.
