# Archive and Directory Organization Policy

Date: 2026-10-16

## Purpose

This directory records how project files are organized and what should be archived instead of left ambiguous in the project root.

## Current organization decision

The documentation system now follows the `AGENTS.md` placement contract. Stable documents live under `docs/`; root documentation is limited to `AGENTS.md`, `CLAUDE.md`, and `README.md`. Runtime data files remain in root until code paths are migrated. Migrated documentation paths include:

- `docs/user-guide.md`
- `docs/readme-zh.md` (replaces the outdated quick usage guide)
- `docs/archive/legacy-improvements.md`

Runtime data that remains in root for compatibility includes:

- `game_history.json`
- `player_stats.json`

Current operational links have been updated to the `docs/` paths.

## Active root files

Root-level Python files are currently treated as active source modules until the engine/UI refactor is complete.

Examples:

- `main.py`
- `game.py`
- `player.py`
- `decision_evaluator.py`
- `decision_provider.py`
- `action_validator.py`
- `headless_simulation.py`
- `ai_system_evaluator.py`

Root-level JSON/DB/log files are runtime data artifacts. They remain in place for compatibility, but future cleanup should migrate runtime data under `data/` after code paths are updated.

## Documentation organization

Use these directories going forward:

- `docs/plans/` — development roadmaps and implementation plans.
- `docs/architecture/` — architecture reviews, system scorecards, design evaluations.
- `docs/reports/` — sprint results, evaluation reports, benchmark summaries.
- `docs/archive/` — historical notes or obsolete documents that should no longer guide current development.

## What to archive later

Consider moving these only after updating links and references:

- `docs/archive/legacy-improvements.md` — migrated legacy improvement summary
- old one-off planning notes -> `docs/archive/`
- old generated reports -> `docs/archive/reports/`

## Runtime data migration target

Future target layout:

```text
data/
  runtime/
    game_history.json
    player_stats.json
    poker_game.db
  logs/
    poker_game.log
  exports/
  backups/
```

Before moving runtime files, update and test:

- `game_history.py`
- `player_styles.py`
- `database.py`
- `enhanced_logging.py`
- README / usage docs

## Current index

See `docs/index.md` for the current file and directory index.
