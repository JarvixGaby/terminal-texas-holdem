# Sprint 2 Overall Plan: Agent Boundary, Benchmarking, and Metric Fidelity

> **For Hermes:** Use this as the umbrella Sprint 2 plan. Execute each unfinished stage with TDD. For any code-producing stage, write failing tests first, verify RED, implement GREEN, then update docs and benchmark artifacts.

**Goal:** Make the local Texas Hold'em trainer ready for future external AI agents by stabilizing action boundaries, headless simulation, benchmark metrics, and trustworthy game outcome data before online-room work.

**Architecture:** Sprint 2 is the platform-foundation sprint. It should turn the current CLI-heavy game into a validated, measurable, agent-compatible core without yet building WebSocket rooms or user-submitted agent infrastructure.

**Tech Stack:** Python 3, pytest, terminal Texas Hold'em modules, JSON/SQLite runtime persistence.

---

## Sprint 2 definition of done

Sprint 2 is done when the project has:

1. A unified provider/validator decision boundary used by actual gameplay.
2. A headless AI-only benchmark path that does not pollute runtime data or singleton AI managers.
3. Machine-readable benchmark reports.
4. Player-level AI behavior metrics.
5. Explicit hand outcome metadata, not proxy-only inference.
6. Blind-aware preflop metric denominators.
7. Profile/style-aware benchmark breakdown.
8. A documented benchmark baseline that can be used for AI tuning.

Online rooms, WebSocket protocol, and external untrusted-agent execution are explicitly post-Sprint-2.

## Completed stages

### Sprint 2.0 — Baseline decision/evaluation modules

Status: completed

Delivered:

- `decision_provider.py`
- `action_validator.py`
- `headless_simulation.py`
- `ai_system_evaluator.py`
- baseline AI intelligence report

Report:

- `docs/reports/2026-05-07-sprint2-ai-intelligence-baseline.md`

### Sprint 2.1 — Provider-driven game flow

Status: completed

Delivered:

- `DecisionProvider -> ActionValidator -> apply action` pipeline in `game.py`
- validated fallback for illegal provider output
- history action metadata
- internal AI live `Card` adapter path
- headless singleton-manager isolation
- provider-driven game flow tests

Report:

- `docs/reports/2026-05-07-sprint2-1-provider-driven-game-flow.md`

### Sprint 2.2 — AI metrics and 1,000-hand benchmark

Status: completed

Delivered:

- `PlayerPokerMetrics`
- player-level VPIP/PFR/aggression/fold/showdown/win/poor-blunder metrics
- `benchmark_ai_system(...)`
- JSON benchmark artifact output
- active-hand counting fix
- 1,000-hand benchmark artifact

Reports/artifacts:

- `docs/reports/2026-05-08-sprint2-2-ai-metrics-and-1000-hand-benchmark.md`
- `docs/reports/2026-05-08-sprint2-2-ai-1000-hand-benchmark.json`

### Sprint 2.3A — Hand outcome metadata and showdown metric fidelity

Status: completed

Delivered:

- `GameRecord.outcome_metadata`
- `ended_by_fold`
- `went_to_showdown`
- `winner_reason`
- hand-level `street_reach`
- headless summary outcome metadata
- `showdown_rate` based on explicit `went_to_showdown` when available
- regenerated 1,000-hand benchmark artifact

Reports/artifacts:

- `docs/reports/2026-05-08-sprint2-3-hand-outcome-and-metric-fidelity.md`
- `docs/reports/2026-05-08-sprint2-3-ai-1000-hand-benchmark.json`

Current verification:

```text
89 passed
```

## Remaining Sprint 2 stages

### Sprint 2.3B — Blind-aware VPIP/PFR and preflop opportunity counting

Status: completed

Why:

Current VPIP/PFR denominators still use `hands_played`, and forced blinds are not cleanly separated from voluntary preflop entries. This makes preflop looseness/tightness less trustworthy.

Deliverables:

- record blind positions per hand
- record forced blind postings separately from voluntary actions
- add `preflop_opportunities` per player
- calculate VPIP from voluntary preflop calls/raises/all-ins only
- calculate PFR from voluntary preflop raises only
- keep legacy metric fallback for old summaries
- regenerate 1,000-hand benchmark

Suggested tests:

- blind postings do not count as VPIP
- big blind check option counts as opportunity but not VPIP/PFR
- voluntary call/raise after blinds counts correctly
- busted/final-stack-only players still do not inflate denominators

### Sprint 2.4 — Profile/style-aware benchmark breakdown

Status: completed

Why:

Aggregate metrics hide whether a specific AI style/profile is underperforming. Before tuning, benchmark output should show behavior by profile.

Deliverables:

- include AI style/profile in hand summaries or benchmark player metadata
- aggregate metrics by profile/style
- compare profile win rate, poor/blunder rate, VPIP/PFR, fold rate
- document which profile is weakest and why
- regenerate 1,000-hand benchmark with profile breakdown

Suggested tests:

- synthetic simulations aggregate player metrics by profile
- missing profile metadata falls back to `unknown`
- benchmark JSON includes `profile_metrics`

### Sprint 2.5 — Targeted AI tuning using benchmark feedback

Status: completed

Why:

Current benchmark still shows too many poor decisions and excessive folding. Tuning should happen only after metrics are trustworthy enough to compare before/after.

Deliverables:

- identify top poor/blunder scenarios from benchmark action records
- tune preflop range / fold thresholds / aggression thresholds
- add regression tests for tuned decision scenarios
- run before/after 1,000-hand benchmark comparison
- document improvement or tradeoff

Suggested tests:

- selected weak preflop scenarios no longer produce poor/blunder action
- legal-action safety remains unchanged
- illegal_action_rate remains 0.0
- full benchmark does not regress stability

### Sprint 2.6 — Headless engine boundary design spike

Status: completed

Why:

`game.py` still mixes CLI printing, sleeps, state mutation, history, and evaluation. External agents and online rooms need a cleaner engine/event boundary.

Deliverables:

- document proposed engine/event API
- identify minimal extraction seams from `game.py`
- define game events emitted by engine
- define command/action inputs consumed by engine
- no large refactor unless the spike identifies a safe incremental path

Suggested tests:

- engine-facing action command schema can be validated without CLI
- current terminal UX remains unchanged

## Post-Sprint-2 stages

These should wait until Sprint 2 is complete:

### Sprint 3 — Engine/UI separation

- extract headless game engine from CLI-heavy `game.py`
- emit structured events instead of direct print-only flow
- keep terminal UI as an adapter

### Sprint 4 — External agent API contract

- immutable public/private state schema
- timeout/error sandbox contract for external agents
- action submission API
- replay/evaluation feedback API

### Sprint 5 — Online room prototype

- WebSocket room lifecycle
- table seats and observers
- agent join/leave
- server-side action validation
- replay/hand-history streaming

### Sprint 6 — Platform hardening

- persistence migration under `data/`
- auth/account model if needed
- multi-table benchmark runners
- agent ranking/leaderboards
- deployment path

## Recommended immediate next action

Start Sprint 2.3B: blind-aware VPIP/PFR and preflop opportunity counting.

Do not start WebSocket room work yet.
