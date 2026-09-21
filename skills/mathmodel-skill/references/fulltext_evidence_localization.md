# 全文获取与证据定位协议

用于高质量短名单形成后，把“这篇文献相关”推进到“这篇文献的具体位置能够支撑论文中的
具体主张”。与 `literature_quality_control.md` 联用。

## 1. 能力检测与获取顺序

按以下顺序获取全文：

1. 用户上传的PDF或项目已有本地全文；
2. 出版商开放全文、DOI落地页的开放PDF、arXiv、PubMed Central、机构知识库、标准或
   官方机构页面；
3. 已安装的合法全文下载工具；
4. 只有付费墙或封闭数据库时，请用户上传有权限访问的全文。

不得绕过付费墙、登录、验证码、版权或数据库访问控制。不能获取全文时，保留元数据/摘要
状态并降低主张强度，不能声称“已核对原文”。

## 2. 本地文件组织

建议保存：

```text
literature/fulltext/<paper_id>.pdf
literature/page_images/<paper_id>/page-XXX.png
reports/fulltext_evidence_map.md
results/fulltext_evidence_locator.csv
```

文件名使用稳定ID、DOI安全变体或短哈希，避免只用可能重复的题名。记录原始下载地址和
SHA-256，防止后续误用不同版本。

## 3. PDF读取与定位

对每篇准备支撑高影响主张的全文：

1. 使用PDF工具提取文本和页数；
2. 同时记录PDF页序号与文献印刷页码，二者不得混淆；
3. 搜索公式符号、参数名、方法名、材料/样本条件和限制词；
4. 打开命中页上下文，不能只靠关键词所在的一行；
5. 对扫描版或公式抽取失败的页面进行渲染和视觉检查；
6. 定位章节、页码、公式号、表号或图号；
7. 保存必要的关键页图像用于内部核验；
8. 写入短摘录或内容指纹，避免保存和输出大段版权文本。

## 4. 证据定位表

`results/fulltext_evidence_locator.csv` 至少包含：

```text
paper_id
claim_id
title
doi_or_standard_id
source_url
local_pdf_path
pdf_page_index
printed_page
section
equation_table_figure
short_excerpt_or_fingerprint
paraphrased_support
conditions_and_scope
access_level
extraction_method
visually_verified
status
```

`short_excerpt_or_fingerprint`只保存定位所需的短片段；写入论文时使用自己的概括，不复制
文献长段落。

## 5. 哪些主张必须全文定位

以下内容原则上必须达到 `full_text_checked` 或 `official_full_text`：

- 精确公式及其适用条件；
- 材料常数、经验参数和数值范围；
- 实验样本、测量条件和数据口径；
- 定量性能、误差、显著性和置信区间；
- 方法局限、失败条件和边界；
- “首次提出”、创新归属或与已有方法的差异；
- 标准规定、法规条款和官方定义。

只用于背景概述的文献可以停留在摘要级，但必须在质量台账中明确。

## 6. 全文不可得时

使用以下顺序降级：

1. 查找同一作者的预印本、机构版本或开放版本；
2. 查找能直接支撑同一主张的其他原始来源；
3. 把精确主张改成摘要能够支持的概括表述；
4. 标记 `conditional` 并列入 `full_text_gaps`；
5. 若该主张会改变模型或参数且无替代来源，状态设为 `block`，向用户索取全文。

不得通过另一篇论文的参考文献列表假装已经核验原文。

## 7. 向用户主动汇报

对所有准备采用的核心全文，主动说明：

- 从哪里获得全文及地址；
- 本地文件路径；
- 定位到第几页、哪一节、公式/表格/图号；
- 它支撑论文中的哪一项主张；
- 适用条件是否与题目一致；
- 是否存在版本、付费墙、扫描质量或文本抽取限制。

若无法提供全文地址，应明确说明只获得元数据或摘要，并指出需要用户补充的PDF。

## 8. 写作阶段复核

Stage 8 的 `citation_claim_audit.md` 必须引用本定位表。论文中的精确参数、公式和定量结论
若没有对应定位记录，应删除、换源、降级或阻塞定稿。
