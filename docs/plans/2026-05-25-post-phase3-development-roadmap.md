# Post-Phase-3 Development Roadmap

Date: 2026-05-25

## 北极星 / 产品愿景

本项目的长期方向是从本地 Texas Hold'em terminal trainer 演进为 **AI Poker Arena / Agent Poker Platform**：

- 近期：先把本地终端训练器、内置 AI、手牌审计、benchmark evidence、public/private safety 做扎实。
- 中期：形成可重复的 AI 评价闭环，让 Builder/Hacker/Evaluator 风格的 agent loop 能基于证据改进 AI，而不是靠主观感觉调参。
- 后期：在 headless/action-driven engine 边界稳定后，再为用户自带或外部 AI agent 定义 contract、SDK、受控 runtime。
- 最后：只有在本地评价、安全、契约和 engine readiness 都通过 gate 后，才进入在线房间、WebSocket、auth、多人平台等工作。

核心判断：平台可信度来自可复现的扑克质量、风格校准、合法行动、安全可见性和清晰边界；不能先做在线外壳再补证据。

## 当前状态摘要

截至 2026-05-25，项目仍是 Python 终端 Texas Hold'em trainer，但已经具备未来平台化所需的一部分本地基础：

- Phase 2 contract-hardening 已完成并文档化：public/private state visibility、benchmark gates、DecisionProvider/ActionValidator/Event 边界、external-agent request/response stub、platform non-goals 都已存在。
- Phase 3 AI Evaluation Loop 已完成到 Stage 3.5：
  - Stage 3.1：canonical primary `10 seeds x 500 hands` benchmark gate 在 practical local execution profile 下可运行；preflop-fold evaluator calibration 后记录为 clean `PASS`。
  - Stage 3.2：profile target-band calibration fields 已加入；reduced `10 seeds x 100 hands` 诊断 gate `PASS`，但 calibration status 跨 seeds 为 `WARN`，说明多个 profile 仍偏紧或参与率偏低。
  - Stage 3.3：benchmark artifact 已能输出 sanitized poor/blunder audit samples；主要诊断类是 pot-odds call mistake、overfold、low-equity bluff。
  - Stage 3.4：public transcript schema、showdown reveal policy、transcript/audit sample safety gate 已加入。
  - Stage 3.5：evaluation-agent role templates 已建立，并完成一次 artifact-review loop。
- Stage 3.5 后续已经完成 pot-odds audit split：用 public equity-vs-pot-odds evidence 将 `pot-odds call mistake` 分成 true negative-equity call、evaluator false-positive candidate、insufficient public context。
- Calling-station negative-equity call tuning 已完成一个目标驱动 Builder/Hacker loop：reduced artifact 从 pot-odds call samples `33 -> 6`，calling-station concentration `23 -> 2`；最终 reduced target 达成，full suite 在报告中记录为 `279 passed`。这只能支持“目标诊断类的 evaluator/policy consistency 改善”，不能夸大为 broad poker strength improvement。

当前最重要的约束没有变化：继续优先证据、边界、安全、评价闭环；不要直接跳到 online rooms / WebSocket / auth / external-agent runtime。

## 头脑风暴池

### AI 质量与风格校准

- 对剩余 `true_negative_equity_call`、`overfold`、`low-equity bluff` 做公开信息审计，确认是 AI policy defect、evaluator artifact，还是 variance。
- 把 profile calibration WARN 拆成命名 slice，例如 TAG/LAG 参与率不足、nit aggression 偏高、calling-station call-rate/fold-rate 偏离。
- 用 pre/post benchmark artifact 固化每次 tuning 的证据，不改 benchmark threshold 来“解决”问题。
- 建立 Builder/Hacker loop：Builder 提交候选策略改动，Hacker 用公开信息寻找可复现 exploit，Evaluator 只接受可回归的公共决策时模式。

### 对局 / 手牌审计与解释

- 扩展 poor/blunder audit payload 的公开上下文，帮助 reviewer 判断错误类型，但不暴露 hole cards、deck、private AI internals。
- 为 terminal learner 提供更清晰的 hand-end review：最差决策、风险标签、下一手训练重点。
- 建立 artifact-to-report 的稳定格式，让 benchmark 结果能被人类快速扫读。
- 区分“AI 调优解释”和“用户训练解释”：前者面向工程证据，后者面向安全、谨慎、可理解的训练反馈。

### Headless Engine / Action API

- 继续把 headless simulation 和 terminal game loop 的 action path 对齐，减少 `game.py` 中终端输出、状态 mutation、benchmark 逻辑混杂。
- 明确 action-driven engine 的最小 contract：public snapshot、legal actions、action response、validated action、engine events、history/evaluation side effects。
- 为未来 adapter 保留边界，但近期只做本地 headless/terminal 验证，不暴露公网 API。
- 用 deterministic headless harness 验证同一 action sequence 的事件、历史、评价一致性。

### 外部 Agent Contract / SDK 前置

- 先冻结 schema 文档和 serialization tests，再写 SDK。
- 明确 request/response versioning、timeout、invalid action fallback、seat-scoped visibility、private reasoning policy。
- 建立 contract fixture corpus：fold-only、showdown、all-in、side-pot、early-winner、validation failure。
- 外部 agent 只能在受控、本地、无网络依赖的 contract test harness 里先行验证；真实 runtime 是后期 gate 后的事项。

### 在线房间平台前置

- 平台前置不是立即实现 WebSocket/auth，而是定义进入平台阶段的 gate。
- 需要确认 engine action API 稳定、public/private safety primary/repeated evidence 稳定、external-agent schema version 可测试。
- 在线房间初期只应考虑 play-money / simulation / evaluation，不涉及 real-money、solver/GTO claim、公开排行榜强度 claim。
- Web UI、account、auth、matchmaking、persistent room server 都应等到本地平台 gate 通过后再进入 active plan。

### 用户训练体验

- 基于已有 hand coach 和 training center，把 benchmark/evaluator 发现转化为人类训练 focus。
- terminal UX 保持可信、克制：不给过度确定的 GTO 结论，不展示不该知道的隐藏信息。
- 增加 session-level review：本局主要 leak、下次训练 checklist、可复盘手牌。
- 未来可考虑 replay/audit view，但先用本地 CLI 和 Markdown/JSON report 保持低复杂度。

### 数据 / 持久化

- 目前 runtime persistence 仍使用项目根目录 JSON 和 SQLite，出于兼容性暂不移动。
- 后续可以先文档化 canonical data shape，再考虑 SQLite canonicalization 或 runtime data migration。
- benchmark artifacts 和 historical reports 不应被重写；新增报告要有日期和明确协议。
- 长期需要区分 runtime user data、benchmark evidence、fixture corpus、stable docs。

### 可视化 / 报告

- 短期优先 Markdown + machine-readable JSON artifact 的一致性。
- 可增加 profile calibration trend、poor/blunder class trend、public/private safety status、gate summary 的人类可读报告。
- 后期再考虑 dashboard；不要为了 dashboard 提前引入 Web 平台复杂度。
- 报告必须标清 protocol：primary `10 x 500`、reduced `10 x 100`、smoke，避免把诊断结果当正式 gate。

## 阶段化路线图

### Phase A：证据闭环巩固

**目标：** 用现有 Phase 3 artifact 继续做小而可证的 AI/evaluator/safety 闭环，形成“发现 -> 分类 -> focused fixture -> 最小改动 -> pre/post artifact”的节奏。

**为什么现在：** Phase 3 已有 primary/reduced benchmark、audit samples、safety gates 和 role templates；继续巩固证据闭环的边际收益高。

**为什么不现在做平台：** 当前仍有 profile calibration WARN，且 broad AI strength 不能从单个 reduced tuning target 推导出来。平台化会放大任何评估口径和隐私边界缺口。

**交付物：**

- Post-Phase-3 evidence-loop active slices。
- 对剩余 poor/blunder classes 的 public-context triage report。
- 至少一个 Builder/Hacker candidate-loop 报告模板或执行报告。
- 必要时新增 focused fixtures 和 post-tuning artifact，但只针对共享公开决策时模式。

**验收标准：**

- 每次 tuning 前都有可命名 error class 和 public decision-time evidence。
- 每次 tuning 后有 focused tests、相关 tests、full suite 或明确降级说明，以及 pre/post benchmark comparison。
- 不改变 benchmark threshold 来制造通过。
- 不引入 online/API/WebSocket/auth/external runtime。

**不要做的事：**

- 不做 WebSocket room server。
- 不做 external-agent runtime。
- 不做用户账号、auth、matchmaking。
- 不把 reduced artifact 解释成 primary long-run strength claim。

**风险：**

- 过度针对 reduced artifact 过拟合。
- evaluator artifact 被误当作 AI policy defect。
- profile identity 被质量修复抹平。

### Phase B：用户训练与审计体验增强

**目标：** 把评价闭环产出的证据转化为本地训练者可理解、可复盘、不会泄露隐藏信息的 terminal / report 体验。

**为什么现在：** 在证据闭环稳定后，用户体验可以用已验证的 evaluator/audit payload 支撑，而不是新增主观建议。

**为什么不现在：** 如果先做体验，容易把未校准 evaluator 输出包装成权威建议。

**交付物：**

- Session-level training review。
- Hand audit summary 的人类可读视图。
- Profile opponent notes，说明风格和观察到的行为差异。
- Report command recipes 和 artifact summary consistency checks。

**验收标准：**

- 所有用户可见反馈只使用合法公开信息或玩家自己的信息。
- 反馈措辞避免 GTO/solver/real-money claim。
- Terminal UX 不被大段报告阻塞；长报告进入 docs/reports 或 replay/audit view。

**不要做的事：**

- 不把 hidden opponent cards 用于用户实时建议。
- 不把 benchmark 内部 private reasoning 暴露给 terminal learner。
- 不做大规模 UI 重写。

**风险：**

- UX 文案过度自信。
- 训练建议和 benchmark evaluator 口径不一致。
- `game.py` 继续变大，增加后续 engine 分离成本。

### Phase C：Headless / Action-Driven Engine Readiness

**目标：** 让 terminal、headless simulation、未来 adapter 共享更清晰的 action/validation/event/history 边界。

**为什么现在：** 只有在本地 action-driven 边界稳定后，外部 agent 和在线 adapter 才能少返工。

**为什么不现在：** Phase A/B 中仍可能发现 evaluator/action metadata 需要补字段；过早冻结 API 可能锁住错误边界。

**交付物：**

- Headless action harness plan。
- Action sequence fixture corpus。
- Event/history/evaluation parity checks。
- `game.py` 中高风险终端耦合点的 inventory 和小 slice 分离计划。

**验收标准：**

- 同一 action sequence 在 headless 与 terminal-adjacent path 中产生一致合法结果。
- `DecisionProvider` / `ActionValidator` 继续是行动合法性边界。
- Public/private snapshot contract 不倒退。

**不要做的事：**

- 不做大型 `game.py` 重写。
- 不改变 canonical hand evaluator semantics。
- 不移动 runtime data paths。

**风险：**

- 边界重构触碰投注流程、历史 schema、AI 行为，导致回归面扩大。
- 事件和历史双写期间出现不一致。

### Phase D：受控 External Agent Contract / SDK 前置

**目标：** 在本地、受控、可测试的前提下，为未来外部 agent 入桌定义 contract、fixtures、SDK skeleton。

**为什么现在：** 只有 Phase C 的 action API 和 Phase A 的 safety evidence 稳定后，contract 才有意义。

**为什么不现在：** 当前 external-agent 仍应停留在 stub 和 serialization safety 层；真实 runtime 会带来 timeout、resource isolation、private state leakage 和 invalid action complexity。

**交付物：**

- External-agent contract v0.x 文档更新。
- Request/response JSON fixture corpus。
- Local contract test harness。
- SDK skeleton 只覆盖 schema validation 和 sample response，不执行真实 agent runtime。

**验收标准：**

- Contract tests 覆盖 fold-only、showdown、all-in、side-pot、early winner、validation failure。
- 所有 fixture 均通过 forbidden private-state scan。
- Invalid/timeout response 明确走 `ActionValidator` safe fallback。

**不要做的事：**

- 不运行不可信外部代码。
- 不做网络 API。
- 不做长期 agent registry、auth、账号系统。

**风险：**

- SDK 过早承诺稳定 API。
- schema versioning 不清晰导致后续平台兼容负担。
- 外部 agent 作者误以为当前已可在线入桌。

### Phase E：本地 Agent Arena 原型

**目标：** 在没有公网房间的情况下，让多个内置或 contract-fixture agent 在本地 arena 中对局、评估和生成报告。

**为什么现在：** 这是进入真实平台前的最后本地验证层，能测试多 agent、长跑 benchmark、public/private safety 和 action contract。

**为什么不现在：** 如果 Phase D 的 contract 未稳定，本地 arena 会变成临时 glue code。

**交付物：**

- Local arena runner。
- Agent roster/config。
- Match report：legality、profile metrics、poor/blunder audit、safety gate、action timeout/invalid count。
- Public replay transcript sample。

**验收标准：**

- Arena 不依赖网络、auth、账号。
- 所有 agent 行动经 `ActionValidator`。
- Safety gate 覆盖 public transcript 和 audit samples。

**不要做的事：**

- 不做多人在线。
- 不做排行榜强度 claim。
- 不做 real-money 或 solver/GTO claim。

**风险：**

- 本地 arena 和 benchmark runner 职责重叠。
- 报告协议过多，维护成本上升。

### Phase F：在线 / 多人平台准备与受控试点

**目标：** 在所有前置 gate 满足后，才设计在线 room、WebSocket、auth、user-agent runtime 的最小受控试点。

**为什么现在：** 仅当前置 gate 已通过时才进入；否则不进入。

**为什么不现在：** 当前项目仍在 post-Phase-3 本地证据巩固期，直接做平台会把未稳定问题公开化。

**交付物：**

- Platform architecture decision record。
- Threat model：hidden state, untrusted agent, timeout, abuse, persistence, observability。
- Minimal room protocol design。
- Auth/account non-goals 或 selected minimal scope。
- Read-only spectator / replay 优先级评估。

**验收标准：**

- 连续 primary/repeated evidence 满足进入 gate。
- External-agent contract v0.x 在 local harness 和 local arena 中稳定。
- Headless/action engine readiness report 通过。
- Maintainer 明确选择平台 slice。

**不要做的事：**

- 不在 gate 前写 WebSocket server。
- 不在 gate 前引入 auth/account complexity。
- 不支持 real-money。
- 不声称 solver/GTO/公开排行榜强度。

**风险：**

- 平台基础设施吞噬 AI/evaluator 质量工作。
- 网络和用户系统带来安全、合规、运维复杂度。
- 外部 agent runtime 资源隔离不足。

## 可执行近期计划

### Slice 1：Post-Phase-3 evidence baseline inventory

**目标：** 汇总 Phase 3 到 2026-05-22 的 primary/reduced artifacts、gate status、诊断类和推荐后续，建立下一轮执行的证据清单。

**可能触达文件：**

- `docs/reports/2026-05-13-phase3-primary-benchmark-preflop-fold-calibration.md`
- `docs/reports/2026-05-16-phase3-profile-calibration-target-bands.md`
- `docs/reports/2026-05-16-phase3-poor-blunder-audit.md`
- `docs/reports/2026-05-16-phase3-public-private-safety-gate.md`
- `docs/reports/2026-05-16-phase3-evaluation-agent-loop.md`
- `docs/reports/2026-05-22-phase3-pot-odds-audit-split.md`
- `docs/reports/2026-05-22-phase3-calling-station-negative-equity-call-tuning.md`
- 可新增：`docs/reports/YYYY-MM-DD-post-phase3-evidence-baseline-inventory.md`
- 更新：`docs/index.md`

**测试 / 验证命令：**

```bash
python3 - <<'PY'
from pathlib import Path
required = [
    'docs/reports/2026-05-13-phase3-primary-benchmark-preflop-fold-calibration.md',
    'docs/reports/2026-05-16-phase3-profile-calibration-target-bands.md',
    'docs/reports/2026-05-16-phase3-poor-blunder-audit.md',
    'docs/reports/2026-05-22-phase3-calling-station-negative-equity-call-tuning.md',
]
missing = [p for p in required if not Path(p).exists()]
if missing:
    raise SystemExit(f'missing evidence docs: {missing}')
print('evidence docs present')
PY
```

**验收标准：**

- Inventory 区分 primary evidence、reduced diagnostic evidence、post-tuning evidence。
- 明确哪些结论可作为 gate claim，哪些只是 tuning clue。
- 新增稳定报告加入 `docs/index.md`。

### Slice 2：Remaining poor/blunder public-context triage

**目标：** 基于最新 post-tuning artifact，审计剩余 `true_negative_equity_call`、`overfold`、`low-equity bluff` 是否存在共享公开决策时模式。

**可能触达文件：**

- 读取：`docs/reports/2026-05-22-phase3-calling-station-negative-equity-call-tuning-benchmark.json`
- 读取：`ai_system_evaluator.py` 仅理解 artifact shape，不做代码改动除非后续 slice 明确需要。
- 可新增：`docs/reports/YYYY-MM-DD-post-phase3-remaining-poor-blunder-triage.md`
- 更新：`docs/index.md`

**测试 / 验证命令：**

```bash
python3 - <<'PY'
import json
from collections import Counter
from pathlib import Path
artifact = json.loads(Path('docs/reports/2026-05-22-phase3-calling-station-negative-equity-call-tuning-benchmark.json').read_text())
classes = Counter()
splits = Counter()
profiles = Counter()
for run in artifact.get('runs', []):
    for sample in run.get('poor_blunder_samples', []):
        classes[sample.get('classification')] += 1
        if sample.get('audit_split'):
            splits[sample.get('audit_split')] += 1
        profiles[sample.get('profile')] += 1
print('classes', dict(classes))
print('splits', dict(splits))
print('profiles', dict(profiles))
PY
```

**验收标准：**

- 报告列出剩余样本的 class/profile/street/action pattern。
- 对每个候选 tuning 点给出 verdict：`policy fixture candidate`、`evaluator calibration candidate`、`variance/watchlist`、`insufficient public context`。
- 没有共享公开决策时模式时，不建议代码调优。

### Slice 3：Builder/Hacker candidate loop template refresh

**目标：** 把 Stage 3.5 evaluation-agent templates 升级为 post-Phase-3 候选改动闭环：Builder 只能提交 contract-safe 候选，Hacker 只能基于 public information 给出可复现 exploit，Coordinator 只接受 fixture-backed 工作。

**可能触达文件：**

- `docs/evaluation-agent-loop-templates.md`
- 可新增：`docs/reports/YYYY-MM-DD-post-phase3-builder-hacker-loop-dry-run.md`
- 更新：`docs/index.md`

**测试 / 验证命令：**

```bash
python3 - <<'PY'
from pathlib import Path
text = Path('docs/evaluation-agent-loop-templates.md').read_text()
required = ['Benchmark Agent', 'Poker Quality Reviewer', 'Safety/Contract Agent', 'Coordinator']
missing = [item for item in required if item not in text]
if missing:
    raise SystemExit(f'missing template roles: {missing}')
print('agent loop templates present')
PY
```

**验收标准：**

- 模板明确要求 artifacts reviewed、commands run、non-goals preserved、public/private safety verdict。
- Builder/Hacker 输出不能直接要求 broad tuning；必须给出 fixture target 或 defer。
- 如果新增报告，必须索引。

### Slice 4：Profile calibration WARN prioritization

**目标：** 将 Stage 3.2 calibration WARN 拆成可执行优先级，不立即调参。

**可能触达文件：**

- `docs/reports/2026-05-16-phase3-profile-calibration-target-bands.md`
- `docs/reports/2026-05-16-phase3-profile-calibration-reduced-benchmark.json`
- 可新增：`docs/reports/YYYY-MM-DD-profile-calibration-warn-prioritization.md`
- 更新：`docs/index.md`

**测试 / 验证命令：**

```bash
python3 - <<'PY'
import json
from pathlib import Path
artifact = json.loads(Path('docs/reports/2026-05-16-phase3-profile-calibration-reduced-benchmark.json').read_text())
statuses = []
for run in artifact.get('runs', []):
    statuses.append(run.get('profile_calibration_status'))
print('profile_calibration_statuses', statuses)
if not statuses:
    raise SystemExit('no profile calibration statuses found')
PY
```

**验收标准：**

- 每个 WARN 被归为：style fidelity issue、quality issue、metric definition issue、sample-size issue。
- 不改变 target bands 和 gate thresholds。
- 产出下一步候选 slice，而不是直接改 AI policy。

### Slice 5：Headless/action API readiness inventory

**目标：** 只做 inventory，识别从本地 trainer 到 future adapter 所需的 action-driven engine 缺口。

**可能触达文件：**

- `docs/architecture/decision-action-event-boundaries.md`
- `docs/architecture/external-agent-contract-stub.md`
- `headless_simulation.py`
- `decision_provider.py`
- `action_validator.py`
- `engine_events.py`
- `game.py` 只读 inventory
- 可新增：`docs/reports/YYYY-MM-DD-headless-action-api-readiness-inventory.md`
- 更新：`docs/index.md`

**测试 / 验证命令：**

```bash
python3 -m pytest -q tests/test_decision_provider.py tests/test_action_validator.py tests/test_headless_simulation.py
```

**验收标准：**

- Inventory 明确当前可复用 contract、缺口、不可碰边界。
- 不提出大型 `game.py` 重写作为下一步。
- 后续实现 slice 必须小于一个独立 action/API contract improvement。

## 决策 Gate

### 继续留在本地评价闭环的条件

满足任一条件，就继续留在本地评价闭环，不进入平台实现：

- Profile calibration 仍有未解释 WARN，且缺少 public-context triage。
- Poor/blunder top class 没有完成 evidence split。
- 最新 tuning 只有 reduced diagnostic artifact，没有 repeated primary evidence。
- Public/private safety gate 只在样本层通过，未覆盖相关新 payload。
- Headless/action path 仍依赖终端副作用或没有 action-sequence parity evidence。
- External-agent contract 只有文档 stub，没有 fixture corpus 和 local validation harness。

### 允许进入 external-agent runtime 前的 gate

必须全部满足：

- Public/private state serialization tests 和 transcript/audit safety gates 覆盖主要 hand outcomes。
- External-agent request/response schema version 固定为 v0.x，并有 JSON fixtures。
- Invalid action、timeout、malformed response 都明确通过 `ActionValidator` fallback。
- Local contract harness 能在无网络、无不可信代码执行的模式下验证 sample agents。
- Maintainer 明确选择 external-agent runtime slice。

### 允许进入平台 / WebSocket / Auth 前的 gate

必须全部满足：

- 至少一次 post-Phase-3 primary `10 x 500` 或更高协议 benchmark gate clean `PASS`，并且关键 safety/profile/poker-quality gates 无未解释回归。
- Headless/action-driven engine readiness inventory 完成，且最小 action API contract 已由 focused tests 保护。
- Local agent arena 或等价本地 harness 证明多 agent/action contract 可以长期运行。
- Platform non-goals 仍明确：no real-money、no solver/GTO claim、no public leaderboard strength claim without protocol。
- Threat model / architecture decision record 写入并索引。
- Maintainer 明确授权平台 slice。

## 推荐下一步

当前推荐先执行第一批 slice，不进入在线平台：

1. **Slice 1：Post-Phase-3 evidence baseline inventory**，先把已有 evidence 和 claim 边界收齐。
2. **Slice 2：Remaining poor/blunder public-context triage**，决定是否还有值得调优的共享公开决策时模式。
3. **Slice 3：Builder/Hacker candidate loop template refresh**，让后续 AI 改动都经过 fixture-backed candidate loop。

这三项完成后，再决定是否进入 profile calibration WARN prioritization 或 headless/action API readiness inventory。平台/WebSocket/auth/external-agent runtime 不应进入当前 active plan。
