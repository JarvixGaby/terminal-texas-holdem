# Sprint 4 AI Opponent Experience Plan

> **For Hermes:** Use `docs/triad-role-workflow.md` adaptive routing. PM/Tech Lead scope and architecture reviews are Claude-primary; implementation is Codex-primary; domain review is required only for risky gameplay, poker-semantics, public/private-state, or trainer-UX changes; Hermes remains the final verifier.

**Goal:** Improve the local CLI Texas Hold'em trainer by making built-in robot opponents more credible, varied, and useful for training before any Web UI or online platform work.

**Architecture:** Build on Sprint 2's `DecisionProvider` / `ActionValidator` / benchmark boundary and Sprint 3's terminal/headless `EngineEvent` foundation. Keep changes small and test-driven: scenario spot tests first, then strategy fixes, then profile separation and benchmark hardening. Preserve canonical No-Limit Texas Hold'em rules and public/private state boundaries.

**Tech Stack:** Python terminal app, `pytest`, existing AI modules (`texas_holdem/ai/advanced_ai_engine.py`, `texas_holdem/ai/decision_provider.py`, `texas_holdem/ai/action_validator.py`, `texas_holdem/analytics/ai_system_evaluator.py`, `texas_holdem/analytics/headless_simulation.py`), project docs/reports under `docs/`.

---

## 1. Executive Summary

Sprint 3 improved the CLI game's presentation layer: terminal output is more stable, key hand narration flows through structured engine events, and headless event collection is available. The next bottleneck is not rendering but opponent credibility.

Current built-in AI is a usable baseline: it produces legal actions, has decision evaluation, and already received one targeted tuning pass. However, the CLI trainer will still feel weak if opponents make obviously bad poker decisions, all play with the same style, use unrealistic bet sizes, or provide no training feedback.

Sprint 4 should therefore focus on an **AI Opponent Experience** track:

1. Remove obvious bad play with scenario tests.
2. Make opponents stylistically different.
3. Improve postflop and sizing realism.
4. Add optional trainer explanations.
5. Harden benchmarks so AI tuning is not overfit to one run.

This sprint is intentionally local-first. It should not start online rooms, WebSockets, external-agent sandboxes, or public API work.

## 2. Current Baseline and Gaps

### Existing baseline

From Sprint 2:

- Provider/validator action boundary exists.
- AI-only headless simulation exists.
- Decision evaluation and player-level metrics exist.
- VPIP/PFR and profile-aware benchmark reporting exist.
- Targeted AI tuning already fixed one obvious free-check preflop overfold issue.

Sprint 2.5 benchmark movement:

```text
average_decision_score: 59.58 -> 63.59
poor actions: 745 -> 603
excellent actions: 34 -> 129
illegal_action_rate: 0.0
```

From Sprint 3:

- `EngineEvent` and `TerminalEventRenderer` exist.
- Terminal UX parity verification passed.
- 100-hand headless event coverage passed.
- Final full suite reached 170 passing tests.

### Remaining gaps

- AI still needs deeper strategic work beyond one targeted tuning fix.
- Opponent styles are not yet a strong product feature.
- Postflop behavior and bet sizing need credibility checks.
- Benchmarks need multi-seed variance and style-separability reporting.
- CLI trainer feedback should explain decisions without pretending to be a solver.

## 3. Why Poker Bots Feel Bad in a CLI Trainer

A poker bot does not need to be superhuman to be enjoyable, but it must avoid trust-breaking behavior:

- Folding when checking is free.
- Open-folding premium hands or playing them too passively.
- Calling or folding without regard to pot odds or bet size.
- Always using the same raise amount.
- Having no visible distinction between tight, loose, aggressive, and passive opponents.
- Playing postflop as if board texture and hand strength do not matter.
- Creating winner-take-all stack concentration too quickly.
- Producing benchmark gains in one seed while regressing elsewhere.

The product goal is credible training opposition, not perfect GTO play.

## 4. Product Goals for Sprint 4

1. **Credibility:** A serious poker player should not see obvious nonsense in common spots.
2. **Variety:** Opponents should have distinguishable tendencies and table personalities.
3. **Stability:** AI actions must remain legal through `ActionValidator`; illegal action rate must stay zero.
4. **Trainer value:** The CLI should help players understand key decisions over time.
5. **Measurability:** Every tuning change should be evaluated by focused scenario tests plus multi-run benchmark evidence.

## 5. Guardrails / Non-Goals

Do not build in Sprint 4:

- Web UI, WebSocket, online room, login/auth, or external-agent platform.
- GTO solver, CFR training, neural network training, or real-money features.
- Broad `texas_holdem/engine/game.py` rewrites.
- `texas_holdem/engine/hand_evaluator.py` semantic changes.
- Core No-Limit Hold'em rule changes.
- Public/private state contract changes unless explicitly planned.
- Benchmark metric definition changes without focused tests and documentation.

## 6. Roadmap and Slices

### P0 — Sanity and Obvious-Bad-Play Fixes

#### Slice 4.1: Add AI scenario sanity test harness

**Goal:** Create fixed spot tests that catch obviously bad AI decisions before tuning.

**Likely files:**

- Create: `tests/test_ai_scenario_sanity.py`
- Possibly create helpers in `tests/` or a small source-side scenario helper if needed.
- Read/inspect: `texas_holdem/ai/advanced_ai_engine.py`, `texas_holdem/ai/decision_provider.py`, `texas_holdem/ai/action_validator.py`, `tests/test_ai_tuning.py`.

**Tests to add:**

- Preflop no-call weak hand should check, not fold.
- Postflop facing no bet should not fold.
- Premium preflop hand should not open-fold.
- Every scenario action passes existing validation.

**Acceptance criteria:**

- Scenario harness is deterministic and easy to extend.
- Tests fail first for at least one currently uncovered behavior, if such behavior exists.
- No production strategy change is made unless needed to pass the scenario.

**Verification:**

```bash
python3 -m pytest -q tests/test_ai_scenario_sanity.py
python3 -m pytest -q tests/test_ai_tuning.py
python3 -m pytest -q
```

**Risks:** Overfitting exact card combos instead of testing general behavior. Keep tests spot-based but policy-oriented.

#### Slice 4.2: Prevent no-bet/free-check fold behavior across streets

**Goal:** Extend the Sprint 2.5 no-free-fold principle beyond preflop so AI does not fold when checking is available.

**Likely files:**

- Modify: `texas_holdem/ai/advanced_ai_engine.py`
- Tests: `tests/test_ai_scenario_sanity.py`, `tests/test_ai_tuning.py`

**Tests to add:**

- Flop/turn/river no-current-bet spots return `check` or legal `raise`/`bet`, not `fold`.
- Weak hands can check; strong hands may bet through existing legal action shape.

**Acceptance criteria:**

- No-bet fold frequency is zero in scenario tests.
- Full suite passes.
- No validator contract changes.

**Verification:**

```bash
python3 -m pytest -q tests/test_ai_scenario_sanity.py tests/test_ai_tuning.py
python3 -m pytest -q
```

**Risks:** Accidentally forcing passive checking in spots where betting is valuable. This slice only forbids meaningless folds; it should not fully redesign postflop strategy.

#### Slice 4.3: Add premium-hand obvious bad-play guards

**Goal:** Prevent premium hands from producing obviously bad preflop decisions in common legal contexts.

**Likely files:**

- Modify: `texas_holdem/ai/advanced_ai_engine.py`
- Tests: `tests/test_ai_scenario_sanity.py`

**Tests to add:**

- AA/KK facing no raise should open/raise rather than fold/check-only where raising is legal.
- AKs/QQ facing small ordinary action should not open-fold.
- All returned amounts remain legal.

**Acceptance criteria:**

- Premium-hand spot tests pass.
- Illegal action rate stays zero.
- No hand-ranking semantics are changed.

**Verification:**

```bash
python3 -m pytest -q tests/test_ai_scenario_sanity.py
python3 -m pytest -q
```

**Risks:** Making premium play too deterministic. Add profile/frequency hooks later; this slice only guards against trust-breaking decisions.

### P1 — Opponent Archetypes / Personas

#### Slice 4.4: Define opponent archetype config

**Goal:** Introduce explicit AI opponent archetype parameters without broad strategy rewrites.

**Likely files:**

- Create or modify: `texas_holdem/ai/ai_profiles.py` or existing profile/config module.
- Modify: `texas_holdem/ai/advanced_ai_engine.py` only if needed to read profile parameters.
- Tests: new or existing AI profile tests.

**Suggested profile fields:**

```text
vpip_target
pfr_target
aggression_bias
call_bias
bluff_frequency
three_bet_frequency
cbet_frequency
fold_to_cbet_bias
showdown_stickiness
sizing_bias
```

**Initial archetypes:**

- nit
- tight_aggressive
- loose_aggressive
- calling_station
- maniac
- balanced

**Acceptance criteria:**

- Profiles are serializable/configurable.
- Values are range-validated.
- Existing AI behavior is preserved if no explicit profile is selected.

**Verification:**

```bash
python3 -m pytest -q tests/test_ai_tuning.py tests/test_ai_system_evaluator.py
python3 -m pytest -q
```

**Risks:** Adding unused configuration. Keep the fields minimal and immediately use at least a subset in Slice 4.5.

#### Slice 4.5: Add preflop range behavior by archetype

**Goal:** Make archetypes observably different preflop: tight players enter fewer pots, aggressive players raise more, calling stations call more.

**Likely files:**

- Modify: `texas_holdem/ai/advanced_ai_engine.py`
- Modify: `texas_holdem/analytics/ai_system_evaluator.py` if benchmark needs profile-level comparisons.
- Tests: `tests/test_ai_scenario_sanity.py`, `tests/test_ai_system_evaluator.py`

**Tests to add:**

- Nit VPIP target lower than TAG/LAG in deterministic scenario batches.
- Calling station call tendency higher than TAG.
- Maniac/TAG PFR tendency higher than calling station.
- All actions legal.

**Acceptance criteria:**

- Opponent styles differ in benchmark metrics.
- Illegal action rate remains zero.
- No single hard-coded seed is required to prove the difference.

**Verification:**

```bash
python3 -m pytest -q tests/test_ai_scenario_sanity.py tests/test_ai_system_evaluator.py
python3 -m pytest -q
```

**Risks:** Targeting exact poker-theory ranges too early. The first goal is distinguishable and credible behavior, not solver-perfect ranges.

#### Slice 4.6: Add style separability benchmark metrics

**Goal:** Report whether profiles are actually behaviorally distinct.

**Likely files:**

- Modify: `texas_holdem/analytics/ai_system_evaluator.py`
- Tests: `tests/test_ai_system_evaluator.py`
- Docs/report update after implementation.

**Metrics:**

```text
style_separability_score
vpip_spread
pfr_spread
aggression_spread
call_rate_spread
```

**Acceptance criteria:**

- Benchmark output includes separability metrics.
- Existing benchmark callers remain compatible.
- Tests validate schema and basic calculations.

**Verification:**

```bash
python3 -m pytest -q tests/test_ai_system_evaluator.py
python3 -m pytest -q
```

### P2 — Postflop and Bet Sizing Realism

#### Slice 4.7: Hand-strength-aware postflop policy

**Goal:** Tie postflop action tendencies to hand strength, board texture, and draw/value categories.

**Likely files:**

- Modify: `texas_holdem/ai/advanced_ai_engine.py`
- Tests: `tests/test_ai_scenario_sanity.py`, possibly new postflop policy tests.

**Behavior categories:**

- strong made hand
- top pair
- medium/weak pair
- draw
- air
- scary board
- paired/flush/straight texture

**Acceptance criteria:**

- Strong hands value bet more often than weak air.
- Draws can semi-bluff at controlled frequencies.
- Weak showdown value does not always overbet.
- No hand evaluator semantic changes.

#### Slice 4.8: Add realistic bet sizing buckets

**Goal:** Replace obviously uniform sizing with legal, pot-aware sizing buckets.

**Suggested buckets:**

```text
small: 25%-33% pot
medium: 50%-66% pot
large: 75%-100% pot
all-in: stack-pressure or short-stack spot
```

**Acceptance criteria:**

- Raise amounts are inside legal min/max.
- Profiles have distinct sizing bias.
- No illegal overbet/all-in edge cases.

#### Slice 4.9: Add c-bet / fold-to-cbet behavior

**Goal:** Model common continuation-bet and response tendencies by profile.

**Metrics:**

```text
cbet_frequency
fold_to_cbet
check_raise_frequency
```

**Acceptance criteria:**

- TAG/LAG c-bet tendencies are visible.
- Calling station folds to c-bet less often.
- Nit folds to pressure more often.

### P3 — Trainer Explainability

#### Slice 4.10: Add optional AI decision explanation payload

**Goal:** Allow trainer mode to show concise, non-solver AI reasoning.

**Likely files:**

- `texas_holdem/ai/decision_provider.py`
- `texas_holdem/ai/advanced_ai_engine.py`
- `texas_holdem/engine/engine_events.py` / `texas_holdem/ui/terminal_renderer.py` only if displaying via event boundary.
- Tests for serialization and terminal toggle behavior.

**Acceptance criteria:**

- Explanation is optional and does not affect validation.
- Headless data remains serializable.
- CLI display can be disabled.

#### Slice 4.11: Add human action trainer feedback

**Goal:** Give simple feedback after human actions using heuristics and cautious language.

**Example tone:**

```text
训练提示：这个 call 得到较好 pot odds，但你的牌力偏弱。
```

Not:

```text
这是 GTO 正确行动。
```

**Acceptance criteria:**

- Feedback is framed as heuristic, not solver truth.
- Does not leak hidden opponent cards.
- Can be covered by terminal renderer tests.

### P4 — Benchmark / Evaluation Hardening

#### Slice 4.12: Add multi-seed benchmark runner

**Goal:** Prevent strategy tuning from overfitting a single benchmark run.

**Suggested protocol:**

```text
seeds: 10
hands_per_seed: 500 or 1000
players: 4
starting_chips: 10000
profiles: mixed archetypes
```

**Acceptance criteria:**

- Mean/std/min/max are reported.
- Benchmark is deterministic by seed.
- Existing single-run benchmark still works.

#### Slice 4.13: Add stack concentration metrics

**Goal:** Detect winner-take-all dynamics that make games end too quickly or feel unrealistic.

**Metrics:**

```text
largest_stack_share
bustout_rate
hands_until_first_bust
stack_gini
```

#### Slice 4.14: Add human-readable benchmark transcript samples

**Goal:** Generate reviewable hand transcripts for Senior Poker Player review.

**Example:**

```text
Hand #42
Preflop: BTN raises 3bb, BB calls
Flop: Ah 7d 2c
BB checks, BTN bets 1/2 pot, BB folds
Result: BTN wins pot
Flags: normal c-bet spot
```

## 7. Metrics Dashboard Proposal

Keep existing metrics:

- decision score
- illegal action rate
- VPIP
- PFR
- fold rate
- showdown rate
- win rate
- poor/blunder rate

Add or harden:

- aggression factor: `(bet + raise) / call`
- aggression frequency: `(bet + raise) / total_actions`
- three-bet frequency
- c-bet frequency
- fold-to-cbet
- call rate
- raise rate
- check rate
- stack concentration / stack Gini
- style separability score
- seed variance
- hands to bustout

Do not treat any one metric as truth. Use metric bundles plus transcript review.

## 8. Benchmark Protocol

Every non-trivial AI strategy change should pass three layers:

### Layer 1 — Scenario tests

```bash
python3 -m pytest -q tests/test_ai_scenario_sanity.py
```

### Layer 2 — Focused AI/evaluator tests

```bash
python3 -m pytest -q tests/test_ai_tuning.py tests/test_ai_system_evaluator.py
```

### Layer 3 — Full suite and benchmark smoke

```bash
python3 -m pytest -q
```

When seed support exists, run multi-seed benchmark smoke before final report.

Suggested regression thresholds:

```text
illegal_action_rate == 0
average_decision_score not down > 3%
poor_blunder_rate not up > 5%
style_separability_score not down once established
multi-seed variance not materially worse
```

## 9. Recommended First Five Implementation Slices

1. **Slice 4.1:** Add AI scenario sanity test harness.
2. **Slice 4.2:** Prevent no-bet/free-check fold behavior across streets.
3. **Slice 4.3:** Add premium-hand obvious bad-play guards.
4. **Slice 4.4:** Define opponent archetype config.
5. **Slice 4.5:** Add preflop range behavior by archetype.

These slices should produce visible CLI opponent-quality improvements before deeper postflop work.

## 10. Source Links

- Awesome Poker AI curated list: https://github.com/PokerBotAI/awesome-poker-ai
- DeepStack: Expert-Level Artificial Intelligence in No-Limit Poker: https://arxiv.org/abs/1701.01724
- Libratus: Superhuman AI for heads-up no-limit poker: https://www.science.org/doi/10.1126/science.aao1733
- Poker player styles (TAG/LAG/Maniac/Calling Station/Nit): https://www.pokerology.com/poker/strategy/playing-styles/
- HUD metrics guide (VPIP/PFR/3-bet): https://deepfold.co/en/blog/hud-stats-guide
- Poker stats / HUD metrics guide: https://www.seekerstart.com/en/columns/poker-stats
