# Phase 2 Platform Non-Goals

Date: 2026-05-12

## Purpose

This document defines what Phase 2 contract-hardening explicitly does not implement, certify, or imply. It prevents the project from sliding into online platform work before the local trainer contracts are stable.

Phase 2 remains a local documentation, contract, and test hardening phase. It prepares the future AI Poker Arena / Agent Poker Platform direction, but it is not the platform build itself.

## Non-Goals

The following are out of scope for Phase 2:

- Online poker rooms.
- Public API endpoints.
- WebSocket table servers.
- Auth, user accounts, permissions, sessions, tokens, or rate limits.
- Agent sandboxing, process isolation, hosted-agent execution, or marketplace packaging.
- Real-money play, deposits, balances, custody, payments, withdrawals, rake, KYC, AML, compliance, or gambling-law readiness.
- Solver validation, GTO proof, exploitability measurement, or claims that the built-in AI plays optimal poker.
- Multi-tenant platform security certification.
- Public external-agent API stability or backward-compatibility guarantees.
- Production deployment, observability, SLOs, incident response, moderation, or abuse handling.

## What Phase 2 Does Produce

Phase 2 may produce local contracts, docs, and tests for future platform readiness:

- Public/private visibility rules for human players, built-in AI, future external agents, benchmark/reporting, and terminal/headless adapters.
- Benchmark acceptance gates for local trainer quality evidence.
- Machine-readable benchmark gate evaluation for local benchmark artifacts.
- Decision/action/event boundary documentation.
- External-agent request/response contract stubs.
- Tests proving external-agent state serialization is seat-scoped and public-safe.
- Tests proving benchmark gate failures are machine-readable and transcript safety is enforced.

These outputs are prerequisites for platform work; they are not a public platform.

## Earliest Trigger for Platform Work

Online/API/WebSocket/auth/platform implementation may begin only after all of the following are true:

1. Public/private state visibility is documented.
2. External-agent state serialization tests pass and prove the acting seat receives only public state plus its own private hand.
3. Benchmark acceptance gates are documented.
4. Machine-readable benchmark gate tests pass and fail safely on incomplete runs, illegal actions, malformed metadata, and unsafe transcript leaks.
5. Decision/action/event boundaries are documented.
6. External-agent request/response contract stubs are documented.
7. This platform non-goals document is indexed and validated.
8. The maintainer explicitly chooses a platform slice after Phase 2, instead of continuing local trainer hardening.

The trigger is not “the idea is clear enough.” The trigger is contract evidence plus an explicit decision to begin platform work.

## Required Language for Reports and Plans

When describing Phase 2 benchmark and contract outputs, use cautious wording:

- Say: “local trainer quality gate,” “public/private state contract,” “future external-agent stub,” and “not an online platform yet.”
- Do not say: “production-ready poker platform,” “GTO-proven AI,” “real-money ready,” “secure external-agent marketplace,” or “public API complete.”
- Benchmark gates are local trainer diagnostics and acceptance gates, not solver/GTO or compliance proof.

## Relationship to Future Work

After Phase 2, possible platform work should start with another explicit plan, likely covering:

- Transport choice: WebSocket, HTTP, stdio/MCP, subprocess, or hosted-agent bridge.
- Auth and account model.
- Agent sandbox/timeout/resource isolation.
- Table room model and chat model.
- Persistence and audit logs.
- Public API versioning and compatibility.
- Abuse/security review.

None of these should be implemented implicitly while editing Phase 2 docs or local benchmark tests.
