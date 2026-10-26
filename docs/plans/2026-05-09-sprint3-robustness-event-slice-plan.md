# Sprint 3 Robustness Event Slice Implementation Plan

> **For Hermes:** Use test-driven-development skill to implement this plan task-by-task.

**Goal:** Resume Sprint 3 with a narrow, low-risk robustness slice: add explicit betting-round lifecycle engine events and document event coverage without changing terminal gameplay behavior.

**Architecture:** Keep `texas_holdem/engine/game.py` behavior stable and add event mirroring at the `_betting_round()` boundary. Do not attempt GameState extraction, online-room work, or broad print migration in this slice. Use focused tests first, then full regression and a small benchmark smoke.

**Tech Stack:** Python, dataclasses-based `EngineEvent`, existing `TerminalEventRenderer`, pytest via `python3 -m pytest -q`.

---

## Guardrails

- No broad rewrite of `texas_holdem/engine/game.py`.
- No canonical poker rule changes.
- Preserve current terminal print behavior.
- Events must not include private hole cards or deck internals.
- Prefer public, serializable payloads that future terminal/headless/online adapters can consume.

## Task 1: Active-plan handoff

**Objective:** Replace the completed terminal-pro active plan with this Sprint 3 robustness slice.

**Files:**
- Modify: `docs/active_plan.md`

**Verification:** Read the file and confirm it points to this plan and tracks the next tasks only.

## Task 2: Add failing betting-round event tests

**Objective:** Specify `betting_round_started` and `betting_round_completed` event behavior before implementation.

**Files:**
- Modify: `tests/test_game_engine_events.py`

**Expected behavior:**
- `_betting_round()` emits exactly one `betting_round_started` event at the beginning.
- `_betting_round()` emits exactly one `betting_round_completed` event before returning.
- Completed event includes `continued`, `active_player_names`, `pot`, `current_bet`, and `iteration_count`.
- Payload contains no private hand/deck information.

**Verification:** `python3 -m pytest -q tests/test_game_engine_events.py::test_betting_round_emits_started_and_completed_events`
Expected first run: FAIL because lifecycle events are not implemented.

## Task 3: Implement minimal lifecycle events

**Objective:** Add event emission to `_betting_round()` without changing betting logic.

**Files:**
- Modify: `texas_holdem/engine/game.py`

**Implementation notes:**
- Emit `betting_round_started` immediately after the existing start print.
- Add a helper closure inside `_betting_round()` to emit `betting_round_completed` once before each return path.
- Do not render these events by default yet unless a test requires it; this slice is event coverage, not terminal output migration.

**Verification:** focused test passes, then `python3 -m pytest -q tests/test_game_engine_events.py`.

## Task 4: Document coverage matrix and update index

**Objective:** Add a durable report showing what events exist and what remains to migrate.

**Files:**
- Create: `docs/reports/2026-05-09-sprint3-robustness-event-slice.md`
- Modify: `docs/index.md`
- Modify: `docs/active_plan.md`

**Verification:** report exists and index links to it.

## Task 5: Full verification

**Objective:** Prove robustness after the slice.

**Commands:**
```bash
python3 -m pytest -q
python3 - <<'PY'
from texas_holdem.analytics.ai_system_evaluator import benchmark_ai_system
result = benchmark_ai_system(num_hands=10, player_count=4)
data = result.to_dict()
print(f"Hands: {data['hands_played']}")
print(f"Illegal rate: {data['illegal_action_rate']}")
print(f"Events collected: {len(data.get('engine_events', []))}")
PY
```

**Success criteria:** all tests pass; benchmark completes with `illegal_action_rate=0.0`.
