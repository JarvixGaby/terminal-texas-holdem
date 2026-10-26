# Sprint 2.3 Hand Outcome and Metric Fidelity Implementation Plan

> **For Hermes:** Use test-driven-development for each code change. Write failing tests first, verify RED, implement minimal GREEN, then refactor.

**Goal:** Make hand outcomes explicit and use those outcomes to make benchmark metrics more trustworthy before online-room work.

**Architecture:** Add hand-level outcome metadata to game history records, expose that metadata through headless summaries, then update AI metrics to use explicit `went_to_showdown` instead of inferring showdown from `final_hands`. Keep backward compatibility for old history JSON that lacks outcome metadata.

**Tech Stack:** Python 3, pytest, current terminal Texas Hold'em modules.

---

## Scope

Sprint 2.3 starts with metric fidelity foundations only:

- `ended_by_fold`
- `went_to_showdown`
- `winner_reason`
- per-player street reach flags: `saw_flop`, `saw_turn`, `saw_river`
- evaluator `showdown_rate` based on explicit outcome metadata

Out of scope for this first Sprint 2.3 slice:

- full blind-aware VPIP/PFR denominator changes
- AI strategy tuning
- WebSocket / online room work
- runtime data path migration

## Task 1: Add failing tests for history outcome metadata

**Objective:** Prove `GameHistoryManager.finish_game(...)` can persist explicit outcome metadata and load old records without it.

**Files:**
- Modify: `tests/test_game_history_outcome_metadata.py`
- Modify later: `texas_holdem/history/game_history.py`

**Steps:**
1. Create tests that call `finish_game(..., outcome_metadata={...})`.
2. Assert saved JSON and loaded `GameRecord` contain the metadata.
3. Add a legacy JSON fixture without `outcome_metadata` and assert loaded record defaults to `{}`.
4. Run: `python3 -m pytest -q tests/test_game_history_outcome_metadata.py`
5. Expected RED: `finish_game()` does not accept `outcome_metadata` yet or loaded record lacks the field.

## Task 2: Implement history outcome metadata

**Objective:** Add backward-compatible outcome metadata to `GameRecord`.

**Files:**
- Modify: `texas_holdem/history/game_history.py`

**Steps:**
1. Add `outcome_metadata: Dict[str, Any] = field(default_factory=dict)` to `GameRecord`.
2. Update `finish_game(...)` signature with optional `outcome_metadata`.
3. Write the metadata to `current_game_record.outcome_metadata`.
4. Include it in `get_current_game_record()`.
5. Load legacy records with `game_data.get('outcome_metadata', {})`.
6. Run targeted tests.

## Task 3: Add failing tests for headless hand summaries

**Objective:** Prove AI-only summaries expose hand outcome metadata for both showdown and fold endings.

**Files:**
- Modify: `tests/test_headless_simulation.py`
- Modify later: `texas_holdem/analytics/headless_simulation.py`
- Modify later: `texas_holdem/engine/game.py`

**Steps:**
1. Add assertions that every hand summary contains `outcome_metadata`.
2. Assert keys include `ended_by_fold`, `went_to_showdown`, `winner_reason`, and `street_reach`.
3. Run targeted test.
4. Expected RED: summaries do not contain `outcome_metadata` yet.

## Task 4: Emit outcome metadata from game endings

**Objective:** Make `texas_holdem/engine/game.py` pass explicit outcome metadata into history for showdown and early-winner endings.

**Files:**
- Modify: `texas_holdem/engine/game.py`
- Modify: `texas_holdem/analytics/headless_simulation.py`

**Steps:**
1. Add helper to build `street_reach` from final game phase.
2. In `_showdown()`, pass `went_to_showdown=True`, `ended_by_fold=False`, `winner_reason='showdown'`.
3. In early winner, pass `went_to_showdown=False`, `ended_by_fold=True`, `winner_reason='fold'`.
4. In invalid all-fold edge case, pass `winner_reason='invalid_all_fold'`.
5. Include `record.outcome_metadata` in `_summarize_record()` and default `{}` for missing record.
6. Run targeted tests.

## Task 5: Add failing tests for explicit showdown rate

**Objective:** Ensure evaluator no longer treats `final_hands` as showdown proxy when `went_to_showdown` is explicitly false.

**Files:**
- Modify: `tests/test_ai_metrics.py`
- Modify later: `texas_holdem/analytics/ai_system_evaluator.py`

**Steps:**
1. Build synthetic two-hand simulation:
   - hand 1: `went_to_showdown=False`, `final_hands` includes both players
   - hand 2: `went_to_showdown=True`, `final_hands` includes both players
2. Assert each player's `showdown_hands == 1` and `showdown_rate == 0.5`.
3. Run the specific test.
4. Expected RED: current evaluator counts both final_hands lists as showdowns.

## Task 6: Use explicit outcome metadata in evaluator

**Objective:** Update `showdown_rate` to prefer `outcome_metadata.went_to_showdown`.

**Files:**
- Modify: `texas_holdem/analytics/ai_system_evaluator.py`

**Steps:**
1. If `outcome_metadata` contains `went_to_showdown`, count showdown only when true.
2. When metadata is absent, keep legacy fallback using `final_hands`.
3. Preserve active-player and winner counting behavior.
4. Run targeted metric tests.

## Task 7: Documentation and verification

**Objective:** Record Sprint 2.3 progress and verify no regressions.

**Files:**
- Modify: `docs/index.md`
- Create: `docs/reports/2026-05-08-sprint2-3-hand-outcome-and-metric-fidelity.md`
- Modify: `docs/active_plan.md`

**Steps:**
1. Run focused tests:
   - `python3 -m pytest -q tests/test_game_history_outcome_metadata.py tests/test_headless_simulation.py tests/test_ai_metrics.py tests/test_ai_system_evaluator.py`
2. Run full suite:
   - `python3 -m pytest -q`
3. Document result and remaining limitations.
4. Update `docs/index.md` with Sprint 2.3 slice status and report path.
5. If all tasks are complete, clear `docs/active_plan.md`.
