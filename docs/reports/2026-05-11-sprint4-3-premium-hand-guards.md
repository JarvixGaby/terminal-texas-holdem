# Sprint 4.3 Premium-Hand Guards

Date: 2026-05-11

## Summary

Slice 4.3 added deterministic AI sanity coverage for common premium preflop spots:

- AA/KK/QQ with no raise must open-raise when raising is legal.
- AKs/QQ facing small ordinary action while short-stacked must not fold when a legal short call is available.
- All scenario actions continue to validate through `ActionValidator`.

The production change is intentionally narrow: premium 3-bet-range hands in `advanced_ai_engine.py` now short-call with remaining chips when they cannot cover a 3-bet or full call, instead of folding.

## Verification

```text
python3 -m pytest -q tests/test_ai_scenario_sanity.py
20 passed

python3 -m pytest -q
190 passed
```
