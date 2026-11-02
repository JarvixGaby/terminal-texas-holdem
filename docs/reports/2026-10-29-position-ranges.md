# Table-size-aware position ranges

Date: 2026-10-29

> **Correction — 2026-10-30:** Astra's subsequent real-entry review found that the existing `position_advantage > 0.5` condition was never true. These historical benchmark results remain valid for the code tested, but do not demonstrate that in-position pure bluffs were reachable. The relative-position repair and renewed validation are documented in [actual-position validation](2026-10-30-actual-position.md).

## Changes

Fixed the inherited seat mapping which labeled the earliest non-blind seats MP and several later seats UTG. `texas_holdem/ai/positions.py` now names every seat for 2–10 players. Ten-player preflop order is UTG, UTG+1, UTG+2, MP, LJ, HJ, CO, BTN, SB, BB. Heads-up BTN remains the small blind.

Expanded the editable persona charts from six to ten full-ring roles. Selection uses distance to BTN: six-player UTG uses the LJ role, eight-player UTG uses UTG+2, and ten-player UTG uses UTG. Intermediate heuristic bonuses are -0.035 (UTG+1), -0.02 (UTG+2), +0.015 (LJ), and +0.03 (HJ); existing roles retain their parameters. Across all six styles and all four action-range types, the non-blind ranges are nested from early to late position.

Custom profiles use the same table-size-aware positional adjustment with their own parameters. Legacy non-profile engines receive explicit nearest-tier aliases for the added names. Six personas remain presets, not an exhaustive classification; balanced does not mean solver equilibrium. Extra-large custom tables retain unique names and cap additional early ranges at UTG.

## Validation

- Full suite: `python3 -m pytest -q` → **349 passed**.
- New tests cover every seat at 2–10 players, range widening, different UTG roles by table size, and the live engine passing table size through to lookup.
- `git diff --check` passed.
- Primary: **10 seeds × 500 hands**, four players, 10,000 starting chips, five equity simulations per decision; **PASS**, 5,000 completed hands, zero illegal actions and zero runtime errors.
- Ten-player diagnostic: **3 seeds × 100 hands**, otherwise the same settings; before and after both **PASS** against the explicitly reduced ten-player protocol, 300 hands each, zero illegal actions and zero runtime errors.

Primary execution resumed completed seed records from its progress file and ran remaining seeds in separate processes using the same `evaluate_ai_system` settings. Results were sorted by seed and aggregated with the existing `_summarize_seed_runs`, then checked by `evaluate_benchmark_gates`. This changes execution scheduling only, not protocol or metric definitions.

The controlled ten-player baseline replaces only `PositionRangeManager.get_position_name` with its previous implementation. The ten-player table size leaves the old range-role names unchanged, reproducing the prior six-category mapping while retaining the same profile/bluff policy. Seeds are 0, 1, 2 for both comparisons.

## Results

Means across seeds:

| Ten-player metric | Old mapping | Corrected mapping |
| --- | ---: | ---: |
| Hands per seed | 100 | 100 |
| Illegal action rate | 0 | 0 |
| Average decision score | 72.3505 | 72.4925 |
| Style separability | 0.2844 | 0.2905 |
| Profile calibration distance (lower is better) | 0.0467 | 0.0602 |

Four-player primary summary values match the preceding `2026-10-29-profile-ranges-primary.json`: average decision score 72.9156, style separability 0.3616. Four-player seats remain SB, BB, CO, BTN and their chart selection is unchanged.

Calibration distance worsened in the ten-player diagnostic; no general style-calibration or playing-strength improvement is claimed. This is a 300-hand ten-player diagnostic, not a full ten-player 5,000-hand acceptance run. The five-rollout equity setting is also not the runtime default of 500. Stack-depth-specific ranges, raiser-position-aware responses, and opponent range inference remain outside this slice.

Artifacts:

- [Primary](2026-10-29-position-ranges-primary.json), [evaluation](2026-10-29-position-ranges-primary-evaluation.json).
- [Ten-player before](2026-10-29-position-ranges-ten-player-before.json), [evaluation](2026-10-29-position-ranges-ten-player-before-evaluation.json).
- [Ten-player after](2026-10-29-position-ranges-ten-player.json), [evaluation](2026-10-29-position-ranges-ten-player-evaluation.json).

To reproduce current behavior, use `benchmark_ai_system_multi_seed()` for primary, or `benchmark_ai_system_multi_seed(seeds=[0,1,2], hands_per_seed=100, player_count=10)` for the diagnostic. Pass the corresponding protocol to `evaluate_benchmark_gates` for the reduced run.
