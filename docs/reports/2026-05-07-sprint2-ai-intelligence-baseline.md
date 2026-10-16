# Sprint 2 AI Intelligence Baseline Report

Date: 2026-05-07
Project: Texas Hold'em local trainer -> AI Poker Arena / Agent Poker Platform

## Purpose

This report records the first runnable baseline for evaluating whether the current AI betting / action logic is close to the target of an online poker game level.

Important: this is not a claim that the current AI already matches strong online poker opponents. It is a measurable baseline so future improvements can be compared objectively.

## What was added in Sprint 2

Core modules:

- `decision_provider.py`
  - `GameStateSnapshot`
  - `VisiblePlayerSnapshot`
  - `ActionResponse`
  - `DecisionProvider`
  - `BuiltInAIDecisionProvider`
  - `HumanCliDecisionProvider`

- `action_validator.py`
  - `ValidatedAction`
  - `validate_action(...)`
  - Safe fallback for illegal or malformed actions.
  - Raise validation now treats raise amount as a total target bet and accounts for chips already committed by the acting player.

- `headless_simulation.py`
  - `run_ai_only_simulation(...)`
  - AI-only simulation without `input()`.
  - Suppresses CLI output and AI sleep delay.
  - Uses temporary history and temporary player stats files so simulation does not modify real `game_history.json` or `player_stats.json`.
  - Returns per-hand action records and decision evaluations.

- `ai_system_evaluator.py`
  - `evaluate_ai_system(...)`
  - `summarize_ai_evaluations(...)`
  - `AISystemEvaluationReport.to_dict()` includes both internal names and compact aliases:
    - `hands_played` / `hands`
    - `total_actions` / `actions`

Tests:

- `tests/test_decision_provider.py`
- `tests/test_action_validator.py`
- `tests/test_headless_simulation.py`
- `tests/test_ai_system_evaluator.py`

## Baseline run

Command:

```bash
python3 - <<'PY'
from ai_system_evaluator import evaluate_ai_system
import json
report = evaluate_ai_system(num_hands=50, player_count=4).to_dict()
print(json.dumps(report, ensure_ascii=False, indent=2))
PY
```

Observed baseline output from this sprint:

```json
{
  "hands_played": 50,
  "total_actions": 258,
  "illegal_action_rate": 0.046511627906976744,
  "average_decision_score": 64.34108527131782,
  "grade_distribution": {
    "good": 192,
    "poor": 26,
    "blunder": 12,
    "questionable": 14,
    "excellent": 14
  },
  "final_stacks": {
    "AI-1": 945,
    "AI-2": 531,
    "AI-3": 985,
    "AI-4": 1539
  },
  "errors": [],
  "hands": 50,
  "actions": 258
}
```

## Initial interpretation

Current AI action legality / stability:

- Good sign: simulation completed with `errors = []`.
- Good sign: the evaluator can now produce non-empty decision grades and scores.
- Gap: `illegal_action_rate` is not zero in this baseline after counting illegal risk tags, so action validation must be integrated into the real game flow before claiming online-level stability.

Current AI quality:

- Average decision score around 66/100 is not enough to claim online-level poker intelligence.
- The system still produced `poor` and `blunder` grades.
- One AI busted in a short 50-hand sample, which may be normal variance but should be investigated over larger samples.
- The current evaluator is rule-based and approximate, not solver-grade.

Conclusion:

- Current level: playable and measurable local AI trainer.
- Not yet: strong online-game-level poker AI.
- Next target: reduce `poor + blunder` rate, stabilize profile behavior, and benchmark over larger AI-only samples.

## Suggested online-level gates

Before claiming the AI is close to online-game quality, require at least:

1. Stability gates
   - 1,000+ AI-only hands complete without crashes.
   - `illegal_action_rate = 0`.
   - No real runtime data files modified during evaluation.

2. Decision quality gates
   - Average decision score consistently > 75.
   - `poor + blunder` rate below 10% on the current evaluator.
   - No repeated obvious leaks such as frequent low-equity all-ins, overfolding high equity, or passive missed-value lines.

3. Poker behavior gates
   - VPIP/PFR/aggression metrics are measured per AI profile.
   - Different AI profiles have distinguishable behavior.
   - No profile collapses into always-fold, always-call, or reckless all-in behavior.

4. Architecture gates
   - Game loop uses `DecisionProvider` and `ActionValidator` directly.
   - Headless simulation no longer depends on suppressing CLI output from `game.py`.
   - Public/private state boundary is tested.

## Known Sprint 2 limitations

- `DecisionProvider` and `ActionValidator` exist, but `game.py` is not fully provider-driven yet.
- `headless_simulation.py` is still a wrapper around `TexasHoldemGame.play_hand()`, not a pure engine simulation.
- `game.py` still contains CLI output, sleep calls, history side effects, and AI model updates.
- AI evaluator currently reports decision-evaluator metrics, but not yet VPIP, PFR, 3-bet frequency, aggression factor, showdown frequency, or win-rate by profile.

## Recommended next development step

Sprint 2.1 should integrate the new abstractions into the game flow:

1. Build `GameStateSnapshot` from `TexasHoldemGame` at each decision point.
2. Send snapshot to a `DecisionProvider`.
3. Validate `ActionResponse` through `validate_action(...)` before state mutation.
4. Record both raw and validated action metadata.
5. Keep existing CLI behavior compatible.

After that, Sprint 2.2 should expand `ai_system_evaluator.py` to include poker behavior metrics: VPIP, PFR, aggression factor, showdown rate, win rate, and poor/blunder rate by AI profile.
