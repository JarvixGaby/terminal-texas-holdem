# Document Index

Date: 2026-10-16

This file is the stable document and file index for the Texas Hold'em project. It reuses the previous root `index.md` content under the `docs/` documentation contract.

## Project purpose

The project is currently a Python terminal Texas Hold'em trainer with built-in AI players, hand history, replay tools, odds calculation, decision feedback, and early AI/system evaluation tooling.

Long-term direction: evolve into an AI Poker Arena / Agent Poker Platform where humans, built-in AI, and user-provided agents can join poker rooms and play/evaluate hands.

## How to run

```bash
./scripts/start.sh
```

Run tests:

```bash
python3 -m pytest -q
```

Note: use `python3`; the current environment does not provide a `python` command.

## Current status

Latest full-suite validation after the README refresh:

```text
302 passed
```

Phase 2 contract-hardening is complete/documented: public/private state visibility docs, benchmark acceptance gates, decision/action/event boundary docs, external-agent state serialization safety tests, executable benchmark gate validation, external-agent request/response contract stubs, and platform non-goals are in place.

Phase 3 AI Evaluation Loop is complete through Stage 3.5. The canonical primary `10 seeds × 500 hands` AI benchmark gate is runnable in a practical local execution profile and currently returns `PASS`: hard legality/error/coverage/transcript/profile gates pass, and the previously warned decision-quality/blunder soft thresholds pass after preflop-fold calibration. Stage 3.2 adds explicit profile target-band calibration fields and a reduced `10 seeds × 100 hands` diagnostic artifact: reduced gate `PASS`, calibration status `WARN` across seeds, showing several profiles are tighter/lower-participation than target bands while poker-quality bands remain healthy. Stage 3.3 adds sanitized poor/blunder audit samples to benchmark reports and identifies top diagnostic classes: pot-odds call mistakes, overfolds, and low-equity bluffs. Stage 3.4 adds explicit public transcript schema/showdown policy fields and extends benchmark safety gates across transcript samples plus poor/blunder audit samples. Stage 3.5 adds repeatable evaluation-agent loop templates and one complete artifact-review loop. Post-Stage 3.5, the public-context pot-odds audit split and calling-station negative-equity call loop reached the reduced-artifact target: pot-odds call samples moved 33→6 and calling-station concentration moved 23→2. The first post-Phase-3 roadmap batch is complete: evidence baseline inventory, remaining poor/blunder public-context triage, Builder/Hacker loop refresh/dry-run, profile calibration WARN prioritization, and headless/action API readiness inventory. The next local-only implementation slice added a deterministic action-sequence headless fixture harness for scripted provider responses, validator metadata, event collection, public-safe result serialization, and runtime artifact isolation. Platform/WebSocket/auth/external-agent runtime remains deferred.

On 2026-10-15 the terminal computer-opponent profile and AI position update passed a fresh primary `10 × 500` gate with zero illegal actions and zero runtime errors. A separate late-position open-raise candidate passed reduced diagnostics but failed primary completion and was rolled back. Profile calibration still reports WARN.

Sprint 2 added:

- `decision_provider.py`
- `action_validator.py`
- `headless_simulation.py`
- `ai_system_evaluator.py`
- tests for all four modules
- AI intelligence baseline report under `docs/reports/`

Sprint 2.1 added:

- provider + validator pipeline integration in `game.py`
- action metadata in history records
- live Card-object adapter path for internal AI
- headless simulation in-memory AI manager isolation
- provider-driven game flow tests

Sprint 2.2 added:

- player-level poker metrics: VPIP, PFR, aggression factor, fold rate, showdown proxy, win rate, poor/blunder rate
- benchmark JSON report output through `benchmark_ai_system(...)`
- 1,000-hand benchmark artifact under `docs/reports/`
- final-hand summaries in headless simulation for outcome metrics
- tests for metrics, benchmark report writing, and active-hand counting

Sprint 2.3 added:

- explicit `GameRecord.outcome_metadata`
- hand outcome flags: `ended_by_fold`, `went_to_showdown`, `winner_reason`
- per-hand `street_reach` metadata: `saw_flop`, `saw_turn`, `saw_river`
- headless summary `outcome_metadata`
- `showdown_rate` based on explicit `went_to_showdown` when available
- blind-aware preflop metadata: `blind_positions` and `forced_blinds`
- `preflop_opportunities` for VPIP/PFR denominators
- regenerated 1,000-hand benchmark artifacts with improved showdown and preflop metric semantics

Sprint 2.4-2.6 completed:

- profile/style-aware benchmark aggregation via `profile_metrics` and `weakest_profile`
- targeted AI tuning for free-check preflop spots
- final 1,000-hand benchmark artifact with profile breakdown
- headless engine boundary design spike for Sprint 3

## Core documentation contract

| Path | Purpose |
| --- | --- |
| `AGENTS.md` | Single source of truth for agent instructions and project-specific agent constraints. |
| `CLAUDE.md` | Tool-specific shim: `See AGENTS.md for all agent instructions.` |
| `docs/context.md` | Project snapshot read at session start. |
| `docs/project-reflection.md` | Durable decision log for major “why did we do this” decisions. |
| `docs/conversations/_example.md` | Template for manually created conversation logs; conversation logs themselves are not indexed. |
| `docs/index.md` | This stable document/file index. |

## Core runtime entry points

| Path | Purpose |
| --- | --- |
| `scripts/start.sh` | Starts the terminal app from any working directory. |
| `main.py` | Terminal application entry point and menu/UI orchestration; assigns distinct built-in archetypes to computer opponents. Still large; future refactor target. |
| `localization.py` | Startup language selection and terminal-only Chinese/English text translation; internal game state and saved history retain their existing values. |
| `game.py` | Main Texas Hold'em game loop, betting rounds, dealing, showdown, history/evaluation integration. Still mixes engine + CLI output. |
| `player.py` | Player, HumanPlayer, AIPlayer, and AI decision dispatch. |
| `card.py` | Card, suit, rank, and deck primitives. |
| `hand_evaluator.py` | Poker hand ranking and comparison. |
| `side_pot_manager.py` | Side-pot calculation and contribution tracking. |
| `official_rules.py` | Rule helper / No-Limit Hold'em rule concepts. |

## AI and decision systems

| Path | Purpose |
| --- | --- |
| `smart_ai_system.py` | Standard AI decision system. |
| `advanced_ai_engine.py` | Advanced AI engine with range/GTO-style concepts. |
| `ai_profiles.py` | Sprint 4 immutable built-in AI archetype profile config for nit, TAG, LAG, calling-station, maniac, and balanced opponents. |
| `optimized_odds_calculator.py` | Monte Carlo equity/odds calculator with caching/performance modes. |
| `decision_evaluator.py` | Rule-based evaluator for individual decisions: grade, score, reasoning, risk tags, metrics. |
| `decision_provider.py` | Sprint 2 provider abstraction: snapshots, action responses, built-in AI adapter, human CLI adapter. |
| `action_validator.py` | Sprint 2 action validation and safe fallback layer. |
| `engine_events.py` | Sprint 3 structured engine event contract used by terminal/headless/future online adapters. |
| `terminal_renderer.py` | Sprint 3 terminal adapter for rendering selected `EngineEvent` objects outside engine mutation code. |
| `agent_state_contract.py` | Immutable public/private state contract for future external-agent APIs; serializes public table state plus only the acting seat's private hand and strips hidden action-history internals. |
| `headless_simulation.py` | Sprint 2 AI-only simulation wrapper for non-interactive benchmark runs. |
| `ai_system_evaluator.py` | Sprint 2 aggregate AI behavior/evaluation report generator; includes player-level poker metrics, benchmark JSON output, blind-aware preflop opportunities, profile metrics, configurable starting chips, optional seeded runs, multi-seed benchmark summaries, stack concentration metrics, human-readable transcript samples, Phase 2 machine-readable benchmark gate evaluation, optional benchmark progress artifacts, Phase 3 profile target-band calibration fields, sanitized poor/blunder audit samples, and public transcript/schema safety metadata. |
| `realtime_assistant.py` | Real-time assistant / coaching support. |
| `hand_coach.py` | Hand-end coaching summary builder for human players; converts action-level decision evaluations into a non-blocking per-hand average score, worst-decision highlight, and next-hand focus while avoiding opponent private-card leaks. |
| `training_center.py` | Local trainer center that converts player evaluation/statistics into next-session focus areas and execution checklists. |
| `player_evaluation.py` | Player evaluation logic. |
| `player_styles.py` | Player style analyzer and persistent style stats. |

## History, replay, analytics, and persistence

| Path | Purpose |
| --- | --- |
| `game_history.py` | JSON hand history manager with atomic saves, damaged-file protection, decision evaluations, and explicit outcome/blind metadata. |
| `history_viewer.py` | History browsing and replay entry points. |
| `instant_replay.py` | Instant replay system. |
| `quick_replay_system.py` | Quick replay and odds review support. |
| `database.py` | SQLite persistence layer. Long-term target is to make SQLite canonical. |
| `advanced_analytics.py` | Higher-level analytics features. |
| `data_visualization.py` | Data visualization/reporting utilities. |
| `optimized_data_manager.py` | Optimized data management helpers. |

## Config, logging, and infrastructure

| Path | Purpose |
| --- | --- |
| `config.py` | General configuration. |
| `game_config.py` | Game configuration helpers. |
| `enhanced_config_manager.py` | Enhanced configuration manager. |
| `enhanced_error_handling.py` | Error handling utilities. |
| `enhanced_logging.py` | Logging utilities. |
| `constants.py` | Shared constants. |
| `exceptions.py` | Custom exceptions. |
| `lru_cache.py` | Cache utility. |

## Tests

| Path | Purpose |
| --- | --- |
| `tests/test_decision_evaluator.py` | Unit tests for decision evaluator. |
| `tests/test_decision_feedback_integration.py` | Game/history integration tests for decision feedback. |
| `tests/test_decision_provider.py` | Sprint 2 tests for provider abstractions, including Phase 2 external-agent public/private serialization safety. |
| `tests/test_action_validator.py` | Sprint 2 tests for action validation. |
| `tests/test_headless_simulation.py` | Sprint 2 tests for AI-only simulation and file isolation. |
| `tests/test_ai_system_evaluator.py` | Sprint 2 tests for aggregate AI evaluation, Phase 2 benchmark gate evaluation, Phase 3 profile target-band calibration, sanitized poor/blunder audit samples, and public/private transcript safety gates. |
| `tests/test_ai_metrics.py` | Sprint 2 tests for player-level poker metrics, benchmark JSON output, explicit showdown-rate semantics, blind-aware VPIP/PFR denominators, and profile-aware metric aggregation. |
| `tests/test_ai_tuning.py` | Sprint 2.5 and Phase 3 regression tests for targeted AI tuning, including focused calling-station negative-equity pot-odds call guards. |
| `tests/test_ai_profiles.py` | Sprint 4 tests for immutable AI archetype profile schema, serialization, validation, and default AI compatibility. |
| `tests/test_ai_scenario_sanity.py` | Sprint 4 deterministic AI spot tests for obvious bad-play and action-validator boundary sanity. |
| `tests/test_game_history_outcome_metadata.py` | Sprint 2.3 tests for explicit hand outcome metadata persistence and legacy history compatibility. |
| `tests/test_training_center.py` | Tests for local trainer report generation, onboarding plans, and leak prioritization. |
| `tests/test_player_evaluation_menu_contract.py` | Regression test for the main-menu player evaluation entrypoint. |
| `tests/test_module_imports.py` | Import smoke tests. |
| `tests/test_hand_coach.py` | Unit tests for hand-end coach summaries, insufficient-sample messaging, risk-tag tips, and opponent-card leak avoidance. |
| `tests/test_hand_coach_integration.py` | Game/instant-replay integration tests for non-blocking human hand-coach summaries. |
| `tests/test_hand_evaluator.py` | Hand evaluation tests. |
| `tests/test_blinds.py` | Blind/dealer behavior tests. |
| `tests/test_dealer.py` | Dealer behavior tests. |
| `tests/test_side_pots.py` | Side-pot tests. |
| `test_integration.py` | Legacy/root integration tests. |
| `test_side_pot_detailed.py` | Legacy/root detailed side-pot tests. |
| `test_side_pot_fix.py` | Legacy/root side-pot regression tests. |

## Documentation

| Path | Purpose |
| --- | --- |
| `README.md` | English project README and entry point to the Chinese version. |
| `docs/readme-zh.md` | Chinese project README. |
| `docs/user-guide.md` | Detailed user guide. |
| `docs/evaluation-agent-loop-templates.md` | Phase 3 templates for Builder Agent, Hacker Agent, Benchmark Agent, Poker Quality Reviewer, Safety/Contract Agent, and Coordinator outputs. |
| `docs/triad-role-workflow.md` | Three-role execution loop: product manager, engineer, and senior poker-player user representative. |
| `docs/archive/legacy-improvements.md` | Legacy improvement summary. |
| `docs/plans/2026-05-07-texas-poker-optimization-roadmap.md` | Local trainer optimization roadmap. |
| `docs/plans/2026-05-07-agent-poker-platform-roadmap.md` | Agent Poker Platform roadmap. |
| `docs/plans/2026-05-08-sprint2-overall-agent-boundary-and-metrics-plan.md` | Umbrella Sprint 2 plan: agent boundary, benchmarking, metric fidelity, and remaining stages. |
| `docs/plans/2026-05-08-sprint2-3-hand-outcome-and-metric-fidelity.md` | Sprint 2.3 implementation plan for explicit outcome metadata and metric fidelity. |
| `docs/plans/2026-05-08-sprint3-engine-event-boundary-plan.md` | Sprint 3 implementation plan for introducing structured engine events before terminal/headless/online adapter separation. |
| `docs/plans/2026-05-09-terminal-pro-trust-plan.md` | Terminal dogfood implementation plan for professional-player trust fixes. |
| `docs/plans/2026-05-11-sprint4-ai-opponent-experience-plan.md` | Sprint 4 plan for improving local CLI robot opponent credibility, style variety, trainer feedback, and AI benchmark hardening. |
| `docs/plans/2026-05-11-phase2-contract-hardening-plan.md` | Phase 2 plan for public/private state contracts, benchmark gates, decision/action/event boundaries, and platform non-goals before online/external-agent work. |
| `docs/plans/2026-05-12-ai-player-evaluation-plan.md` | Evaluation plan for testing current built-in AI player effectiveness through focused tests, smoke benchmarks, transcript safety checks, and a durable report. |
| `docs/plans/2026-05-12-phase3-ai-evaluation-loop-plan.md` | Phase 3 plan for formalizing primary AI benchmark gates, profile calibration, poor/blunder audit, public/private safety gates, and repeatable evaluation-agent loops before platform work. |
| `docs/plans/2026-05-25-post-phase3-development-roadmap.md` | Post-Phase-3 roadmap from local trainer evidence loops toward AI Poker Arena / Agent Poker Platform, with staged gates before external-agent runtime or online rooms. |
| `docs/architecture/system-design-scorecard.md` | Architecture scorecard. |
| `docs/architecture/ai-system-review-001.md` | AI/system design review. |
| `docs/architecture/public-private-state-contract.md` | Actor-by-phase public/private visibility contract for human players, built-in AI, future external agents, benchmark/reporting, and terminal/headless adapters. |
| `docs/architecture/benchmark-gates.md` | Phase 2 benchmark acceptance gates for local trainer evidence: protocol, product gates, diagnostics, artifact expectations, transcript safety, and GTO/solver non-goals. |
| `docs/architecture/decision-action-event-boundaries.md` | Phase 2 contract for `DecisionProvider`, `ActionResponse`, `ValidatedAction`, `EngineEvent` payloads, metadata handling, renderer/headless/report consumption, and future external-agent adapters. |
| `docs/architecture/external-agent-contract-stub.md` | Phase 2 documentation-only external-agent request/response stub covering versioning, JSON serialization, timeout/error behavior, legal-action dependency, and seat-scoped visibility. |
| `docs/architecture/platform-non-goals.md` | Phase 2 platform non-goals and earliest trigger for online/API/WebSocket/auth/platform work; explicitly excludes real-money and solver/GTO claims. |
| `docs/no-limit-holdem-rule-compliance-checklist.md` | No-Limit Hold'em rule compliance checklist. |
| `docs/reports/2026-05-07-sprint2-ai-intelligence-baseline.md` | Sprint 2 AI intelligence baseline report. |
| `docs/reports/2026-05-07-sprint2-1-provider-driven-game-flow.md` | Sprint 2.1 provider-driven game flow completion report. |
| `docs/reports/2026-05-08-sprint2-2-ai-metrics-and-1000-hand-benchmark.md` | Sprint 2.2 AI metrics and 1,000-hand benchmark completion report. |
| `docs/reports/2026-05-08-sprint2-2-ai-1000-hand-benchmark.json` | Sprint 2.2 machine-readable 1,000-hand benchmark artifact. |
| `docs/reports/2026-05-08-sprint2-3-hand-outcome-and-metric-fidelity.md` | Sprint 2.3 completion report for explicit hand outcome metadata and metric fidelity. |
| `docs/reports/2026-05-08-sprint2-3-ai-1000-hand-benchmark.json` | Sprint 2.3 regenerated 1,000-hand benchmark artifact with explicit showdown semantics. |
| `docs/reports/2026-05-08-sprint2-3b-blind-aware-preflop-metrics.md` | Sprint 2.3B completion report for blind-aware VPIP/PFR and preflop opportunities. |
| `docs/reports/2026-05-08-sprint2-3b-ai-1000-hand-benchmark.json` | Sprint 2.3B regenerated 1,000-hand benchmark artifact with blind-aware preflop metrics. |
| `docs/reports/2026-05-08-sprint2-4-profile-aware-benchmark.md` | Sprint 2.4 completion report for profile-aware benchmark breakdown. |
| `docs/reports/2026-05-08-sprint2-5-targeted-ai-tuning.md` | Sprint 2.5 completion report for targeted AI tuning. |
| `docs/reports/2026-05-08-sprint2-6-headless-engine-boundary-spike.md` | Sprint 2.6 spike report for headless engine boundary design. |
| `docs/reports/2026-05-08-sprint2-final-ai-1000-hand-benchmark.json` | Final Sprint 2 1,000-hand benchmark artifact with profile metrics. |
| `docs/reports/2026-05-08-sprint2-completion-report.md` | Final Sprint 2 completion report. |
| `docs/reports/2026-05-08-documentation-system-migration.md` | Completion report for the AGENTS.md-centered documentation system migration. |
| `docs/reports/2026-05-09-terminal-pro-trust-dogfood-fix.md` | Completion report for terminal professional-player trust dogfood fixes. |
| `docs/reports/2026-05-09-claude-code-sprint3-and-architecture-audit.md` | Claude Code audit of Sprint 3 plan and full technical framework robustness. |
| `docs/reports/2026-05-09-sprint3-robustness-event-slice.md` | Completion report and event coverage matrix for Sprint 3 betting-round lifecycle events. |
| `docs/reports/2026-05-09-sprint3-hand-phase-lifecycle-event-slice.md` | Completion report and event coverage matrix for Sprint 3 hand/phase lifecycle events. |
| `docs/reports/2026-05-09-sprint3-headless-event-coverage-summary.md` | Batch 1 completion report for headless collect-events summary fields. |
| `docs/reports/2026-05-09-sprint3-full-hand-event-coverage-gate.md` | Batch 2 completion report for full-hand collect-events regression gate. |
| `docs/reports/2026-05-09-sprint3-terminal-renderer-parity.md` | Batch 3 completion report for terminal renderer lifecycle-event parity tests. |
| `docs/reports/2026-05-09-sprint3-action-display-boundary-inventory.md` | Batch 4 report inventorying direct `_betting_round()` action/display IO boundaries. |
| `docs/reports/2026-05-09-sprint3-action-applied-renderer-slice.md` | Batch 5 completion report for routing call/raise display through `action_applied` terminal rendering. |
| `docs/reports/2026-05-09-sprint3-fold-action-renderer-slice.md` | Slice 6.1 completion report for routing fold display through `action_applied` terminal rendering. |
| `docs/reports/2026-05-09-sprint3-check-action-renderer-slice.md` | Slice 6.2 completion report for routing check display through `action_applied` terminal rendering. |
| `docs/reports/2026-05-09-sprint3-betting-round-start-renderer-slice.md` | Slice 7.1 completion report for routing betting round start display through `betting_round_started` terminal rendering. |
| `docs/reports/2026-05-09-sprint3-betting-round-completion-renderer-slice.md` | Slice 7.2 completion report for routing silent betting round completion lifecycle events through terminal rendering. |
| `docs/reports/2026-05-09-sprint3-hand-start-renderer-slice.md` | Slice 8.1 completion report for routing hand start display through `hand_started` terminal rendering. |
| `docs/reports/2026-05-09-sprint3-hand-completion-renderer-slice.md` | Slice 8.2 completion report for routing early-winner hand completion display through `hand_completed` terminal rendering. |
| `docs/reports/2026-05-09-sprint3-validation-failure-renderer-slice.md` | Slice 9.1 completion report for routing validation failure display through `validation_failed` terminal rendering. |
| `docs/reports/2026-05-09-sprint3-showdown-start-renderer-slice.md` | Slice 10.1 completion report for routing showdown start display through `showdown_started` terminal rendering. |
| `docs/reports/2026-05-09-sprint3-player-hand-reveal-renderer-slice.md` | Slice 10.2 completion report for routing player hand reveal display through `player_hand_revealed` terminal rendering. |
| `docs/reports/2026-05-09-sprint3-winner-announcement-renderer-slice.md` | Slice 10.3 completion report for routing winner announcement display through `winner_announced` terminal rendering. |
| `docs/reports/2026-05-09-sprint3-pot-distribution-renderer-slice.md` | Slice 11.1 completion report for routing pot distribution display through `pot_distributed` terminal rendering. |
| `docs/reports/2026-05-10-sprint3-decision-feedback-renderer-slice.md` | Slice 12.1 completion report for routing human decision feedback through `decision_feedback_displayed` terminal rendering. |
| `docs/reports/2026-05-09-sprint3-terminal-only-paths-inventory.md` | Sprint 3 inventory of terminal-only diagnostic paths intentionally deferred from renderer-event migration. |
| `docs/reports/2026-05-10-sprint3-terminal-ux-parity-verification.md` | Slice 13.1 report for full terminal UX parity verification after Sprint 3 renderer migrations. |
| `docs/reports/2026-05-10-sprint3-headless-event-coverage-verification.md` | Slice 13.2 report for 100-hand headless collect-events coverage, serialization, and privacy verification. |
| `docs/reports/2026-05-09-sprint3-completion-report.md` | Final Sprint 3 completion report for local terminal/headless event-boundary readiness. |
| `docs/reports/2026-05-11-sprint4-ai-scenario-sanity-harness.md` | Slice 4.1 report for deterministic AI scenario sanity tests and no-bet raise-size legality fix. |
| `docs/reports/2026-05-11-sprint4-3-premium-hand-guards.md` | Slice 4.3 report for premium preflop obvious-bad-play guards. |
| `docs/reports/2026-05-11-sprint4-4-ai-archetype-profiles.md` | Slice 4.4 report for immutable AI archetype profile config. |
| `docs/reports/2026-05-11-sprint4-5-preflop-archetype-behavior.md` | Slice 4.5 report for profile-driven preflop archetype behavior separation. |
| `docs/reports/2026-05-11-sprint4-6-style-separability-metrics.md` | Slice 4.6 report for observed style separability benchmark metrics. |
| `docs/reports/2026-05-11-sprint4-7-postflop-hand-strength-policy.md` | Slice 4.7 report for postflop made-hand, air, and draw strength-aware AI policy. |
| `docs/reports/2026-05-11-sprint4-8-realistic-bet-sizing-buckets.md` | Slice 4.8 report for named realistic postflop bet sizing buckets. |
| `docs/reports/2026-05-11-sprint4-9-cbet-fold-to-cbet.md` | Slice 4.9 report for profile-aware flop c-bet and fold-to-cbet behavior. |
| `docs/reports/2026-05-11-sprint4-10-ai-decision-explanation-payload.md` | Slice 4.10 report for optional JSON-safe AI decision explanation metadata. |
| `docs/reports/2026-05-11-sprint4-11-human-action-trainer-feedback.md` | Slice 4.11 report for cautious human-only trainer hints through the decision feedback event boundary. |
| `docs/reports/2026-05-11-sprint4-12-multi-seed-benchmark-runner.md` | Slice 4.12 report for deterministic seeded AI benchmarks and multi-seed mean/std/min/max summaries. |
| `docs/reports/2026-05-11-sprint4-13-stack-concentration-metrics.md` | Slice 4.13 report for winner-take-all stack concentration metrics in AI benchmark reports. |
| `docs/reports/2026-05-11-sprint4-14-benchmark-transcript-samples.md` | Slice 4.14 report for human-readable benchmark transcript samples with public-card safety. |
| `docs/reports/2026-05-11-phase1-local-ai-trainer-completion.md` | Final Phase 1 completion report for the local AI trainer credibility foundation. |
| `docs/reports/2026-05-12-ai-player-evaluation.md` | Fresh AI player evaluation report covering focused tests, 100-hand smoke benchmark, micro multi-seed diagnostics, transcript safety, and next tuning priorities. |
| `docs/reports/2026-05-12-phase3-primary-benchmark-gate.md` | Phase 3 Stage 3.1 benchmark gate report documenting the full primary protocol timeout, reduced 10×100 diagnostic run, gate checks, profile coverage, and follow-up slices. |
| `docs/reports/2026-05-12-phase3-reduced-benchmark-gate.json` | Machine-readable reduced 10-seed × 100-hand benchmark artifact for Phase 3 Stage 3.1 diagnostics. |
| `docs/reports/2026-05-12-phase3-reduced-benchmark-gate-evaluation.json` | Machine-readable gate evaluation for the reduced Phase 3 Stage 3.1 benchmark artifact. |
| `docs/reports/2026-05-13-phase3-primary-benchmark-gate.md` | Phase 3 follow-up report for making the canonical 10-seed × 500-hand primary benchmark gate runnable with explicit benchmark equity-rollout settings; this pre-calibration full-primary status was WARN. |
| `docs/reports/2026-05-13-phase3-primary-benchmark-gate.json` | Machine-readable pre-calibration full primary 10-seed × 500-hand benchmark artifact using the practical benchmark execution profile. |
| `docs/reports/2026-05-13-phase3-primary-benchmark-gate-evaluation.json` | Machine-readable gate evaluation for the pre-calibration full primary Phase 3 benchmark artifact. |
| `docs/reports/2026-05-13-phase3-primary-benchmark-preflop-fold-calibration.md` | Phase 3 follow-up report documenting the preflop-fold evaluator calibration, validation, and clean full-primary benchmark gate PASS. |
| `docs/reports/2026-05-13-phase3-primary-benchmark-gate-after-preflop-fold-calibration.json` | Machine-readable post-calibration full primary 10-seed × 500-hand benchmark artifact. |
| `docs/reports/2026-05-13-phase3-primary-benchmark-gate-after-preflop-fold-calibration-evaluation.json` | Machine-readable gate evaluation for the post-calibration full primary Phase 3 benchmark artifact. |
| `docs/reports/2026-05-13-phase3-benchmark-progress-artifacts.md` | Phase 3 report for optional per-seed progress artifacts during long multi-seed benchmark runs and the verification method for future evaluator/AI tuning. |
| `docs/reports/2026-05-16-phase3-profile-calibration-target-bands.md` | Phase 3 Stage 3.2 report for explicit AI profile target bands, additive calibration fields, reduced benchmark findings, and next audit priorities. |
| `docs/reports/2026-05-16-phase3-profile-calibration-reduced-benchmark.json` | Machine-readable reduced 10-seed × 100-hand Stage 3.2 calibration benchmark artifact. |
| `docs/reports/2026-05-16-phase3-profile-calibration-reduced-benchmark.progress.json` | Final progress artifact from the reduced Stage 3.2 calibration benchmark run. |
| `docs/reports/2026-05-16-phase3-profile-calibration-reduced-benchmark-evaluation.json` | Machine-readable gate evaluation for the reduced Stage 3.2 calibration benchmark artifact. |
| `docs/reports/2026-05-16-phase3-poor-blunder-audit.md` | Phase 3 Stage 3.3 report for sanitized poor/blunder audit samples, taxonomy counts, and targeted future regression/tuning slices. |
| `docs/reports/2026-05-16-phase3-poor-blunder-audit-benchmark.json` | Machine-readable reduced 10-seed × 100-hand Stage 3.3 poor/blunder audit benchmark artifact with sanitized samples. |
| `docs/reports/2026-05-16-phase3-poor-blunder-audit-benchmark.progress.json` | Final progress artifact from the reduced Stage 3.3 audit benchmark run. |
| `docs/reports/2026-05-16-phase3-poor-blunder-audit-benchmark-evaluation.json` | Machine-readable canonical-gate evaluation for the reduced Stage 3.3 audit artifact; expected `FAIL` because the diagnostic artifact is `10×100`, not primary `10×500`. |
| `docs/reports/2026-05-16-phase3-public-private-safety-gate.md` | Phase 3 Stage 3.4 report for explicit public transcript schema/showdown policy, expanded safety cases, and audit-sample gate integration. |
| `docs/reports/2026-05-16-phase3-evaluation-agent-loop.md` | Phase 3 Stage 3.5 report for evaluation-agent role templates and one complete benchmark-artifact review loop. |
| `docs/reports/2026-05-22-phase3-pot-odds-audit-split.md` | Stage 3.5 follow-up report for public-context pot-odds call audit splits before any AI tuning. |
| `docs/reports/2026-05-22-phase3-pot-odds-audit-split-benchmark.json` | Machine-readable reduced 10-seed × 100-hand benchmark artifact with pot-odds audit split fields. |
| `docs/reports/2026-05-22-phase3-pot-odds-audit-split-benchmark.progress.json` | Final progress artifact from the reduced pot-odds audit split benchmark run. |
| `docs/reports/2026-05-22-phase3-pot-odds-audit-split-benchmark-evaluation.json` | Machine-readable gate evaluation for the reduced pot-odds audit split benchmark artifact. |
| `docs/reports/2026-05-22-phase3-calling-station-negative-equity-call-tuning.md` | Phase 3 follow-up report for the goal-driven Builder/Hacker negative-equity call loop, final reduced benchmark target, and evaluator/policy calibration evidence. |
| `docs/reports/2026-05-22-phase3-calling-station-negative-equity-call-tuning-benchmark.json` | Machine-readable reduced 10-seed × 100-hand post-tuning benchmark artifact. |
| `docs/reports/2026-05-22-phase3-calling-station-negative-equity-call-tuning-benchmark.progress.json` | Final progress artifact from the reduced calling-station negative-equity call tuning benchmark run. |
| `docs/reports/2026-05-22-phase3-calling-station-negative-equity-call-tuning-benchmark-evaluation.json` | Machine-readable gate evaluation for the reduced post-tuning benchmark artifact. |
| `docs/reports/2026-05-25-post-phase3-evidence-baseline-inventory.md` | Post-Phase-3 evidence baseline inventory separating primary evidence, reduced diagnostics, post-tuning evidence, and claim boundaries before further tuning or platform work. |
| `docs/reports/2026-05-25-post-phase3-remaining-poor-blunder-triage.md` | Public-context triage of remaining post-tuning poor/blunder samples, classifying candidates before any policy or evaluator tuning. |
| `docs/reports/2026-05-25-post-phase3-builder-hacker-loop-dry-run.md` | Dry-run of the refreshed Builder/Hacker evaluation loop against remaining poor/blunder findings, deferring implementation until fixture-backed public targets exist. |
| `docs/reports/2026-05-25-profile-calibration-warn-prioritization.md` | Prioritization of Stage 3.2 profile calibration WARNs into style fidelity, quality, metric-definition, and sample-size categories without changing bands or policy. |
| `docs/reports/2026-05-25-headless-action-api-readiness-inventory.md` | Read-only inventory of existing headless/action contracts, gaps, forbidden platform boundaries, and smallest safe local implementation slices. |
| `docs/reports/2026-05-25-action-sequence-headless-fixture-harness.md` | Completion report for the local-only deterministic action-sequence headless fixture harness. |
| `docs/reports/2026-10-15-computer-opponents-and-reliability.md` | Current local computer-opponent behavior, history safety, event/history parity, tests, and benchmark claim limits. |
| `docs/reports/2026-10-15-companion-position-primary-benchmark.json` | Final primary-protocol artifact after AI seat-position correction; all gate checks passed. |
| `docs/reports/2026-10-15-companion-position-primary-benchmark-evaluation.json` | Gate evaluation for the final position-only primary artifact. |
| `docs/reports/2026-10-15-companion-position-reduced-benchmark.json` | Reduced diagnostic artifact after AI seat-position correction. |
| `docs/reports/2026-10-15-companion-position-reduced-benchmark-evaluation.json` | Reduced-protocol gate evaluation for the position-only diagnostic artifact. |
| `docs/reports/2026-10-15-companion-late-open-reduced-benchmark.json` | Rejected CO/BTN open-raise candidate's reduced diagnostic artifact. |
| `docs/reports/2026-10-15-companion-late-open-reduced-benchmark-evaluation.json` | Reduced-protocol gate evaluation for the rejected candidate. |
| `docs/reports/2026-10-15-companion-late-open-primary-benchmark.json` | Rejected CO/BTN open-raise candidate's primary artifact; seed 9 ended at hand 237. |
| `docs/reports/2026-10-15-companion-late-open-primary-benchmark-evaluation.json` | Failed primary gate evaluation for the rejected candidate. |
| `docs/archive/README.md` | Archive and directory organization policy. |

## Runtime data artifacts

These files are currently in the project root for compatibility with existing code paths.

| Path | Purpose |
| --- | --- |
| `game_history.json` | JSON hand history data. |
| `player_stats.json` | Player style/statistics data. |
| `poker_game.db` | SQLite database. |
| `poker_game.log` | Runtime log file. |
| `game_config.json` | Game config. |
| `enhanced_game_config.json` | Enhanced game config. |
| `data/` | Additional indexed/runtime data directory. |

Future migration target:

```text
data/runtime/game_history.json
data/runtime/player_stats.json
data/runtime/poker_game.db
data/logs/poker_game.log
```

Do not move these runtime files until code references and docs are updated and tested.

## Recommended next development order

1. Choose the next smallest local fixture/evidence slice from the completed post-Phase-3 reports, such as nit preflop overfold evaluator fixtures, TAG/LAG preflop participation fixtures, calling-station sticky-but-not-negative-EV fixtures, or an action-sequence headless fixture harness.
2. Require fixture-backed public-information targets, safety verdicts, commands run, non-goals preserved, and pre/post benchmark comparison before accepting policy or evaluator changes.
3. Keep profile target-band calibration WARNs as evidence for named tuning slices, not as benchmark gate failures.
4. Keep online/API/WebSocket/auth/platform and external-agent runtime implementation deferred until the roadmap gates are met.
