# Sprint 2.2 Completion Report: AI Metrics and 1,000-hand Benchmark

Date: 2026-05-08
Project: Texas Hold'em local trainer -> AI Poker Arena / Agent Poker Platform

## Goal

Sprint 2.2 focused on measuring AI poker behavior over a longer AI-only run before starting online-room work.

Scope:

- add poker profile metrics to `ai_system_evaluator.py`
- add 1,000-hand benchmark JSON output
- preserve headless simulation isolation
- run the benchmark and document results

## Result

Sprint 2.2 is complete.

Final benchmark command used:

```bash
python3 - <<'PY'
from ai_system_evaluator import benchmark_ai_system
report = benchmark_ai_system(
    num_hands=1000,
    player_count=4,
    output_path='docs/reports/2026-05-08-sprint2-2-ai-1000-hand-benchmark.json',
)
print(report.to_dict())
PY
```

Benchmark JSON artifact:

- `docs/reports/2026-05-08-sprint2-2-ai-1000-hand-benchmark.json`

## Final 1,000-hand benchmark summary

```json
{
  "hands_played": 1000,
  "total_actions": 2281,
  "illegal_action_rate": 0.0,
  "average_decision_score": 55.61814993423937,
  "grade_distribution": {
    "questionable": 70,
    "good": 1351,
    "excellent": 20,
    "poor": 840
  },
  "final_stacks": {
    "AI-1": 0,
    "AI-2": 1387,
    "AI-3": 2613,
    "AI-4": 0
  },
  "errors": []
}
```

Key stability checks:

```text
hands_played = 1000
errors = []
illegal_action_rate = 0.0
```

## Player-level poker metrics

The evaluator now reports `player_metrics` for each AI player.

Metrics added:

- `hands_played`
- `actions`
- `vpip`
- `pfr`
- `aggression_factor`
- `fold_rate`
- `showdown_rate`
- `win_rate`
- `poor_blunder_rate`
- `average_decision_score`
- raw supporting counts:
  - `preflop_vpip_hands`
  - `preflop_raise_hands`
  - `aggressive_actions`
  - `call_actions`
  - `fold_actions`
  - `showdown_hands`
  - `won_hands`
  - `poor_blunder_actions`

### 1,000-hand player metrics

```json
{
  "AI-1": {
    "hands_played": 219,
    "actions": 232,
    "vpip": 0.0867579908675799,
    "pfr": 0.0684931506849315,
    "aggression_factor": 2.0,
    "fold_rate": 0.8448275862068966,
    "showdown_rate": 1.0,
    "win_rate": 0.0958904109589041,
    "poor_blunder_rate": 0.21982758620689655,
    "average_decision_score": 62.09051724137931
  },
  "AI-2": {
    "hands_played": 1000,
    "actions": 1016,
    "vpip": 0.027,
    "pfr": 0.021,
    "aggression_factor": 3.0,
    "fold_rate": 0.8818897637795275,
    "showdown_rate": 1.0,
    "win_rate": 0.104,
    "poor_blunder_rate": 0.3858267716535433,
    "average_decision_score": 54.71948818897638
  },
  "AI-3": {
    "hands_played": 1000,
    "actions": 1025,
    "vpip": 0.021,
    "pfr": 0.013,
    "aggression_factor": 1.5714285714285714,
    "fold_rate": 0.8546341463414634,
    "showdown_rate": 1.0,
    "win_rate": 0.124,
    "poor_blunder_rate": 0.3873170731707317,
    "average_decision_score": 54.91219512195122
  },
  "AI-4": {
    "hands_played": 1,
    "actions": 8,
    "vpip": 1.0,
    "pfr": 1.0,
    "aggression_factor": 6.0,
    "fold_rate": 0.0,
    "showdown_rate": 1.0,
    "win_rate": 0.0,
    "poor_blunder_rate": 0.0,
    "average_decision_score": 72.5
  }
}
```

## Implementation notes

### `ai_system_evaluator.py`

Added:

- `PlayerPokerMetrics`
- `player_metrics` field on `AISystemEvaluationReport`
- `benchmark` metadata field on `AISystemEvaluationReport`
- `benchmark_ai_system(num_hands=1000, player_count=4, output_path=None)`
- `_calculate_player_metrics(...)`
- `_players_in_hand(...)`

The report `to_dict()` output now includes nested player metrics and benchmark metadata.

### `headless_simulation.py`

Expanded hand summaries with `final_hands`, so evaluator can calculate showdown/win-related metrics.

For hands with no record, summaries now include:

- `final_hands: []`

For completed hands, each final hand includes:

- `player_name`
- `hole_cards`
- `final_chips`
- `is_winner`
- `hand_rank`
- `winnings`

### Tests

New tests:

- `tests/test_ai_metrics.py`

Covered:

- VPIP calculation
- PFR calculation
- aggression factor
- fold rate
- showdown rate
- win rate
- poor/blunder rate
- average per-player decision score
- JSON benchmark report writing
- final-stack-only inactive players are not counted as active in every hand

Targeted verification:

```bash
python3 -m pytest -q tests/test_ai_metrics.py tests/test_ai_system_evaluator.py tests/test_headless_simulation.py
```

Result:

```text
10 passed
```

## Interpretation

### Stability

The system is stable enough for long local AI-only benchmarking:

- no benchmark runtime errors
- no illegal actions detected by evaluator
- provider/validator pipeline from Sprint 2.1 held across 1,000 hands

### AI behavior quality

The benchmark exposes major AI weaknesses:

1. Decision quality is not high enough yet.

   Average decision score is about 55.6.

2. Poor-decision volume is high.

   Grade distribution includes 840 `poor` decisions out of 2,281 actions.

3. VPIP/PFR look unrealistically low for long-running survivors.

   AI-2 and AI-3 survived all 1,000 hands but had VPIP around 2-3% and PFR around 1-2%.
   This indicates overly tight/passive preflop behavior or metric distortion from blind handling.

4. Fold rates are extremely high.

   AI-1/2/3 fold rates are around 84-88%.
   This confirms the agents are avoiding many spots rather than playing balanced poker.

5. Showdown metric is currently a proxy.

   `showdown_rate` is based on `final_hands` presence in current history records. Because the existing history system may create final hand records for non-showdown endings, this metric should be treated as a rough proxy until the game engine records an explicit `went_to_showdown` flag.

## Recommended Sprint 2.3

Sprint 2.3 should improve metric fidelity and AI decision quality before online-room work.

Recommended next steps:

1. Add explicit hand outcome metadata:
   - `ended_by_fold`
   - `went_to_showdown`
   - `winner_reason`
   - per-player `saw_flop`, `saw_turn`, `saw_river`

2. Improve blind-aware VPIP/PFR:
   - exclude forced blinds from voluntary pot entry
   - track blind positions
   - count preflop opportunities precisely

3. Add profile-aware benchmark breakdown:
   - style name / AI skill level per player
   - win rate by profile
   - poor/blunder rate by profile

4. Start targeted AI tuning:
   - reduce excessive folding
   - improve preflop ranges
   - reduce poor actions in common states
   - compare before/after 1,000-hand reports

5. Keep online-room/WebSocket work blocked until:
   - benchmark metrics are more trustworthy
   - poor/blunder rate improves materially
   - showdown/outcome metadata is explicit
