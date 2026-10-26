# Sprint 3 Engine Event Boundary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Introduce a small structured engine event boundary so terminal rendering can be separated from game state mutation without changing the current CLI experience.

**Architecture:** Add non-invasive event mirroring first: `TexasHoldemGame` keeps printing exactly as it does today, while also emitting serializable `EngineEvent` objects to optional subscribers. After that is stable, move terminal output into a renderer and keep history/headless/benchmark flows consuming the same event stream.

**Tech Stack:** Python 3.12-compatible code, dataclasses, pytest via `python3 -m pytest -q`, existing `DecisionProvider`, `ActionValidator`, `GameHistoryManager`, and `HeadlessSimulation` boundaries.

---

## Scan Summary

- `texas_holdem/engine/game.py` is the main Sprint 3 target: about 1388 lines and still mixes state mutation, CLI `print/input`, sleeps, history, decision evaluation, and side-pot payout.
- Sprint 2 boundaries are already in place: `texas_holdem/ai/decision_provider.py`, `texas_holdem/ai/action_validator.py`, `texas_holdem/analytics/headless_simulation.py`, `texas_holdem/analytics/ai_system_evaluator.py`, and action/outcome metadata in `texas_holdem/history/game_history.py`.
- The strongest next move is not a web/API prototype. It is a narrow event boundary that can later support terminal, headless benchmark, and online adapters.
- Current test command could not run in this environment because `pytest` is not installed: `/Library/Developer/CommandLineTools/usr/bin/python3: No module named pytest`.
- No dependency manifest was found (`requirements.txt`, `pyproject.toml`, `setup.py`, lockfiles absent), so reproducible test setup should be fixed before larger refactors.
- The current directory is not a git repository, so execution checkpoints should rely on tests and docs rather than commits.

## File Structure

- Create `texas_holdem/engine/engine_events.py`: immutable event dataclasses and payload serialization helpers.
- Modify `texas_holdem/engine/game.py`: add event subscriber support and mirror narrow existing paths into events while preserving current prints.
- Create `tests/test_engine_events.py`: event serialization and privacy tests.
- Create `tests/test_game_engine_events.py`: game-level event emission tests.
- Later modify `texas_holdem/analytics/headless_simulation.py`: collect events without terminal rendering after event mirroring is stable.
- Later create `texas_holdem/ui/terminal_renderer.py`: terminal event renderer after enough events exist to replace selected print paths.

## Task 0: Restore Reproducible Test Baseline

**Files:**
- Create: `requirements.txt`
- Test: existing test suite

- [ ] **Step 1: Add minimal test dependency manifest**

Create `requirements.txt`:

```text
pytest
```

- [ ] **Step 2: Install test dependency in the local environment**

Run:

```bash
python3 -m pip install -r requirements.txt
```

Expected: `pytest` is installed for `python3`.

- [ ] **Step 3: Run full test suite**

Run:

```bash
python3 -m pytest -q
```

Expected: suite runs. Historical project baseline is `92 passed`; if the count differs, record the actual result before code changes.

## Task 1: Add Engine Event Data Contract

**Files:**
- Create: `texas_holdem/engine/engine_events.py`
- Test: `tests/test_engine_events.py`

- [ ] **Step 1: Write event contract tests**

Add `tests/test_engine_events.py`:

```python
from texas_holdem.engine.engine_events import EngineEvent


def test_engine_event_serializes_public_and_private_payloads():
    event = EngineEvent(
        type="cards_dealt",
        hand_id="hand-1",
        phase="flop",
        public_payload={"community_cards": ["A♠", "K♠", "Q♠"]},
        private_payload_by_player={"Hero": {"hole_cards": ["J♠", "T♠"]}},
        metadata={"source": "test"},
    )

    data = event.to_dict()

    assert data["type"] == "cards_dealt"
    assert data["hand_id"] == "hand-1"
    assert data["phase"] == "flop"
    assert data["public_payload"]["community_cards"] == ["A♠", "K♠", "Q♠"]
    assert data["private_payload_by_player"]["Hero"]["hole_cards"] == ["J♠", "T♠"]
    assert data["metadata"]["source"] == "test"


def test_engine_event_defaults_do_not_share_mutable_payloads():
    first = EngineEvent(type="phase_started", hand_id="h1", phase="preflop")
    second = EngineEvent(type="phase_started", hand_id="h2", phase="flop")

    first.public_payload["changed"] = True

    assert "changed" not in second.public_payload
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest -q tests/test_engine_events.py
```

Expected: FAIL because `engine_events` does not exist yet.

- [ ] **Step 3: Implement minimal event module**

Create `texas_holdem/engine/engine_events.py`:

```python
# -*- coding: utf-8 -*-
"""Structured engine events emitted by the poker engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict


@dataclass(frozen=True)
class EngineEvent:
    type: str
    hand_id: str
    phase: str
    public_payload: Dict[str, Any] = field(default_factory=dict)
    private_payload_by_player: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
```

- [ ] **Step 4: Run event tests**

Run:

```bash
python3 -m pytest -q tests/test_engine_events.py
```

Expected: PASS.

## Task 2: Mirror Phase/Card Events Without Replacing Prints

**Files:**
- Modify: `texas_holdem/engine/game.py`
- Test: `tests/test_game_engine_events.py`

- [ ] **Step 1: Write game event emission tests**

Add `tests/test_game_engine_events.py`:

```python
from texas_holdem.engine.engine_events import EngineEvent
from texas_holdem.engine.game import TexasHoldemGame
from texas_holdem.engine.player import AIPlayer


def make_game():
    players = [AIPlayer("AI-1", 100), AIPlayer("AI-2", 100)]
    game = TexasHoldemGame(players, small_blind=5, big_blind=10)
    game.current_game_id = "test-hand"
    game.active_players = players
    return game


def test_game_can_subscribe_to_engine_events():
    game = make_game()
    events = []

    game.subscribe_to_events(events.append)
    game._emit_event("phase_started", public_payload={"phase": "preflop"})

    assert len(events) == 1
    assert isinstance(events[0], EngineEvent)
    assert events[0].type == "phase_started"
    assert events[0].hand_id == "test-hand"
    assert events[0].phase == "preflop"
    assert events[0].public_payload == {"phase": "preflop"}


def test_deal_flop_emits_cards_dealt_event_without_private_cards():
    game = make_game()
    game.deck.reset()
    events = []
    game.subscribe_to_events(events.append)

    game._deal_flop()

    event = events[-1]
    serialized = repr(event.to_dict())
    assert event.type == "cards_dealt"
    assert event.phase == "flop"
    assert event.public_payload["community_cards"] == [str(card) for card in game.community_cards]
    assert event.private_payload_by_player == {}
    assert "AI-1" not in serialized
    assert "AI-2" not in serialized
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest -q tests/test_game_engine_events.py
```

Expected: FAIL because `subscribe_to_events` and `_emit_event` do not exist yet.

- [ ] **Step 3: Add event subscriber support to `texas_holdem/engine/game.py`**

Update imports:

```python
from typing import Callable, List, Optional, Dict, Tuple, Any
from texas_holdem.engine.engine_events import EngineEvent
```

Add in `TexasHoldemGame.__init__`:

```python
self.event_subscribers: List[Callable[[EngineEvent], None]] = []
```

Add methods near `set_decision_provider`:

```python
def subscribe_to_events(self, subscriber: Callable[[EngineEvent], None]) -> None:
    self.event_subscribers.append(subscriber)

def _emit_event(
    self,
    event_type: str,
    public_payload: Optional[Dict[str, Any]] = None,
    private_payload_by_player: Optional[Dict[str, Dict[str, Any]]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> EngineEvent:
    event = EngineEvent(
        type=event_type,
        hand_id=self.current_game_id or "",
        phase=self.game_phase,
        public_payload=public_payload or {},
        private_payload_by_player=private_payload_by_player or {},
        metadata=metadata or {},
    )
    for subscriber in list(self.event_subscribers):
        subscriber(event)
    return event
```

- [ ] **Step 4: Emit card events from street-deal methods**

In `_deal_flop`, after `history_manager.start_new_phase(...)`, add:

```python
self._emit_event(
    "cards_dealt",
    public_payload={"community_cards": [str(card) for card in self.community_cards]},
    metadata={"street": "flop"},
)
```

In `_deal_turn`, after `history_manager.start_new_phase(...)`, add:

```python
self._emit_event(
    "cards_dealt",
    public_payload={"community_cards": [str(card) for card in self.community_cards]},
    metadata={"street": "turn"},
)
```

In `_deal_river`, after `history_manager.start_new_phase(...)`, add:

```python
self._emit_event(
    "cards_dealt",
    public_payload={"community_cards": [str(card) for card in self.community_cards]},
    metadata={"street": "river"},
)
```

- [ ] **Step 5: Run focused tests**

Run:

```bash
python3 -m pytest -q tests/test_engine_events.py tests/test_game_engine_events.py
```

Expected: PASS.

## Task 3: Mirror Action-Applied and Validation-Failed Events

**Files:**
- Modify: `texas_holdem/engine/game.py`
- Test: `tests/test_game_engine_events.py`

- [ ] **Step 1: Add tests around validated action events**

Append to `tests/test_game_engine_events.py`:

```python
from texas_holdem.ai.action_validator import ValidatedAction
from texas_holdem.ai.decision_provider import ActionResponse


def test_record_processed_action_emits_action_applied_event():
    game = make_game()
    events = []
    game.subscribe_to_events(events.append)
    game.history_manager.start_new_game_record(["AI-1", "AI-2"], 5, 10, 0)
    game.history_manager.start_new_phase("preflop", [], 15, 10)
    game.last_action_response = ActionResponse("call", 10)
    game.last_validated_action = ValidatedAction("call", 10, True, "ok", "call", 10)

    game._record_processed_action(
        game.active_players[0],
        "call",
        10,
        chips_before=100,
        amount_to_call=10,
        legal_actions=["call", "raise", "fold"],
        min_raise=20,
        decision_pot_size=15,
        decision_player_chips=100,
        decision_current_bet=10,
    )

    action_events = [event for event in events if event.type == "action_applied"]
    assert action_events[-1].public_payload["player_name"] == "AI-1"
    assert action_events[-1].public_payload["action"] == "call"
    assert action_events[-1].public_payload["amount"] == 10


def test_invalid_provider_action_emits_validation_failed_event():
    game = make_game()
    events = []
    game.subscribe_to_events(events.append)
    game.history_manager.start_new_game_record(["AI-1", "AI-2"], 5, 10, 0)
    game.history_manager.start_new_phase("preflop", [], 15, 10)
    game.last_action_response = ActionResponse("check", 0)
    game.last_validated_action = ValidatedAction("fold", 0, False, "check illegal when facing a bet", "check", 0)

    game._record_processed_action(
        game.active_players[0],
        "fold",
        0,
        chips_before=100,
        amount_to_call=10,
        legal_actions=["call", "raise", "fold"],
        min_raise=20,
        decision_pot_size=15,
        decision_player_chips=100,
        decision_current_bet=10,
    )

    failed_events = [event for event in events if event.type == "validation_failed"]
    assert failed_events[-1].public_payload["player_name"] == "AI-1"
    assert failed_events[-1].public_payload["fallback_action"] == "fold"
    assert "check illegal" in failed_events[-1].public_payload["reason"]
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest -q tests/test_game_engine_events.py
```

Expected: FAIL because action events are not emitted yet.

- [ ] **Step 3: Emit action events from `_record_processed_action`**

At the end of `_record_processed_action`, after history/evaluation feedback has been recorded, add:

```python
action_payload = {
    "player_name": player.name,
    "action": action,
    "amount": amount,
    "chips_before": chips_before,
    "chips_after": player.chips,
    "pot_size": self.pot,
    "current_bet": self.current_bet,
}
self._emit_event("action_applied", public_payload=action_payload)
if self.last_validated_action is not None and not self.last_validated_action.is_valid:
    self._emit_event(
        "validation_failed",
        public_payload={
            "player_name": player.name,
            "original_action": self.last_validated_action.original_action,
            "original_amount": self.last_validated_action.original_amount,
            "fallback_action": self.last_validated_action.action,
            "reason": self.last_validated_action.reason,
        },
    )
```

- [ ] **Step 4: Run focused tests**

Run:

```bash
python3 -m pytest -q tests/test_game_engine_events.py tests/test_provider_driven_game_flow.py
```

Expected: PASS.

## Task 4: Mirror Hand Completion Events

**Files:**
- Modify: `texas_holdem/engine/game.py`
- Test: `tests/test_game_engine_events.py`

- [ ] **Step 1: Add tests for hand-completed event privacy**

Append to `tests/test_game_engine_events.py`:

```python
def test_early_winner_emits_hand_completed_without_private_payload():
    game = make_game()
    game.pot = 15
    game.active_players[1].fold()
    events = []
    game.subscribe_to_events(events.append)
    game.history_manager.start_new_game_record(["AI-1", "AI-2"], 5, 10, 0)

    game._handle_early_winner()

    completed = [event for event in events if event.type == "hand_completed"][-1]
    assert completed.public_payload["winner_names"] == ["AI-1"]
    assert completed.public_payload["total_pot"] == 15
    assert completed.public_payload["outcome_metadata"]["ended_by_fold"] is True
    assert completed.private_payload_by_player == {}
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest -q tests/test_game_engine_events.py::test_early_winner_emits_hand_completed_without_private_payload
```

Expected: FAIL because no `hand_completed` event is emitted.

- [ ] **Step 3: Emit `hand_completed` before replay rendering**

In `_handle_early_winner`, after `history_manager.finish_game(...)` for the single-winner branch, add:

```python
self._emit_event(
    "hand_completed",
    public_payload={
        "winner_names": [winner.name],
        "total_pot": self.pot,
        "final_hands": [
            {
                "player_name": hand["player_name"],
                "final_chips": hand["final_chips"],
                "hand_rank": hand["hand_rank"],
                "winnings": hand["winnings"],
            }
            for hand in final_hands
        ],
        "outcome_metadata": self._build_outcome_metadata(
            ended_by_fold=True,
            went_to_showdown=False,
            winner_reason="fold",
        ),
    },
)
```

Apply the same pattern to `_showdown`, with `winner_names`, `final_hands` without hole cards, and `outcome_metadata` using `went_to_showdown=True`.

- [ ] **Step 4: Run focused tests**

Run:

```bash
python3 -m pytest -q tests/test_game_engine_events.py
```

Expected: PASS.

## Task 5: Keep Headless Benchmark and CLI Behavior Stable

**Files:**
- Modify if needed: `texas_holdem/analytics/headless_simulation.py`
- Test: existing test suite and benchmark command

- [ ] **Step 1: Run headless simulation tests**

Run:

```bash
python3 -m pytest -q tests/test_headless_simulation.py tests/test_ai_system_evaluator.py tests/test_ai_metrics.py
```

Expected: PASS.

- [ ] **Step 2: Run full test suite**

Run:

```bash
python3 -m pytest -q
```

Expected: PASS.

- [ ] **Step 3: Run a small benchmark smoke test**

Run:

```bash
python3 - <<'PY'
from texas_holdem.analytics.ai_system_evaluator import benchmark_ai_system

report = benchmark_ai_system(num_hands=20, player_count=4)
data = report.to_dict()
print(data["hands_played"])
print(data["illegal_action_rate"])
PY
```

Expected: prints `20` and an illegal action rate of `0.0`.

## Task 6: Next Sprint After Event Mirroring

Do not start this task until Tasks 0-5 pass.

- [x] Extract `texas_holdem/ui/terminal_renderer.py` that renders selected `EngineEvent` objects.
- [x] Replace direct street-deal prompts in `texas_holdem/engine/game.py` with renderer-driven `cards_dealt` output while preserving CLI text.
- [x] Replace `_display_community_cards()` direct print with renderer-driven `community_cards_displayed` output while preserving CLI text.
- [x] Replace `_display_game_state()` direct print block with renderer-driven `game_state_displayed` output while preserving CLI text.
- [x] Replace `_display_active_players()` direct print block with renderer-driven `active_players_displayed` output while preserving CLI text.
- [x] Move AI delay sleeps from `texas_holdem/engine/game.py` into terminal-facing flow only.
- [x] Make `texas_holdem/analytics/headless_simulation.py` attach an event collector.
- [x] Define stricter immutable public/private state schema for external agents.
- [ ] Only after the event and state contracts are stable, start external-agent API and online room design.

## Verification Checklist

- [ ] `python3 -m pytest -q` passes.
- [ ] Focused Sprint 3 event tests pass.
- [ ] CLI output remains playable and unchanged for existing terminal users.
- [ ] Public events never include opponent hole cards or deck contents.
- [ ] Headless simulation does not modify real runtime data files.
- [ ] 20-hand benchmark smoke test returns `illegal_action_rate == 0.0`.
