---
stage: 9
name: review
duration_h: 2-6
inputs: ["paper.tex", "paper.pdf", "decision_log_full", "decision_log.competition", "assets/workflow_manifest.json", "results/code_manifest.json", "paper_workspace/code_appendix.md"]
outputs:
  - "stage.9.{anti_patterns_check, compliance_checks, panel_scores, weakest_section, redo_log, red_team_record, final_pdf_path, submission_ready}"
loads_reference:
  - "competitions/<comp>/current_rules.md"
  - "competitions/<comp>/anti_patterns.md"
  - "competitions/<comp>/rubric_overlay.json"
  - "references/paper_depth_audit.md"
  - "references/manuscript_delivery_gates.md"
  - "references/judge_view_restructuring.md"
  - "references/revision_case_history.md"
  - "references/final_manuscript_calibration.md"
  - "references/feedback_layer3_panel.md"
loads_template: ["templates/latex/<comp>/"]
feedback: ["L1", "L3_panel", "red_team_in_championship"]
next: SUBMIT
---

# Stage 9 — Submission review

The final gate is compliance first, content consistency second, presentation third. A polished paper that violates the current rules is not submission-ready.

## 1. Re-open the official rules

Read `competitions/<comp>/current_rules.md`, open its official links, and compare the final artifacts against the current contest year. Record the check in `decision_log.stages.9.compliance_checks`.

Minimum branches:

### CUMCM

- electronic paper starts with the abstract page;
- no commitment form, numbering page, table of contents, or identity information;
- main text and file size meet the current limits;
- appendix lists the supporting-material files;
- support ZIP/RAR contains runnable code and required evidence, is within the size limit, and excludes secrets;
- AI-assisted content is marked and cited;
- if AI was used, support materials contain `AI工具使用详情.pdf`; otherwise the required no-AI declaration is present.

### MCM/ICM

- Summary Sheet is page 1;
- main solution, including references, appendices, code, TOC, and required letter/memo, is at most 25 pages;
- readable font is at least 12pt;
- each solution page has the control number and page number, with no personal or institutional identity;
- AI tools are cited in the main solution;
- `Report on Use of AI` follows the main solution and is not counted inside the 25-page solution.

### Diangong

- page 1 is the anonymous cover with registration number and the official problem title; page 2 contains title, abstract and keywords and begins Arabic page numbering at 1;
- the body begins on page 3, contains no table of contents and stays within the current 25-page body limit; appendices follow the body;
- A4 margins are 2.5 cm and Chinese body text uses 小四; no team-member or school identity appears anywhere;
- the paper is a single uncompressed PDF or Word file, while support materials are ZIP/RAR no larger than 20 MB and contain the runnable code and necessary evidence;
- citations appear in the text and references follow citation order;
- the currently checked official pages do not define a dedicated AI-disclosure format, so recheck the annual notice and preserve the ledger rather than inventing one.

Any unresolved rule violation sets `submission_ready=false` and yields `block`.

## 2. Run the active anti-pattern checklist

Read `competitions/<comp>/anti_patterns.md` and derive the count from the active file rather than copying a remembered or example count.

These are maintainer heuristics, not official scoring weights. Fix high-severity hits; record accepted medium-risk items with an explicit rationale.

## 3. Verify the evidence chain

Cross-check the final paper against `decision_log.json` and the saved artifacts:

- no abandoned model remains in the abstract or conclusion;
- no symbol changes meaning between sections;
- all headline values reproduce from stored results;
- every figure/table path resolves and its caption matches the content;
- every external claim has a verified source;
- code manifest hashes match current files and the code appendix lists the real entrypoints;
- the latest rerun plan has no unfinished stage affecting the final artifact;
- AI-generated citations have been opened and checked manually.

## 3.1 语言终审：允许改表达，不允许改技术

终审可以修正真实的表达缺陷：重复句式、模板化过渡、成段被动语态、术语前后不一致。

**禁止为压低 AIGC 检测比例做以下任何一项：**

- 把术语替换成同义词，使其不再与公式、图注、结果文件中的写法一致；
- 拆散或改写公式、变量名、单位；
- 打乱本来正确的逻辑顺序，或插入冗余从句制造“人味”；
- 删除限定语（“在本组参数下”“在16位静态策略空间内”）以换取句子更短。

判据只有一条：**这次修改让论文更准确了，还是只是更不像机器写的。** 只满足后者就撤销。

术语一致性优先于表达多样性。同一对象在摘要、公式、图注、结果文件和结论中必须用同一个
词；为避免重复而在不同章节换用不同说法，会直接破坏本节与 `manuscript_delivery_gates.md`
§7 所依赖的可核对性，也会让评委怀疑两处说的不是同一件事。

AIGC 检测报告可用作定位重复句式的线索，**不作为改写目标**；检测比例不是本技能的门禁项。

## 4. Review presentation

- labels, units, legends, equations, and captions remain readable at final PDF size;
- fonts and colors are consistent and accessible;
- tables use consistent units and precision;
- there are no unresolved `??` references, missing glyphs, clipped figures, or large overfull boxes;
- all required sections are present in the compiled PDF, not merely on disk as detached `.tex` files.

## 4.1 Recheck depth, not only page-limit compliance

Read `references/paper_depth_audit.md` and verify the Stage 8 depth audit against
the compiled PDF. A paper can satisfy the official page limit and still fail this
gate when its core technical chain is compressed.

Set `submission_ready=false` until:

- total pages are separated from effective body, references, and appendices;
- every subproblem contains formulation, solver, result, validation, and interpretation;
- implemented baselines, ablations, robustness tests, and negative results are either
  shown or explicitly excluded with a reason;
- the manuscript has no evidence-free padding added only to imitate an excellent
  paper's page count.

When the user first asks for diagnosis, return the audit and expansion blueprint
before editing the paper.

## 4.2 Audit the final revision history

When the manuscript has undergone repeated structural or wording revisions, read
`references/judge_view_restructuring.md` and verify:

- every accepted change has a recorded problem, reason, invariant, affected file, and validation;
- rejected suggestions have an evidence-based rationale rather than being silently ignored;
- no body-to-appendix move removed the main conclusion or its key number;
- abstract, keywords, innovation claims, AI dates, figure/page counts, README, reports,
  authoritative PDF path, and support archive all match the latest source;
- text-only edits were recompiled and visually checked on affected pages; figure/result
  edits were fully rerun and cross-file checked;
- stable sections are frozen and no further global rewrite is justified.

Any stale submission artifact sets `submission_ready=false` even when `paper/main.pdf`
itself is correct.

## 4.3 Calibrate final defects before adding work

When the user asks for remaining weaknesses, a percentage score, or another improvement pass,
read `references/final_manuscript_calibration.md`.

- separate actionable defects from problem-data and ideal-research ceilings;
- distinguish real observations, external target truth, and parameter identifiability;
- distinguish target-parameter stability from nuisance-parameter interpretation;
- match solver claims to the available evidence level;
- report heuristic scores with uncertainty and no award prediction;
- prefer a minimal clarification patch over a new experiment when the evidence is already
  sufficient and only the wording overreaches;
- freeze the paper when every remaining gap requires genuinely new evidence.

Record each concern as `resolved`, `mitigated`, `unchanged_not_a_defect`, or `open`.
Wording-only fixes may improve readability but must not inflate technical-evidence scores.

## 5. Run the five-view panel

Use `references/feedback_layer3_panel.md` as the single source for panel roles and aggregation. Prefer independent parallel views when the harness supports them; otherwise run the views separately to reduce cross-contamination.

Map every high-severity concern back to one source section and apply a targeted patch. Re-run only the affected checks and panel views. Do not ask the panel to predict an award; use `ready`, `refine`, or `block` against the repository rubric.

## 6. Generate AI disclosure artifacts

For CUMCM or MCM, run from the user project root:

```bash
python <skill>/scripts/render_ai_usage.py \
  --competition <competition> \
  --decision-log state/decision_log.json \
  --paper-workspace paper_workspace/ \
  --support-dir support_materials/
```

For CUMCM with AI use, verify `support_materials/AI工具使用详情.pdf` is in the supporting archive, that inline marks and AI-tool references are present, and that `paper_workspace/AI工具使用声明.md` renders immediately before the references. For an explicit empty CUMCM ledger, the helper instead creates `paper_workspace/AI工具未使用声明.md`; rerender and verify that the declaration appears immediately before the references, with no details PDF. Exactly one of the two declarations may be present, and the wording of each is fixed verbatim by 《人工智能工具使用规定（2026 年试行）》第 3 条 — do not paraphrase either one. For MCM, verify `paper_workspace/11_ai_use_report.md` is rendered once, after the 25-page main solution. The helper intentionally does not invent a Diangong disclosure format; for Diangong, compare the ledger with the current official notice and record that manual check.

## 7. Compile and inspect the final PDF

Use `<skill>/scripts/render_paper.py` or the selected LaTeX engine. Compilation succeeds only when the PDF exists, includes all intended sections, and has no unresolved high-severity warnings. Visually inspect the first page, dense equations, wide tables, figure-heavy pages, references, appendices, and the AI report.

## 8. Persist the final gate

Write actual runtime-derived counts and paths. The schema is:

```json
{
  "anti_patterns_check": {
    "total": null,
    "passed": null,
    "fixed": null,
    "deferred": null
  },
  "compliance_checks": {
    "rules_verified": null,
    "anonymity_passed": null,
    "page_limit_passed": null,
    "ai_disclosure_passed": null
  },
  "final_pdf_path": "paper_output/paper.pdf",
  "submission_ready": null
}
```

The `null` values above are schema placeholders only. Replace every one with an observed count or verified boolean before persisting Stage 9; never copy a sample result into the final gate.

## Exit conditions

- current official rules verified with no unresolved violation;
- anti-pattern and consistency checks completed;
- all high-severity panel findings resolved;
- PDF compiled and visually inspected;
- AI disclosure and supporting materials complete when required;
- `run_readiness_audit.py` derives `submission_ready == true`; a handwritten state value is not evidence.

Only then hand the final submission package back to the team.
