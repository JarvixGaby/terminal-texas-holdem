# Adaptive Role Workflow

Date: 2026-05-11

## Purpose

This project uses role-based agent routing to keep development aligned with product value, technical architecture, poker realism, and verification quality.

The previous default was a mandatory three-agent loop for every slice. The current policy is lighter and adaptive:

- **PM and Tech Lead tasks:** use Claude as the primary agent; use Codex as backup if Claude is unavailable, times out, or gives unusable output.
- **Implementation tasks:** use Codex by default.
- **Reviews:** run only when the task risk justifies them; Hermes always performs independent verification before claiming completion.

Hermes remains the coordinator and final verifier. Agent outputs are advisory until Hermes inspects files and runs verification commands.

## Role Routing

### 1. PM / Scope Agent — Claude Primary

Use for:

- Product scope definition.
- Acceptance criteria and non-goals.
- Roadmap sequencing.
- Deciding whether a task should be split, batched, paused, or escalated.
- User-facing value judgment.

Default mode:

```bash
claude -p --allowedTools 'Read,Bash' --max-turns 8 < /tmp/<task>-pm-prompt.md
```

Fallback:

```bash
codex exec --skip-git-repo-check --sandbox read-only - < /tmp/<task>-pm-prompt.md
```

Expected output:

- Scope verdict: `PASS`, `BLOCKED`, or `NEEDS_SPLIT`.
- User-visible acceptance criteria.
- Non-goals / out-of-scope.
- Risks that should stop implementation.

### 2. Tech Lead / Architecture Agent — Claude Primary

Use for:

- Architecture boundaries.
- Cross-file/system design.
- Public/private state contracts.
- Benchmark metric definition changes.
- Plans that affect more than one module or future platform direction.

Default mode:

```bash
claude -p --allowedTools 'Read,Bash' --max-turns 10 < /tmp/<task>-tech-lead-prompt.md
```

Fallback:

```bash
codex exec --skip-git-repo-check --sandbox read-only - < /tmp/<task>-tech-lead-prompt.md
```

Expected output:

- Recommended architecture.
- Files/modules likely touched.
- Boundaries that must not move.
- Verification strategy.
- Whether the task can be batched or needs isolated review.

### 3. Engineer Agent — Codex Primary

Use for:

- Focused code implementation.
- TDD behavior changes.
- Test additions.
- Mechanical migrations once scope and architecture are clear.
- Report/doc updates tied to implementation.

Default mode:

```bash
codex exec --skip-git-repo-check --sandbox workspace-write - < /tmp/<task>-engineer-prompt.md
```

Engineer requirements:

- Execute only the current `[>]` item or explicitly scoped batch in `docs/active_plan.md`.
- Use strict TDD for behavior changes: RED, GREEN, focused tests, full suite.
- Preserve canonical No-Limit Hold'em rules and `texas_holdem/engine/hand_evaluator.py` semantics.
- Preserve `DecisionProvider` / `ActionValidator` as the legality boundary.
- Preserve public/private state safety; no hidden cards in public trainer feedback or benchmark summaries.
- Avoid broad `texas_holdem/engine/game.py` rewrites.
- Add stable reports under `docs/reports/` and index them when production code or durable decisions change.

Expected output:

- TDD RED evidence when applicable.
- GREEN/focused test evidence.
- Full-suite result or explicit blocker.
- Files changed.
- Active-plan advancement.

### 4. Domain / Poker UX Review Agent — Codex by Default

Use only when the task affects visible gameplay, poker semantics, player trust, or training feedback quality.

Default mode:

```bash
codex exec --skip-git-repo-check --sandbox read-only - < /tmp/<task>-poker-review-prompt.md
```

Expected output:

- Verdict: `APPROVED` or `REQUEST_CHANGES`.
- Poker UX observations.
- Poker-rule or trust blockers.
- Whether execution may proceed.

## Execution Patterns

### Pattern A — Claude Scope + Claude Tech Lead + Codex Batch

Use when several related tasks share architecture or can be safely executed as a batch.

1. Claude PM defines batch scope and acceptance criteria.
2. Claude Tech Lead defines architecture and boundaries.
3. Codex executes the batch item-by-item with TDD where applicable.
4. Hermes verifies changed files, focused tests, full suite, and active-plan state.

Good for:

- Planned benchmark/reporting batches.
- Documentation synchronization before a new phase.
- Feature groups where architecture is already clear.

### Pattern B — Single Sensitive Slice With Review

Use when a slice touches player-visible behavior, poker semantics, public/private state contracts, or benchmark metric definitions.

1. Claude PM or Codex PM pre-check.
2. Optional Claude Tech Lead architecture check.
3. Codex engineer implementation.
4. Codex poker/domain review.
5. Hermes verification.

Good for:

- Terminal UX changes.
- Betting/action semantics.
- Showdown/visibility behavior.
- New public state contracts.
- AI decision policy changes that affect gameplay feel.

### Pattern C — Direct Codex Implementation + Hermes Verification

Use when scope is already clear and risk is low.

1. Codex engineer implementation.
2. Hermes verification.

Good for:

- Additive tests.
- Additive benchmark/report fields when metric semantics are already defined.
- Mechanical docs/report updates.
- Small utilities that do not affect runtime gameplay.

### Pattern D — Hermes Direct Edit + Verification

Use for tiny local documentation or bookkeeping edits where invoking an implementation agent would add overhead.

1. Hermes edits the file.
2. Hermes validates links/tests/active-plan consistency.

Good for:

- Updating this workflow document.
- Correcting stale active-plan checkboxes after verified implementation.
- Indexing a stable report.

## Review Escalation Rules

Run PM and/or Tech Lead review before coding when any of these are true:

- The task changes architecture, public/private state shape, benchmark metric definitions, or module boundaries.
- The task has ambiguous scope or might expand into online/API/WebSocket/platform work.
- The task affects future AI Poker Arena / external-agent direction.
- The task can be batched but needs scope control.

Run Poker UX/domain review after coding when any of these are true:

- Terminal gameplay output changes.
- Poker action semantics, betting order, pot distribution, showdown reveal, all-in/side-pot behavior, or trainer feedback changes.
- The change could make a serious poker player distrust the hand flow.

Skip extra agent review when:

- The task is additive/reporting-only.
- Existing tests and Hermes verification directly cover the acceptance criteria.
- There is no player-visible UX, poker-rule, or public contract change.

## Hermes Verification Gate

Before reporting completion, Hermes must independently verify:

1. Relevant file snippets or docs were inspected.
2. Focused tests ran from Hermes when code changed.
3. Full suite ran from Hermes when production behavior changed or when the active plan requires it.
4. `docs/active_plan.md` has exactly one `[>]` active item unless a phase is complete.
5. Active-plan counting uses actual task/slice rows, not raw `text.count('[>]')`.
6. Stable docs/reports are indexed in `docs/index.md` when appropriate.

If verification fails after an agent advanced the plan, stop and treat the task as blocked until fixed.

## Current Project Interpretation

For the current Texas Hold'em roadmap:

- Keep local CLI trainer and built-in AI credibility first.
- Do not start Web UI, WebSocket, online room, auth, external-agent sandbox, or public API work until local AI, event boundaries, and benchmark evidence are stable.
- Use Claude for PM/Tech Lead planning of the next phase.
- Use Codex for implementation.
- Use Codex poker review only for gameplay/training UX changes.
