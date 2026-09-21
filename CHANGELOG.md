# 改动清单

本仓库基于 [handsomeZR-netizen/mathmodel-skill](https://github.com/handsomeZR-netizen/mathmodel-skill) **v6.1.0**（基线最后推送 2026-07-22）改造。下面是与基线的完整差异，用脚本逐文件比对得出（已忽略换行符差异）。

| | 数量 | 规模 |
|---|---:|---|
| 基线文件总数 | 103 | — |
| 原样保留 | 72 | — |
| 改动的引擎文件 | 30 | +1323 / −479 行 |
| 新增的文件 | 35 | 7283 行 / 332 KB |
| 删除的文件 | 0 | — |
| 入口 `26math/SKILL.md` | 1 | +3 / −1 行 |

## 一、两处针对 2026-09-01 新规的合规修正

**AI 工具使用声明**（原版三处不合规，均已修正并补测试）：

1. 声明块移到参考文献**之前**（新规要求）——`templates/latex/cumcm/main.tex`、`scripts/render_paper.py`
2. 「未使用 AI」措辞补上「在竞赛过程中」——`scripts/render_ai_usage.py`
3. 使用 AI 时同样在**正文**生成声明（原版只在支撑材料出 PDF）——`scripts/render_ai_usage.py`、`competitions/cumcm/current_rules.md`
4. 配套守卫测试——`tests/test_ai_usage.py`、`tests/test_render_guard.py`、`tests/fixtures/cumcm_empirical_inject.json`

**被标错来源的参考数据**：`competitions/cumcm/empirical.json` 自称 59 份国赛样本，题号却覆盖 A–F（国赛本科组只有 A/B/C，专科组 D/E），实为别的赛事（研究生"华为杯"）样本。已撤回为空占位，`empirical_notes.md` 写明原因与重建进展；缺数据时如实报告，不再用错锚点给论文打分。

## 二、改动的文件（引擎 30 个 + 入口 1 个，按改动量排序）

| 文件 | 加 | 删 | 说明 |
|---|---:|---:|---|
| `SKILL.md` | +121 | −176 | 主流程重写：阶段门禁、就绪度判定、状态落盘口径 |
| `references/stage_05_subproblem_loop.md` | +144 | −1 | 子问题循环：改动必须回扫下游问与摘要 |
| `references/stage_08_writing.md` | +132 | −4 | 写作：摘要与正文一致性、措辞不得替换技术口径 |
| `references/stage_02_analysis.md` | +120 | −5 | 读题与分析：题目要求逐条登记、附件先审后选模型 |
| `references/stage_09_review.md` | +81 | −3 | 评审：终稿红队与交付前检查 |
| `references/stage_03_model_selection.md` | +73 | −4 | 建模选择：先确认路线再求解 |
| `references/stage_06_robustness.md` | +38 | −0 | 稳健性：扰动与敏感性口径 |
| `references/papers/_DOWNLOAD_REPORT.md` | +33 | −16 | 范文来源核对结论 |
| `references/papers/README.md` | +5 | −5 | 同上 |
| `competitions/cumcm/paper_skeleton.md` | +54 | −37 | 国赛论文骨架（含前置页与声明位置） |
| `competitions/cumcm/distilled_structures.md` | +52 | −17 | 章节结构归纳 |
| `competitions/cumcm/distilled_formats.md` | +15 | −14 | 格式归纳 |
| `competitions/cumcm/anti_patterns.md` | +45 | −1 | 反例清单扩充 |
| `competitions/cumcm/winning_patterns.md` | +8 | −4 | 获奖论文常见做法 |
| `competitions/cumcm/current_rules.md` | +7 | −2 | 规则基线更新至当年官方文件 |
| `competitions/cumcm/phrase_bank.md` | +3 | −3 | 句式库 |
| `competitions/cumcm/distilled_phrases.md` | +4 | −0 | 句式归纳 |
| `competitions/cumcm/README.md` | +2 | −1 | 国赛包说明 |
| `competitions/cumcm/empirical.json` | +20 | −33 | **撤回错标数据**（见上） |
| `competitions/cumcm/empirical_notes.md` | +24 | −103 | **撤回说明与重建进展** |
| `templates/latex/cumcm/main.tex` | +23 | −10 | **声明块位置修正** |
| `templates/shared/decision_log.json` | +59 | −7 | 决策日志模板升到 v3.2 |
| `scripts/render_ai_usage.py` | +45 | −5 | **声明措辞与正文声明块** |
| `scripts/render_paper.py` | +31 | −6 | 渲染守卫 |
| `scripts/doctor.py` | +32 | −6 | 自检项 9 → 10（新增 `workflow-manifest`） |
| `scripts/README.md` | +50 | −1 | 脚本索引 |
| `tests/test_core.py` | +63 | −7 | 新增守卫测试 |
| `tests/test_render_guard.py` | +23 | −2 | 同上 |
| `tests/test_ai_usage.py` | +15 | −5 | 同上 |
| `skills/26math/SKILL.md`（入口） | +3 | −1 | 统计语义门禁那条规则 |

## 三、新增的文件（35 个）

### 检查脚本 `scripts/`（15 个，3142 行）

| 脚本 | 行数 | 干什么 |
|---|---:|---|
| `audit_data.py` | 675 | 数据体检：缺失、重复、量纲、异常值、可复现性 |
| `build_code_manifest.py` | 393 | 代码清单：每个结果对应哪段代码、哪个数据版本 |
| `workflow_manager.py` | 347 | 阶段状态机：完成门禁、改动影响面 |
| `sanity_check.py` | 254 | 结果合理性：数量级、边界、与常识冲突 |
| `check_manuscript_hygiene.py` | 247 | 稿件卫生：占位符、TODO、图表编号、引用完整性 |
| `check_cross_file_consistency.py` | 246 | 跨文件一致性：摘要/正文/图表/附录的数字对不对得上 |
| `derive_readiness.py` | 154 | 交卷就绪度推导 |
| `check_requirement_coverage.py` | 146 | 题目要求逐条覆盖检查 |
| `check_manuscript_evidence.py` | 128 | 稿件主张的证据矩阵核对 |
| `check_figure_audit.py` | 108 | 图表溯源：每张图的来源与生成脚本 |
| `context_snapshot.py` | 86 | 上下文快照：长会话不丢设定 |
| `check_encoding_registry.py` | 76 | 术语编码登记核对 |
| `audit_common.py` | 71 | 上述脚本的公共库 |
| `run_readiness_audit.py` | 50 | 一次性跑完全部审计 |

### 流程文档 `references/`（13 篇，2662 行）

`statistical_semantics_gate.md`（统计语义门禁）、`external_review_intake.md`（外部审查意见接收）、`optimization_search_rigor.md`（优化搜索严谨性）、`revision_case_history.md`（多轮改稿案例与反例，引 2023 CUMCM A 题等公开题）、`figure_evidence_system.md`（图表证据体系）、`problem_only_literature_bootstrap.md`（只用题目信息起步的文献检索）、`manuscript_delivery_gates.md`（交付门禁）、`paper_depth_audit.md`（论文深度审计）、`judge_view_restructuring.md`（评审视角重构）、`model_route_confirmation.md`（模型路线确认）、`literature_quality_control.md`（文献质量控制）、`fulltext_evidence_localization.md`（全文证据定位）、`final_manuscript_calibration.md`（终稿校准）。

### 其余

- `competitions/cumcm/paper_writing.md`（1099 行）：国赛论文写作规则汇总
- `assets/workflow_manifest.json`（375 行）：阶段执行清单，`doctor.py` 第 10 项自检的对象
- `templates/shared/*.csv`（5 张登记表）：主张登记、图表审计、术语编码、稿件证据矩阵、统计语义登记

---

## 复现这份差异

```powershell
git clone --depth 1 https://github.com/handsomeZR-netizen/mathmodel-skill.git upstream
# 把本仓库 skills/mathmodel-skill 与 upstream 逐文件对比即可
```
