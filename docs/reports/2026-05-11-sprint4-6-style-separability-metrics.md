# Sprint 4 Slice 4.6 — Style Separability Benchmark Metrics

Date: 2026-05-11

## Summary

Slice 4.6 adds benchmark/report fields that describe whether observed AI profiles are behaviorally separable during simulation:

- `style_separability_score`
- `vpip_spread`
- `pfr_spread`
- `aggression_spread`
- `call_rate_spread`

The metrics are derived from observed player/profile action data produced by benchmark summaries. They do not use archetype target configuration values.

## Implementation Notes

- `PlayerPokerMetrics` now records observed `call_rate`.
- `ProfilePokerMetrics` now records observed `aggression_factor`, `call_rate`, `aggressive_actions`, and `call_actions`.
- `AISystemEvaluationReport.to_dict()` remains backward compatible through dataclass serialization and keeps the existing `hands` and `actions` aliases.
- Empty data or fewer than two observed profiles returns zero separability values.

## Verification

RED:

```text
python3 -m pytest -q tests/test_ai_system_evaluator.py
4 failed, 1 passed
```

GREEN:

```text
python3 -m pytest -q tests/test_ai_system_evaluator.py
5 passed
```

Final focused/full verification is recorded in the Engineer Codex Agent output for this slice.
