# Sprint 4.13 — Stack concentration metrics

Date: 2026-05-11

## Slice

Add benchmark metrics that flag winner-take-all stack dynamics so AI tuning can detect games that end too quickly or produce unrealistic chip concentration.

## Changes

- Added stack concentration fields to `AISystemEvaluationReport`:
  - `largest_stack_share`
  - `bustout_rate`
  - `hands_until_first_bust`
  - `stack_gini`
- Added stack metric calculation from headless simulation summaries and final stacks.
- Added `largest_stack_share`, `bustout_rate`, and `stack_gini` to multi-seed benchmark mean/std/min/max summaries.
- Added focused synthetic evaluator coverage for a high-concentration, multi-bustout benchmark scenario.

## Guardrails

- No hand ranking, betting legality, pot distribution, or No-Limit Hold'em rule semantics changed.
- No terminal UX changes.
- No online/API/WebSocket/platform work.
- Existing single-run benchmark output remains backward compatible with additional fields only.

## Verification

Focused tests passed:

```bash
python3 -m pytest -q tests/test_ai_system_evaluator.py
# 8 passed
```

Full-suite verification was run after this report during the Hermes verification gate.
