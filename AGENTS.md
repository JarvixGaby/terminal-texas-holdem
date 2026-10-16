# AGENTS.md

> Single source of truth for all agent instructions.
> CLAUDE.md contains only: `See AGENTS.md for all agent instructions.`

---
## Meta Rule

Do not modify AGENTS.md unless the user explicitly instructs it.

Sections that must never be modified without explicit user instruction:
- Session Start
- Documentation System
- Plan Management
- Meta Rule itself

Sections that may be updated when project facts change:
- Tech Stack
- Commands
- Boundaries

When a task requires a new permanent document:
1. Place it in the existing directory with the correct responsibility.
2. Use `docs/` only for stable project documentation, specs, decisions, and indexes.
3. If no suitable directory exists, create a clearly named top-level directory with a stable responsibility instead of dumping unrelated content into `docs/`.
4. Add stable docs to `docs/index.md` when they belong to the documentation index.
5. Do not add references to individual documents in AGENTS.md.

---

## Session Start
 On every session start:
  1. Read `AGENTS.md` first and treat it as the single source of truth for project instructions.

Read only when relevant:
- `docs/project-reflection.md` — before major decisions or architecture changes
- `docs/conversations/` — when historical context is needed
- `docs/index.md/` — when need to understand project structure and look up file
- `docs/active_plan.md` when continuing implementation, resuming work, or determining next development steps.
- `docs/context.md` when project background, current phase, constraints, or direction are needed.
- If `docs/active_plan.md` has content and the task is execution-related, resume from the last unchecked step and preserve the file until all listed steps are complete.

## File Naming & Placement

The table below gives common default locations, not an exhaustive allowlist. Use it as routing guidance, not as a restriction on creating new folders.

| Type | Default location | Naming |
|------|------------------|--------|
| Core project docs | `docs/` | lowercase, hyphen-separated |
| Product/spec/decision docs | `docs/` | lowercase, hyphen-separated |
| Conversation logs | `docs/conversations/` | `YYYY-MM-DD-[topic-slug].md` |
| Stable reports / evaluations | `reports/` or `docs/reports/` when already established | lowercase, date-prefixed when useful |
| Research notes / source material | `research/` | lowercase, hyphen-separated |
| Experiments / spikes | `experiments/` or `spikes/` | lowercase, hyphen-separated; prefix temporary files with `_` |
| Assets / media | `assets/` | descriptive names |
| Reusable helper scripts | `scripts/` | descriptive names |
| Data / fixtures | `data/` or existing project data directory | follow existing project convention |

Do not create loose documentation or ad-hoc files directly in the project root except: `AGENTS.md`, `CLAUDE.md`, `README.md`, and toolchain/runtime files that must live at root.

Agents may create new top-level directories when:
- the content has a clear, durable responsibility;
- no existing directory fits without becoming a dumping ground;
- the directory name describes its role rather than a one-off task session;
- the directory is expected to hold multiple related files over time.

Prefer reusing an existing responsible directory before creating a new one. Avoid vague catch-all names such as `misc/`, `temp/`, `new/`, or `stuff/`.

If a new top-level directory becomes important to ongoing project work, add a short description of its purpose to the placement guidance or project index later. Do not expand this table for every one-off folder.

`docs/` is not a dumping ground. Use it for stable documentation system artifacts only: project context, indexes, specs, architecture notes, plans, decisions, and other long-lived docs that should be discoverable from `docs/index.md`.

Temporary files are never indexed in `docs/index.md`.

---

## Core Documents

### `docs/context.md`
Project snapshot for new sessions.  
Update when project phase or direction changes significantly.

### `docs/index.md`
Project structure Lists only stable, permanent documents.  
**Include:** core docs, key design docs, `project-reflection.md`  
**Exclude:** temp files, conversation logs, `active_plan.md`  
Update whenever a permanent doc is added or removed.

### `docs/project-reflection.md`
Records the "why" behind the project.  
When adding an entry, follow the format of the example entry in the file.

**✅ Update when:**
- Major technical decision made
- Design philosophy shifts
- Important user feedback received
- Market positioning adjusted
- Architecture changes
- Any "why did we do it this way" moment worth preserving

**⛔ Do not update for:**
- Routine bug fixes
- Standard feature additions
- Simple refactoring
- Dependency version bumps

### `docs/conversations/`
Manually triggered. When creating a log, follow the format in `docs/conversations/_example.md`

---

## Plan Management

On session start, read `docs/active_plan.md`.  
If it has content: resume from last unchecked step without asking user to re-explain context.  
After each completed step: check the box and update `Last updated` date.  
When all steps are done: clear `docs/active_plan.md`.

---

## Project Specifics

### Tech Stack
- Python terminal application for Texas Hold'em poker.
- Python 3.12-compatible local environment; use `python3` commands.
- Test runner: `pytest` via `python3 -m pytest -q`.
- Runtime persistence currently uses JSON files and SQLite in the project root for compatibility.
- Core systems include terminal UI/game loop, poker engine logic, hand history/replay, odds/evaluation, DecisionProvider/ActionValidator flow, headless simulation, and AI benchmark metrics.

### Commands
- Run terminal app: `python3 main.py`
- Run full test suite: `python3 -m pytest -q`
- Run focused tests: `python3 -m pytest -q tests/<test_file>.py`
- Run 1,000-hand AI benchmark artifact generation:
  ```bash
  python3 - <<'PY'
  from ai_system_evaluator import benchmark_ai_system
  benchmark_ai_system(
      num_hands=1000,
      player_count=4,
      output_path='docs/reports/2026-05-08-sprint2-2-ai-1000-hand-benchmark.json',
  )
  PY
  ```

### Boundaries

#### Never modify without explicit user instruction:
- `AGENTS.md` protected sections: Session Start, Documentation System, Plan Management, and Meta Rule.
- Canonical poker hand ranking/comparison semantics in `hand_evaluator.py`.
- Core No-Limit Hold'em legality/scoring rules and public agent state contracts unless the task is explicitly about those contracts.
- Historical benchmark/report artifacts under `docs/reports/` except to add new reports or clearly marked corrections.

#### Confirm before modifying:
- Runtime data paths or moving root runtime artifacts: `game_history.json`, `player_stats.json`, `poker_game.db`, `poker_game.log`, config JSON files.
- Large `game.py` refactors that change terminal UX, betting flow, history schema, or AI decision behavior.
- Public/private state schema exposed through `GameStateSnapshot` or future external-agent APIs.
- AI benchmark metric definitions such as VPIP/PFR denominators, showdown proxy, poor/blunder rate, and win-rate calculation.
