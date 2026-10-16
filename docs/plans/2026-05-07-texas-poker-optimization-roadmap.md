# Texas Poker Optimization Roadmap

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Turn the current terminal Texas Hold'em game into a cleaner, more maintainable, more professional poker training product.

**Architecture:** Keep the existing CLI game as the first-class interface, but separate domain engine, persistence, AI, analytics, replay, and UI boundaries. Consolidate duplicated storage/config paths and add tests around poker correctness before changing behavior.

**Tech Stack:** Python 3, pytest, sqlite3, JSON migration utilities, terminal UI.

---

## Current Product Summary

The project is a local terminal Texas Hold'em game. It supports human vs AI play, hand evaluation, blinds, side pots, history, replay, AI decision engines, odds calculation, and player evaluation.

Current validation after baseline cleanup:

- Command: `python3 -m pytest -q`
- Result: `21 passed`

Remaining main risks:

1. Data layer is split between JSON files and SQLite database.
2. `main.py` mixes CLI UI, system initialization, menus, and orchestration in a 997-line file.
3. AI systems are powerful but not clearly productized for training outcomes.
4. Decision feedback/evaluation is not yet integrated into every hand.
5. The engine is not yet agent-ready for future online poker rooms.

---

## Strategic Direction

### Product Positioning

Recommended positioning:

**A terminal-based Texas Hold'em training simulator for Chinese-speaking learners, focused on AI opponents, replay, decision review, and measurable skill improvement.**

Avoid positioning it as a generic poker game only. The most differentiated asset is not just gameplay; it is the combination of:

- AI styles
- replay
- odds calculation
- player style evaluation
- historical analytics
- training feedback

---

## Phase 0: Stabilize and Clarify Baseline

### Task 0.1: Fix stale documentation references

**Objective:** Make README and usage docs match the actual repository.

**Files:**
- Modify: `README.md`
- Modify: `docs/usage-zh.md`
- Modify: `docs/user-guide.md`

**Steps:**
1. Remove or correct references to obsolete launch-file docs.
2. Remove or correct references to obsolete backup-file docs.
3. Standardize launch command as `python3 main.py`.
4. Run: `python3 -m pytest -q`.
5. Verify docs no longer mention missing files:
   - Search for obsolete launch/backup file references.

### Task 0.2: Fix pytest warnings

**Objective:** Make the test suite clean.

**Files:**
- Modify: `test_integration.py`
- Modify: `test_side_pot_detailed.py`

**Steps:**
1. Replace test functions that `return True/False` with `assert` statements.
2. Run: `python3 -m pytest -q`.
3. Expected: all tests pass with zero PytestReturnNotNoneWarning warnings.

### Task 0.3: Fix missing replay dependency

**Objective:** Prevent replay imports from failing.

**Files:**
- Modify: `quick_replay_system.py`
- Possibly create: `odds_calculator.py` compatibility shim, only if necessary.

**Steps:**
1. Replace `from odds_calculator import OddsCalculator` with compatible usage of `optimized_odds_calculator.py`.
2. Add a focused import test for `quick_replay_system.py`.
3. Run: `python3 -m pytest -q`.

---

## Phase 1: Technical Architecture Refactor

### Task 1.1: Split `main.py` into smaller modules

**Objective:** Reduce the 997-line main file and isolate UI concerns.

**Proposed files:**
- Create: `ui/cli_app.py`
- Create: `ui/game_setup.py`
- Create: `ui/menus.py`
- Create: `system/bootstrap.py`
- Modify: `main.py`

**Target structure:**

- `main.py`: minimal entry point only.
- `system/bootstrap.py`: optimization system initialization and fallback behavior.
- `ui/cli_app.py`: main application loop.
- `ui/game_setup.py`: player creation and settings prompts.
- `ui/menus.py`: history, optimization, player evaluation menus.

**Verification:**
- `python3 main.py` still launches.
- `python3 -m pytest -q` passes.

### Task 1.2: Define clear domain boundaries

**Objective:** Make game logic independent from terminal printing where possible.

**Files:**
- Modify: `game.py`
- Create: `events.py` or `game_events.py`

**Approach:**
Introduce simple game event objects instead of printing from every core method. Keep immediate CLI compatibility by allowing the CLI layer to render events.

**Priority:** Medium. Do after tests are expanded.

### Task 1.3: Consolidate configuration system

**Objective:** Avoid confusion between `config.py`, `game_config.py`, `enhanced_config_manager.py`, `game_config.json`, and `enhanced_game_config.json`.

**Files:**
- Audit: `config.py`
- Audit: `game_config.py`
- Audit: `enhanced_config_manager.py`
- Decide one canonical config manager.

**Recommendation:**
Use `enhanced_config_manager.py` as the canonical path if the enhanced version is stable, then mark older config modules as compatibility wrappers.

### Task 1.4: Consolidate persistence around SQLite

**Objective:** Move from mixed JSON/SQLite persistence to one canonical data store.

**Files:**
- Modify: `game_history.py`
- Modify: `database.py`
- Create: `migrations/json_to_sqlite.py`
- Add tests under: `tests/test_persistence.py`

**Recommendation:**
SQLite should become canonical because poker history, actions, player stats, and analytics are relational and query-heavy.

**Migration plan:**
1. Keep JSON read support temporarily.
2. Add importer from `game_history.json` and `player_stats.json` to `poker_game.db`.
3. Write new games to SQLite.
4. Add export-to-JSON as optional backup only.

---

## Phase 2: Poker Correctness and Professional Rule Engine

### Task 2.1: Expand hand evaluator tests

**Objective:** Increase confidence in hand ranking correctness.

**Files:**
- Modify: `tests/test_hand_evaluator.py`

**Add cases:**
- Kicker comparison for one pair.
- Two pair tie-breakers.
- Full house higher trips comparison.
- Flush high-card comparison.
- Board-only best hand tie.
- Duplicate card rejection if supported.

### Task 2.2: Expand betting and side-pot tests

**Objective:** Make no-limit Hold'em betting robust.

**Files:**
- Modify: `tests/test_blinds.py`
- Modify: `tests/test_side_pots.py`
- Create: `tests/test_betting_round.py`

**Add cases:**
- Heads-up preflop action order.
- Multiway preflop action order.
- All-in less than minimum raise should not reopen action.
- Multiple all-ins across different stack sizes.
- Folded player contribution remains in pot but cannot win.

### Task 2.3: Add official rule compliance checklist

**Objective:** Make professionalization measurable.

**Files:**
- Create: `docs/rules/no-limit-holdem-compliance.md`

**Sections:**
- Blinds and dealer button.
- Preflop action order.
- Postflop action order.
- Minimum raise rules.
- All-in and side-pot rules.
- Showdown rules.
- Tie and split-pot rules.

---

## Phase 3: Product Feature Optimization

### Task 3.1: Create guided training mode

**Objective:** Convert the product from game-only to training-first.

**Feature:**
A new mode that pauses after human decisions and explains:

- pot odds
- estimated equity
- recommended action
- why the action is good or bad
- risk level

**Files:**
- Modify: `main.py` or future `ui/menus.py`
- Modify: `realtime_assistant.py`
- Add: `training_mode.py`
- Add tests: `tests/test_training_mode.py`

**MVP behavior:**
- Before human action, show a compact advice panel.
- After action, record whether it matched the recommendation.
- At end of hand, show decision quality summary.

### Task 3.2: Improve replay into “decision review”

**Objective:** Make replay useful for learning, not only viewing history.

**Files:**
- Modify: `instant_replay.py`
- Modify: `quick_replay_system.py`
- Modify: `history_viewer.py`

**Add:**
- Mark key decision points.
- Show equity before/after each street.
- Label decisions as good / questionable / poor.
- Highlight biggest EV mistakes if an EV model exists or approximate using equity + pot odds.

### Task 3.3: Add session summary after each game

**Objective:** Give users immediate feedback.

**Files:**
- Modify: `game.py`
- Modify: `player_evaluation.py`
- Add: `session_summary.py`

**Summary metrics:**
- Hands played.
- VPIP approximation.
- PFR approximation.
- Fold rate.
- Aggression frequency.
- Biggest pot won/lost.
- Best hand.
- 3 suggestions for next session.

### Task 3.4: Add difficulty presets

**Objective:** Make onboarding clearer.

**Presets:**
1. 新手训练
2. 标准练习
3. 激进牌桌
4. 紧凶挑战
5. 专家/GTO挑战

**Files:**
- Modify: `game_config.py` or canonical config manager.
- Modify: AI setup path in player creation.

---

## Phase 4: AI Professionalization

### Task 4.1: Make AI profiles explicit and selectable

**Objective:** Let users choose opponent lineup.

**Profiles:**
- 鱼玩家 / Fish
- 跟注站 / Calling Station
- 紧弱 / Tight Passive
- 紧凶 / TAG
- 松凶 / LAG
- 鲨鱼 / Shark
- 平衡型 / Balanced

**Files:**
- Modify: `player_styles.py`
- Modify: `smart_ai_system.py`
- Modify: `advanced_ai_engine.py`
- Modify: player creation UI.

### Task 4.2: Add transparent AI explanation mode

**Objective:** Turn AI into a teaching tool.

**Feature:**
After a hand, allow viewing AI reasoning:

- hand strength
- pot odds
- position
- selected action
- style influence
- bluff/value classification

**Privacy/product note:**
Do not show during active hand by default, because that breaks gameplay. Show during replay/training mode.

### Task 4.3: Calibrate AI behavior with target stats

**Objective:** Make AI styles statistically believable.

**Files:**
- Add: `ai_calibration.py`
- Add tests: `tests/test_ai_calibration.py`

**Metrics:**
- VPIP
- PFR
- 3bet frequency
- aggression factor
- fold-to-bet
- showdown rate

**Method:**
Run simulated AI-only sessions and compare outputs to target ranges.

---

## Phase 5: Analytics and Data Product

### Task 5.1: Build a player leak detector

**Objective:** Provide professional feedback.

**Examples of leaks:**
- VPIP too high.
- PFR too low.
- Calling too much out of position.
- Folding too much to small bets.
- Overplaying weak pairs.
- Not value betting strong hands.

**Files:**
- Add: `leak_detector.py`
- Modify: `player_evaluation.py`
- Add tests: `tests/test_leak_detector.py`

### Task 5.2: Improve terminal visualizations

**Objective:** Make analytics readable in CLI.

**Files:**
- Modify: `data_visualization.py`

**Charts:**
- VPIP/PFR trend line.
- Win/loss by session.
- Profit by position.
- Action frequency stacked bars.

### Task 5.3: Add exportable reports

**Objective:** Make progress shareable and reviewable.

**Formats:**
- Markdown report.
- JSON report.
- Optional CSV for hand history/actions.

**Files:**
- Add: `reports.py`
- Add tests: `tests/test_reports.py`

---

## Phase 6: UX and Packaging

### Task 6.1: Add a real CLI command structure

**Objective:** Support non-interactive commands in addition to menus.

**Suggested commands:**

```bash
python3 main.py play
python3 main.py history
python3 main.py replay <game_id>
python3 main.py stats <player_name>
python3 main.py train
python3 main.py export-report <player_name>
```

**Files:**
- Modify: `main.py`
- Add: `cli.py`

### Task 6.2: Add dependency and packaging metadata

**Objective:** Make setup reproducible.

**Files:**
- Create: `pyproject.toml`
- Optionally create: `requirements-dev.txt`

**Minimum:**
- Python version requirement.
- pytest dev dependency.
- package metadata.

### Task 6.3: Improve first-run experience

**Objective:** Reduce friction for new users.

**Feature:**
On first launch:
- detect terminal UTF-8 support
- create config if missing
- create database if missing
- offer beginner preset
- explain controls briefly

---

## Recommended Priority Order

### Baseline cleanup: completed

1. Fixed stale docs.
2. Fixed pytest warnings.
3. Fixed missing replay import by using `optimized_odds_calculator`.
4. Added module import smoke tests.
5. Added rule compliance doc.

### Immediate next: 1-2 days

1. Add decision evaluator MVP.
2. Store and display compact decision feedback after each hand.
3. Create first AI/system design review document.
4. Add missing professional poker rule tests beyond the compliance checklist.
5. Start extracting `main.py` after evaluator integration is stable.

### Short term: 1 week

1. Expand hand evaluator and side-pot tests.
2. Split `main.py` into UI/bootstrap modules.
3. Choose canonical config path.
4. Add difficulty presets.
5. Add session summary.

### Medium term: 2-4 weeks

1. Consolidate persistence to SQLite.
2. Add guided training mode.
3. Improve replay as decision review.
4. Add AI explanation mode.
5. Add leak detector.

### Long term: 1-2 months

1. Calibrate AI profiles statistically.
2. Add richer analytics dashboards.
3. Add exportable reports.
4. Add proper CLI command mode.
5. Package project with `pyproject.toml`.

---

## Success Metrics

### Technical

- `python3 -m pytest -q` passes with zero warnings.
- Import test passes for every top-level module intended for use.
- `main.py` reduced below 250 lines.
- One canonical persistence path.
- One canonical configuration path.

### Product

- A new user can start a beginner game in under 30 seconds.
- A player can review the previous hand in under 3 menu actions.
- Every session ends with at least 3 actionable suggestions.
- Training mode explains pot odds and recommended actions.

### Professional Poker Quality

- Betting order covered by tests.
- Side pots covered by multi-all-in tests.
- Tie/split-pot scenarios covered by tests.
- AI profile stats are measurable and tunable.
- Replay identifies important decisions, not just chronological actions.

---

## Suggested First Implementation Batch

1. Baseline cleanup. ✅ Done.
2. Add decision evaluator MVP.
3. Add missing professional poker rule tests beyond the initial checklist.
4. Start extracting `main.py`.

This batch reduces breakage risk and creates a safe base for larger product improvements.
