# Sprint 3 Hand/Phase Lifecycle Event Slice Implementation Plan

> **For Hermes:** Use test-driven-development skill to implement this plan task-by-task.

**Goal:** Continue Sprint 3 robustness with public `hand_started` and `phase_started` lifecycle events while preserving terminal gameplay behavior.

**Architecture:** Add non-rendered event mirroring at existing hand and street transition boundaries. Keep `game.py` as orchestrator for now; do not extract `GameState`, do not alter rules, and do not broaden benchmark artifact semantics.

**Tech Stack:** Python, existing `EngineEvent`, existing pytest suite via `python3 -m pytest -q`.

---

## Guardrails

- No broad rewrite of `game.py`.
- No canonical poker rule changes.
- Preserve terminal print behavior.
- No online-room/API work in this slice.
- Payloads must be public, serializable, and free of hole cards/deck internals.

## Task 1: Active-plan handoff

**Objective:** Point `docs/active_plan.md` at this new hand/phase lifecycle event slice.

**Files:**
- Create: `docs/plans/2026-05-09-sprint3-hand-phase-lifecycle-event-slice-plan.md`
- Modify: `docs/active_plan.md`

## Task 2: Add failing lifecycle tests

**Objective:** Specify behavior before implementation.

**Files:**
- Modify: `tests/test_game_engine_events.py`

**Expected behavior:**
- `start_new_hand()` emits exactly one `hand_started` event after a game id exists.
- `hand_started` public payload includes `players`, `small_blind`, `big_blind`, `dealer_position`, `phase`, `pot`, and `current_bet`.
- `_deal_flop()`, `_deal_turn()`, and `_deal_river()` each emit `phase_started` for the new street.
- `phase_started` payload includes `phase`, `community_cards`, `pot`, and `current_bet`.
- No lifecycle payload exposes hole-card or deck internals.

**Verification:**
```bash
python3 -m pytest -q tests/test_game_engine_events.py::test_start_new_hand_emits_public_hand_started_event tests/test_game_engine_events.py::test_street_deal_methods_emit_phase_started_events
```
Expected first run: FAIL because these lifecycle events are not implemented yet.

## Task 3: Implement lifecycle events minimally

**Objective:** Add event emission at stable boundaries.

**Files:**
- Modify: `game.py`

**Implementation notes:**
- Emit `hand_started` in `start_new_hand()` after `current_game_id` is assigned and before dealing private cards.
- Emit `phase_started` in each street deal method after `game_phase` is assigned and history phase starts.
- Do not add these events to default terminal renderer allowlist.

## Task 4: Document event coverage update

**Objective:** Record the new lifecycle coverage in durable docs.

**Files:**
- Create: `docs/reports/2026-05-09-sprint3-hand-phase-lifecycle-event-slice.md`
- Modify: `docs/index.md`
- Modify: `docs/active_plan.md`

## Task 5: Verification

**Commands:**
```bash
python3 -m pytest -q tests/test_game_engine_events.py
python3 -m pytest -q
python3 - <<'PY'
from headless_simulation import run_ai_only_simulation
result = run_ai_only_simulation(num_hands=1, player_count=4, starting_chips=500, collect_events=True)
print(f"Hands completed: {result.hands_completed}")
print(f"Errors: {result.errors}")
print(f"Events collected: {len(result.engine_events)}")
print(f"Has hand started: {any(e['type'] == 'hand_started' for e in result.engine_events)}")
print(f"Has phase started: {any(e['type'] == 'phase_started' for e in result.engine_events)}")
PY
```

**Success criteria:** focused tests and full suite pass; collect-events smoke confirms both lifecycle event families.
