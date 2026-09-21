---
stage: 8
name: writing
duration_h: 12-30
inputs: ["decision_log.stages.0-7", "decision_log.competition", "decision_log.task_type", "results/code_manifest.json", "paper_workspace/code_appendix.md"]
outputs:
  - "stage.8.{section_word_counts, figures_per_subproblem, tables_per_subproblem, abstract_drafts, ai_use_log, compliance, depth_audit}"
  - "paper_workspace/*.md"
  - "paper.tex"
loads_reference:
  - "competitions/<competition>/current_rules.md"
  - "competitions/<competition>/winning_patterns.md"
  - "competitions/<competition>/phrase_bank.md"
  - "competitions/<competition>/empirical.json"
  - "references/paper_depth_audit.md"
  - "references/manuscript_delivery_gates.md"
  - "references/figure_evidence_system.md"
  - "references/judge_view_restructuring.md"
  - "references/literature_quality_control.md"
  - "references/fulltext_evidence_localization.md"
  - "references/revision_case_history.md"
loads_template:
  - "competitions/cumcm/paper_writing.md"   # CUMCM 写作与排版硬规则，写作前必读，冲突时以其为准
  - "competitions/<competition>/paper_skeleton.md"
  - "competitions/<competition>/abstract_template.md"
  - "templates/latex/<competition>/"
feedback: ["L1", "L2_at_end"]
next: stage_09_review
---

# Stage 8 — Assemble the paper

Turn the validated Stage 0–7 outputs into one coherent paper. Do not invent new results while writing. If the paper exposes a modeling contradiction, record it and trigger a targeted L2 backtrack.

## 0. CUMCM: read the writing spec before anything else

For CUMCM, read `competitions/cumcm/paper_writing.md` **before** creating the workspace
skeleton or writing any section. It is the authoritative source for chapter order,
heading numbering, abstract discipline, figure/table caption format, equation
selection, appendix rules, and the final self-check list. Where any other file in this
skill — including `paper_skeleton.md`, `distilled_structures.md`, `distilled_phrases.md`,
`distilled_formats.md`, `winning_patterns.md`, or `phrase_bank.md` — disagrees with it,
`paper_writing.md` wins.

Two rules from that spec change the file layout below and are repeated here so they are
not missed:

- The legal chapter order is `一、问题重述 → 二、问题分析 → 三、模型假设 → 四、符号说明 → 五、问题一的模型建立与求解 → 六、问题二…（每问一章，依次顺延）→ 模型的评价与推广 → 参考文献 → 附录`. Restatement and analysis are **adjacent**; assumptions and notation sit right before the modelling chapters that use them.
- **Model checking and robustness never form a top-level chapter.** They go inside the relevant problem's own chapter as `5.X` subsections, or are omitted. Do not create a standalone `模型的检验与稳健性分析` chapter.

Layout is a blocking item, not a polish step: a paper that violates this spec is not
finished, regardless of how good the modeling is.

## 1. Lock the current rules first

1. Read `competitions/<competition>/current_rules.md` when present.
2. Open the linked official rules and confirm they are still current for the contest year.
3. Record the verification date, source URL, page/font/file-size limits, anonymity rules, and AI-disclosure requirements in `decision_log.compliance.ruleset`.
4. If the repository baseline conflicts with the official source, follow the official source and flag the repository mismatch.

Do not treat empirical distributions, `winning_patterns.md`, or rubric scores as official rules. They are writing aids only.

## 2. Load only the active competition pack

Read from `competitions/<competition>/`:

- `paper_skeleton.md`
- `abstract_template.md`
- `winning_patterns.md`
- `phrase_bank.md`
- `empirical.json`

For MCM and Diangong, `empirical.json` explicitly records `n=0` and provides no numeric distribution. For CUMCM, 91 source documents were collected but only 59 text-extractable documents entered the aggregate statistics; the values are observational baselines, not award thresholds.

## 3. Write into a stable workspace contract

Create these files under `<cwd>/paper_workspace/`:

| File | Content |
|---|---|
| `01_abstract.md` | Abstract or Summary Sheet, written last |
| `02_problem_restate.md` | Problem context and restatement |
| `03_analysis.md` | Decomposition and technical route |
| `04_assumptions.md` | Supported assumptions |
| `05_notation.md` | Unique symbols and units |
| `06_models.md` | Models, algorithms, results, and interpretation |
| `07_sensitivity.md` | MCM/Diangong only. **CUMCM: do not create this file** — checking and robustness live inside `06_models.md` as `5.X.X` subsections (see §0). The CUMCM template no longer carries a `6_sensitivity` marker |
| `08_evaluation.md` | Strengths, limitations, and transfer conditions |
| `09_references.md` | Verified references, including AI tools when required |
| `10_appendix.md` | Essential code and supporting-material manifest |
| `11_ai_use_report.md` | MCM only: Report on Use of AI after the main solution |

`01_abstract.md` contains abstract/summary content without a top-level heading because the template supplies its wrapper. Files `02`–`10` each own one clear top-level Markdown heading; the MCM/Diangong templates intentionally do not print duplicate body headings. `11_ai_use_report.md` also omits its top-level heading because the MCM template supplies it.

Write the body first, then references and appendices, and write the abstract/summary last. Every number in the abstract must point to a result already present in the body.

## 4. Keep one evidence chain

For every subproblem, preserve this chain:

`question → assumptions → formulation → solver → result → validation → interpretation`

Before moving on, verify:

- symbols match Stage 4;
- chosen models match Stage 3;
- reported values match stored results rather than regenerated prose;
- figures have readable labels, units, captions, and source paths;
- claims and citations are verifiable;
- limitations name a concrete failure mode and mitigation.

## 4.1 Run the depth audit before polishing

After assembling the first complete draft, read
`references/paper_depth_audit.md`. Separate total pages from effective technical
body pages, references, appendices, and code. Audit section text, equations,
figures, tables, and the evidence chain for every subproblem.

Do not treat “below the page limit” as a quality pass. If code or stored results
contain completed derivations, comparisons, diagnostics, sensitivity tests, or
negative results that the paper does not show, produce a depth-gap report and a
page-by-page evidence blueprint before expanding the manuscript.

Record under `decision_log.stages.8.depth_audit`:

```json
{
  "total_pages": null,
  "effective_body_pages": null,
  "core_technical_pages": null,
  "reference_main_pages": [],
  "missing_evidence_units": [],
  "code_to_paper_gaps": [],
  "expansion_blueprint": [],
  "padding_risk": false,
  "verdict": "pass | expand | block"
}
```

Reference-paper page counts are calibration evidence, not official thresholds.
Never add generic background, repeated theory, code screenshots, font changes,
or blank space merely to approach a reference paper's length.

After the first complete draft, read `references/manuscript_delivery_gates.md` and create
`reports/manuscript_evidence_matrix.csv`. Requirement and Claim passing do not substitute for
the six narrative layers. Record section state as `draft`, `reconstructed`, `validated`, or
`frozen`; do not reopen a frozen section without a named trigger.



## 4.2 Build a figure evidence system

When the draft lacks visual evidence, or the user asks to learn from an excellent
paper's figures, read `references/figure_evidence_system.md`.

1. Inventory current figure references and code-produced but unpublished diagnostics.
2. Map each proposed figure to one evidence question; split overloaded composites.
3. Generate previews and a contact sheet before editing the paper when the user asks
   to review figures first.
4. After approval, generate formal figures from the real pipeline, save a numeric
   snapshot, and add nearby interpretation rather than “as shown in the figure”.
5. Re-run the full pipeline, check paper–figure–result consistency, compile, render
   every PDF page, and inspect layout.

Create `reports/figure_audit.csv` before formal drawing. Each candidate must have one evidence
question and a `KEEP/REDESIGN/DELETE` decision; audit final-width readability, grayscale use,
and overlap with tables. Deleting a redundant figure is a valid improvement.

Do not use figure count or enlarged graphics as a page-length target.

## 4.3 Restructure from the judge's reading path

When the technical foundation is stable but the paper remains hard to read, or when
multiple rounds of external feedback request conclusion-forward writing, read
`references/judge_view_restructuring.md`.

1. Restore the actual workspace, latest backups, diffs, decision log, and authoritative
   results before editing.
2. Lock the technical baseline and classify each suggestion as keep, move forward,
   compress, move to appendix, rewrite, or reject.
3. Build the judge path with a challenge–strategy workflow, per-question conclusions,
   a core-results table, and explicit body/appendix evidence levels.
4. Keep at least one baseline, one fair ablation, one uncertainty result, one meaningful
   sensitivity result, and one negative result in the main text.
5. Maintain a revision ledger explaining why each change was made, what remained
   invariant, and which checks passed.
6. Write the abstract and keywords only after the body stabilizes. Avoid tool-list
   openings, generic-only keywords, and unsupported innovation language.

Do not reopen frozen sections without new evidence, a rule change, or a concrete defect.

## 4.4 Audit citation-to-claim landing

Before final prose polishing, read `references/literature_quality_control.md` and generate
`reports/citation_claim_audit.md`.

- exact formulas, parameters, quantitative results, limitations, and novelty claims require
  sources whose access level supports that precision and a record in
  `results/fulltext_evidence_locator.csv`;
- resolve literature conflicts by conditions rather than majority vote;
- every external parameter must match `results/parameter_provenance.csv`;
- verify standards, data, software documentation, corrections, and retractions are current;
- do not cite excellent papers or reviews as if they were the original source;
- remove citation clusters that do not individually support the adjacent claims.

The draft cannot be frozen while the literature quality gate is `block` or the citation audit
contains an unresolved core claim.

## 5. Apply the competition branch

| Competition | Current repository baseline | Renderer |
|---|---|---|
| CUMCM | 2026 electronic paper: first page abstract, no commitment/numbering page, no TOC or identity; main text ≤30 pages; paper and support archive each ≤20 MB; exactly one AI declaration immediately before the references, plus `AI工具使用详情.pdf` when AI is used | `xelatex` |
| MCM/ICM | COMAP 2027: complete main solution ≤25 pages including summary, TOC, references, appendices and code; English, ≥12pt; `Report on Use of AI` follows outside the 25-page solution | `pdflatex` |
| Diangong | Current official baseline: cover on page 1; title, abstract and keywords on page 2 with numbering starting at 1; body starts on page 3 with no TOC and is limited to 25 pages; appendices follow; A4 with 2.5 cm margins and Chinese body text in 小四; support ZIP/RAR ≤20 MB | `xelatex` |

Problem-specific deliverables such as letters or memos also count toward the applicable page limit unless the current official problem states otherwise.

## 6. Maintain the AI-use ledger

Because this skill itself uses an AI agent, keep `decision_log.compliance.ai_usage` current. For each material use, record:

- tool, provider, and model/version;
- use date, stage, and purpose;
- key prompt and key response, or paths to those records;
- what was adopted;
- human changes and verification performed.

Use `<skill>/scripts/render_ai_usage.py` in Stage 9 to generate the contest-specific disclosure artifact. Never place API keys, tokens, private data, or credentials in the ledger.

## 7. Render without detached sections

From the user project root, call the installed script explicitly:

```bash
python <skill>/scripts/render_paper.py \
  --competition <competition> \
  --workspace paper_workspace/ \
  --output-dir paper_output/
```

The renderer assembles CUMCM directly and automatically wires MCM/Diangong section files into `main.tex`. A generated PDF with missing section inputs is a failure even if LaTeX exits successfully.

## 8. Score using the active overlay

Use the five Stage 8 dimensions from `competitions/<competition>/rubric_overlay.json` when that competition overrides the baseline. Do not reuse CUMCM's five-part abstract dimensions for MCM or Diangong.

## Exit conditions

- all required sections and problem-specific deliverables exist;
- the paper agrees with the Stage 0–7 decision log;
- the current official rules were rechecked and recorded;
- AI uses and citations are logged;
- `build_code_manifest.py --check` passes and the automatic code appendix matches current source;
- literature quality, parameter provenance, conflicts, source currency, and citation-to-claim audit pass;
- the depth audit is complete and no required evidence unit is missing;
- manuscript evidence, figure audit, Claim evidence level, and any applicable encoding registry pass;
- the active competition's renderer includes every section;
- L1 passes and the final L2 consistency check has no unresolved high-severity conflict.

Then enter `stage_09_review.md`.
