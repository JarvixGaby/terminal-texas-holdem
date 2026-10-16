# Action Sequence Headless Fixture Harness

Date: 2026-05-25

## Goal

Implement the first local-only `action-sequence-headless-fixture-harness` slice: a deterministic headless hand fixture that can inject scripted `ActionResponse` objects through `DecisionProvider.decide(...)`, route them through `validate_action(...)`, and return observable action/event metadata for tests.

## Non-goals

- No online rooms, WebSocket/API, auth/accounts, matchmaking, network server, or arena runtime.
- No external-agent runtime, SDK, registry, subprocess execution, or untrusted code execution.
- No benchmark threshold, target-band, evaluator scoring, or AI policy changes.
- No broad `game.py` rewrite and no poker hand-ranking/comparison changes.
- No runtime data path migration and no historical benchmark artifact edits.

## Files Changed

- `headless_simulation.py`
- `tests/test_headless_simulation.py`
- `docs/active_plan.md`
- `docs/index.md`
- `docs/reports/2026-05-25-action-sequence-headless-fixture-harness.md`

## Harness API Summary

- `ScriptedDecisionProvider(responses)` is a local-only `DecisionProvider` implementation for deterministic fixture tests. It returns scripted `ActionResponse` objects in order, then falls back to safe local check/call/fold defaults.
- `run_action_sequence_fixture(...)` builds a local `TexasHoldemGame` with `AIPlayer` seats, registers scripted providers through `TexasHoldemGame.set_decision_provider(...)`, plays one hand, and returns `ActionSequenceFixtureResult`.
- `ActionSequenceFixtureResult` exposes `action_records`, `engine_events`, `final_stacks`, `winner_names`, `provider_call_counts`, `errors`, and `to_dict()`.
- Action records include sanitized provider metadata plus validation metadata from the existing provider/validator path: original action/amount, validated action/amount, validity, and validation reason.

## TDD RED/GREEN Evidence

Focused tests added:

- `test_action_sequence_fixture_routes_scripted_responses_through_provider_and_validator`
- `test_action_sequence_fixture_serializes_public_safely_and_isolates_runtime_files`

RED command:

```bash
python3 -m pytest -q tests/test_headless_simulation.py -k action_sequence_fixture
```

Observed RED output:

```text
FAILED tests/test_headless_simulation.py::test_action_sequence_fixture_routes_scripted_responses_through_provider_and_validator
FAILED tests/test_headless_simulation.py::test_action_sequence_fixture_serializes_public_safely_and_isolates_runtime_files
AttributeError: module 'headless_simulation' has no attribute 'run_action_sequence_fixture'
AttributeError: module 'headless_simulation' has no attribute 'ScriptedDecisionProvider'
2 failed, 10 deselected
```

GREEN commands:

```bash
python3 -m pytest -q tests/test_headless_simulation.py -k action_sequence_fixture
python3 -m pytest -q tests/test_headless_simulation.py
python3 -m pytest -q tests/test_headless_simulation.py tests/test_decision_provider.py tests/test_action_validator.py
```

Observed GREEN output:

```text
2 passed, 10 deselected
12 passed
35 passed
```

## Safety and Contract Notes

- The harness uses `TexasHoldemGame.set_decision_provider(...)`, `DecisionProvider.decide(...)`, and the existing `validate_action(...)` path; it does not mutate player actions directly.
- Invalid actions and normalization are observable through result action-record validation metadata and through collected `validation_failed` / `action_applied` events.
- Result serialization strips forbidden private keys from returned fixture metadata: `deck`, `opponent_hole_cards`, and `private_ai_internals`.
- Collected events are serialized from `EngineEvent.to_dict()` and sanitized; public events retain empty `private_payload_by_player` dictionaries.
- Runtime artifact isolation mirrors `run_ai_only_simulation(...)`: temporary history/stats files are used, then removed, and global AI/style state is restored.

## Verification Output

Final verification commands for this slice:

```bash
python3 -m pytest -q tests/test_headless_simulation.py tests/test_decision_provider.py tests/test_action_validator.py
python3 -m pytest -q
python3 - <<'PY'
from pathlib import Path
required = [
    'docs/reports/2026-05-25-action-sequence-headless-fixture-harness.md',
]
idx = Path('docs/index.md').read_text()
missing = [p for p in required if not Path(p).exists() or p not in idx]
if missing:
    raise SystemExit(f'missing report/index entries: {missing}')
print('action-sequence harness report indexed')
PY
git diff --check
git diff -- AGENTS.md --exit-code
```

Observed output:

```text
35 passed in 19.71s
281 passed in 47.44s
action-sequence harness report indexed
git diff --check: exit 0
git diff -- AGENTS.md --exit-code: exit 0
```

## Recommended Next Slice

Next local-only slice: `event-history-parity-checks`, focused on comparing collected `action_applied`, `validation_failed`, showdown, winner, and pot-distribution events with history summaries for the same local fixture hand. Keep it test/reporting-only with no renderer rewrite and no platform runtime.
