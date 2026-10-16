# Sprint 2.6 Spike: Headless Engine Boundary Design

Date: 2026-05-08
Project: Texas Hold'em local trainer -> AI Poker Arena / Agent Poker Platform

## Spike Goal

Define the smallest safe boundary for evolving the current terminal-first `game.py` into a true headless engine without breaking the terminal UX or existing benchmark flow.

This is a design spike, not a large refactor. The goal is to identify seams, contracts, and migration order for Sprint 3.

## Current State

`game.py` still combines several responsibilities:

- game state mutation
- betting order and action application
- CLI printing and sleeps
- decision provider orchestration
- action validation
- history recording
- decision evaluation feedback
- side-pot handling
- replay-facing hand result formatting

Sprint 2 already created important seams:

- `DecisionProvider` receives a serializable `GameStateSnapshot`.
- `ActionValidator` normalizes and rejects invalid raw actions.
- `GameHistoryManager` persists action metadata and hand outcome metadata.
- `headless_simulation.py` can run AI-only hands without terminal input.
- `ai_system_evaluator.py` can produce machine-readable benchmark artifacts.

## Proposed Sprint 3 Boundary

Introduce a small event-oriented engine layer before any online-room work.

### Engine Input Command

A future command should be serializable and independent from terminal UI:

```python
{
  "type": "player_action",
  "hand_id": "...",
  "player_name": "AI-1",
  "action": "fold|check|call|raise|all-in",
  "amount": 0,
  "source": "human-cli|built-in-ai|external-agent",
  "metadata": {},
}
```

### Engine Output Event

The engine should emit structured events instead of printing directly:

```python
{
  "type": "action_applied|phase_started|cards_dealt|hand_completed|validation_failed",
  "hand_id": "...",
  "phase": "preflop|flop|turn|river|showdown",
  "public_payload": {},
  "private_payload_by_player": {},
  "metadata": {},
}
```

### Adapter Responsibilities

Terminal adapter:

- renders events as text
- prompts human players
- keeps current terminal UX unchanged

Headless/benchmark adapter:

- consumes events silently
- supplies built-in AI actions through `DecisionProvider`
- collects benchmark summaries

Future online adapter:

- broadcasts public events over WebSocket
- sends private payload only to the owning player/agent
- submits actions back as engine commands

## Migration Seams

1. Keep `DecisionProvider` and `ActionValidator` as the action boundary.
2. Extract pure action-application helpers from `_betting_round`.
3. Replace direct prints with event emission behind an adapter interface.
4. Move sleeps to terminal adapter only.
5. Keep `GameHistoryManager` as an event/history subscriber.
6. Preserve current JSON history schema during migration.

## Non-goals

- Do not rewrite `game.py` in one step.
- Do not start WebSocket rooms before engine events exist.
- Do not change public/private state schema casually.
- Do not move runtime data paths in the same sprint.

## Verification Strategy

Sprint 3 should retain these checks:

- full pytest suite passes
- AI-only 1,000-hand benchmark completes
- `illegal_action_rate == 0.0`
- terminal `python3 main.py` remains playable
- no deck/opponent hole-card leakage in public snapshots

## Recommended Sprint 3 First Task

Create an `EngineEvent` dataclass/module and make one narrow path emit events while preserving existing prints. Start with non-invasive event mirroring before replacing terminal rendering.
