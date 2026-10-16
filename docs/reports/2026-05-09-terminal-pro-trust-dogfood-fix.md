# Terminal Pro Trust Dogfood Fix Report

Date: 2026-05-09

## Summary

Implemented the first terminal-product trust slice from professional-player dogfood feedback. The changes target the highest-risk training-product issues: contradictory live/post-action recommendations, raw-equity-only preflop calls for poor hands, and terminal noise when `TERM` is unavailable.

## Changes

### 1. Realtime assistant preflop playability

`RealtimeAssistant` now detects weak offsuit disconnected preflop hands facing a bet and recommends folding instead of treating raw hot/cold equity as enough to continue.

Example addressed from dogfood:

- `93o` facing a raise with raw equity above pot odds now recommends fold because playability/equity realization is poor.
- Playable control hands such as pairs can still continue when price is good.

### 2. Decision evaluator recommendation consistency

`DecisionEvaluator` now applies a compatible poor-preflop-playability rule before standard pot-odds call/fold logic.

This prevents the observed contradiction where live assistance said fold but post-action feedback reported `recommended: call` for the same kind of trash offsuit preflop spot.

### 3. Terminal clear-screen fallback

`main.py` now skips POSIX `clear` when `TERM` is unset, eliminating the visible runtime noise:

```text
TERM environment variable not set.
```

Windows `cls` behavior is preserved.

## Tests Added

- `tests/test_realtime_assistant.py`
  - `93o` facing a preflop raise prefers fold despite raw pot odds.
  - `66` can still continue when the price is good.

- `tests/test_decision_evaluator.py`
  - `93o` fold does not recommend call from raw equity alone.
  - `93o` call is questionable even when raw equity beats price.
  - `66` profitable call still recommends call.

- `tests/test_terminal_environment.py`
  - `clear_screen()` skips shell `clear` when `TERM` is missing.

## Verification

Focused tests:

```text
python3 -m pytest -q tests/test_realtime_assistant.py
2 passed

python3 -m pytest -q tests/test_decision_evaluator.py
30 passed

python3 -m pytest -q tests/test_terminal_environment.py
1 passed
```

Full suite:

```text
python3 -m pytest -q
134 passed in 24.28s
```

Terminal smoke:

```text
env -u TERM python3 main.py
```

The app reached the welcome prompt without printing `TERM environment variable not set.`

## Remaining Product Work

This slice intentionally does not solve the full professional-training problem. Recommended next steps:

1. Add a proper Pro Mode / compact HUD.
2. Add explicit hand-action history to every decision point.
3. Replace heuristic preflop advice with position/range-aware charts.
4. Make AI opponent profiles visible and behaviorally distinct.
5. Continue Sprint 3 renderer separation from `docs/plans/2026-05-08-sprint3-engine-event-boundary-plan.md`.
