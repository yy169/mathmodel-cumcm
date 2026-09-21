# 论文样本维护区

> 本目录只用于维护者离线更新描述性统计。运行时工作流不读取原始 PDF，也不需要此目录存在。

## 当前口径

**本目录当前没有语料。** 此前的 91 份来源清单因来源标注错误已整体撤回，原始 PDF 未保留在本机。

- 撤回原因与重建口径: [`../../competitions/cumcm/empirical_notes.md`](../../competitions/cumcm/empirical_notes.md)
- 错误如何发生、脚本有哪些已知缺口: [`_DOWNLOAD_REPORT.md`](./_DOWNLOAD_REPORT.md)

重建前请先读这两份文件。任何新语料都必须逐一核验来源到一手出处 —— 目录名和文件名不构成证据，上一版正是栽在这里。

## 更新流程

仅处理你有权访问和分析的文件，并保留来源、年份、题号与使用条件。不要把原始论文 PDF 提交到本仓库。

```bash
python -m pip install -r scripts/requirements-maintenance.txt

python scripts/ingest_papers.py \
  --papers-dir /path/to/authorized-papers \
  --output /tmp/empirical_distribution.md
```

更新后必须人工检查：

1. 来源数量与成功提取数量是否分别记录；
2. 图片型、乱码和正文过短文件是否被排除；
3. 年份与题型构成是否造成明显偏差；
4. 分位数是否只被描述为样本观察，而非官方阈值；
5. `competitions/cumcm/empirical.json`、说明文档与测试是否同步。

下载与提取工具的依赖、参数和限制见 [`../../scripts/README.md`](../../scripts/README.md)。
