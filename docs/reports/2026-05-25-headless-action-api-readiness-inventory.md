# Headless / Action API Readiness Inventory

Date: 2026-05-25

## Scope

Inputs reviewed:

- `docs/architecture/decision-action-event-boundaries.md`
- `docs/architecture/external-agent-contract-stub.md`
- `headless_simulation.py`
- `decision_provider.py`
- `action_validator.py`
- `engine_events.py`
- `game.py`

This is a read-only readiness inventory. It does not implement online rooms, WebSocket/API, auth/accounts, external-agent runtime, SDKs, arena runtime, or platform code. It does not refactor `game.py`.

## Current Reusable Contracts

| Contract | Current location | Reusable status |
| --- | --- | --- |
| Decision snapshot | `GameStateSnapshot` in `decision_provider.py`; built by `TexasHoldemGame._build_game_state_snapshot(...)` | Reusable for local providers and future adapters because it includes public state plus the acting seat's private hole cards. |
| Provider response | `ActionResponse` and `DecisionProvider.decide(...)` in `decision_provider.py` | Reusable as the local adapter boundary. Built-in AI and legacy human CLI already sit behind this shape. |
| Legality normalization | `validate_action(...) -> ValidatedAction` in `action_validator.py` | Reusable mandatory boundary before state mutation. Handles invalid action fallback, call normalization, raise limits, and all-in normalization. |
| Engine events | `EngineEvent` in `engine_events.py`; emitted through `TexasHoldemGame._emit_event(...)` | Reusable public event stream for lifecycle/action/showdown/report consumers. `private_payload_by_player` exists but is intentionally unused for current public headless collection. |
| Headless harness | `run_ai_only_simulation(...)` in `headless_simulation.py` | Reusable local benchmark runner. It isolates temp history/stats files, can seed runs, suppresses terminal output, and can collect serialized engine events. |
| External-agent stub | `docs/architecture/external-agent-contract-stub.md` | Reusable as documentation for a future adapter, but not an implementation contract for public runtime yet. |

## Current Gaps

| Gap | Evidence | Readiness impact |
| --- | --- | --- |
| No action-sequence harness | `headless_simulation.py` drives AI-only hands through `play_hand()`, not externally supplied deterministic action sequences. | Future contract fixtures need a local harness that can replay known action responses through `DecisionProvider` and `ActionValidator`. |
| Terminal game loop still owns mutation and UX coupling | `game.py` builds snapshots, asks providers, validates actions, mutates chips/pot/history, emits events, and still contains terminal/human paths. | Do not start a broad rewrite. The next safe work is inventory-backed extraction or fixture harnesses around existing methods. |
| Event parity is useful but not canonical for all analytics | Headless summaries still use history records for decision evaluations, action records, final hands, and outcome metadata. | Future action API work needs parity checks between event stream, history records, and benchmark summaries before relying on events alone. |
| External-agent request serialization is documented but not implemented | The stub defines `external-agent.v0` request/response behavior, but no runtime adapter exists. | Keep runtime deferred. A future local-only serialization fixture can validate shape without executing untrusted agents. |
| Provider metadata is not automatically public-safe | `game.py` records raw response/provider metadata; the architecture doc says it must be filtered before public reports. | Any future adapter/report slice needs explicit JSON-safety and forbidden-field tests. |
| Legacy AI action helper remains present | `game.py` still has `_get_ai_action(...)` alongside the provider pipeline. | Inventory before removal or reuse; do not delete it in this batch. A future test can prove active betting paths use provider + validator. |

## Forbidden Boundaries

The following work remains explicitly out of scope until roadmap gates are met:

- Online room server, WebSocket/API, auth/accounts, matchmaking, or persistent platform runtime.
- External-agent runtime, subprocess runner, SDK, registry, marketplace, or network transport.
- Untrusted external code execution.
- Public API promises for `external-agent.v0`.
- Bypassing `ActionValidator` for any provider or adapter action.
- Broad `game.py` rewrite as the immediate next step.
- Runtime data path migration.
- Canonical poker hand-ranking/comparison changes.

## Next Smallest Safe Implementation Slices

These are future candidate slices only; none were implemented in this batch.

1. `action-sequence-headless-fixture-harness`
   - Goal: allow tests to inject deterministic `DecisionProvider` responses into a local hand and assert validated actions, history records, and public events.
   - Boundary: local test harness only; no external runtime or network.
   - Verification: focused tests around invalid action fallback, call normalization, raise bounds, all-in, fold-only, and early-winner cases.

2. `event-history-parity-checks`
   - Goal: compare `action_applied`, `validation_failed`, showdown, winner, and pot-distribution events with history summaries for the same hand.
   - Boundary: tests/reporting only; no renderer rewrite.
   - Verification: `tests/test_headless_simulation.py` additions plus existing decision/action validator tests.

3. `external-agent-v0-serialization-fixtures`
   - Goal: convert a `GameStateSnapshot` or existing external-agent state into documented request JSON and validate forbidden-field exclusion.
   - Boundary: serialization fixtures only; no adapter execution and no SDK.
   - Verification: JSON dumps, schema-version rejection cases, forbidden private-state scan.

4. `provider-pipeline-active-path-regression`
   - Goal: prove all active betting decisions pass through `DecisionProvider.decide(...)` and `validate_action(...)` before mutation.
   - Boundary: focused tests and small instrumentation if needed; no `game.py` redesign.
   - Verification: monkeypatched provider responses and validation metadata assertions.

## Readiness Verdict

The project has enough local contracts to start small, test-only action-driven readiness slices. It is not ready for online rooms, public WebSocket/API, auth/accounts, external-agent runtime, or SDK implementation.

The immediate next implementation should be a local deterministic action-sequence fixture harness, not a broad `game.py` rewrite and not platform/runtime work.

## Verification

Focused readiness tests:

```bash
python3 -m pytest -q tests/test_decision_provider.py tests/test_action_validator.py tests/test_headless_simulation.py
```

Observed output:

```text
33 passed
```
