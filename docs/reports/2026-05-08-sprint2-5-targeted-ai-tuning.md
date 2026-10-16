# Sprint 2.5 Completion Report: Targeted AI Tuning Baseline

Date: 2026-05-08
Project: Texas Hold'em local trainer -> AI Poker Arena / Agent Poker Platform

## Goal

Use benchmark feedback to make one safe targeted AI tuning change without weakening legality guarantees.

The specific issue addressed in this slice: weak preflop hands could return `fold` even when no call was required, which is strategically equivalent to overfolding a free check spot and inflates poor/fold-heavy behavior.

## Implementation

Updated `advanced_ai_engine.py`:

- In `_preflop_decision_v2(...)`, when `current_bet <= 0`:
  - open-raise valid range hands when selected by range/frequency logic;
  - otherwise return `check`, not `fold`.

Added `tests/test_ai_tuning.py`:

- Verifies a weak hand in a no-call-required preflop spot checks instead of folding.

Updated `ai_system_evaluator.py` benchmark API:

- `evaluate_ai_system(..., starting_chips=1000)` now forwards starting chips to the headless simulation.
- `benchmark_ai_system(..., starting_chips=1000)` records starting chips in benchmark metadata.

This preserves existing callers while allowing long benchmark runs with deeper stacks when needed.

## Before/After Benchmark Comparison

Before tuning reference: Sprint 2.3B artifact

`docs/reports/2026-05-08-sprint2-3b-ai-1000-hand-benchmark.json`

```text
hands_played: 1000
total_actions: 2785
illegal_action_rate: 0.0
average_decision_score: 59.581687612208256
poor actions: 745
excellent actions: 34
```

After tuning final Sprint 2 artifact

`docs/reports/2026-05-08-sprint2-final-ai-1000-hand-benchmark.json`

```text
hands_played: 1000
starting_chips: 10000
total_actions: 2528
illegal_action_rate: 0.0
average_decision_score: 63.58979430379747
poor actions: 603
excellent actions: 129
weakest_profile: advanced
```

The final benchmark used deeper starting stacks to ensure the table completed all 1,000 requested hands after more aggressive/check-preserving behavior.

## Verification

Focused tests:

```text
17 passed in 15.72s
```

Full suite:

```text
92 passed in 23.07s
```

## Remaining AI Quality Notes

The tuning improved average decision score and reduced poor actions in this run, but the built-in AI still needs deeper strategic work:

- profile-specific strategy separation;
- better postflop aggression control;
- less winner-take-all stack concentration;
- regression benchmarks across multiple seeds/runs.
