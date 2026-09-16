# 26math

> 大学生数学建模竞赛的工作流入口 —— 支持 CUMCM 国赛、MCM/ICM 美赛和电工杯。
> 适用于 Claude Code 与 Codex CLI。

[![License](https://img.shields.io/badge/license-MIT-22c55e)](./LICENSE)
[![Harness](https://img.shields.io/badge/Claude%20Code%20%7C%20Codex-skill-6f42c1)](#安装)

比赛里最常见的失败不是「模型不够聪明」，而是流程散掉：换了模型但摘要没跟着改，第二问重算后第三问还在引用旧结果，关键假设只活在聊天记录里，交卷前才发现页数或 AI 使用披露不合规。

`26math` 是这套流程的入口。**它本身只有 1.4 KB**，真正干活的是 [`mathmodel-skill`](https://github.com/handsomeZR-netizen/mathmodel-skill) 核心引擎；`26math` 负责把请求接进去，并卡住四条容易在赶工时出事的行为。

## 它卡住了什么

- **引擎读不到就报错** —— 不偷偷退回临时提示词流程假装在干活
- **不无差别跑全流程** —— 只要求读题、调代码、单项审查或排版时，只进对应阶段
- **先讨论再动手** —— 用户说「先聊聊」时，未经确认不改文件、不启动全量求解
- **统计语义先对齐** —— 题目把「信度 / 显著性 / 两类错误 / 功效 / OC 概率 / 后验区间」混着用时，先走统计语义门禁；映射没做完，不锁数值也不锁摘要措辞

## 三档模式

| 模式 | 何时用 |
|---|---|
| `standard` | 默认 |
| `championship` | 明确要求冲刺、终稿红队、提交前冠军级审查 |
| `economy` | 额度敏感 |

---

## 安装

### ⚠️ 必读：这个 skill 单独装不能用

`26math` 通过相对路径 `../mathmodel-skill/` 找核心引擎，所以**两者必须是同级目录**，缺一不可：

```
skills/
├── 26math/            ← 本仓库
└── mathmodel-skill/   ← 核心引擎，必须一起装
```

核心引擎是 [@handsomeZR-netizen](https://github.com/handsomeZR-netizen) 的独立 MIT 项目，本仓库不包含、也不重新分发它的任何代码。

### Claude Code

```bash
git clone https://github.com/handsomeZR-netizen/mathmodel-skill.git ~/.claude/skills/mathmodel-skill
git clone https://github.com/yy169/26math.git ~/.claude/skills/26math
```

Windows PowerShell 里 `~` 可能不展开，用完整路径：

```powershell
git clone https://github.com/handsomeZR-netizen/mathmodel-skill.git "$HOME\.claude\skills\mathmodel-skill"
git clone https://github.com/yy169/26math.git "$HOME\.claude\skills\26math"
```

### Codex CLI

把上面命令里的 `.claude` 换成 `.codex` 即可：

```bash
git clone https://github.com/handsomeZR-netizen/mathmodel-skill.git ~/.codex/skills/mathmodel-skill
git clone https://github.com/yy169/26math.git ~/.codex/skills/26math
```

### 验证装对了

装完**重启 Claude Code / Codex**（skill 在启动时扫描，热加载不一定生效），然后：

```bash
python ~/.claude/skills/mathmodel-skill/scripts/doctor.py --competition cumcm --skip-tools
```

上游 v6.1.0 的预期输出是 `Summary: 9 passed, 0 optional warnings, 0 failed`。`pandoc not found` 是可选警告，不影响主流程，只影响正式编译论文。

再确认 `26math` 本身被识别到 —— 在会话里直接说：

```
Use 26math to guide my CUMCM team from kickoff to submission.
```

如果回复里提到「核心引擎不存在或不可读」，就是 `mathmodel-skill` 没装到同级目录。

---

## 已知问题

**上游核心引擎当前版本（v6.1.0，最后更新 2026-07）有两处需要注意**，装之前请知悉：

1. **AI 使用披露不符合 2026 新规。** 《全国大学生数学建模竞赛人工智能工具使用规定（2026 年试行）》自 2026-09-01 起施行，要求在**参考文献之前**放唯一一条 AI 工具使用声明，措辞二者择一、按原文固定。v6.1.0 把声明放在参考文献之后，未使用声明漏了「在竞赛过程中」，且使用 AI 时不生成正文声明（只生成支撑材料里的详情 PDF）。**提交前务必对照当年官方文件自行核对。**

2. **`competitions/cumcm/empirical.json` 的来源标注存疑。** 其分位数据的样本题号覆盖 A–F，而国赛本科组只设 A/B/C、专科组只设 D/E，不设 F 题。这批数据很可能来自其他赛事，不宜当作国赛基准使用。

这两点属于上游项目，不在本仓库范围内。任何情况下，**当年官方通知都优先于任何工具的内置规则**。

## 依赖与致谢

核心引擎 [`mathmodel-skill`](https://github.com/handsomeZR-netizen/mathmodel-skill) 由 [@handsomeZR-netizen](https://github.com/handsomeZR-netizen) 开发并以 MIT 授权发布。本仓库只包含入口层。

## 授权

MIT，见 [LICENSE](./LICENSE)。
