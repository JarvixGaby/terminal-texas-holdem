# Texas Poker System Design Scorecard

Date: 2026-05-07

Purpose: provide a repeatable architecture review rubric for evolving this project from a local terminal Texas Hold'em trainer into an AI Poker Arena / Agent Poker Platform.

Scoring scale:

- 0 = absent or actively blocking
- 1 = very weak / prototype-only
- 2 = partially present but fragile
- 3 = usable MVP with known gaps
- 4 = production-leaning, well tested
- 5 = platform-ready and continuously monitored

## Scorecard dimensions

| Dimension | Score | Current assessment | Target state |
| --- | ---: | --- | --- |
| Rule correctness | 3 | Core Hold'em flow exists; side-pot tests pass; rule checklist exists. More betting-order, all-in, split-pot, and edge-case coverage is still needed. | Exhaustive No-Limit Hold'em rule tests for blinds, betting rounds, raises, all-ins, side pots, ties, and early wins. |
| Engine/UI separation | 1 | `game.py` and `main.py` still mix engine, CLI, prints, prompts, replay, and analytics. | Headless engine with explicit state snapshots and action responses; CLI/Web/agent adapters outside engine. |
| Decision evaluation loop | 3 | Rule-based `decision_evaluator.py` exists and is integrated into hand history plus compact human feedback. | Every decision is evaluated, persisted, replayable, and comparable across sessions; evaluator has calibrated heuristics and eventually stronger models. |
| AI behavior quality | 2 | Standard and advanced AI exist with equity/range/GTO-style concepts, but behavior is not yet benchmarked statistically. | AI profiles measured by VPIP, PFR, aggression, fold rates, showdown rate, win rate, bluff proxies, illegal action rate. |
| Data persistence | 2 | JSON hand history and SQLite database coexist; new decision feedback is stored in JSON history. | One canonical persistence layer, likely SQLite, with JSON import/export compatibility. |
| Observability/debuggability | 2 | Logging/error-handling modules exist, but action/evaluation/system metrics are not fully centralized. | Structured event logs for table events, actions, evaluations, exceptions, agent timeouts, and simulation metrics. |
| Test coverage | 3 | Current suite passes and covers evaluator, decision-feedback integration, hand evaluation, blinds, dealer, side pots, and imports. | Broader scenario tests, property/regression tests, headless simulation tests, and CI-style quality gates. |
| Agent interface readiness | 1 | No unified `DecisionProvider` interface yet. Built-in AI and CLI decisions are still directly coupled to game flow. | Human CLI, built-in AI, remote agent, and future web users all use the same validated decision interface. |
| Public/private state separation | 1 | Game objects contain all information; no formal public/private snapshot boundary. | Agents only receive public table state plus their private hole cards; server retains full authoritative state. |
| Action validation/fairness | 2 | Basic legal action checks exist in UI/game flow; evaluator detects illegal actions. | Central validator rejects illegal/late/timed-out actions before state mutation and records audit events. |
| Replay and coaching UX | 3 | Instant replay exists; decision feedback is now attached to action history for future replay. | Replay highlights key decisions, missed value, bad pot-odds calls, overfolds, and session-level leaks. |
| Online room scalability | 1 | No server/table event model yet. | Event-driven table state, WebSocket/HTTP API, room/chat model, agent sandbox/timeouts, persistence, rankings. |

Current average: 2.0 / 5

Interpretation: the product is a strong local prototype/trainer with early coaching capability, but not yet an agent platform. The next architecture leap is not a web UI; it is separating decision providers and creating a headless, validated, event-driven engine core.

## Review cadence

Run this scorecard after each major sprint:

1. Baseline cleanup and evaluator integration.
2. DecisionProvider interface extraction.
3. Headless AI-only simulation harness.
4. SQLite persistence consolidation.
5. Agent request/response schema and public/private state split.
6. First online room prototype.

## Gates before online poker room work

Do not start real online multiplayer/agent room work until these are true:

- `python3 -m pytest -q` passes with no warnings.
- A hand can be run headlessly without CLI input/print dependencies.
- Every action goes through one validator and one decision/evaluation pipeline.
- Hand history records every action, legal context, evaluation, and final result.
- Public/private state snapshots are defined and tested.
- Illegal action and timeout behavior are deterministic and audited.

## Next recommended actions

1. Extract a `DecisionProvider` abstraction.
2. Move CLI prompting into a `HumanCliDecisionProvider`.
3. Wrap existing AI in `BuiltInAIDecisionProvider`.
4. Add headless simulation tests using these providers.
5. Add AI system evaluator that runs many hands and produces behavior metrics.
