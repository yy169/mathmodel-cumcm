# 数学建模国赛全流程 Skill

> CUMCM 国赛 / MCM-ICM 美赛 / 电工杯：从拿到题到交卷前的完整工作流，可直接装进 Claude Code 与 Codex。

它不是"帮你写论文的提示词"，而是**一套带门禁的流程**。每一步要做完什么、缺什么会卡住、哪些结论必须留下证据，都写在文件里：AI 按文件走，你按阶段查。目标是把比赛里最常见的失败挡住——换了模型但摘要没跟着改、第二问重算后第三问还在引用旧结果、关键假设只活在聊天记录里、交卷前才发现页数或 AI 使用披露不合规。

---

## 先说清楚这仓库里哪些是谁写的

| 部分 | 来源 |
|---|---|
| 底座引擎 `skills/mathmodel-skill/` | 第三方开源项目 [handsomeZR-netizen/mathmodel-skill](https://github.com/handsomeZR-netizen/mathmodel-skill) **v6.1.0**（MIT）。基线 103 个文件里 72 个原样保留 |
| 本仓库的增量 | 30 个文件的改动（**+1323 / −479 行**）+ 35 个新文件（**332 KB**），共约 65 个文件；另有 `skills/26math/` 入口调度器 |

逐文件差异见 [CHANGELOG.md](./CHANGELOG.md)，第三方版权声明与免责见 [THIRD_PARTY_NOTICES.md](./THIRD_PARTY_NOTICES.md)。

---

## 两处针对 2026 年新规的修正（原版没有）

《全国大学生数学建模竞赛人工智能工具使用规定（2026 年试行）》自 **2026-09-01** 起施行。原版生成的论文工程有三处对不上，每一项都补了渲染守卫测试：

1. **声明位置**：AI 使用声明原先生成在**参考文献之后**，新规要求在**参考文献之前**。已改。
2. **声明措辞**：「未使用 AI」的固定措辞漏了「**在竞赛过程中**」。已按官方原文补齐。
3. **用了 AI 就没有正文声明**：原版只在支撑材料里出详情 PDF，正文不生成使用声明。已补上正文声明块。

对应测试：`tests/test_ai_usage.py`、`tests/test_render_guard.py`；模板改动在 `templates/latex/cumcm/main.tex` 与 `scripts/render_ai_usage.py`。

> ⚠️ 任何情况下，**当年官方通知优先于本仓库内置规则**。工具帮你少踩坑，不替你签字。

## 一处被撤回的错误参考数据

原版带着一份 `competitions/cumcm/empirical.json`，自称"59 份 CUMCM 公开样本"，喂给打分模块当国赛论文的篇幅/图表分位锚点。但它的题号覆盖 **A–F**，而国赛本科组只有 A/B/C、专科组只有 D/E——这批样本来自别的赛事（研究生"华为杯"），不是国赛。

拿它卡国赛论文会被系统性带偏。本仓库已将其**撤回为空占位**并在 `empirical_notes.md` 写明原因：缺数据时如实报告，不用错锚点。

---

## 安装

本仓库自带引擎，**一条命令 clone、一次拷贝**即可，不需要再去找上游。

### Claude Code（Windows PowerShell）

```powershell
git clone https://github.com/yy169/mathmodel-cumcm.git "$HOME\mathmodel-cumcm"
Copy-Item "$HOME\mathmodel-cumcm\skills\*" "$HOME\.claude\skills\" -Recurse -Force
```

> 别在 `git clone` 的路径里写 `~`。PowerShell 不展开它，实测会在当前目录建一个字面量名为 `~` 的文件夹，然后 skill 永远不会被发现，而且没有任何报错。

### Claude Code（macOS / Linux）

```bash
git clone https://github.com/yy169/mathmodel-cumcm.git ~/mathmodel-cumcm
cp -r ~/mathmodel-cumcm/skills/* ~/.claude/skills/
```

### Codex CLI

把上面命令里的 `.claude` 换成 `.codex` 即可。

### 装完必须重启

Skill 在启动时扫描，热加载不一定生效。

### 验证（30 秒）

```powershell
python "$HOME\.claude\skills\mathmodel-skill\scripts\doctor.py" --competition cumcm --skip-tools
```

预期最后一行：

```
Summary: 10 passed, 0 optional warnings, 0 failed
```

`mcm`、`diangong` 各跑一次同样是 10 passed。`pandoc not found` 属于可选警告，不影响流程，只影响正式编译论文。

原版全新安装是 **9 passed**——第 10 项是本仓库新增的 `workflow-manifest`（阶段执行清单自检）。

跑完整测试（可选，需要先把依赖装上）：

```powershell
pip install -r "$HOME\.claude\skills\mathmodel-skill\templates\shared\requirements.txt"
cd "$HOME\.claude\skills\mathmodel-skill"
python -m pytest tests -q
```

本机实测：`74 passed, 113 subtests passed`，0 失败。不装 `seaborn` 会让 `tests/test_code_starters.py` 在收集阶段报错，与流程本身无关。

### 确认真的接上了

在会话里直接说：

```
用 26math 带我打这一次数学建模竞赛，从读题到交卷。
```

如果回答里提到"核心引擎不存在或不可读"，说明拷贝时只拷了 `26math` 没拷 `mathmodel-skill`——它俩必须是同级目录。

---

## 三档模式

| 模式 | 何时用 |
|---|---|
| `standard` | 默认 |
| `championship` | 明确要求冲刺、终稿红队、提交前冠军级审查 |
| `economy` | 额度敏感 |

## 里面有什么

- **10 个阶段**：读题 → 分析 → 建模选择 → 求解 → 子问题循环 → 稳健性 → 检验 → 写作 → 评审 → 交付。
- **入口调度器 `26math`**：卡住四条容易在赶工时出事的行为——引擎读不到就报错而不是假装在干活；你只要单项服务时不无差别跑全流程；你说"先讨论"时未经确认不改文件；统计术语（信度／显著性／两类错误／功效／OC 概率／后验区间）被混用时先过语义门禁，映射没做完不锁数值也不锁摘要措辞。
- **15 个体检脚本**（本仓库新增，3142 行）：`audit_data.py` 数据体检、`sanity_check.py` 结果合理性、`check_manuscript_hygiene.py` 稿件卫生、`check_claim_evidence.py` 主张—证据对应、`check_cross_file_consistency.py` 跨文件一致性、`check_figure_audit.py` 图表溯源、`check_requirement_coverage.py` 题目要求覆盖、`run_readiness_audit.py` 交卷前就绪度、`workflow_manager.py` 阶段状态机等。
- **13 篇流程文档**（本仓库新增，2662 行）：外部审查接收、图表证据体系、交付门禁、统计语义门禁、模型路线确认、文献质量控制、只做题目信息的文献起步、改稿案例时间线、优化搜索严谨性等；另有 `competitions/cumcm/paper_writing.md` 国赛写作规则一篇（1099 行）。

## 没有随本仓库发布的东西

配套的 `mathmodel-latex-skill`（另一套排版模板包，20 个文件）**没有许可证文件、出处也无法确认**，因此不包含在本仓库内。本仓库自带的 `templates/latex/` 已覆盖 CUMCM 与 MCM 的模板需求。

---

## 许可

MIT。见 [LICENSE](./LICENSE)。基线引擎的版权声明保留在 `skills/mathmodel-skill/LICENSE`。

## 致谢

底座引擎作者 [handsomeZR-netizen](https://github.com/handsomeZR-netizen)。本仓库是在打 2026 赛季的过程中改出来的，改动部分按 MIT 开放，欢迎提问题。
