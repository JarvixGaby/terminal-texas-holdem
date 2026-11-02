# Actual postflop position: Astra repair and validation

Started: 2026-10-30
Completed: 2026-10-31

## Outcome

Fixed the unreachable in-position strategy path identified by Astra. The old condition required an absolute position score greater than 0.5, although its maximum was 0.5. Consequently, ordinary pure bluffs never occurred through real decisions and every ordinary semi-bluff received the out-of-position discount.

The built-in provider now derives relative postflop position from existing public seats and the dealer. Folded, all-in and zero-chip opponents do not participate in action-order comparisons. All-in opponents remain in equity calculations and multiway pressure discounts. Two internal optional keyword arguments carry this context through AIPlayer to AdvancedAIEngine; public snapshot schemas, poker legality, persistence paths and metric definitions are unchanged. Standard AI calls remain unchanged.

With no actionable opponent, weak hands (equity below 45%) check before the c-bet shortcut as well as ordinary bluff branches. Old direct engine calls without seat context conservatively recognize only BTN as in position and require a nonempty opponent list; those callers cannot distinguish all-in opponents by name alone.

Restoring relative position also enables existing facing-bet pure/semi-bluff raises and the existing c-bet position adjustment. Their frequencies were not separately retuned. This is a correction to the shared position input, not an isolated change to one bluff probability.

## Verification

- Astra implementation/focused verification: **98 passed** across five test files.
- Independent full suite: `python3 -m pytest -q` → **389 passed**.
- New `tests/test_postflop_position.py`: **40 cases**, including real provider → AIPlayer → AdvancedAIEngine decisions; explicit checks that errors/fallbacks did not mask the result; BTN, CO versus BTN, earlier seats after late-player folds, both heads-up seats, all-in opponents, no actionable opponents, c-bet opportunities, direct-call fallback, and standard AI compatibility.
- Deterministic equity/random inputs demonstrate an actual weak-hand raise in position and a check out of position, with persona-sensitive probabilities. Out-of-position semi-bluffing remains possible at its discounted rate.
- `git diff --check` passed.

## Benchmarks

All simulations use 10,000 starting chips and five equity rollouts per decision. Independent seed runs used isolated Python processes, then the existing `_summarize_seed_runs` and `evaluate_benchmark_gates` functions aggregated and checked results.

- Primary: seeds 0–9, four players, 500 hands each. **PASS**, all **5,000 hands** completed, zero illegal actions, zero runtime errors.
- Ten-player diagnostic: seeds 0–2, 100 hands each. **PASS** against its explicitly declared reduced protocol, all **300 hands** completed, zero illegal actions, zero runtime errors.

Means across seeds, compared with the corresponding `2026-10-29-position-ranges-*` artifacts:

| Metric | Four-player before | Four-player after | Ten-player before | Ten-player after |
| --- | ---: | ---: | ---: | ---: |
| Average decision score | 72.9156 | 72.7696 | 72.4925 | 71.8246 |
| Style separability | 0.3616 | 0.3544 | 0.2905 | 0.2823 |
| Profile calibration distance (lower is better) | 0.0990 | 0.0804 | 0.0602 | 0.0948 |

Scores and separability decreased slightly while passing all gates. Calibration improved in the four-player sample but worsened in the ten-player sample. No broad strength or universal calibration improvement is claimed. The key verified outcome is that the intended position-dependent strategy is now reachable through the real game pipeline without failing the existing acceptance gates.

The four-player primary covers nit, tight_aggressive, loose_aggressive and calling_station. Ten-player diagnostics cover all six presets but remain only 300 hands. Five-rollout benchmarks do not predict exact frequencies under the normal 500-rollout runtime setting. Gate PASS alone does not prove branch reachability; the new real-entry tests provide that evidence.

Artifacts:

- [Primary](2026-10-30-actual-position-primary.json), [gate evaluation](2026-10-30-actual-position-primary-evaluation.json).
- [Ten-player diagnostic](2026-10-30-actual-position-ten-player.json), [gate evaluation](2026-10-30-actual-position-ten-player-evaluation.json).

The prior range and position reports retain their original results with an explicitly dated correction explaining the unreachable branch.

## Reproduce

Use `benchmark_ai_system_multi_seed()` for primary. For the ten-player diagnostic use `benchmark_ai_system_multi_seed(seeds=[0, 1, 2], hands_per_seed=100, player_count=10)` and evaluate against that reduced protocol. Run `python3 -m pytest -q tests/test_postflop_position.py` to verify strategy reachability directly.
