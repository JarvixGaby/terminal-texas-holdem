# Documentation System Migration Completion Report

Date: 2026-05-08

## Goal

Apply the `AGENTS.md` agent-core documentation contract to the current Texas Poker project documentation system, reusing existing documents where possible.

## Completed Changes

- Kept `AGENTS.md` as the single source of truth for agent instructions.
- Added `CLAUDE.md` as the required shim: `See AGENTS.md for all agent instructions.`
- Created required session-start and core docs:
  - `docs/context.md`
  - `docs/active_plan.md`
  - `docs/project-reflection.md`
  - `docs/conversations/_example.md`
- Reused the existing root project index by moving it to `docs/index.md` and adapting it to the stable document index role.
- Moved root-level permanent docs into `docs/` according to the placement contract:
  - `USER_GUIDE.md` -> `docs/user-guide.md`
  - `使用说明.md` -> `docs/usage-zh.md`
  - `IMPROVEMENTS.md` -> `docs/archive/legacy-improvements.md`
- Updated operational references in README and documentation to point at the new paths.
- Added a decision-log entry to `docs/project-reflection.md` explaining why the AGENTS-centered documentation system was adopted.
- Removed the `First Run` template section from `AGENTS.md` after completing the setup.
- Filled the `Project Specifics` section in `AGENTS.md` with current tech stack, commands, and boundaries.

## Current Root Documentation Policy

Only these Markdown documents remain in the project root:

- `AGENTS.md`
- `CLAUDE.md`
- `README.md`

All other stable project documentation now lives under `docs/`.

## Verification

- Markdown relative link check: `missing_links=0`.
- Root Markdown inventory check:
  - `AGENTS.md`
  - `CLAUDE.md`
  - `README.md`
- Git status could not be produced because this directory is not currently inside a Git repository.

## Notes

Runtime artifacts remain in the project root for compatibility with current code paths:

- `game_history.json`
- `player_stats.json`
- `poker_game.db`
- `poker_game.log`
- config JSON files

They should only be moved after code references and docs are migrated together and tested.
