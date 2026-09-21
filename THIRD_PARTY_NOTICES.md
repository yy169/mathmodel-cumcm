# 第三方来源与版权声明

## 基线引擎

`skills/mathmodel-skill/` 来自第三方开源项目：

- 仓库：https://github.com/handsomeZR-netizen/mathmodel-skill
- 版本：v6.1.0，基线 commit `d3941e14d8693fb4a79948e59afff3098734127e`（2026-07-22）
- 许可：MIT，Copyright (c) 2026 handsomeZR-netizen

原作者的完整许可证文本保留在 `skills/mathmodel-skill/LICENSE`，原版的第三方说明保留在 `skills/mathmodel-skill/THIRD_PARTY_NOTICES.md`，两者均未改动。

本仓库在其之上做了 30 个文件的改动与 35 个文件的新增，逐文件清单见 [CHANGELOG.md](./CHANGELOG.md)。改动部分按 MIT 授权（Copyright (c) 2026 yy169），但这不构成对基线部分的所有权声明——基线代码与文档的版权归原作者。

## 国赛 LaTeX 模板

`skills/mathmodel-skill/templates/latex/cumcm/main.tex` 由原作者依据公开竞赛格式要求独立编写，不含 `latexstudio/CUMCMThesis` 的代码或素材，本仓库同样不重新分发任何第三方模板包。它是排版辅助，不是官方模板，也不代表主办方背书。

## 未随本仓库发布的东西

配套的 `mathmodel-latex-skill`（另一套 MCM/ICM 与 CUMCM 的 LaTeX 项目生成包）**没有许可证文件、作者与出处无法确认**，因此没有包含进来。

## 外部研究材料

比赛规则、链接指向的论文、数据集、网站与商标等外部资料不因本仓库的 MIT 许可而改变其原有权利。仓库里的范文清单只保留来源链接与核对结论，不含任何他人论文原文；派生的描述性统计不转移所有权或再分发权。用户对自己下载与提交的材料自行负责。

## 运行时依赖

Python、Pandoc、TeX Live / MiKTeX、XeLaTeX、CTeX 及 requirements 文件中列出的 Python 包由用户自行安装，本仓库不内置，各自遵循其原有许可。
