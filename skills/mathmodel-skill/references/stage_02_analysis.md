---
stage: 2
name: analysis
duration_h: 2-3
inputs:
  - "stage.1.selected"
  - "problem_pdf"
  - "attachment_data_paths"
outputs:
  - "stage.2.{data_sanity, decomposition, key_variables, key_constraints, objective_per_subproblem, data_schema, subproblem_dependency}"
loads_reference:
  - "references/rubrics.md§Stage_2"
  - "references/problem_only_literature_bootstrap.md"
  - "references/literature_quality_control.md"
  - "references/fulltext_evidence_localization.md"
feedback: ["L1"]
next: stage_03_model_selection
---

# Stage 2 — 问题深度解析与分解

**时长**: 2-3h | **反馈层**: L1

---

## 目标

把题目从**自然语言描述**转化为**数学语言骨架**: 识别决策变量、目标函数、约束、子问题间关系。这一步质量决定后续 5/6/8 阶段的天花板。

---

## 输入

- stage 1 输出: 选定题号 + 子问题清单 + 数据路径
- 题目原文 (再读一次)
- 附件数据 (先跑 Step 0 体检，再看 schema)

## 产出

- **附件体检结论 + 每条问题的处理决定与理由** (Step 0 产出，直接进论文数据预处理小节)
- 子问题分解树 (全部 Qi 的输入/输出/约束/目标)
- 关键变量清单 (覆盖实际模型所需变量并标注决策/状态/参数；不设凑数下限)
- 子问题间关联图 (谁依赖谁的结果)
- 目标函数雏形 (符号级,不必精确)
- 数据 schema 与变量映射

---

## 操作流程

### Step 0: 附件体检 (15 min，有附件就必须做)

在读题和建模之前先跑一遍，**因为体检结果会改变后面的建模选择**。典型例子：附件表面上是 1082 条独立样本，体检后发现只来自 267 个个体，那么 Stage 3 就不能选普通回归。

```bash
python scripts/sanity_check.py "<附件目录>/*.xlsx" -o <项目>/state/sanity
```

`sanity_check.py` 回答三个问题：

1. **有没有物理上讲不通的数字** —— 靠表头的词和单位判断。`反射率 (%)` 说明这列只能落在 0~100；浓度、质量、时长不能为负；概率必须在 0~1。
2. **自变量轴是否单调、等间隔** —— 步长不均匀时，插值、求导、FFT、积分都会静默出错，必须先重采样。
3. **多个附件的轴是否对齐** —— 决定能直接按行合并，还是要先插值到统一网格。

对**结构复杂的多表数据**（同一主体多次出现、跨表主键、大量缺失），另跑 `audit_data.py`
（带 `-p 题面` 可做题面-数据对账，抓"题面写的范围和附件给的数据对不上"）。
两表以内、列数很少的科学测量数据不必跑，`sanity_check.py` 就够。

**关键纪律：脚本只报告，不改数**。每一条发现都要留下"怎么处理 + 为什么"：

| 发现 | 处理方式 | 理由 |
|---|---|---|
| 附件2 有 262 个反射率 > 100% | 截断至 100 | 反射率超过 100% 无物理意义，判定为仪器基线漂移；占比 3.5%，截断前后主结论不变（见灵敏度分析） |

这张表最后原样进论文的数据预处理小节。**评委扣分不是扣你删了数据，是扣你删了不说为什么。**

先查题面有没有解释异常值——题面解释过就保留并引用（如 2025C 明确写了 X 染色体浓度可能为负），没解释才按异常处理。

### Step 1: 题目精读 (30 min)

**精读三遍,每遍不同任务:**

第一遍 (10 min): 抓动词。题目让你做什么? "求最优..." / "预测..." / "评价..." → 决定问题类型。

第二遍 (10 min): 抓约束。哪些条件不能违反? 列出来。

第三遍 (10 min): 抓数据接口。哪些参数题目会给? 哪些要从附件提? 哪些要假设?

### Step 2: 子问题正式分解 (45 min)

对每个 sub-problem Qi,填写卡片:

```
Q1 卡片
├── 自然语言描述: <一句话提炼>
├── 输入:
│   - 题目给定参数: ...
│   - 附件数据: 附件 1 第 X 列
│   - 上游问题结果: 无 (Q1 是入口)
├── 输出 (最终决策变量):
│   - x_1, x_2, ... (含义、单位)
├── 约束:
│   - C1: ...
│   - C2: ...
├── 目标:
│   - 最小化/最大化 <什么>
├── 问题类型: <model_catalog 第几类>
└── 难度估计: easy / medium / hard
```

**关键**: 每张 Qi 卡片的“上游依赖”列必须明确写依赖哪些结果。只有题面、数学接口或业务机制支持时才建立依赖；“题目未禁止”不构成复用证据。没有合理依赖时写“无”，并保留理由。

### Step 3: 关键变量统一编号 (30 min)

跨子问题统一符号 (anti_pattern B4: 符号重复定义):

```
全局变量表 (stage 4 会复制到论文)

| 符号 | 含义 | 单位 | 类型 | 出现于 |
|------|-----|------|------|-------|
| x_i | 第 i 个产品的产量 | 件 | 决策变量 | Q1, Q2 |
| p_i | 第 i 个产品的单价 | 元/件 | 参数 (附件 1) | Q1, Q3 |
| α  | 折扣率 | 无量纲 | 参数 | Q3 |
| ξ  | 需求随机扰动 | 件 | 随机变量 | Q3 |
| ... |
```

只收录在目标、约束、数据映射或验证中实际使用的变量；缺少必要变量要补齐，无用途变量要删除。

### Step 4: 数据 schema 扫描 (30 min)

用 pandas 快速扫附件:

```python
import pandas as pd
df = pd.read_excel("附件1.xlsx")
print(df.shape)
print(df.dtypes)
print(df.describe())
print(df.isnull().sum())
```

输出 schema 卡片:
```
附件 1 (xlsx):
- 行数/列数: `<由扫描结果写入>`
- 时间跨度: `<由原始字段计算>`
- 缺失: `<列名、计数与比例；不得预填>`
- 异常: `<检测口径与实际命中；不得预填>`
- 与变量映射: p_i ← 列 "价格", d_i ← 列 "需求量"
```


### Step 4.1: 仅题面输入的文献引导启动

无论用户未提供文献，还是只提供了部分技术文献，都读取
`problem_only_literature_bootstrap.md`，按每个 Qi 建立知识缺口和中英文文献问题矩阵，
并自动调用 `paper-search-pro` 做独立补充检索。用户文献只作为种子，必须分类、去重、
核验和查缺；不能把优秀论文自动当作技术权威。

写入：

- `reports/literature_search_plan.md`
- `reports/literature_search_trace.md`
- `results/literature_retrieval_all.csv`
- `results/literature_shortlist.csv`
- `reports/literature_claim_map.md`
- `reports/refs_verified.json`
- `results/literature_quality_assessment.csv`
- `reports/literature_conflict_matrix.md`
- `results/parameter_provenance.csv`
- `results/fulltext_evidence_locator.csv`
- `reports/fulltext_evidence_map.md`
- `decision_log.stages.2.literature_bootstrap`
- `decision_log.stages.2.literature_quality_gate`

在该状态为 `pass` 或有明确边界的 `conditional` 前，不得进入论文正文写作。
`block` 时输出缺失证据和用户需要补充的最小资料清单。

### Step 5: 子问题关系图 (15 min)

以 mermaid / ASCII 表达:

```
<上游 Qi> (<任务>)
  ↓ <有证据支持的输出接口>
<下游 Qj> (<任务>)
  ↓ <有证据支持的输出接口>
最终: <题面要求的交付>
```

#### Step 5.1: 用一句话写出全文主线

关系图说明各问**怎么衔接**，还要再回答各问**共同在回答什么**。用一句话填空并写入
`decision_log.stages.2.spine`：

```
本文四问都在回答：______________________
  Q1 是它的 ______ 侧面
  Q2 是它的 ______ 侧面
  ...
```

填不出来，说明当前分解只是把题目抄成了四段任务。这不阻断后续阶段，但必须在
`decision_log` 中显式记为 `spine: null`，Stage 8 写摘要和问题分析时会再次要求。

**为什么在这里问**：主线决定摘要的第一句、问题分析的组织方式和结论的收束方式，
是写作阶段无法追加的结构选择。四套各自很强但并列的模型，读起来是"堆模型"；
同一想法的四个侧面，读起来才是一篇论文。

2024B 的实际情况是主线存在但从未被写出来——四问共同刻画的是**质量信息在生产链中
如何被获取、保留与丢失**（Q1 抽样获取、Q2 拆解保留条件质量、Q3 回流永久丢失、
Q4 后验信息的价值）。这条线到终稿仍需读者自行发现。发现得越晚，越无法回填。

写入 `decision_log.stages.2.decomposition`。

### Step 6: 目标函数雏形 (30 min)

每个 Qi 写出符号化目标 (不必完整,要框架):

```
Q1: max  Σ_i p_i * x_i  - C(x)
    s.t. Σ_i x_i ≤ B (预算)
         x_i ≥ 0, x_i ∈ Z

Q2: 在 Q1 基础上加约束 K_i ≤ K_max
    
Qi: <与该子问题匹配的符号化目标>
    若使用上游结果或 warm start，注明接口与依据；否则保持独立
```

### Step 7: 输出移交 (5 min)

写入 `decision_log.stages.2`:
```json
{
  "decomposition": [...],
  "key_variables": [...],
  "key_constraints": [...],
  "objective_per_subproblem": {"<Qi>": "..."},
  "data_schema": {...},
  "subproblem_dependency": {"<Qi>": ["<only evidence-backed upstream IDs>"]},
  "literature_bootstrap": {
    "input_mode": "problem_only | problem_plus_user_literature",
    "search_tier": "quick | standard | deep | audit",
    "status": "pass | conditional | block",
    "query_plan_path": "reports/literature_search_plan.md",
    "search_trace_path": "reports/literature_search_trace.md",
    "retrieval_all_path": "results/literature_retrieval_all.csv",
    "shortlist_path": "results/literature_shortlist.csv",
    "claim_map_path": "reports/literature_claim_map.md",
    "verified_sources_path": "reports/refs_verified.json",
    "missing_evidence": [],
    "user_documents_needed": []
  },
  "literature_quality_gate": {
    "status": "pass | conditional | block",
    "quality_assessment_path": "results/literature_quality_assessment.csv",
    "conflict_matrix_path": "reports/literature_conflict_matrix.md",
    "parameter_provenance_path": "results/parameter_provenance.csv",
    "citation_audit_path": "reports/citation_claim_audit.md",
    "fulltext_locator_path": "results/fulltext_evidence_locator.csv",
    "saturation": null,
    "stop_reason": "",
    "full_text_gaps": [],
    "unresolved_conflicts": [],
    "outdated_or_corrected_sources": []
  }
}
```

---

## L1 Rubric (`rubrics.md` Stage 2)

| 维度 | 满分行为 |
|------|---------|
| 1. 子问题分解清晰度 | 每 Qi 卡片完整 |
| 2. 关键变量识别 | 覆盖目标、约束与数据接口，标注类型，无占位变量 |
| 3. 数学化程度 | 每 Qi 有目标雏形 |
| 4. 数据契合度 | schema 已扫,变量映射清楚 |
| 5. 子问题关联性 | 每个 Qi 的依赖或独立理由均已识别 |

---

## 常见坑

- 题目仅读一次就开干 → 强制读 3 遍
- 子问题间符号不统一 (B4) → 统一变量表
- 附件数据没扫 → strictly 必做 Step 4
- 为了“串起来”强行复用上游结果 (G1) → 只保留题面、数学或业务机制支持的依赖

---

## 退出条件

1. 题面中的全部子问题卡片完整
2. 全局变量表覆盖后续模型实际所需项且无凑数项
3. 数据 schema 扫描完成
4. 每个 Qi 的依赖关系明确 (依赖 / 独立,均有理由)
4.1 `stages.2.spine` 已写入：一句话说明各问共同在回答什么；确实找不到主线时
   显式记为 `null`，不得留空字段蒙混过关
5. 文献门禁已形成检索计划、检索轨迹、完整命中、短名单、主张映射和核验结果；
   已逐篇向用户报告高质量短名单的检索词、来源、地址和采用理由；质量门禁完成来源、
   全文获取与页码/公式定位、冲突、参数来源、时效和饱和检查；任一门禁为 `block` 时
   不得进入 Stage 3 最终选型
6. L1 rubric 全维 ≥7

→ 跳转 `stage_03_model_selection.md`
