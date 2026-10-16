# Sprint 2.1 Completion Report: Provider-Driven Game Flow

Date: 2026-05-07
Project: Texas Hold'em local trainer -> AI Poker Arena / Agent Poker Platform

## Goal

Continue Sprint 2 by connecting the new decision abstractions to the real game flow.

Sprint 2 created the standalone modules:

- `decision_provider.py`
- `action_validator.py`
- `headless_simulation.py`
- `ai_system_evaluator.py`

Sprint 2.1 connects those abstractions into `game.py` so actions go through a single decision pipeline before game state is mutated.

## Result

Sprint 2.1 is complete.

Final verification:

```bash
python3 -m pytest -q
```

Result:

```text
83 passed in 20.47s
```

100-hand AI-only benchmark:

```json
{
  "hands_played": 100,
  "total_actions": 470,
  "illegal_action_rate": 0.0,
  "average_decision_score": 66.5,
  "grade_distribution": {
    "good": 344,
    "questionable": 30,
    "poor": 62,
    "excellent": 34
  },
  "final_stacks": {
    "AI-1": 2660,
    "AI-2": 526,
    "AI-3": 0,
    "AI-4": 814
  },
  "errors": [],
  "hands": 100,
  "actions": 470
}
```

## What changed

### 1. `game.py` now uses a provider + validator action pipeline

New flow:

```text
_build_game_state_snapshot(...)
-> DecisionProvider.decide(snapshot)
-> validate_action(snapshot, response)
-> mutate game state with validated action only
-> _record_processed_action(...)
```

New/updated game-level methods:

- `set_decision_provider(player_name, provider)`
- `_get_default_decision_provider(player)`
- `_build_game_state_snapshot(...)`
- `_get_player_action(...)` now routes through provider + validator
- `_build_action_metadata()`

### 2. AI actions now use `BuiltInAIDecisionProvider`

Internal AI players now go through `BuiltInAIDecisionProvider` instead of direct `AIPlayer.make_decision(...)` from `_get_player_action`.

Important compatibility detail:

- Public `GameStateSnapshot.community_cards` stays string/serializable.
- Existing internal AI still needs live `Card` objects.
- `BuiltInAIDecisionProvider` now accepts `community_cards_provider`, and `game.py` passes `lambda: list(self.community_cards)`.

This fixed the earlier risk where advanced AI logic received strings and raised errors such as:

```text
AttributeError: 'str' object has no attribute 'rank'
```

### 3. Human CLI path remains compatible

Human players are now behind `_LegacyHumanGameDecisionProvider`.

The adapter calls the existing rich CLI method `_get_human_action(...)`, so current user experience remains intact:

- status/help options
- realtime assistant display
- confirmation flow
- existing raise UI

No recursion was introduced:

```text
_get_player_action
-> provider.decide
-> _LegacyHumanGameDecisionProvider.decide
-> _get_human_action
```

The human provider does not call `_get_player_action` again.

### 4. Invalid provider responses are blocked before state mutation

`_get_player_action(...)` now returns only the `ValidatedAction` result.

This means malformed or illegal provider responses fall back before `game.py` mutates chips, pot, current bet, folded state, or side pots.

Examples covered by tests:

- provider returns `check` while facing a bet -> fallback to fold/check depending legal state
- illegal action -> fallback
- raise below minimum -> fallback
- raise above available total bet -> fallback
- bad amount input -> fallback/normalization

### 5. History now records raw + validated action metadata

`game_history.PlayerAction` now includes:

```python
action_metadata: Optional[Dict[str, Any]] = None
```

When provider/validator metadata exists, actions can record:

- `raw_action`
- `raw_amount`
- `raw_response`
- `provider_error`
- `provider_metadata`
- `validated_action`
- `validated_amount`
- `is_valid`
- `validation_reason`

Backward compatibility:

- old history records without `action_metadata` still load
- old history records without `decision_evaluation` still load
- existing tests for decision evaluation still pass

### 6. Human raise UI now matches validator semantics

A code quality review found a mismatch:

- `game.py` mutation treats raise amount as total target bet
- `ActionValidator` also treats raise amount as total target bet
- old human raise prompt used a different min/max interpretation

Fixed:

- min raise now uses `_get_min_raise_total()`
- max raise now uses `player.chips + player.current_bet`

This avoids a confusing case where the human UI accepted/rejected a raise differently from the validator.

### 7. Headless simulation now restores in-memory AI managers

Earlier Sprint 2 already isolated real files:

- `game_history.json`
- `player_stats.json`

Sprint 2.1 also restores in-memory singleton managers after simulation:

- `smart_ai_system.ai_engine_manager.engines`
- `advanced_ai_engine.advanced_ai_manager.engines`

This prevents AI-only benchmark runs from polluting later interactive games in the same Python process.

## New/updated tests

New file:

- `tests/test_provider_driven_game_flow.py`

Expanded files:

- `tests/test_decision_provider.py`
- `tests/test_headless_simulation.py`

Covered behavior:

- public snapshot does not leak opponent hole cards or deck
- provider responses are validated before mutation
- invalid provider action fallback is recorded
- action metadata is stored in history
- built-in AI provider can receive live `Card` objects for existing AI internals
- human raise prompt uses the same total-bet range as validator
- headless simulation restores global AI engine managers

## Reviews

Two review passes were run through subagents.

Spec compliance review:

- Verdict: PASS
- Verified provider + validator pipeline, snapshot privacy, history metadata, decision evaluation compatibility, 100-hand benchmark, and full tests.

Code quality review:

- Initial verdict: no critical blocker; two important issues found.
- Issues found:
  1. headless simulation did not restore global AI manager in-memory state
  2. human raise UX had min/max semantics mismatch with validator
- Both issues were fixed and covered by tests.

## Current AI intelligence interpretation

The system is now more stable architecturally:

- 100-hand AI-only benchmark completed
- `errors = []`
- `illegal_action_rate = 0.0`
- full tests pass

But AI quality is still not online-level yet:

- average decision score is around mid-60s
- poor/questionable decisions remain common
- evaluator is still heuristic/rule-based
- profile-level VPIP/PFR/aggression/showdown/win-rate metrics are still missing

Current status:

```text
Architecture readiness for agents: improved
Action legality stability: improved
AI playing strength: measurable but not yet online-level
```

## Files changed in Sprint 2.1

Core:

- `game.py`
- `decision_provider.py`
- `game_history.py`
- `headless_simulation.py`

Tests:

- `tests/test_provider_driven_game_flow.py`
- `tests/test_decision_provider.py`
- `tests/test_headless_simulation.py`

Docs:

- `docs/reports/2026-05-07-sprint2-1-provider-driven-game-flow.md`
- `docs/index.md`

## Remaining limitations

1. `game.py` still mixes engine, CLI output, sleep, history, AI updates, and state mutation.
2. `headless_simulation.py` is still a wrapper around `TexasHoldemGame.play_hand()`, not a pure headless engine.
3. `ActionValidator` supports `all-in`, but `game.py` legal actions do not yet expose a separate `all-in` branch.
4. AI system evaluator does not yet calculate VPIP/PFR/aggression/showdown/win-rate by profile.
5. Public/private snapshot boundaries are tested for basic leakage, but not yet frozen/immutable for external untrusted agents.

## Recommended next step: Sprint 2.2

Sprint 2.2 should focus on poker quality metrics, not Web UI yet.

Recommended scope:

1. Expand `ai_system_evaluator.py`:
   - VPIP
   - PFR
   - aggression factor
   - fold rate
   - showdown rate
   - win rate
   - poor/blunder rate by AI profile

2. Add larger benchmark command/report:
   - 1,000 hands
   - no runtime file pollution
   - no in-memory singleton pollution
   - JSON report output under `docs/reports/`

3. Start reducing AI weaknesses:
   - identify repeated poor/blunder patterns
   - tune AI decision logic
   - compare before/after metrics

4. Keep online poker room work blocked until:
   - 1,000+ hand benchmark is stable
   - action legality remains 0 illegal actions
   - public/private state schema is stricter
