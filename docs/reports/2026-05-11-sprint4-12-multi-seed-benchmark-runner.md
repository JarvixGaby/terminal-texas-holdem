# Sprint 4.12 — Multi-seed benchmark runner

Date: 2026-05-11

## Slice

Add a multi-seed AI benchmark runner so AI tuning can be reviewed across variance instead of a single lucky or unlucky run.

## Changes

- Added optional `seed` support to `run_ai_only_simulation(...)`, `evaluate_ai_system(...)`, and `benchmark_ai_system(...)`.
- Added `benchmark_ai_system_multi_seed(...)` in `ai_system_evaluator.py`.
- Multi-seed output includes:
  - benchmark protocol metadata: seeds, hands per seed, player count, starting chips, generated timestamp;
  - per-seed run reports using the existing single-run report schema plus `seed`;
  - summary mean/std/min/max for key numeric metrics.
- Seeded headless runs now isolate global random state, AI managers, temporary stats/history files, and odds-calculator singleton caches so repeated runs with the same seed are deterministic inside the same process.

## Guardrails

- Existing single-run benchmark behavior is preserved; `seed` is optional and defaults to `None`.
- No poker hand-ranking or No-Limit Hold'em legality semantics changed.
- No online/API/WebSocket/platform work added.
- Runtime root artifact paths were not moved.

## Verification

Focused tests passed:

```bash
python3 -m pytest -q tests/test_ai_system_evaluator.py
# 7 passed
```

Additional full-suite verification was run after this report during the Hermes verification gate.
