# Phase 2 Contract Hardening Plan

Date: 2026-05-11

## Goal

Define and harden the local contracts that must be stable before online rooms, public external-agent APIs, WebSocket coordination, or platform security work begins.

## Scope

Phase 2 is a planning, contract, and validation phase. It keeps the project local-first while making the future AI Poker Arena / Agent Poker Platform safer to build.

Primary boundaries:

- `texas_holdem/ai/agent_state_contract.py` remains the future external-agent state-shape anchor.
- `texas_holdem/ai/decision_provider.py` remains the decision input/output abstraction.
- `texas_holdem/ai/action_validator.py` remains the legality and fallback boundary for actions returned by providers.
- `texas_holdem/engine/engine_events.py` remains the terminal/headless/future-adapter event boundary.
- `texas_holdem/analytics/headless_simulation.py` remains the local benchmark and event-collection runner.
- `texas_holdem/analytics/ai_system_evaluator.py` remains the local aggregate benchmark/report generator.

## Explicit Non-Goals

Phase 2 does not implement:

- Online poker rooms.
- WebSocket servers.
- Public external-agent API endpoints.
- Auth, user accounts, permissions, or rate limits.
- Real-money play, payments, balances, custody, or compliance systems.
- Solver-backed or GTO-correct strategy claims.

## Agent Routing

- Claude is primary for PM and Tech Lead decisions: scope, sequencing, acceptance criteria, architecture boundaries, and public/private contract review.
- Codex is primary for implementation: documentation edits, tests, code changes, and verification evidence.
- Domain poker review is used only when visibility, player trust, poker semantics, or terminal UX risk justifies it.
- Hermes remains final coordinator and verifier; agent outputs are advisory until files and validation commands are inspected.

## Slices

### Slice 2.1 Public/Private State Visibility Matrix

Type: docs-only.

Deliverable: [docs/architecture/public-private-state-contract.md](../architecture/public-private-state-contract.md)

Acceptance criteria:

- Defines visibility by actor and hand phase.
- Names hidden/private data explicitly.
- Defines showdown reveal and benchmark transcript/reporting rules.
- References current modules accurately.
- Does not implement an API, server, or runtime behavior change.

Validation:

```bash
test -f docs/architecture/public-private-state-contract.md
rg -n "agent_state_contract.py|decision_provider.py|action_validator.py|engine_events.py|headless_simulation.py|ai_system_evaluator.py" docs/architecture/public-private-state-contract.md
```

### Slice 2.2 Benchmark Acceptance Criteria Definition

Type: docs-only.

Deliverable: stable benchmark-gates document under `docs/architecture/` or `docs/plans/`.

Acceptance criteria:

- Separates product gates from observational diagnostics.
- Defines default benchmark protocol: seeds, hand count, player count, starting stacks, and output artifacts.
- Defines acceptance thresholds for illegal action rate, completion rate, public-card transcript safety, and metric availability.
- Explicitly says benchmark metrics are local trainer quality gates, not solver/GTO proof.

Validation:

```bash
rg -n "benchmark|acceptance|illegal action|seed|GTO" docs/architecture docs/plans
```

### Slice 2.3 Decision/Action/Event Boundary Documentation

Type: docs-only.

Deliverable: boundary document describing how decisions, validation, history, events, and benchmark summaries relate.

Acceptance criteria:

- Documents `DecisionProvider.decide(...) -> ActionResponse`.
- Documents `validate_action(...) -> ValidatedAction` as the legality/fallback layer.
- Documents `EngineEvent` public/private payload responsibilities.
- Documents which surfaces may consume metadata and which must ignore hidden/private information.

Validation:

```bash
rg -n "DecisionProvider|ActionResponse|ValidatedAction|EngineEvent" docs/architecture docs/plans
```

### Slice 2.4 Public State Schema Validation Tests

Type: implementation later.

Acceptance criteria:

- Adds tests that serialize external-agent state snapshots.
- Verifies no unrevealed opponent hole cards, deck order, private AI internals, or unsafe seeds appear in public state.
- Verifies the acting player/agent receives only its own private hole cards.
- Keeps `texas_holdem/ai/agent_state_contract.py` immutable-state intent intact.

Validation:

```bash
python3 -m pytest -q tests/test_decision_provider.py
```

### Slice 2.5 Benchmark Gate Validation Tests

Type: implementation later.

Acceptance criteria:

- Adds tests around benchmark gate evaluation once Slice 2.2 defines thresholds.
- Verifies transcript samples preserve public-card safety.
- Verifies seeded and multi-seed report metadata are present when configured.
- Verifies benchmark gate failures are explicit and machine-readable.

Validation:

```bash
python3 -m pytest -q tests/test_ai_system_evaluator.py
```

### Slice 2.6 Context/Index/Reflection Sync

Type: docs bookkeeping.

Acceptance criteria:

- `docs/context.md` describes Phase 2 contract-hardening as active.
- `docs/index.md` indexes stable Phase 2 documents.
- `docs/project-reflection.md` records durable decisions only when the why matters.
- `docs/active_plan.md` advances one active `[>]` slice at a time.

Validation:

```bash
rg -n "Phase 2|contract-hardening|public/private" docs/context.md docs/index.md docs/project-reflection.md docs/active_plan.md
```

### Slice 2.7 External-Agent Contract Stub Documentation

Type: docs-only.

Acceptance criteria:

- Documents future external-agent request/response shape without implementing endpoints.
- Defines versioning, serialization expectations, timeout/error behavior, and legal-action dependency.
- States that external agents may decide only from public state plus their own private hand.
- Keeps API/server/auth work out of scope.

Validation:

```bash
rg -n "external agent|request|response|version|timeout|legal_actions" docs/architecture docs/plans
```

### Slice 2.8 Platform Non-Goals Documentation

Type: docs-only.

Acceptance criteria:

- Creates or updates stable docs to make online/API/WebSocket/auth/real-money/solver-GTO non-goals explicit for Phase 2.
- Defines the earliest allowed trigger for platform work: public/private state tests and benchmark gates are documented and passing.
- Keeps roadmap language aligned with local trainer first, platform later.

Validation:

```bash
rg -n "Non-Goals|WebSocket|auth|real-money|GTO|online" docs/context.md docs/index.md docs/plans docs/architecture
```
