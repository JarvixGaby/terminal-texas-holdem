# Terminal Pro Trust Implementation Plan

> **For Hermes:** Use test-driven-development skill to implement this plan task-by-task.

**Goal:** Fix the most damaging terminal dogfood findings from a professional poker-player perspective: contradictory advice, preflop raw-equity traps, and terminal environment noise.

**Architecture:** Keep the current terminal product stable and make a narrow, reversible improvement. Add a shared recommendation concept in `texas_holdem/training/realtime_assistant.py` for poor preflop playability when facing a bet, then make `texas_holdem/ai/decision_evaluator.py` use compatible preflop playability penalties so post-action feedback does not contradict the live assistant. Finally make terminal clearing tolerant of missing `TERM`.

**Tech Stack:** Python 3.12, pytest via `python3 -m pytest -q`, existing terminal UI, `RealtimeAssistant`, and `DecisionEvaluator`.

---

## Dogfood Findings Addressed

1. **P0 contradictory advice:** live assistant can say fold while post-action evaluator says recommended call.
2. **P0 raw-equity preflop trap:** hands like `93o` can be labeled borderline call only because hot/cold equity beats pot odds, despite poor playability and realization.
3. **P2 terminal noise:** non-interactive PTY sessions print `TERM environment variable not set.` due to clear-screen calls.

## Non-goals

- Do not change canonical hand ranking in `texas_holdem/engine/hand_evaluator.py`.
- Do not change No-Limit legality rules or action validation semantics.
- Do not redesign AI opponent strategy in this slice.
- Do not add full solver/chart support yet; this is a conservative heuristic bridge.

## Task 1: Add regression tests for preflop assistance playability

**Objective:** Prove the assistant no longer recommends calling trash offsuit hands facing a raise just because raw equity clears pot odds.

**Files:**
- Create: `tests/test_realtime_assistant.py`
- Test: `texas_holdem/training/realtime_assistant.py`

**Steps:**
1. Add a test for `93o` facing a preflop bet with apparently sufficient raw equity.
2. Assert the suggested action is `FOLD` and reasoning mentions playability/realization.
3. Add a control test that a playable hand such as `66` can still continue when price is good.
4. Run `python3 -m pytest -q tests/test_realtime_assistant.py` and confirm RED.

## Task 2: Implement preflop playability penalty in RealtimeAssistant

**Objective:** Make terminal live advice more professional for preflop call spots.

**Files:**
- Modify: `texas_holdem/training/realtime_assistant.py`
- Test: `tests/test_realtime_assistant.py`

**Steps:**
1. Pass the preflop hand key or hand strength into suggestion generation.
2. Add a small helper to classify poor preflop playability when no community cards and facing a bet.
3. Penalize unpaired, offsuit, non-broadway, disconnected hands before comparing equity to pot odds.
4. Keep pairs, suited aces, broadways, and suited connectors playable.
5. Run `python3 -m pytest -q tests/test_realtime_assistant.py` and confirm GREEN.

## Task 3: Add regression tests for decision evaluator recommendation consistency

**Objective:** Prove post-action feedback does not recommend calling the same poor preflop folds the assistant recommends folding.

**Files:**
- Modify: `tests/test_decision_evaluator.py`
- Test: `texas_holdem/ai/decision_evaluator.py`

**Steps:**
1. Add a test where `93o` folds preflop facing a bet with equity above pot odds.
2. Assert grade is not poor/blunder, recommended action is `fold`, and risk/reasoning mentions playability/realization.
3. Add a control test where a clearly playable profitable call still recommends `call`.
4. Run focused test and confirm RED.

## Task 4: Implement preflop playability in DecisionEvaluator

**Objective:** Align post-action recommendation with live terminal advice without changing legality or benchmark metrics definitions.

**Files:**
- Modify: `texas_holdem/ai/decision_evaluator.py`
- Test: `tests/test_decision_evaluator.py`

**Steps:**
1. Add helpers to parse card rank/suit strings from `DecisionContext.hole_cards`.
2. Add `_has_poor_preflop_playability(context)` for unpaired offsuit disconnected trash facing a call.
3. Before standard pot-odds call/fold logic, if poor preflop playability applies, recommend fold.
4. If the user folds in that spot, grade as good and do not recommend call.
5. If the user calls in that spot, grade as questionable/poor with `poor_preflop_playability` risk tag.
6. Run focused decision evaluator tests and confirm GREEN.

## Task 5: Suppress TERM noise in terminal clear flow

**Objective:** Remove `TERM environment variable not set.` from terminal product sessions.

**Files:**
- Inspect/modify: likely `main.py` and any helper using `os.system('clear')`
- Test: add/adjust focused test if clear helper exists; otherwise verify with an automated short PTY run.

**Steps:**
1. Search for clear-screen calls.
2. Replace direct `clear` shell calls with a safe helper that only clears when `TERM` is set.
3. Run focused tests or import smoke tests.
4. Start `python3 main.py` briefly in the same environment and verify no `TERM environment variable not set.` appears.

## Task 6: Verification and documentation

**Objective:** Prove the slice is safe and record results.

**Files:**
- Modify: `docs/active_plan.md`
- Optionally add report: `docs/reports/2026-05-09-terminal-pro-trust-report.md`

**Steps:**
1. Run `python3 -m pytest -q`.
2. Run a quick terminal smoke to check launch and first action prompt.
3. Update `docs/active_plan.md` checklist as tasks complete.
4. If all tasks complete, add a short completion report and update `docs/index.md` if the report is permanent.
