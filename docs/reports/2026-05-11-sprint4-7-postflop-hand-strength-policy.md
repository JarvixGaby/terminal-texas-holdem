# Sprint 4 Slice 4.7 — Postflop Hand-Strength-Aware Policy

Date: 2026-05-11

## Summary

Slice 4.7 makes the advanced AI's postflop hand-strength model recognize made hands before the river. Flop and turn made hands now evaluate the best available five-card hand instead of falling through to `unknown`, so strong made hands can continue/value bet more credibly while weak air and draws remain distinct.

This is not a solver/GTO change and does not add realistic sizing buckets, c-bet behavior, or fold-to-cbet behavior.

## Implementation Notes

- Added deterministic scenario coverage for strong flop made hands, weak flop air, and nut-flush-draw facing-bet spots.
- Added a focused hand-strength regression test proving a flop top set is recognized as showdown value and stronger than weak air.
- Updated `advanced_ai_engine.py` only, reusing existing hand-evaluation semantics to evaluate 5-card flop states, best 5-of-6 turn states, and existing 7-card river states.
- Preserved the Slice 4.2 free-check guard and Slice 4.5 premium preflop guard.
- Did not modify `ActionValidator` or `hand_evaluator.py`.

## Verification

RED:

```text
python3 -m pytest -q tests/test_ai_scenario_sanity.py
1 failed, 39 passed

FAILED tests/test_ai_scenario_sanity.py::test_postflop_hand_strength_distinguishes_strong_flop_made_hand_from_air
AssertionError: assert 'unknown' != 'unknown'
```

GREEN:

```text
python3 -m pytest -q tests/test_ai_scenario_sanity.py
40 passed

python3 -m pytest -q tests/test_ai_scenario_sanity.py tests/test_ai_tuning.py
41 passed

python3 -m pytest -q
216 passed
```
