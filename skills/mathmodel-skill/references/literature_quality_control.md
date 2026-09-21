# 文献质量、冲突与引用落地门禁

在 `problem_only_literature_bootstrap.md` 完成检索和短名单后使用。本门禁不增加无意义的
篇数要求，而是判断短名单是否真的能支撑模型、参数、验证和创新主张。

## 1. 来源质量按主张适配，不按期刊名一刀切

| 来源类型 | 最适合支撑 | 注意事项 |
|---|---|---|
| 官方标准、法规、机构文档 | 定义、现行规则、测量方法、推荐参数 | 核对版本、发布日期、生效状态和适用范围 |
| 原始研究或经典原始论文 | 公式来源、机制、算法、实验结果、创新归属 | 检查假设、材料/样本、尺度和实验条件 |
| 权威教材、专著 | 稳定基础理论和标准推导 | 不用于声称最新进展或具体实验性能 |
| 系统综述、高质量综述 | 术语、研究谱系、争议和引文网络 | 核心公式和创新归属尽量回溯原始来源 |
| 相近应用论文 | 参数范围、实现方式、场景可迁移性 | 相近不等于同条件，不能直接照搬参数 |
| 优秀竞赛论文 | 结构、证据密度、评委阅读路径 | 不是默认技术权威，不复制结论和措辞 |
| 博客、新闻、问答、聚合页 | 发现术语或线索 | 不作为核心技术主张的最终来源 |

“高影响力”“高分区”“高引用”只作质量先验，不能替代与当前小问、数据和条件的相关性。

## 2. 可访问深度限制表述强度

为每篇短名单文献记录：

`metadata_only | abstract_checked | full_text_checked | official_full_text`

| 访问深度 | 允许用途 |
|---|---|
| 仅元数据 | 证明文献存在、题名、作者、年份、期刊和检索线索 |
| 已看摘要 | 判断主题相关性、研究对象和概括性结论 |
| 已看全文 | 支撑精确公式、参数、假设、实验设置、局限和定量结果 |
| 官方全文/标准 | 支撑现行规范、标准定义、参数口径和版本信息 |

不得只凭摘要或二手引用写精确公式、具体参数、显著性数值或“首次提出”。全文不可得时，
应降低主张强度、寻找可访问的原始替代来源，或标记为 `conditional`。

### 2.1 核心证据进一步执行全文定位

高质量短名单中的精确公式、参数、定量结果、局限和创新归属，读取
`fulltext_evidence_localization.md`。全文定位未完成时，访问深度不能写为
`full_text_checked`，相应主张必须降级、换源或阻塞。

## 3. 文献冲突不能多数投票

对会改变模型路线、参数值或结论的冲突建立：

`reports/literature_conflict_matrix.md`

至少记录：

| 冲突主张 | 文献 A | 文献 B | 条件差异 | 当前题目更接近哪方 | 处理 |
|---|---|---|---|---|---|

比较条件包括材料、样本、时间、空间尺度、测量方法、模型假设、单位、温度、地域、版本和
评价指标。处理方式可以是：

- 选择与题目条件更匹配的一方；
- 分条件使用不同来源；
- 把差异作为参数范围或敏感性分析；
- 无法裁决时保留为模型形式不确定性；
- 若足以改变主模型且无法解决，状态设为 `block`。

不得按引用量、篇数或期刊级别简单投票。

## 4. 外部参数必须有来源台账

生成 `results/parameter_provenance.csv`，每个非题面给定参数记录：

```text
symbol
value_or_range
unit
material_population_or_region
temperature_time_scale_or_other_conditions
source_title
source_url_or_doi
page_equation_table_location
access_level
conversion_or_interpolation
used_in_code
used_in_paper
uncertainty_treatment
```

若参数经过单位换算、插值、拟合或取中值，必须记录过程。不能只在参考文献列表中出现来源，
却无法说明论文和代码中的具体数值来自哪里。

## 5. 时效、版本和撤稿状态

对以下来源必须做时效检查：

- 法规、竞赛规则、标准和软件文档：核对当前有效版本和确认日期；
- 经济、人口、市场、政策与行业数据：核对统计期和发布日期；
- 快速演化的软件库、算法实现和在线数据库：核对版本；
- 准备重点引用的论文：查看出版商或数据库页面是否标注撤稿、更正、勘误或版本替换。

发现更正或撤稿时，记录原文与更新状态；撤稿论文原则上不得作为正面核心证据，除非研究
目的就是讨论该事件。

## 6. 检索饱和与停止

使用 `paper-search-pro` 的 saturation/stop-decision 信号，不凭感觉或固定篇数停止。

停止检索至少同时满足：

1. 文献问题矩阵中的核心类别均有来源或明确缺失原因；
2. 影响模型选择、参数和创新归属的主张都有核验来源；
3. 最近一轮扩展关键词或引文追踪没有新增会改变路线的高质量来源；
4. 冲突已解决、降级或明确阻塞；
5. 达到当前竞赛时间预算。

若饱和度不足但时间必须停止，应报告剩余缺口和可能影响，不能把“预算耗尽”写成“检索已
充分”。同样，饱和信号较高也不能覆盖尚未解决的关键证据类别。

## 7. 引用必须落到具体主张

Stage 8 写作前生成 `reports/citation_claim_audit.md`：

| 论文位置 | 具体主张 | 引用 | 是否直接支撑 | 访问深度 | 处理 |
|---|---|---|---|---|---|

检查：

- 同一句中的公式、参数和结论是否来自同一来源；不是时分别引用；
- 段末堆叠的多个引用是否真的分别支撑前文；
- 是否把综述引用成原始创新来源；
- 是否通过优秀论文或二手论文进行“引用洗白”；
- 论文中的限定条件是否与来源一致；
- BibTeX 元数据、正文编号和链接是否一致。

无法定位支撑位置的引用应删除、替换或降低主张强度。

## 8. 必须形成的质量产物

- `results/literature_quality_assessment.csv`
- `reports/literature_conflict_matrix.md`
- `results/parameter_provenance.csv`
- `results/fulltext_evidence_locator.csv`
- `reports/fulltext_evidence_map.md`
- `reports/citation_claim_audit.md`
- `reports/literature_search_trace.md` 中的饱和与停止记录

写入 `decision_log.stages.2.literature_quality_gate`：

```json
{
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
```

`pass` 只表示当前竞赛论文的核心主张具有足够证据，不表示完成系统综述。Stage 3 不得在
`block` 下锁定模型；Stage 8 不得在引用审计未完成时定稿。
