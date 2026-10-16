# Sprint 4 Slice 4.10 — AI Decision Explanation Payload

Date: 2026-05-11

## Summary

Slice 4.10 adds a small optional explanation payload for built-in AI decisions.

The payload is metadata only. It is attached after the AI action and amount are selected, so it does not influence strategy, legality, fallback behavior, or terminal UX.

## Implementation Notes

- Added focused tests for `ActionResponse.metadata` explanation carriage, mutable-default isolation, `dataclasses.asdict()`, and `json.dumps()`.
- Added `AdvancedAIEngine.last_decision_explanation` as a JSON-safe sidecar after `make_decision()` chooses `(action, amount)`.
- Exposed the latest advanced-engine explanation through `AIPlayer.last_decision_metadata`.
- Added `BuiltInAIDecisionProvider` plumbing that prefers engine-provided explanation metadata and otherwise builds a conservative public-state explanation.
- Explanation tags are intentionally high-level and heuristic, including `value`, `c-bet`, `fold-to-cbet`, `pot-odds`, `semi-bluff`, `pressure`, `pot-control`, and `fold` where feasible.
- Payloads avoid raw `Card` objects, deck state, hidden-card keys, private engine objects, and runtime secrets.
- Did not modify `ActionValidator`, `hand_evaluator.py`, gameplay decisions, benchmark runners, terminal display, or human trainer feedback UI.

## Verification

RED:

```text
python3 -m pytest -q tests/test_decision_provider.py tests/test_ai_scenario_sanity.py
4 failed, 61 passed

KeyError: 'ai_explanation'
AttributeError: 'AdvancedAIEngine' object has no attribute 'last_decision_explanation'
```

GREEN:

```text
python3 -m pytest -q tests/test_decision_provider.py tests/test_ai_scenario_sanity.py
65 passed
```

```text
python3 -m pytest -q tests/test_decision_provider.py tests/test_ai_scenario_sanity.py tests/test_ai_tuning.py
66 passed
```

```text
python3 -m pytest -q
234 passed
```

## Re-review Fix Pass

Senior Poker Player review requested one focused live-path test covering:
`BuiltInAIDecisionProvider -> AIPlayer.make_decision -> AIPlayer._advanced_decision -> AdvancedAIEngine.last_decision_explanation -> AIPlayer.last_decision_metadata -> ActionResponse.metadata["ai_explanation"]`.

Added a coverage-only regression test using a real `AIPlayer` through `BuiltInAIDecisionProvider`. The test verifies the returned action and amount remain legal, the explanation source is `AdvancedAIEngine`, the provider uses `AIPlayer.last_decision_metadata`, and the serialized `ActionResponse` does not expose `hole_cards`, `opponent_hole_cards`, `deck`, or raw `Card` object text.

RED/coverage note:

```text
python3 -m pytest -q tests/test_decision_provider.py::test_builtin_ai_provider_live_ai_player_carries_advanced_engine_explanation_json_safely
1 passed
```

The new test passed immediately, so no production bug was found and no production code changed for this fix pass.

Re-review verification:

```text
python3 -m pytest -q tests/test_decision_provider.py tests/test_ai_scenario_sanity.py
66 passed
```

```text
python3 -m pytest -q
235 passed
```
