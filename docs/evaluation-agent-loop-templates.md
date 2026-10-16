# Phase 3 Evaluation Agent Loop Templates

Date: 2026-05-16

## Purpose

These lightweight templates define how future AI evaluation cycles should turn benchmark evidence into scoped decisions without drifting into platform work, broad AI rewrites, or unsupported improvement claims.

Use these templates after running or reviewing a benchmark artifact. A complete review loop requires Benchmark Agent, Poker Quality Reviewer, Safety/Contract Agent, and Coordinator outputs. When creating or tuning a candidate AI Player, extend the loop with a Builder Agent and a Hacker Agent: Builder creates a contract-safe candidate, then Hacker tries to exploit it using only public decision-time information plus the acting seat's private hand.

## Shared guardrails

Every role must preserve these constraints:

- No online rooms, public WebSocket/API surfaces, auth/accounts, or external-agent runtime implementation in Phase 3.
- No real-money or solver/GTO claims.
- No AI policy tuning without a named evidence class and a regression target.
- No AI policy or evaluator calibration change is accepted without a fixture-backed public-information target, a public/private safety verdict, artifact evidence, commands run, explicit non-goals preserved, and a pre/post benchmark comparison plan or result.
- No benchmark-threshold weakening to hide warnings.
- No public/private schema changes unless safety tests and reports are updated.
- Every output must list artifacts reviewed and commands run, or explicitly say none were run.

## Builder Agent output template

Use when creating or tuning a candidate AI Player. Builder produces the player candidate; it does not claim strength without benchmark artifacts.

```markdown
## Builder Agent Output

**Candidate:**
- name:
- version:
- provider class / selection hook:
- base profile / strategy family:

**Files changed:**
- `[path]`

**Contract compliance:**
- Decision boundary: `DecisionProvider.decide(GameStateSnapshot) -> ActionResponse`
- Validator path preserved:
- Public/private state respected:
- JSON-safe metadata:

**Strategy summary:**
- [public-state-only strategy description]

**Tests added/updated:**
- provider contract:
- legality/fallback:
- public/private safety:
- deterministic poker spot fixtures using public decision-time information:
- benchmark smoke:

**Benchmark artifact(s):**
- `[path]`

**Pre/post benchmark comparison:**
- before artifact:
- after artifact:
- compared metric/class target:

**Key metrics:**
- illegal action rate:
- errors:
- average decision score:
- poor/blunder rate:
- transcript safety:

**Known weaknesses / Hacker targets:**
1. [target]
2. [target]
3. [target]

**Safety/contract verdict:**
- public/private state safety:
- metadata/transcript safety:
- validator path preserved:

**Explicit non-goals preserved:**
- no online/API/WebSocket/auth
- no real-money or solver/GTO claim
- no benchmark threshold weakening
```

## Hacker Agent output template

Use after Builder output or after a benchmark artifact. Hacker is an adversarial evaluator: it looks for exploitable patterns, safety/contract leaks, and benchmark/report weaknesses. It must not use hidden information to win; if hidden information is visible, report it as a safety exploit.

```markdown
## Hacker Agent Output

**Target reviewed:**
- AI/player version:
- Artifact(s) reviewed:
- Commands run:

**Attack scope:**
- [strategy exploit / safety-contract exploit / benchmark exploit]

**Public-information compliance:**
- Used only public decision-time information:
- Used acting-seat private hand only where appropriate:
- Hidden/private information observed:

**Exploit summary:**
1. [Exploit name]
   - Type: strategy / safety / benchmark
   - Severity: critical / high / medium / low
   - Affected profile(s):
   - Phase:
   - Public trigger:
   - Exploit action:
   - Expected victim behavior:
   - Evidence:
   - Reproducibility:
   - Impact:
   - Suggested regression target:
   - Suggested Builder fix:

**Exploit metrics:**
- win-rate delta if measured:
- chip EV proxy if measured:
- poor/blunder class count:
- profile concentration:
- seed concentration:
- before/after comparison if available:

**Safety findings:**
- private-card leak:
- deck/future-card leak:
- unsafe metadata:
- illegal action / invalid amount behavior:
- JSON serialization issue:
- timeout/fallback issue:

**Benchmark/report findings:**
- protocol mismatch:
- missing gate metadata:
- threshold weakening:
- insufficient seeds/hands:
- unsafe transcript sample:
- unsupported claim:

**Recommended next action:**
- [block / add focused fixture / run focused slice / rerun benchmark / send to Builder / defer]

**Builder handoff:**
- Minimal failing scenario using public decision-time information:
- Proposed test name:
- Files likely involved:
- Do not modify:
- Verification command:
```

## Benchmark Agent output template

```markdown
## Benchmark Agent Output

**Artifact(s) reviewed:**
- `[path]`

**Protocol:**
- seeds:
- hands per seed:
- player count:
- starting chips:
- AI equity simulations:

**Gate status:**
- Primary/reduced:
- Overall status:
- Expected deviations:

**Key metrics:**
- illegal action rate:
- errors:
- average decision score:
- poor/blunder share:
- blunder share:
- style separability:
- profile calibration status:

**Outlier seeds / profiles:**
- [seed/profile + evidence]

**Recommended next action:**
- [pass / rerun / inspect / block / defer]
```

## Poker Quality Reviewer output template

```markdown
## Poker Quality Reviewer Output

**Artifact(s) reviewed:**
- `[path]`

**Poor/blunder sample count:**
- total:

**Top classes:**
1. [class] — [count] — [policy defect / evaluator defect / needs split]
2. [class] — [count] — [policy defect / evaluator defect / needs split]
3. [class] — [count] — [policy defect / evaluator defect / needs split]

**Representative public examples:**
- [hand/profile/phase/action/grade/risk tags only; no hidden cards]

**Regression targets:**
- [targeted public-information test or fixture to add before tuning]

**Public/private safety verdict:**
- public-only fields used:
- acting-seat private hand used only where appropriate:
- hidden/private fields excluded:

**Do not tune yet:**
- [classes needing more evidence or safety gating]
```

## Safety/Contract Agent output template

```markdown
## Safety/Contract Agent Output

**Artifact(s) reviewed:**
- `[path]`

**Schema/policy version:**
- public transcript schema:
- showdown reveal policy:

**Safety checks:**
- transcript sample forbidden tokens:
- poor/blunder sample forbidden tokens:
- folded/non-showdown private-card reveal:
- hostile-fixture coverage:

**Blocked claims or surfaces:**
- [claims/surfaces blocked until tests/evidence exist]

**Recommended next action:**
- [pass / add tests / block report publication / defer]
```

## Coordinator decision template

```markdown
## Coordinator Decision

**Inputs:**
- Builder Agent, when candidate/tuning cycle:
- Benchmark Agent:
- Hacker Agent, when adversarial review is in scope:
- Poker Quality Reviewer:
- Safety/Contract Agent:

**Decision:**
- [pass / run focused slice / rerun benchmark / defer / block]

**Rationale:**
- [evidence-based reason]

**Allowed next slice:**
- [name, regression target, verification command]

**Acceptance requirements for policy/evaluator changes:**
- fixture-backed public-information target:
- public/private safety verdict:
- artifacts reviewed:
- commands run:
- pre/post benchmark comparison:

**Explicit non-goals preserved:**
- [platform/API/runtime/tuning items intentionally not done]

**Required verification before claiming improvement:**
- focused tests:
- full suite:
- before artifact:
- after artifact:
```
