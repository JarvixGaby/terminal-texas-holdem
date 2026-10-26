# Sprint 3 Robustness Batch Execution Plan

> **For Hermes:** Use test-driven-development skill to execute each batch task-by-task. Keep the active batch expanded in `docs/active_plan.md` and record durable outcomes in reports.

**Goal:** Continue Sprint 3 engine/UI separation through a sequence of robustness-preserving event-boundary slices before any larger `GameState` extraction or online platform work.

**Architecture:** Prefer additive public `EngineEvent` coverage and headless observability at existing stable boundaries. Batch work by risk: first add coverage assertions and collect-events summaries, then renderer parity tests, then only small routing/extraction steps.

**Tech Stack:** Python, pytest, existing `EngineEvent`, `texas_holdem/analytics/headless_simulation.py`, `texas_holdem/ui/terminal_renderer.py`.

---

## Global guardrails

- No broad rewrite of `texas_holdem/engine/game.py`.
- No canonical poker rule changes.
- Preserve terminal behavior unless a parity test is written first.
- Do not start online-room/API/WebSocket work in these batches.
- Event payloads must stay public/serializable unless explicitly stored in `private_payload_by_player`.
- Keep benchmark default semantics stable unless a batch explicitly changes and documents them.

## Batch 0 — Completed baseline slices

- [x] Terminal Pro Trust dogfood fixes.
- [x] Betting-round lifecycle events: `betting_round_started`, `betting_round_completed`.
- [x] Hand/phase lifecycle events: `hand_started`, `phase_started`.

## Batch 1 — Headless event coverage summary

**Objective:** Make collect-events runs self-auditing so future slices can assert full-hand event coverage without ad-hoc scripts.

**Tasks:**

1. Add failing tests in `tests/test_headless_simulation.py` requiring:
   - `SimulationResult.event_type_counts` counts event types when `collect_events=True`.
   - `SimulationResult.event_types_by_hand_id` groups event types by hand id.
   - At least one completed hand has `hand_started`, `betting_round_started`, `action_applied`, and `hand_completed`.
2. Implement the minimal summary fields in `texas_holdem/analytics/headless_simulation.py`.
3. Verify:
   ```bash
   python3 -m pytest -q tests/test_headless_simulation.py::test_run_ai_only_simulation_summarizes_event_coverage
   python3 -m pytest -q tests/test_headless_simulation.py
   python3 -m pytest -q
   ```

## Batch 2 — Full-hand coverage regression gate

**Objective:** Add a compact regression test that fails if a full collect-events hand loses critical engine lifecycle/action/completion coverage.

**Tasks:**

1. Add or strengthen a test around `run_ai_only_simulation(..., collect_events=True)`.
2. Require at least one hand id to include:
   - `hand_started`
   - `betting_round_started`
   - `betting_round_completed`
   - `action_applied`
   - `hand_completed`
3. Require privacy checks: no `hole_cards`, no `deck` in public event serialization.

## Batch 3 — Terminal renderer parity before rendering new lifecycle events

**Objective:** Prepare safe rendering expansion without changing UX blindly.

**Tasks:**

1. Add terminal renderer tests for any lifecycle events we intend to render.
2. Keep `hand_started` / `phase_started` non-rendered unless expected lines are explicitly tested.
3. If rendering is added, update allowlist only after tests pass.

## Batch 4 — Action prompt/display boundary inventory

**Objective:** Inventory remaining `print/input` paths in `_betting_round()` and classify which are event-ready versus terminal-only.

**Tasks:**

1. Create a short report listing remaining direct IO in `texas_holdem/engine/game.py` by category.
2. Do not modify production code unless a tiny tested event slice is identified.

## Batch 5 — Next safe event slice from inventory

**Objective:** Execute exactly one additional tiny event-boundary migration based on Batch 4.

**Tasks:**

1. Write failing test.
2. Implement minimal event emission or renderer adapter.
3. Run focused/full verification.
4. Update report and active plan.

## Verification for every batch

Run at minimum:

```bash
python3 -m pytest -q <focused tests>
python3 -m pytest -q
```

For event batches, also run a collect-events smoke:

```bash
python3 - <<'PY'
from texas_holdem.analytics.headless_simulation import run_ai_only_simulation
result = run_ai_only_simulation(num_hands=1, player_count=4, starting_chips=500, collect_events=True)
print(result.errors)
print(len(result.engine_events))
PY
```
