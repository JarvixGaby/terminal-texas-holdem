# AI Player Evaluation

Date: 2026-05-12

## Scope

本报告执行 `docs/plans/2026-05-12-ai-player-evaluation-plan.md` 中的 read-mostly 评估任务，目标是评估当前本地 Texas Hold'em trainer 内置 AI player 的稳定性、基础扑克合理性、profile/风格可分性、benchmark 健康度与 transcript public/private safety。

边界：本次只运行测试、benchmark 与安全检查，并生成报告；未修改 AI 行为代码，未启动 online/API/WebSocket/auth/platform 相关工作。

## Commands Run

1. Focused AI tests:

```bash
python3 -m pytest -q tests/test_ai_scenario_sanity.py tests/test_ai_profiles.py tests/test_ai_tuning.py tests/test_ai_metrics.py tests/test_ai_system_evaluator.py
```

Result: PASS, `79 passed in 5.72s`.

2. Smoke benchmark:

```bash
python3 - <<'PY'
from ai_system_evaluator import benchmark_ai_system
report = benchmark_ai_system(
    num_hands=100,
    player_count=4,
    starting_chips=10000,
    seed=0,
)
print(report.to_dict())
PY
```

Result: PASS/completed. Runtime was reasonable, so no reduction to 30 hands was needed.

3. Optional micro multi-seed benchmark:

```bash
python3 - <<'PY'
from ai_system_evaluator import benchmark_ai_system_multi_seed
report = benchmark_ai_system_multi_seed(
    seeds=[0, 1, 2],
    hands_per_seed=30,
    player_count=4,
    starting_chips=10000,
)
print(report)
PY
```

Result: PASS/completed.

## Automated Test Results

Focused AI correctness suite passed fully:

- `tests/test_ai_scenario_sanity.py`
- `tests/test_ai_profiles.py`
- `tests/test_ai_tuning.py`
- `tests/test_ai_metrics.py`
- `tests/test_ai_system_evaluator.py`

Summary: `79 passed in 5.72s`.

Interpretation: deterministic scenario sanity, profile behavior, tuning constraints, AI metrics, and evaluator coverage are currently stable enough to support this evaluation. No failing tests blocked benchmark interpretation.

## Smoke Benchmark Parameters

Fresh smoke benchmark parameters:

- `num_hands`: 100
- `player_count`: 4
- `starting_chips`: 10000
- `seed`: 0
- generated_at: `2026-05-12T12:42:56+00:00`

Optional multi-seed diagnostic parameters:

- `seeds`: `[0, 1, 2]`
- `hands_per_seed`: 30
- `player_count`: 4
- `starting_chips`: 10000
- generated_at: `2026-05-12T12:43:38+00:00`

## Metrics Summary

### Smoke benchmark headline metrics

| Metric | Value |
|---|---:|
| hands completed | 100 |
| total actions | 426 |
| illegal action rate | 0.0023474178 / 0.235% |
| average decision score | 70.5282 |
| style separability score | 0.0 |
| VPIP spread, profile-level | 0.0 |
| PFR spread, profile-level | 0.0 |
| aggression spread, profile-level | 0.0 |
| call-rate spread, profile-level | 0.0 |
| largest stack share | 0.446625 |
| stack gini | 0.3693 |
| bustout rate | 0.0 |
| hands until first bust | None |
| transcript sample count | 3 |
| errors | `[]` |

Grade distribution over 426 actions:

| Grade | Count | Share |
|---|---:|---:|
| excellent | 23 | 5.40% |
| good | 358 | 84.04% |
| questionable | 11 | 2.58% |
| poor | 33 | 7.75% |
| blunder | 1 | 0.23% |

Combined poor+blunder share: 34 / 426 = 7.98%.

### Per-player smoke metrics

| Player | VPIP | PFR | Aggression factor | Call rate | Fold rate | Showdown rate | Win rate | Poor/blunder rate | Avg decision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| AI-1 | 0.14 | 0.10 | 1.70 | 0.0971 | 0.6893 | 0.09 | 0.27 | 0.1262 | 68.1068 |
| AI-2 | 0.17 | 0.11 | 1.9091 | 0.0991 | 0.6126 | 0.09 | 0.30 | 0.0811 | 70.7207 |
| AI-3 | 0.08 | 0.08 | 6.50 | 0.0215 | 0.7849 | 0.09 | 0.27 | 0.0323 | 72.2043 |
| AI-4 | 0.14 | 0.12 | 1.5455 | 0.0924 | 0.6555 | 0.09 | 0.18 | 0.0756 | 71.1345 |

Per-player observed spreads in the smoke run:

- VPIP range: 0.08–0.17, spread 0.09.
- PFR range: 0.08–0.12, spread 0.04.
- Aggression factor range: 1.5455–6.50, spread 4.9545.
- Call-rate range: 0.0215–0.0991, spread 0.0776.

Important caveat: evaluator profile metrics grouped all players under `advanced`, so profile-level style separability and profile-level VPIP/PFR/aggression/call spreads were all 0.0. This means the smoke benchmark does not currently demonstrate cross-profile variety, even though individual players diverged somewhat within the run.

### Optional micro multi-seed diagnostic

Across seeds `[0, 1, 2]`, 30 hands each:

| Metric | Mean | Std | Min | Max |
|---|---:|---:|---:|---:|
| hands played | 30.0 | 0.0 | 30.0 | 30.0 |
| total actions | 119.6667 | 10.3387 | 110.0 | 134.0 |
| illegal action rate | 0.0 | 0.0 | 0.0 | 0.0 |
| average decision score | 70.0891 | 1.5969 | 68.2273 | 72.1269 |
| style separability score | 0.0 | 0.0 | 0.0 | 0.0 |
| VPIP spread | 0.0 | 0.0 | 0.0 | 0.0 |
| PFR spread | 0.0 | 0.0 | 0.0 | 0.0 |
| aggression spread | 0.0 | 0.0 | 0.0 | 0.0 |
| call-rate spread | 0.0 | 0.0 | 0.0 | 0.0 |
| largest stack share | 0.3576 | 0.0659 | 0.27435 | 0.43545 |
| bustout rate | 0.0 | 0.0 | 0.0 | 0.0 |
| stack gini | 0.1591 | 0.0953 | 0.03635 | 0.26875 |

The micro run was clean for illegal actions, but remains diagnostic only due to small sample size.

## Transcript Safety Check

Smoke benchmark returned 3 transcript samples. The samples include public hand flow such as hand number, streets, public actions, board cards, result, and limited flags.

Safety findings:

- No sample text contained the explicit unsafe tokens `deck`, `opponent_hole_cards`, `private_ai_internals`, or `unsafe_seed`.
- Fold-only samples did not expose private hole cards.
- One showdown sample exposed folded players' private hole cards in the showdown text. This is a public/private safety issue for report/public transcript usage because folded/non-contesting players' private cards should not be revealed in public transcript samples, even when the hand reaches showdown.
- This report intentionally does not reproduce hidden deck order or non-showdown/folded private card values.

Conclusion: transcript samples are partially usable for aggregate/qualitative review, but public transcript publishing should be gated or sanitized until folded-player private-card leakage in showdown sample text is corrected.

## Qualitative Assessment

整体看，当前 AI 对本地 terminal trainer 已具备基础练习价值：focused tests 全部通过，100-hand smoke benchmark 完成且没有 crash/errors，绝大多数动作被 evaluator 评为 `good` 或 `excellent`，平均决策分约 70.5。multi-seed micro 也显示小样本下 average decision score 稳定在约 68–72 区间。

主要不足有三点：

1. **Legality signal mixed**: 100-hand smoke 出现 1 次 illegal action 计数，illegal action rate 约 0.235%。虽然 benchmark 没有崩溃且 micro multi-seed 为 0.0，但对于 AI action legality 来说仍应视为 must-fix/triage 信号。
2. **Style separability not demonstrated**: profile-level `style_separability_score`、VPIP/PFR/aggression/call spreads 全为 0.0，且 `profile_metrics` 只出现 `advanced`。这说明当前 benchmark 配置或 profile assignment 没有证明多风格 opponent 体验。
3. **Transcript safety needs hardening**: benchmark sample 有 folded private cards leakage 风险，不能直接作为 public-safe transcript artifact 发布。

Player-facing value: 作为本地训练陪练，当前 AI 可以提供稳定的基础对局与一定决策质量；但还不能宣称强对抗、多风格体验成熟，或 transcript 已满足严格 public/private 发布标准。

## Recommended Next Tuning Slices

### Must-fix

- Triage smoke benchmark 中的 1 次 illegal action：定位 action type、street、stack/bet context，并补充回归测试，目标是 benchmark illegal action rate 回到 0.0。
- 修复或屏蔽 transcript 中 folded/non-contesting players private-card exposure；public report/sample 只应展示公开信息与合法 showdown reveal。

### Should-improve

- 调整 benchmark player profile setup，使 4-player runs 能覆盖不同 profiles，并让 `style_separability_score` 与 profile-level VPIP/PFR/aggression/call spreads 有实际含义。
- 增加 style separability 的 targeted scenario/metric tests，避免所有 profile 被折叠为同一个 `advanced` group。
- 对 poor/blunder actions 做抽样审计，优先检查 premium-hand、pot-odds/call、river large-bet、short-stack all-in 等高影响 spot。

### Later

- 扩大 benchmark 至更多 hands/seeds，用 confidence interval 或 run-to-run variance 观察 stack concentration、bustout rate、win-rate stability。
- 加入更多 player-facing qualitative fixtures，例如 tight/aggressive/loose/passive opponent feel checks。
- 在不改变核心规则合同的前提下，改进 benchmark artifact 输出，使安全摘要、aggregate metrics 与 sample transcript 分离。

## Follow-up Fix Pass

Date: 2026-05-12

After user approval, the must-fix items from this report were executed with focused regression tests first.

### Changes made

- Decision evaluator now treats a below-minimum raise as legal when it is exactly the short stack player's all-in total, matching the action validator's accepted short-stack all-in raise path.
- Benchmark transcript generation now excludes players who folded from showdown hole-card reveals, preventing folded/non-contesting private card exposure in public transcript samples.
- Headless AI-only benchmark runs now assign distinct default archetype profiles to the four built-in AI players instead of grouping every player under `advanced`.

### Regression tests added

- `tests/test_decision_evaluator.py::test_short_stack_all_in_raise_below_minimum_is_not_illegal`
- `tests/test_ai_system_evaluator.py::test_showdown_transcript_excludes_folded_players_private_cards`
- `tests/test_headless_simulation.py::test_run_ai_only_simulation_assigns_distinct_default_ai_profiles`

### Verification after fixes

Focused/full test validation:

```bash
python3 -m pytest -q tests/test_decision_evaluator.py tests/test_ai_system_evaluator.py tests/test_headless_simulation.py tests/test_ai_scenario_sanity.py tests/test_ai_profiles.py tests/test_ai_tuning.py tests/test_ai_metrics.py
```

Result: PASS, `121 passed in 15.75s`.

Full suite:

```bash
python3 -m pytest -q
```

Result: PASS, `247 passed in 33.04s`.

Fresh 100-hand smoke benchmark after fixes:

| Metric | Value |
|---|---:|
| hands completed | 100 |
| total actions | 524 |
| illegal action rate | 0.0 |
| average decision score | 72.3855 |
| style separability score | 0.2568 |
| VPIP spread, profile-level | 0.17 |
| PFR spread, profile-level | 0.14 |
| aggression spread, profile-level | 1.1682 |
| call-rate spread, profile-level | 0.1784 |
| errors | `[]` |

Profile groups in the fresh smoke run: `calling_station`, `loose_aggressive`, `nit`, `tight_aggressive`.

Fresh micro multi-seed benchmark after fixes, seeds `[0, 1, 2]`, 30 hands each:

| Metric | Mean | Std | Min | Max |
|---|---:|---:|---:|---:|
| hands played | 30.0 | 0.0 | 30.0 | 30.0 |
| total actions | 142.3333 | 15.1731 | 121.0 | 155.0 |
| illegal action rate | 0.0 | 0.0 | 0.0 | 0.0 |
| average decision score | 70.9279 | 0.6826 | 70.0 | 71.6225 |
| style separability score | 0.2907 | 0.0548 | 0.2254 | 0.3594 |
| VPIP spread | 0.1778 | 0.0416 | 0.1333 | 0.2333 |
| PFR spread | 0.1111 | 0.0157 | 0.1 | 0.1333 |
| aggression spread | 2.6111 | 1.0915 | 1.3333 | 4.0 |
| call-rate spread | 0.1787 | 0.0902 | 0.0968 | 0.3043 |

Conclusion after follow-up: the previously observed smoke-run illegal-action signal is resolved in the fresh benchmark, transcript samples no longer reveal folded players' private cards in showdown text, and benchmark profile metrics now demonstrate non-zero style separability across distinct AI archetypes.

## Non-Claims

This evaluation does not claim:

- GTO correctness or solver validation.
- Real-money readiness.
- Online-platform certification.
- Exhaustive poker strategy quality.
- Full public/private safety certification beyond the transcript samples inspected in this run.
- Long-run win-rate or exploitability guarantees from the 100-hand smoke and 3-seed micro benchmark.
