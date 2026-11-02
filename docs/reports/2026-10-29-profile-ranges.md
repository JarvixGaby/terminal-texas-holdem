# Explicit profile ranges and contextual bluffs

Date: 2026-10-29

> **Correction — 2026-10-30:** Astra's subsequent real-entry review found that the existing `position_advantage > 0.5` condition was never true. These historical benchmark results remain valid for the code tested, but do not demonstrate that in-position pure bluffs were reachable. The relative-position repair and renewed validation are documented in [actual-position validation](2026-10-30-actual-position.md).

## Result

Added an editable preflop range table for all six built-in archetypes and six positions, covering entry, opening raises, calls facing raises, and three-bets. Built-in engine decisions now query membership; custom profiles retain their parameter-based fallback. Initial tables expand the previous thresholds, so this extraction deliberately preserves preflop selection boundaries. Existing price exceptions and mixed-action frequencies remain active.

Ordinary postflop pure bluffs and semi-bluffs now use the archetype bluff frequency. Pure bluffs require position; semi-bluffs can occur out of position at a discount. Multiple opponents and dangerous boards reduce frequency. Existing c-bet and facing-bet policies remain separate.

See [range guide](../architecture/profile-hand-ranges.md) for notation, examples, probabilities and limits.

## Verification

- `python3 -m pytest -q`: **330 passed** (including 12 new range/bluff cases).
- Primary benchmark: seeds 0–9 × 500 hands, four players, 10,000 starting chips, five equity simulations per decision.
- All 5,000 requested hands completed; zero illegal actions and zero runtime errors.
- `evaluate_benchmark_gates(...)`: **PASS**, including decision quality, style separability and public transcript safety.
- Engine rules, evaluator semantics, public state contracts, persistence paths and metric definitions were not changed.

Artifacts: [primary](2026-10-29-profile-ranges-primary.json), [gate evaluation](2026-10-29-profile-ranges-primary-evaluation.json).

## Comparison

Baseline is the latest accepted same-protocol artifact, `2026-10-26-calling-station-astra-medium-equity-check-primary.json`. Values below are arithmetic means across seeds.

| Metric | Baseline | Range/bluff update |
| --- | ---: | ---: |
| Hands per seed | 500 | 500 |
| Illegal action rate | 0 | 0 |
| Average decision score | 72.8459 | 72.9156 |
| Style separability | 0.3530 | 0.3616 |
| Profile calibration distance (lower is better) | 0.0877 | 0.0990 |
| Bustout rate | 0.175 | 0.125 |

The gate passes, but aggregate style-target calibration is worse; this is not a claim that every persona became more realistic or stronger. Action changes alter subsequent random draws and game trajectories, so small score movements are descriptive rather than causal strength estimates. The primary protocol uses only five equity simulations, while normal terminal play uses 500; exact runtime action frequencies need separate evaluation.

## Reproduce

```python
import json
from pathlib import Path
from texas_holdem.analytics.ai_system_evaluator import (
    benchmark_ai_system_multi_seed, evaluate_benchmark_gates,
)

artifact = benchmark_ai_system_multi_seed()
print(json.dumps(evaluate_benchmark_gates(artifact), indent=2))
```
