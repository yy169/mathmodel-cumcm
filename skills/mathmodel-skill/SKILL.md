---
name: mathmodel-skill
description: CUMCM、MCM/ICM和电工杯数学建模竞赛的端到端工作流。用于题面与附件审计、文献证据、模型路线确认、真实代码求解、稳健性、论文写作、合规和提交前审查。支持可恢复状态、Requirement/Claim门禁和增量重跑。
---

# mathmodel-skill

## 1. 最高原则

固定顺序：

> 题面与证据 → 路线确认 → 真实计算 → 科学验证 → 交付验证 → 写作 → 提交预检

禁止：

- 编造数据、文献、指标、图表或运行结果；
- 把方法存在当作原题完成；
- 把统计筛选第一名写成已证明全局最优；
- 把单调收缩的不动点、贪心前缀或"某邻域内无改进"写成全局最优；
- 用代理口径（对称压缩、降采样、粗档位、冻结的个体收益）的数字充当上报值或验收判据；
- 把题面原始目标（尤其是比值形式）静默重述为另一个更易求解的目标（如用最小规模代替最大比值），
  只凭"约束在最优处取等"就宣称二者等价，而不做严格证明或对真实候选集的数值对拍；
  暴力穷举对拍的 oracle 同样必须优化原目标，不能验证代理目标却当作验证了原目标；
- 未经显式映射就把置信水平、两类错误、功效、OC端点概率、后验区间或预测区间视为等价；
- 在`result_ready`前锁定摘要数字和完成性结论；
- 因PDF、图表或提交包存在而反推答案已经完成；
- 把并列最优写成唯一最优，或只在部分子问题做并列检查；
- 直接采用外部意见中未经本项目计算验证的具体数值。

## 2. 三种模式

| 模式 | 默认行为 |
|---|---|
| `economy` | 一轮必要检索；每问主模型+基线；小规模验证；不默认子代理；不写正式论文 |
| `standard` | 完整真实求解；一轮高影响稳健性；一次技术审查；一次正式制图；一次完整流水线 |
| `championship` | 仅在结果稳定后启用红队、评委视角、Claim全审计和逐页终审 |

默认`standard`。额度或时间敏感时主动建议`economy`，不得静默降级。

## 3. 每回合的最小加载

1. 优先运行：

```bash
python scripts/context_snapshot.py --project <cwd>
```

2. 默认不全文读取`state/decision_log.json`；只有权威结果迁移、回退、冲突或用户要求完整
   历史时才读取相关阶段或事件。
3. 只读取当前阶段的`references/stage_NN_*.md`。
4. 只在明确触发时读取专题reference；同一阶段形成摘要后不重复全文加载。
5. 脚本检查只把失败、阻断和矛盾项送入模型，不加载全部通过项。

## 4. 五级状态

```text
problem_ready → model_ready → result_ready → manuscript_ready → submission_ready
```

- `problem_ready`：原题交付项已拆解；阻断性语义已解决、分支或登记。
- `model_ready`：每个核心项有路线、验证和失败回退。
- `result_ready`：每个核心项有真实运行结果和验证证据。
- `manuscript_ready`：Requirement与Claim双向审计通过。
- `submission_ready`：答案、论文一致性和提交包均通过。

状态必须派生，禁止手写`submission_ready=true`替代上游门禁。

Stage 8以后优先使用单一入口，避免模型反复读取全部通过项：

```bash
python scripts/run_readiness_audit.py \
  --project <cwd> --output-dir <cwd>/reports/readiness
```

核心状态：

- `PASS`：模型、运行、证据和结论闭环；
- `PARTIAL`：方法存在但实例、验证或证据不足；
- `FAIL`：本应完成但尚未完成；
- `BLOCKED`：因缺数据、外部条件或核心语义无法唯一完成。

核心项存在`FAIL`时，禁止生成高质量final；允许形成诚实降级的应急包，但不得伪装完整。

## 5. 十阶段路由

阶段开始只读取对应协议：

| # | 阶段 | 协议 |
|---:|---|---|
| 0 | 启动与附件扫描 | `references/stage_00_kickoff.md` |
| 1 | 选题 | `references/stage_01_problem_selection.md` |
| 2 | 深度分析与拆解 | `references/stage_02_analysis.md` |
| 3 | 文献与模型选型 | `references/stage_03_model_selection.md` |
| 4 | 假设、符号、术语 | `references/stage_04_foundation.md` |
| 5 | 逐问求解 | `references/stage_05_subproblem_loop.md` |
| 6 | 稳健性 | `references/stage_06_robustness.md` |
| 7 | 评价与推广 | `references/stage_07_evaluation.md` |
| 8 | 论文写作 | `references/stage_08_writing.md` |
| 9 | 终审与提交 | `references/stage_09_review.md` |

使用`assets/workflow_manifest.json`和`scripts/workflow_manager.py`验证依赖、checkpoint和
最小重跑范围。代码变化后运行`scripts/build_code_manifest.py`。

## 6. 必要专题门禁

仅在对应条件触发：

| 条件 | 读取 |
|---|---|
| 开始写作或搭 paper_workspace 骨架前（CUMCM） | `competitions/cumcm/paper_writing.md` |
| 只有题面/部分文献 | `references/problem_only_literature_bootstrap.md` |
| 子问题交付物是被搜索出的设计/方案/子集 | `references/optimization_search_rigor.md` |
| 文献短名单形成 | `references/literature_quality_control.md` |
| 精确公式、参数、标准 | `references/fulltext_evidence_localization.md` |
| Stage 3锁路线 | `references/model_route_confirmation.md` |
| 图表证据缺口 | `references/figure_evidence_system.md` |
| 页数/证据密度问题 | `references/paper_depth_audit.md` |
| 正文完成度、强措辞或策略编码 | `references/manuscript_delivery_gates.md` |
| 信度/假设检验/OC/后验Monte Carlo语义 | `references/statistical_semantics_gate.md` |
| 多轮改稿且存在回退 | `references/revision_case_history.md` |
| 收到外部/其他模型的审稿意见 | `references/external_review_intake.md` |
| 评委视角结构重构 | `references/judge_view_restructuring.md` |
| 最终评分与停止判断 | `references/final_manuscript_calibration.md` |

文献检索调用`paper-search-pro`只发生在文献阶段或真实证据缺口出现时；不在每个子问题和
每轮改稿重复启动。技术稳定后才调用`sciwrite`；提交阶段才调用
`mathmodel-latex-skill`。

## 7. 人工确认边界

只有以下情况必须暂停：

- 不同解释会改变目标函数、状态空间、策略集合或关键数值；
- Stage 3主路线尚未批准；
- 新附件或高质量证据足以改变已批准路线；
- 将启动明显耗时的全量求解或完整重跑，而此前仅批准小规模验证。

题面能唯一推出时自动解决并登记。配色、措辞等纯观感问题不反复询问；但**排版规范属阻断项，不询问也不省略——一律按 `competitions/cumcm/paper_writing.md` 执行**（章节顺序、自动编号、图题表题、三线表、摘要与附录纪律等），排版不合规视同未完成。

## 8. 额度与重复运行纪律

- 标准模式默认不用子代理；只在核心争议或终稿独立红队时使用。
- 文献检索默认最多两轮，除非仍有高影响证据缺口。
- 先静态检查，再小规模验证，再决定全量求解。
- 关键图先预览；风格锁定后只生成一次正式图。
- 技术终审一次；完整流水线一次。失败后仅重跑受影响阶段。
- 章节按`draft → reconstructed → validated → frozen`推进；冻结后无新证据不做全局重写。
- 原始结果、长日志和通过项写入文件；对话只报告摘要和阻断项。
- Skill缺陷记录到独立维护任务，不在论文任务中边解题边重构Skill。

## 9. 论文与提交

摘要是结果索引，不是结果承诺。`result_ready`前只允许结构占位摘要。

正式图必须来自真实数据和代码；生成式图片只能承担非定量示意。

Stage 9先核对当届官方规则，再检查：

- 匿名、页数、大小；
- 引用和交叉引用；
- AI使用披露；
- 代码清单和支撑材料；
- 权威PDF路径与哈希；
- Requirement和Claim门禁。

当剩余问题只能依赖题面未提供的新数据、新仪器或独立实验解决时，明确停止继续润色。
