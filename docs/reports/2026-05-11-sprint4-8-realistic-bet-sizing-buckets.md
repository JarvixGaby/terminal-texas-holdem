# Sprint 4 Slice 4.8 — Realistic Bet Sizing Buckets

Date: 2026-05-11

## Summary

Slice 4.8 replaces loose postflop bet-size formulas with simple named buckets: `small`, `half-pot`, `two-thirds-pot`, `pot-ish`, and `all-in`.

The goal is more credible local CLI opponent sizing, not solver/GTO play. Value, thin-value, semi-bluff, and bluff lines now map to plausible bucket families, and postflop facing-bet raise amounts route through the same sizing helper where practical.

## Implementation Notes

- Added deterministic sizing tests in `tests/test_ai_scenario_sanity.py`.
- Added `BetSizingEngine.SIZING_BUCKETS` and action-line bucket mappings in `advanced_ai_engine.py`.
- Routed hardcoded postflop facing-bet raise formulas for value, thin-value, semi-bluff, and bluff raises through `BetSizingEngine.calculate_bet_size(...)`.
- Kept raise amounts bounded by `min_raise` and `player_chips` before returning a raise.
- Fix pass after Senior Poker Player review: facing-bet raises now use target-total semantics based on the table's current bet, not `amount_to_call + bucket`, when the acting AI has already committed chips on the street.
- Threaded optional `table_current_bet` and `player_current_bet` context through the built-in AI provider while preserving compatibility for callers that only pass amount-to-call.
- Preserved earlier Sprint 4 guards: free-check behavior, premium preflop behavior, and Slice 4.7 postflop hand-strength behavior.
- Did not modify `ActionValidator`, `hand_evaluator.py`, c-bet/fold-to-cbet behavior, or terminal UX.

## Verification

RED:

```text
python3 -m pytest -q tests/test_ai_scenario_sanity.py
6 failed, 41 passed

FAILED tests/test_ai_scenario_sanity.py::test_bet_sizing_engine_exposes_simple_named_buckets
AttributeError: type object 'BetSizingEngine' has no attribute 'SIZING_BUCKETS'
```

GREEN:

```text
python3 -m pytest -q tests/test_ai_scenario_sanity.py
47 passed

python3 -m pytest -q tests/test_ai_scenario_sanity.py tests/test_ai_tuning.py
48 passed

python3 -m pytest -q
223 passed
```

Review fix RED:

```text
python3 -m pytest -q tests/test_ai_scenario_sanity.py::test_postflop_facing_bet_raise_after_committed_chips_uses_target_total_semantics
1 failed

AssertionError: assert 240 in {233, 280}
```

Review fix GREEN:

```text
python3 -m pytest -q tests/test_ai_scenario_sanity.py::test_postflop_facing_bet_raise_after_committed_chips_uses_target_total_semantics
1 passed

python3 -m pytest -q tests/test_ai_scenario_sanity.py::test_postflop_facing_bet_raise_uses_legal_bucketed_total_amount
1 passed

python3 -m pytest -q tests/test_decision_provider.py::test_builtin_ai_provider_wraps_existing_make_decision
1 passed

python3 -m pytest -q tests/test_ai_scenario_sanity.py tests/test_decision_provider.py
55 passed

python3 -m pytest -q tests/test_ai_scenario_sanity.py tests/test_ai_tuning.py tests/test_decision_provider.py
56 passed

python3 -m pytest -q
224 passed
```
