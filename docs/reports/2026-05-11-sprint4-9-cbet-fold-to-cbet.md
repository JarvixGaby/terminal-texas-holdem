# Sprint 4 Slice 4.9 — C-Bet / Fold-To-CBet Behavior

Date: 2026-05-11

## Summary

Slice 4.9 adds profile-aware flop continuation-bet and fold-to-cbet behavior for the built-in local CLI AI opponents.

The goal is opponent credibility, not solver-level play. Preflop aggressors can now c-bet plausible dry flop spots at profile-specific frequencies, while defenders use profile fold-to-cbet tendencies when weak air faces a credible flop c-bet.

## Implementation Notes

- Added deterministic c-bet and fold-to-cbet scenario tests in `tests/test_ai_scenario_sanity.py`.
- Threaded existing public `GameStateSnapshot.action_history` through `BuiltInAIDecisionProvider`, `AIPlayer`, and `AdvancedAIEngine`.
- Used only serializable public action context: phase, player name, action, and amount.
- Added flop c-bet detection from the last preflop aggressor and first flop aggressive action.
- TAG/LAG profiles c-bet more often than calling-station on the same dry-flop batch.
- Calling-station folds weak air to c-bets less often than TAG, while strong made hands and good draws do not fold to credible c-bets.
- Preserved Slice 4.8 target-total raise semantics and named sizing buckets.
- Did not modify `ActionValidator`, `hand_evaluator.py`, trainer explanation payloads, benchmark runners, or terminal UX.

## Verification

RED:

```text
python3 -m pytest -q tests/test_ai_scenario_sanity.py
47 failed, 6 passed

TypeError: AdvancedAIEngine.make_decision() got an unexpected keyword argument 'action_history'
```

```text
python3 -m pytest -q tests/test_decision_provider.py::test_builtin_ai_provider_wraps_existing_make_decision
1 failed

KeyError: 'action_history'
```

GREEN:

```text
python3 -m pytest -q tests/test_ai_scenario_sanity.py tests/test_decision_provider.py
60 passed
```

```text
python3 -m pytest -q tests/test_ai_scenario_sanity.py tests/test_ai_tuning.py tests/test_decision_provider.py
61 passed
```

```text
python3 -m pytest -q
229 passed
```
