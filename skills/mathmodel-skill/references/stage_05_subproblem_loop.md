---
stage: 5
name: subproblem_loop
duration_h: 6-12 per Qi
inputs:
  - "stage.2.subproblem_cards"
  - "stage.3.selected_per_subproblem"
  - "stage.4.{assumptions, symbols}"
outputs:
  - "stage.5.sub_problems.{Qi}.{model_name, math_formulation_path, code_path, results_path, figures, key_metrics, physical_meaning_summary, scores, issues, iterations}"
  - "stage.5.cross_reference_chain"
  - "stage.5.assumption_change_history"
  - "results/code_manifest.json"
  - "paper_workspace/code_appendix.md"
loads_reference: ["references/model_catalog.md", "references/figure_evidence_system.md", "competitions/<comp>/winning_patterns.md§5", "references/rubrics.md§Stage_5", "references/optimization_search_rigor.md (当 Qi 交付物是被搜索出的设计/方案/子集)"]
loads_template: ["templates/shared/code_starter/<problem_type>.py"]
feedback: ["L1_per_Qi", "sub_checkpoint", "L2_at_end_for_stage_3_4_consistency"]
next: stage_06_robustness
---

# Stage 5 — 递归子问题循环 (Q1..Qn)

**时长预算**: 6-12h × n 个子问题 | **反馈层**: L1 + 子检查点

---

## 目标

为每个子问题 Qi 跑一遍完整的 mini-pipeline: **建模 → 求解 → 子结果分析 → 必要的子灵敏度**。子问题间只有在题面、数学接口或业务机制提供依据时才建立复用链；不存在合理依赖时保留独立结构并记录理由。这是论文的主体, 也是最容易翻车的阶段。

---

## 输入

- stage 2 子问题卡片
- stage 3 选定模型 + toy demo 通过
- stage 4 假设/符号/术语
- (进入存在依赖的 Qi 时) 已验证的上游结果

## 产出

- 每 Qi 的: 数学模型完整公式 + 求解代码 + 可复现结果 + 支撑关键论点所需的图/表 + 物理意义讨论
- 跨子问题: 有依据的依赖显式传递；无依赖时显式记录独立理由
- 写入 `decision_log.stages.5.sub_problems.{Q1, Q2, Q3, ...}`

---

## 递归循环结构

```
for Qi in [Q1, Q2, ..., Qn]:
    A. 模型完整化 (45 min)
    B. 求解实现 (2-4h)
    C. 结果验证 (30 min)
    D. 有证据需要时做子灵敏度
    E. 物理意义 (15 min)
    F. L1 自评 + 必要时 diff-only 精修
    G. 输出移交 (写 decision_log)
    H. 子检查点: Qi 的依赖/独立理由是否成立? 符号是否与 stage 4 一致?
```

---

## 单 Qi 操作流程详解

### A. 模型完整化 (45 min)

把 stage 2 的目标雏形 + stage 3 的已选模型, 升级为正式数学公式:

```
问题 Qi 数学模型 (<与实际实现一致的模型名>):

Decision Variables:
  x_i ∈ X_i, i ∈ I

Parameters:
  p_i: 单价 (元/件), 来自附件 1 列 P
  c_i: 成本 (元/件), 来自附件 1 列 C
  B: 总预算 (元), 来自 <题面/附件/配置路径>

Objective:
  max f(x) = Σ_i (p_i - c_i) x_i

Constraints:
  C1: Σ_i c_i x_i ≤ B              (预算约束)
  C2: l_i ≤ x_i ≤ u_i              (由题面/数据确定的边界)
  C3: x_i ∈ X_i                    (变量域)
```

要求:
- 每个变量、参数、约束都有编号
- 公式用 LaTeX (即使现在是 markdown, stage 8 直接复制)
- 声称的松弛、复合或自适应机制必须出现在公式与代码中，并在结果中提供可核验证据；否则使用标准模型名

### B. 求解实现 (2-4h)

用 Python (numpy/scipy/sklearn/cvxpy) 实现。**约定**:

```python
"""
Q1 求解 - 对应论文 §5.1
<与 stage 3 和公式一致的模型名称>
"""
import numpy as np
import pandas as pd
import cvxpy as cp
import matplotlib.pyplot as plt
import json
np.random.seed(42)  # 可复现性

# Step 1: 加载数据
df = pd.read_excel("data/附件1.xlsx")
with open("config/problem.json", encoding="utf-8") as fh:
    config = json.load(fh)
p = df["price"].values
c = df["cost"].values
n = len(p)
B = float(config["budget"])
lower = df["lower_bound"].values
upper = df["upper_bound"].values

# Step 2: 建模
x = cp.Variable(n, integer=True)
profit = (p - c) @ x
constraints = [
    cp.sum(c * x) <= B,
    x >= lower,
    x <= upper
]
prob = cp.Problem(cp.Maximize(profit), constraints)

# Step 3: 求解
prob.solve(solver=cp.GLPK_MI)
print(f"Q1 求解状态: {prob.status}")
print(f"目标函数值: {prob.value:.2f}")
print(f"求解时间: {prob.solver_stats.solve_time:.2f} s")

# Step 4: 保存结果
x_star = x.value.astype(int)
np.save("results/Q1_x.npy", x_star)
```

代码要求:
- 中文注释 (anti_pattern D1)
- 首行明确 "对应论文 §X" (`competitions/<comp>/winning_patterns.md` §10)
- 设 random seed (anti_pattern D4)
- `print` 关键状态 (sanity check)
- 结果保存到 `results/Qi_*.npy` 或 `.csv`

### C. 结果验证 (30 min)

四步 sanity check (anti_pattern D2/D3):

1. **状态检查**: `prob.status == "optimal"` ?
2. **数量级**: 结果是否满足题面/数据给出的边界与单位?
3. **边界 case**: 对该模型最关键的边界输入，输出是否符合可独立推导的预期?
4. **与基线对比**: 和一个满足同一约束的简单基线比较；若同目标下反而更差，先排查模型与求解器。

```python
# 共享同一份剩余预算的可行贪心基线
x_greedy = lower.astype(int).copy()
remaining = float(B - c @ x_greedy)
assert remaining >= -1e-8, "题面下界已超过预算，需回查数据或模型"
margin = p - c
order = np.argsort(-np.divide(
    margin, c, out=np.full_like(margin, -np.inf, dtype=float), where=c > 0
))
for i in order:
    if c[i] <= 0 or margin[i] <= 0:
        continue
    capacity = max(0, int(upper[i] - x_greedy[i]))
    addition = min(capacity, int(max(remaining, 0) // c[i]))
    x_greedy[i] += addition
    remaining -= addition * c[i]

assert c @ x_greedy <= B + 1e-8
profit_greedy = ((p - c) * x_greedy).sum()
print(f"贪心基线利润: {profit_greedy:.2f}")
print(f"本模型利润: {prob.value:.2f}")
if abs(profit_greedy) > 1e-12:
    print(f"相对变化: {(prob.value - profit_greedy) / abs(profit_greedy) * 100:.2f}%")
else:
    print("贪心基线为 0，不报告百分比")
```

不通过任一项 → 回 A 检查模型。

### C.1 搜索类子问题的附加门禁 ⭐

**触发判据**（满足任一即触发，不需要更多理由）:

- 本 Qi 的交付物是一个**被搜索出来的设计/方案/子集**（设计参数、选址、选型、取舍、排产、布局、分配）；
- 目标函数是**比值**形式（单位成本产出、性价比），或约束在最优处取等；
- 个体收益 `g_i` 的计算里出现了**其他个体**（互相遮挡、竞争、共享容量、排队干扰）。

触发后读取 `references/optimization_search_rigor.md`，本阶段至少完成其 §1–§6（含 §1.5）：

1. **题面符号逐条对账**（§1）——唯一能发现题意误读的检查，其余自检在题意读错时全部会通过；
2. **目标函数台账**（§1.5）⭐——题面原始目标（尤其是比值形式）与代码实际优化的目标并排列出；
   不是同一表达式时必须登记 `EQUIVALENT_BY_PROOF`（附证明）或 `PROXY_UNVERIFIED`
   （必须在真实候选集上对拍原目标与代理目标，不能只靠"约束在最优处取等"这类直觉论证）；
   **暴力穷举对拍的 oracle 必须优化原目标，不能也优化同一个代理目标**；
3. **决策变量审计**（§2）——题面明文列为设计对象的每个变量登记为
   `SEARCHED / FIXED_BY_PROOF / FIXED_BY_HEURISTIC / GIVEN`，
   每个 `FIXED_BY_HEURISTIC` 必须做反方向探针；
4. **"精确最优"分档**（§3）——排序取前缀的成立条件按成本是否相等、收益是否耦合分三档措辞；
5. **耦合则迭代到不动点**（§4）——识别信号是"上报值明显高于预测值"；不动点不得写成全局最优；
6. **代理口径以验收口径收口**（§6）——搜索判据 ≡ 验收判据；档位一致写成硬断言。

C.1 的产出写入 `decision_log.stages.5.sub_problems.{Qi}.search_rigor`:

```json
{
  "triggered": true,
  "symbol_reconciliation": "12/12 通过 | 见 reports/symbol_check.md",
  "objective_ledger": "原目标 max E/A s.t. E>=E0；代码目标 min A s.t. E>=E0；PROXY_UNVERIFIED -> 已用真实候选集对拍 exact_select_ratio，选出集合一致",
  "decision_variable_ledger": "results/decision_variable_audit.md",
  "heuristic_probes": [{"var": "z0", "probe": "{2.81,3.2,3.6,4.0}", "verdict": "原取值最优，但原理由错误，已重写"}],
  "optimality_tier": "各单元成本相等 → 0-1 精确最优 | 成本不等冻结收益 → 分组枚举精确 | 耦合 → 逐轮精确自洽稳定",
  "fixed_point_trace": "results/{Qi}_select_trace.json",
  "proxy_closure": "搜索直接用验收口径 | 代理前提未被搜索破坏（附证据）"
}
```

**未触发时**也要显式记录 `{"triggered": false, "reason": "..."}`，不允许静默跳过。

### C.2 验证类型台账：自检不能支撑 PASS ⭐

**规则**：验证分三类，**只有第三类能支撑 `PASS`**。每个 Qi 收尾时必须把本问做过的验证
按类型分栏列出，不允许把一堆自检堆在一起当作"已充分验证"。

| 类型 | 举例 | 能证明什么 | 可支撑的最高状态 |
|---|---|---|---|
| **内部自洽** | 收敛曲线、守恒量、单调性、不动点、求解器 status、断言未报错 | 代码在按设计者的想法运行 | `PARTIAL` |
| **结构性断言** | 计数守恒（进 N 个出 N 个）、增量累加 vs 全量重算的漂移、可行性恒等式、量纲 | 该次运行没有破坏结构不变量 | `PARTIAL`（必需但不充分） |
| **独立方法对拍** | 原理不同的第二套算法重算同一个量；外部权威结果比对 | 收敛到的值是对的 | `PASS` |

**为什么必须分栏**：内部自洽检验在**内核本身错**时**全部会通过**，因为它们与内核共享同一套
逻辑和同一个错误前提。这与 §0 总纲、`optimization_search_rigor.md` §12 是同一条道理，
只是这次自洽的对象是"验证体系本身"。

**触发**：所有 Qi，无一例外。不因问题简单而豁免。

**硬门**：

1. **每个 Qi 至少有一个核心量完成过独立方法对拍**，否则该 Qi 只能标 `PARTIAL`，
   不得标 `PASS`，也不得据此进入 `result_ready`。
2. 必须显式回答一句：**"本问哪个核心量至今只有一套实现？"**
   答案非空时，该量上的一切结论只能写成"在本实现下"，不得写成客观事实。
3. **本门在该 Qi 收尾时执行，不得推迟到 Stage 6/9。** 错误产生于分析轮次之间，
   把门放到交付前意味着错误已经污染了下游全部工作。

**对拍的第二套算法怎么选**：原理必须不同，不能只是"换个写法"。可用方向——

- 精确 vs 枚举（子集 DP ↔ 候选枚举 + 组合构造）；
- 解析 vs 数值（闭式 ↔ 蒙特卡罗 / 数值求积）；
- 增量 vs 全量（增量累加 ↔ 从零重算）；
- 自建 vs 外部（自写求解器 ↔ 成熟库 / 题面附件给出的参考值）。

第二套算法**允许慢几个数量级**，它只承担对拍，不承担主算法。无法全覆盖时，分层抽样若干
实例 + 若干极端情形，报告逐例差值的最大值、非零个数与**符号分布**（同号占压倒多数即为
系统偏差而非随机误差，必须定位机理，见 §12）。

**两个反面案例**（真实项目，全部自检通过而结论错误）：

- 某搜索型 Qi 目标值一路下降、收敛曲线正常、无任何报错，实际解中数百对个体互相重叠——
  自检问的是"目标有没有下降"，而它确实在下降，只是在一个物理上不存在的解上下降。
  真正抓出问题的是**计数守恒断言**与**增量 vs 全量重算的漂移断言**。
- 某核心几何量全程只有一套实现，下游全部结论依赖它。若该实现存在系统偏差，
  除附件比对外的所有自检都会显示通过。补一套原理不同的实现逐例对拍后方可采信。

产出写入 `decision_log.stages.5.sub_problems.{Qi}.verification_ledger`:

```json
{
  "internal_consistency": ["收敛曲线单调", "求解器 status=optimal", "量纲检查通过"],
  "structural_assertions": ["个体计数 N 进 N 出", "增量累加 vs 全量重算漂移 0.0"],
  "independent_crosscheck": [
    {"quantity": "核心几何量", "method_a": "子集 DP",
     "method_b": "候选点枚举 + 最小生成树",
     "n_cases": 140, "max_abs_diff": 0, "nonzero": 0, "sign_split": "0/140/0",
     "evidence": "results/crosscheck.csv"}
  ],
  "single_implementation_quantities": [],
  "verdict": "PASS"
}
```

`single_implementation_quantities` 非空时 `verdict` 不得为 `PASS`。

### D. 子灵敏度 (按需)

只对本子问题中会影响结论、且存在测量误差、估计误差或情景不确定性的参数做局部灵敏度 (全局留 stage 6)。扰动范围来自数据精度、置信区间、规则边界或领域证据；若没有有意义的不确定参数，记录理由并跳过，不生成装饰性曲线:

```python
# documented_deltas 来自测量精度、估计区间或领域证据
deltas = documented_deltas
profits = []
for d in deltas:
    p_perturb = p * (1 + d)
    # 重新求解
    profit_d = (p_perturb - c) @ x_star  # 用同一 x*, 看新参数下利润
    profits.append(profit_d)

plt.plot(deltas, profits, 'o-')
plt.xlabel("p 扰动比例")
plt.ylabel("利润 (元)")
plt.title("Q1 子灵敏度: 单价扰动")
plt.savefig("figures/Q1_sensitivity.png", dpi=300)
```

### E. 物理意义讨论 (15 min)

围绕题面所问的含义解释结果，并把每个判断绑定到保存的产物；以下是占位结构，不得把示意数字复制进论文:

```
求解状态与主结果: <从 results/Qi_* 自动读取，不手填>。
关键结构: <哪些变量/群组驱动结果>；证据: <表、图或诊断路径>。
机制解释: <由约束、参数或数据支持的解释>；不确定部分明确标注。
基线比较: <仅在目标、约束和数据相同且可公平比较时报告实际差异>。
结论边界: <哪些假设或数据变化会使解释失效>。
```

### E.1 图表候选与溯源登记

读取 `figure_evidence_system.md`。本 Qi 的结果稳定后，不等待 Stage 8 才考虑图表：

1. 列出能够支持基线、主结果、消融、诊断、稳健性或负面结论的候选图；
2. 每张图绑定一个命名主张和真实结果路径；
3. 定量图标记为 A 级程序制图，结构示意图标记为 B 级确定性重绘；
4. 只有非定量说明需求才允许 C 级生成式图像；
5. 更新 `reports/figure_evidence_map.md` 和 `results/figure_provenance.json`；
6. 本阶段可以生成预览，不得在结果未冻结时把候选图视为正式图。

向用户报告最关键的候选图及其证据用途。若用户上传了满意样式，先记录风格校准，不直接
复制参考图。

### F. L1 自评 + diff-only 精修

调用 `references/feedback_layer1_critic.md` 协议:
- 输出 5 维 JSON 评分
- 保留该 Qi 的完整 `issues`；任一未解决 `severity=high` 立即将聚合 verdict 置为 `block`，分数不能覆盖高严重度问题
- 修复后的 issue 移入事件历史并附验证证据；传给聚合器的 `issues` 只保留当前未解决项，不能直接丢弃来绕过 block
- 若任一维 <7 → diff-only 精修, iter+=1, 上限 3
- 全维 ≥9 → 早退

### G. 输出移交

写入 `decision_log.stages.5.sub_problems.Q1`:
```json
{
  "model_name": "...",
  "math_formulation_path": "results/Q1_model.tex",
  "code_path": "results/Q1_solve.py",
  "results_path": "results/Q1_x.npy",
  "figures": ["<only figures that support a named claim>"],
  "figure_evidence_map": "reports/figure_evidence_map.md",
  "figure_provenance_path": "results/figure_provenance.json",
  "key_metrics": {"<metric_name>": "<value loaded from saved result>"},
  "physical_meaning_summary": "...",
  "scores": {...},
  "issues": [
    {"severity": "high|medium|low", "where": "...", "problem": "...", "fix": "..."}
  ],
  "iterations": 1
}
```

### G.1 更新代码清单与附录

本 Qi 代码稳定后运行：

```bash
python <skill>/scripts/build_code_manifest.py --project <cwd>
```

阶段结束前再运行一次`--check`，确认代码清单没有陈旧。写入：

- `decision_log.stages.5.code_manifest_path`
- `decision_log.stages.5.code_appendix_path`
- `decision_log.execution.code_manifest_path`
- `decision_log.execution.code_appendix_path`

代码清单不能替代真实运行和结果验证。

### H. 子检查点 (跨 Qi 后)

进入 Qi+1 之前,**自检**:

1. **复用链**: Q2 是否要用 Q1 的 x_star?
   - 题目要求? → 必须用
   - 题目允许? → 只有在依赖关系有数学或业务依据时复用，并记录理由
   - 题目禁止? → 跳过

2. **符号一致**: Qi 中用的 x, p, c 是否与 stage 4 符号表一致?
   - 不一致 → 立即更新本 Qi 或更新符号表 (二选一并记录)

3. **假设一致**: Qi 模型是否引入了新假设?
   - 是 → 回 stage 4 加假设, 写入 decision_log
   - 否则 → 继续

4. **假设变更历史检查** (P2-3 新增) ⭐: 若 stage 4 的某假设在已完成 Qi 之后被 patch (L2 触发), 自检该 Qi 是否依赖被改假设。
   - **依赖** → 重跑该 Qi 的 Step C (sanity check) + Step D (子灵敏度), 不重跑完整 5 步
   - **不依赖** → 在 `decision_log.stages.5.assumption_change_history` 标记 "Qi 不受 patch X 影响, 跳过重跑"
   - 检查方法: 读 `decision_log.events.log` 找 `type=L2_backtrack` 且 `target=stage.4.assumptions[k]` 的记录, 然后 grep Qi 的代码与 math_formulation 是否引用 assumption k

---

## L1 Rubric (Per-Qi)

| 维度 | 满分行为 |
|------|---------|
| 1. 模型与问题契合 | 目标/变量/约束 与题面 1:1 |
| 2. 数学严谨性 | 符号一致, 推导无跳跃 |
| 3. 求解正确性 | 代码运行 + sanity check 通过 |
| 4. 结果表达 | 每个关键论点有最合适的图、表或数值证据；不重复、不凑数量 |
| 5. 物理意义讨论 | 解释与结果证据绑定；baseline 仅在公平可比时使用 |

## L1 Rubric (Stage-level)

| 维度 | 满分行为 |
|------|---------|
| 1. 子问题完整性 | 所有 Qi 都跑完 |
| 2. 依赖链 | 有依据的上下游接口均显式传递；无合理依赖时理由已记录 |
| 3. 符号一致 | 全 Qi 用同一套 stage 4 符号 |
| 4. 证据表达 | 图、表与数值产物足以支持关键论点且无装饰性重复 |
| 5. 时间预算 | 在已确认的 stage 5 预算内完成；偏差已留痕并获用户确认 |

## 常见坑

- D1-D5 求解类全部 → Step B/C 严格执行
- D6-D13 搜索与最优性类 → Step C.1 门禁 + `references/optimization_search_rigor.md`
- E1-E4 结果分析类 → Step E 物理意义必写
- G1 子问题各做各 → Step H 子检查点强制
- G2 子问题模型族突变 → 切换需在 H 显式记录触发条件

## H.2 per-Qi 差异化降级机制 (v3.0 新增)

整体均分可能掩盖单个 Qi 的薄弱项。新协议保留每个 Qi 的分数与 issues，并引入 per-Qi 加权聚合 + 差异化降级；任何未解决 high issue 优先 block:

### 聚合规则

```python
# 加载 decision_log.stages.5.qi_weights (默认 [1.0]*qi_count)
qi_results = [
    {"qi": "Q1", "min": 8, "mean": 8.5, "scores": {...}, "issues": []},
    {"qi": "Q2", "min": 7, "mean": 7.2, "scores": {...}, "issues": [...]},
    {"qi": "Q3", "min": 8, "mean": 8.8, "scores": {...}, "issues": []}
]
qi_weights = decision_log.stages.5.qi_weights  # e.g. [1.0, 1.5, 1.0] 若 Q2 是题目核心

weighted_mean = Σ(qi.mean × weight) / Σ(weight)
weighted_min  = min(qi.min for qi in qi_results)

# issue gate 优先于任何分数 verdict
high_issues = [
    {"qi": qi["qi"], **issue}
    for qi in qi_results
    for issue in qi["issues"]
    if issue.get("severity") == "high"
]
if high_issues:
    verdict = "block"
    # 停止聚合放行，保存 high_issues 并请求用户处理
else:
    # Qi 状态判定 (单 Qi 独立)
    for qi in qi_results:
        if qi["min"] >= 7 and qi["mean"] >= 8: qi["status"] = "pass"
        elif qi["min"] >= 7:                    qi["status"] = "mark_for_review"
        else:                                    qi["status"] = "refine"
```

### Verdict 决策

| 场景 | verdict | 后续 |
|------|---------|------|
| 任一 Qi 有未解决 high issue | `block` | 保存 issues 并暂停；不得由高分、平均分或 carryover 覆盖 |
| 全 Qi pass + weighted_min ≥ 9 + weighted_mean ≥ 9 | `pass_early` | iter-1 早退 |
| 全 Qi pass + weighted_min ≥ 7 + weighted_mean ≥ 8 | `pass` | 进 stage 6 |
| 无 refine 且任 Qi 为 mark_for_review，且加权阈值满足 | `pass_with_review` | 进 stage 6, **L2 必读 review_qis** (写入 stage 5 末尾的 L2 触发条件) |
| 仅部分 Qi 为 refine，至少一个 Qi 非 refine | `refine_partial` | **只 refine 低分 Qi**, 不动其他已验证 Qi |
| 全部 Qi 都为 refine | `refine` | 整体回到 Step A-G，优先排查共享模型、数据或假设问题 |
| 无 refine，仅有 mark_for_review 但 weighted_mean < 8 | `refine` | 对薄弱内容做 stage-level 修补 |

### 示例

`Q2 mean=7.2 min=7` (mark_for_review) + Q1/Q3 都 pass + weighted_mean=8.2:
- verdict = `pass_with_review`, review_qis = ["Q2"]
- decision_log.stages.5.qi_status = {"Q1": "pass", "Q2": "mark_for_review", "Q3": "pass"}
- L2 在 stage 5 末尾必读 Q2 段, 检查"是否需要 stage 6 顺便重跑 Q2 灵敏度"

`Q2 min=5` (refine) + Q1/Q3 都 pass:
- verdict = `refine_partial`, refine_qis = ["Q2"]
- 只重跑 Q2 的 Step A-G; Q1/Q3 的已验证产物保持不动
- iter+=1 仅对 Q2; 老 iter cap 3 仍生效。仅低分且无 high issue 时可按既有协议 carryover；high issue 永不 carryover

全部 Qi 都低于 per-Qi 门槛:
- verdict = `refine`，不是 `refine_partial`
- 整体检查共享数据处理、符号、假设和模型接口，再重跑受共同原因影响的 Step A-G

### 调用脚本 + verdict 问答确认 (v5 Friendly Mode)

```bash
# 在所有 Qi 跑完 per-Qi critic 后, agent 自动触发 (用户不必敲):
python <skill>/scripts/score_artifact.py \
  --mode aggregate_qi \
  --qi-results state/qi_results.json \
  --decision-log state/decision_log.json
# qi_results.json schema: {qi_results: [{qi, min, mean, scores, issues}], qi_weights: [...]}
# 输出并写入 state: {verdict, weighted_min, weighted_mean, qi_status, block_qis, review_qis, refine_qis}
# 完整 issue 对象仍保留在各 qi_results 与 decision_log 中
```

脚本出 `verdict` 后，先应用 high-issue gate。若 verdict=`block`，保存完整 issues 并停止放行，以编号问答让用户选择处理方式；不得提供“强制 carryover”选项:

```
【Stage 5 已阻断: <Qi> 存在未解决 high issue】

  1) 按 issue.fix 修复并重跑受影响 Qi (推荐)
  2) 回退到 issue 指向的上游阶段重新决策
  3) 暂停并保留当前可恢复状态

回复数字。
```

非 block verdict 再由 agent **问用户一次**确认 (Claude Code: AskUserQuestion; Codex CLI: 编号列表):

```
【Stage 5 聚合完成: verdict=refine_partial, Q2 需 refine, Q1/Q3 已 pass】

  1) 按推荐 refine Q2 (重跑 Q2 Step A-G, Q1/Q3 不动, 耗时按当前预算估算)
  2) 全 stage refine (含 Q1/Q3, 耗时按当前预算估算)
  3) 强制 carryover, 接受当前结果进 stage 6 (Q2 弱点留 stage 9 panel 处理)
  4) 让我决定 (推荐 1)

回复数字。
```

用户回复后 agent 自动执行, **不要**让用户编辑 decision_log 或重跑脚本。

### qi_weights 调整时机

默认 `[1.0] * qi_count` 由 stage 1 锁题后初始化。用户可在 stage 5 第一个 Qi 完成时根据题目重要性调整 (e.g., `[1.0, 1.5, 1.0]` 若 Q2 是核心)。调整后写回 `decision_log.stages.5.qi_weights`, 后续聚合按新权重。

---

## 退出条件 (整个 stage 5)

1. 所有 Qi 通过 per-Qi rubric (全维 ≥7) **或** verdict ∈ {pass, pass_with_review} 经 H.2 聚合
2. Stage-level rubric 全维 ≥7
2.5. 每个 Qi 的 `search_rigor` 字段已写入（触发时 §1–§6 全部完成；未触发时已记录理由）
2.6. 每个 Qi 的 `verification_ledger` 字段已写入（C.2）：三类验证分栏列出，
   **至少一个核心量完成独立方法对拍**；`single_implementation_quantities` 非空的 Qi
   一律标 `PARTIAL`，不得计入本阶段通过
3. 所有有依据的依赖链已实现并验证；不存在合理依赖时已有明确记录
4. (championship) red-team 一次,针对最弱的 Qi (优先 review_qis)
5. 触发 L2: 跨阶段回检 stage 3 (模型选择前提是否被结果推翻) + stage 4 (符号一致性) + **review_qis 列表 (若 verdict=pass_with_review)**

→ 跳转 `stage_06_robustness.md`

---

## 与 stage 6/8 的衔接

stage 6 全局灵敏度需要本节的求解器代码 (重用)。
stage 8 写论文 §5 直接基于本节产出, 每 Qi 一个小节。
