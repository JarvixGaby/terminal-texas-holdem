# Agent Poker Platform Roadmap

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Evolve the current local terminal Texas Hold'em project into a continuously evaluated AI poker training system, and eventually into an online poker chatroom where users' agents can join tables and play poker.

**Architecture:** Build in stages. First stabilize the local poker engine and add AI feedback/evaluation loops. Then separate the game engine from CLI UI. Then introduce an agent-facing protocol and online multiplayer room architecture. The final product should support humans, built-in AI, and external user agents at the same poker table.

**Tech Stack:** Python 3, pytest, sqlite3, terminal UI initially, future WebSocket/FastAPI or similar online service, structured event logs, agent protocol contracts.

---

## 0. Updated Product Vision

The product should not only be a terminal poker game.

The final vision is:

**An online poker chatroom / poker arena where users can bring their own AI agents to play Texas Hold'em against humans and other agents.**

The local terminal game becomes the first prototype and evaluation sandbox.

Long-term differentiated value:

1. Humans can play poker against AI agents.
2. Users can connect their own poker agents.
3. Agents can be evaluated, ranked, and improved.
4. The system can explain and review decisions.
5. The platform can host agent-vs-agent poker rooms.
6. Historical hands become training/evaluation data.

---

## 1. Key Strategic Shift

Previous plan focused on:

- technical cleanup
- training mode
- replay
- AI profiles
- analytics

New plan adds three higher-priority layers:

1. **AI feedback loop**
   - The system should evaluate every AI/human decision.
   - The project should continuously measure whether AI behavior is improving.

2. **System design evaluation loop**
   - The codebase architecture itself should be periodically reviewed.
   - We need objective criteria for whether the design is good enough.

3. **Agent platform foundation**
   - The game engine should eventually expose a table protocol that external agents can use.
   - CLI UI should become just one client, not the center of the architecture.

---

## 2. Product Architecture Target

### Current Architecture

```text
main.py CLI
  -> TexasHoldemGame
    -> Player / AIPlayer
    -> HandEvaluator
    -> SidePotManager
    -> GameHistoryManager JSON
    -> AI engines
```

### Target Architecture

```text
Clients
  - Terminal CLI
  - Future web chatroom
  - External user agents

Application Layer
  - Table manager
  - Room/session manager
  - Matchmaking
  - Replay viewer
  - Training/evaluation UI

Game Engine Layer
  - Poker rules engine
  - Betting state machine
  - Hand evaluator
  - Pot/side-pot manager
  - Event emitter

Agent Layer
  - Built-in AI agents
  - External agent protocol adapter
  - Agent sandbox/timeouts
  - Agent decision validation

Evaluation Layer
  - Decision evaluator
  - AI behavior metrics
  - System design review checklist
  - Regression benchmark suite
  - Agent leaderboard

Persistence Layer
  - SQLite initially
  - Future server DB
  - Hand histories
  - Agent decisions
  - Evaluation results
```

Core architectural principle:

**The poker engine should not know whether a decision came from a terminal user, built-in AI, web user, or external agent. It should only receive validated actions.**

---

## 3. New Required Subsystems

## 3.1 AI Feedback and Decision Evaluation System

### Purpose

Evaluate whether a poker decision is good, questionable, or bad.

This should apply to:

- human decisions
- built-in AI decisions
- external agent decisions in the future

### New module

Create:

```text
decision_evaluator.py
```

### Inputs

A decision evaluator should receive a structured snapshot:

```python
@dataclass
class DecisionContext:
    game_id: str
    hand_id: str
    player_name: str
    phase: str
    position: str
    hole_cards: list[str]
    community_cards: list[str]
    pot_size: int
    current_bet: int
    amount_to_call: int
    player_chips: int
    legal_actions: list[str]
    action_taken: str
    amount: int
    estimated_equity: float | None
    pot_odds: float | None
    opponent_count: int
```

### Outputs

```python
@dataclass
class DecisionEvaluation:
    grade: str  # excellent/good/questionable/poor/blunder
    score: float  # 0-100
    recommended_action: str
    reasoning: str
    risk_tags: list[str]
    metrics: dict
```

### Initial evaluation logic

MVP rule-based evaluator:

1. If facing a bet and estimated equity < pot odds by large margin, calling is poor.
2. If equity is very high and player checks/calls passively, mark missed value.
3. If fold with equity much higher than pot odds, mark over-fold.
4. If raise size is below min raise or illegal, mark invalid.
5. If all-in with low equity and no fold equity approximation, mark high-risk.

Later evaluator can become model-based or GTO-solver-assisted.

---

## 3.2 AI System Quality Evaluator

### Purpose

Evaluate whether the current AI system design is good enough.

This is different from evaluating one hand. It evaluates AI behavior across many simulated hands.

### New module

Create:

```text
ai_system_evaluator.py
```

### Metrics

For each AI profile, measure:

- VPIP
- PFR
- 3bet frequency
- aggression factor
- fold-to-bet rate
- showdown frequency
- win rate
- average pot size
- bluff frequency estimate
- illegal action rate
- timeout/error rate

### Target ranges

Example:

```python
TARGET_PROFILE_STATS = {
    "calling_station": {
        "vpip": (35, 60),
        "pfr": (2, 12),
        "aggression_factor": (0.2, 1.0),
        "fold_to_bet": (10, 35),
    },
    "tag": {
        "vpip": (16, 26),
        "pfr": (12, 22),
        "aggression_factor": (1.5, 3.5),
        "fold_to_bet": (40, 65),
    },
    "lag": {
        "vpip": (25, 40),
        "pfr": (20, 34),
        "aggression_factor": (2.0, 5.0),
        "fold_to_bet": (35, 60),
    },
}
```

### Acceptance criteria

The AI system is not considered good enough until:

1. Each profile has target statistical ranges.
2. Simulated hands produce metrics inside or near target ranges.
3. Illegal action rate is 0.
4. AI does not crash during long simulations.
5. AI decisions can be explained after the hand.

---

## 3.3 System Design Review Loop

### Purpose

Periodically evaluate whether the project architecture still supports the final vision.

### New document

Create:

```text
docs/architecture/system-design-scorecard.md
```

### Score dimensions

Score 1-5:

1. Poker rule correctness.
2. Test coverage quality.
3. Engine/UI separation.
4. Persistence consistency.
5. AI decision transparency.
6. Agent protocol readiness.
7. Online multiplayer readiness.
8. Observability/logging.
9. Replay/evaluation quality.
10. Extensibility.

### Review cadence

Run design review after every major phase.

Each review should answer:

- What is currently good?
- What will block online agent poker rooms?
- What technical debt is increasing fastest?
- What should be refactored before adding more features?

---

## 4. Final Platform Requirements

## 4.1 Online Poker Chatroom

Future users should be able to enter a poker room like a chatroom.

Room features:

- Create room.
- Join room.
- Watch room.
- Sit at table.
- Stand up.
- Chat.
- Start hand.
- Show public table state.
- Private hole cards only visible to owning player/agent.
- Hand history and replay.

## 4.2 Agent Participation

Users should be able to register an agent.

Agent types:

1. Built-in local AI.
2. User-submitted local strategy module.
3. Remote HTTP/WebSocket agent.
4. LLM-powered conversational agent.

Initial agent protocol should be simple:

```json
{
  "type": "decision_request",
  "table_id": "table_123",
  "hand_id": "hand_456",
  "player_id": "agent_alice",
  "private_state": {
    "hole_cards": ["A♠", "K♥"],
    "chips": 980
  },
  "public_state": {
    "phase": "preflop",
    "community_cards": [],
    "pot": 15,
    "current_bet": 10,
    "amount_to_call": 10,
    "legal_actions": ["call", "raise", "fold"]
  }
}
```

Agent response:

```json
{
  "action": "raise",
  "amount": 30,
  "reasoning": "Strong broadway hand preflop in position."
}
```

The server must validate every action. Agents are never trusted.

## 4.3 Agent Safety and Fairness

Required before public online version:

- Private state isolation.
- Agents only see their own hole cards.
- Time limit per decision.
- Illegal action rejection.
- Disconnect fallback.
- Collusion detection later.
- Full audit logs.

---

## 5. Revised Implementation Phases

## Phase 0: Baseline Cleanup and Safety

### Goal

Remove known breakage and make the current local game reliable.

### Tasks

1. Fix docs referencing obsolete launch/backup file names. ✅ Done in baseline cleanup.
2. Fix pytest warnings caused by tests returning bool. ✅ Done in baseline cleanup.
3. Fix `quick_replay_system.py` missing `odds_calculator` import. ✅ Done in baseline cleanup by switching to `optimized_odds_calculator`.
4. Add module import smoke tests. ✅ Done in baseline cleanup.
5. Add No-Limit Hold'em rule compliance checklist. ✅ Done in baseline cleanup.

### Acceptance

- `python3 -m pytest -q` passes with zero warnings.
- No import errors for intended modules.
- Docs match actual launch command.

---

## Phase 1: Add AI Feedback MVP

### Goal

Every completed hand should have machine-readable decision evaluations.

### Tasks

1. Create `decision_evaluator.py` data structures.
2. Implement pot odds calculation helper.
3. Implement rule-based evaluation for call/fold/check/raise.
4. Add evaluation records to hand history.
5. Show compact feedback after each hand.
6. Add tests for obvious decision cases.

### Example CLI output

```text
本手关键决策反馈：
- Preflop: 你用 A♠ K♥ 加注到 30。评分: Good 82/100
  理由: 强起手牌，主动加注合理。
- Turn: 面对 200 底池中的 150 下注选择跟注。评分: Questionable 48/100
  理由: 估算胜率低于所需底池赔率，除非认为对手诈唬频率很高。
```

### Acceptance

- Each human decision can be evaluated.
- Evaluation is stored.
- At least 10 tests cover evaluator behavior.

---

## Phase 2: Add AI System Evaluation Harness

### Goal

Evaluate whether the built-in AI is actually good and profile-consistent.

### Tasks

1. Create `ai_system_evaluator.py`.
2. Add headless simulation mode.
3. Simulate 1,000+ hands with AI-only tables.
4. Collect AI profile stats.
5. Compare stats against target ranges.
6. Generate `reports/ai_evaluation_report.md`.

### Acceptance

- Can run: `python3 ai_system_evaluator.py --hands 1000`.
- Produces profile metrics.
- Flags profiles outside target ranges.
- Illegal action rate must be 0.

---

## Phase 3: Refactor Toward Agent-Ready Engine

### Goal

Separate poker engine from CLI so future online rooms and agents can use the same engine.

### Tasks

1. Split `main.py` into UI/bootstrap modules.
2. Introduce `GameStateSnapshot` object.
3. Introduce `ActionRequest` and `ActionResponse` objects.
4. Make AI and human input both implement the same decision-provider interface.
5. Ensure game engine accepts validated action objects.

### Proposed interface

```python
class DecisionProvider:
    def decide(self, state: GameStateSnapshot) -> ActionResponse:
        raise NotImplementedError
```

Implementations:

- `HumanCliDecisionProvider`
- `BuiltInAIDecisionProvider`
- future `RemoteAgentDecisionProvider`

### Acceptance

- CLI game still works.
- Built-in AI uses same action interface as future agents.
- Tests can run headless games without terminal input.

---

## Phase 4: Persistence and Replay Upgrade

### Goal

Make hand histories useful for training, evaluation, and future online audits.

### Tasks

1. Consolidate persistence around SQLite.
2. Store every decision context.
3. Store every decision evaluation.
4. Store agent reasoning if available.
5. Upgrade replay to show decision quality.
6. Add exportable hand history JSON.

### Acceptance

- Can query all decisions by player/agent.
- Can replay a hand with evaluations.
- Can export hand history for external analysis.

---

## Phase 5: Agent Protocol Local Prototype

### Goal

Support agents as pluggable local decision providers before building online rooms.

### Tasks

1. Define `agent_protocol.py`.
2. Define JSON schema for decision request/response.
3. Add local agent adapter that calls a Python strategy class.
4. Add validation for illegal responses.
5. Add timeout wrapper.
6. Add sample dumb agent and sample tight agent.

### Acceptance

- A local custom agent can join a CLI table.
- Illegal agent actions are rejected safely.
- Agent timeouts do not crash the game.

---

## Phase 6: Online Poker Chatroom Prototype

### Goal

Create minimal online table service.

### Suggested stack

- FastAPI or similar HTTP framework.
- WebSocket for table updates.
- SQLite/Postgres depending deployment needs.
- Existing engine reused as backend.

### MVP features

1. Create table.
2. Join table.
3. Sit as human or agent.
4. Receive public table events.
5. Receive private hole cards securely.
6. Submit action.
7. Validate action.
8. Broadcast table updates.
9. Store hand history.

### Acceptance

- Two browser/CLI clients can join one table.
- At least one built-in agent can sit at table.
- Game completes one full hand online.

---

## Phase 7: Public Agent Arena

### Goal

Allow many users' agents to compete and be ranked.

### Features

1. Agent registration.
2. Agent identity and versioning.
3. Leaderboard.
4. Match history.
5. Agent evaluation reports.
6. Anti-cheating and collusion monitoring.
7. Tournament mode.

---

## 6. Immediate Next Sprint

## Sprint Goal

Add the first AI feedback/evaluation loop while keeping the existing local game stable.

## Sprint Tasks

### Task A: Baseline quality issues ✅ Done

- Fixed docs with obsolete/missing file references.
- Fixed pytest warnings.
- Fixed replay import issue by using `optimized_odds_calculator`.
- Added import smoke tests.

### Task B: Add decision evaluation models

Create `decision_evaluator.py` with:

- `DecisionContext`
- `DecisionEvaluation`
- `evaluate_decision(context)`
- pot odds helper

### Task C: Add evaluator tests

Create `tests/test_decision_evaluator.py` with cases:

1. Good call when equity > pot odds.
2. Bad call when equity far below pot odds.
3. Bad fold when equity far above pot odds.
4. Missed value when strong equity checks behind.
5. Illegal raise amount is blunder.

### Task D: Integrate evaluator into local game history

After each human decision:

1. Build `DecisionContext`.
2. Estimate equity if available.
3. Run evaluator.
4. Store result in memory/history.
5. Show compact feedback after the hand, not during normal mode.

### Task E: Add first AI system review report

Create:

```text
docs/architecture/ai-system-review-001.md
```

Include:

- Current AI architecture summary.
- Strengths.
- Weaknesses.
- What blocks agent-platform vision.
- Next improvements.

---

## 7. System Design Evaluation Criteria

The system is “good enough for current phase” only if:

### Local training phase

- Poker rules are correct and tested.
- Human and AI decisions are recorded.
- Decisions can be evaluated.
- Replays can explain key decisions.
- AI profiles can be measured.

### Agent protocol phase

- Game engine is UI-independent.
- All decision sources use same interface.
- Private/public state separation exists.
- Illegal agent actions are safely rejected.
- Agent decision timeout exists.

### Online room phase

- Table state is event-driven.
- Private cards are never broadcast publicly.
- Multiple clients can observe consistent state.
- Hand history is auditable.
- Agent identity/version is tracked.

---

## 8. Risks and Mitigations

### Risk 1: Building online too early

Mitigation:
First create headless engine and local agent protocol. Do not build WebSocket room until the engine no longer depends on CLI input/output.

### Risk 2: AI looks smart but is statistically bad

Mitigation:
Add AI system evaluator and profile target ranges.

### Risk 3: Agent cheating / hidden card leakage

Mitigation:
Design public/private state snapshots now. Never expose full game state to agents.

### Risk 4: Replay data too weak for evaluation

Mitigation:
Store full decision context, not just final action.

### Risk 5: Too many features before correctness

Mitigation:
No online platform work until betting, side pot, and showdown tests are stronger.

---

## 9. Recommended Priority Order

1. Baseline cleanup.
2. Decision evaluator MVP.
3. AI/system review scorecard.
4. Headless simulation mode.
5. AI profile evaluation harness.
6. Engine/UI separation.
7. Unified action interface.
8. Local external-agent adapter.
9. SQLite decision/evaluation persistence.
10. Online poker room MVP.

---

## 10. Success Metrics

### AI feedback metrics

- 100% of human decisions have evaluation records.
- 100% of built-in AI decisions can be evaluated in simulation mode.
- Evaluation output includes grade, score, recommendation, and reasoning.

### AI system metrics

- AI-only simulation can run 1,000 hands without crashing.
- Illegal action rate is 0.
- Each AI profile has target stat ranges.
- Reports identify profiles needing calibration.

### Agent platform readiness metrics

- CLI human and built-in AI both use the same action interface.
- External local agent can play one full hand.
- Agent sees only public state plus its own private state.
- Invalid/timeout agent responses are handled safely.

### Online room metrics

- Two clients can join one table.
- One built-in or external agent can join table.
- One full hand can complete online.
- Hand history can be replayed with decisions and evaluations.

---

## 11. Concrete Next Action

Start with Sprint Tasks A-E.

The most important new first feature is not the online room yet. It is:

**Decision evaluation records for every action.**

That creates the data foundation for:

- training feedback
- replay quality
- AI evaluation
- agent leaderboard
- future online audits
