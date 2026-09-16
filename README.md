# 26math

> 大学生数学建模竞赛的工作流入口 —— 支持 CUMCM 国赛、MCM/ICM 美赛和电工杯。

[![License](https://img.shields.io/badge/license-MIT-22c55e)](./LICENSE)
[![Harness](https://img.shields.io/badge/Claude%20Code%20%7C%20Codex-skill-6f42c1)](#安装)

比赛里最常见的失败不是「模型不够聪明」，而是流程散掉：换了模型但摘要没跟着改，第二问重算后第三问还在引用旧结果，关键假设只活在聊天记录里，交卷前才发现页数或 AI 使用披露不合规。

`26math` 是这套流程的入口。它本身很薄 —— 真正干活的是 [`mathmodel-skill`](https://github.com/handsomeZR-netizen/mathmodel-skill) 核心引擎，`26math` 负责把请求接进去，并约束几条容易出事的行为。

## 它约束了什么

- **不退回旧提示词流程** —— 核心引擎读不到就直接报错，不偷偷降级
- **不无差别跑全流程** —— 只要求读题、调代码、单项审查或排版时，只进对应阶段
- **先讨论再动手** —— 用户说「先聊聊」时，未经确认不改文件、不启动全量求解
- **统计语义先对齐** —— 题目把「信度 / 显著性 / 两类错误 / 功效 / OC 概率 / 后验区间」混着用时，先走统计语义门禁，映射没做完不锁数值和摘要

## 三档模式

| 模式 | 何时用 |
|---|---|
| `standard` | 默认 |
| `championship` | 明确要求冲刺、终稿红队、提交前冠军级审查 |
| `economy` | 额度敏感 |

## 安装

**前置依赖**：本 skill 需要 [`mathmodel-skill`](https://github.com/handsomeZR-netizen/mathmodel-skill)（MIT，作者 [@handsomeZR-netizen](https://github.com/handsomeZR-netizen)）。两者必须是**同级目录** —— `26math` 用 `../mathmodel-skill/` 这个相对路径找核心引擎。

目录结构应当是：

```
skills/
├── 26math/            ← 本仓库
└── mathmodel-skill/   ← 核心引擎，需另行安装
```

### Claude Code

```bash
git clone https://github.com/handsomeZR-netizen/mathmodel-skill.git ~/.claude/skills/mathmodel-skill
git clone https://github.com/yy169/26math.git ~/.claude/skills/26math
```

### Codex CLI

```bash
git clone https://github.com/handsomeZR-netizen/mathmodel-skill.git ~/.codex/skills/mathmodel-skill
git clone https://github.com/yy169/26math.git ~/.codex/skills/26math
```

装好后直接触发：

```
Use 26math to guide my CUMCM team from kickoff to submission.
```

如果报「核心引擎不存在或不可读」，说明 `mathmodel-skill` 没装到同级目录。

## 致谢

核心引擎 [`mathmodel-skill`](https://github.com/handsomeZR-netizen/mathmodel-skill) 由 [@handsomeZR-netizen](https://github.com/handsomeZR-netizen) 开发并以 MIT 授权发布。本仓库只包含入口层，不包含也不重新分发核心引擎的任何代码。

## 授权

MIT，见 [LICENSE](./LICENSE)。
