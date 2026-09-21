#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
sanity_check.py — 物理量合理性检查

用法:
    python sanity_check.py <文件1> [文件2 ...] [-o 输出目录]
    python sanity_check.py "B题/附件/*.xlsx"

回答一个问题: 这些数字在物理上讲得通吗?

    反射率 102.74%  → 不可能, 反射掉的光不会比入射的还多
    浓度 -0.03      → 除非题面解释过, 否则不可能
    概率 1.4        → 不可能

判断依据是表头里的单位和词。`反射率 (%)` 这个表头本身就说明:
这列是百分比, 只能落在 0~100。

同时检查:
    - 自变量轴(波数/时间/距离)是否单调、是否等间隔
    - 多个文件的轴是否对齐(能不能直接合并)
"""
from __future__ import annotations

import argparse
import glob
import re
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------- 物理约束库
# (匹配词, 下界, 上界, 依据) —— 上下界为 None 表示不限
RULES = [
    (("反射率", "透射率", "吸收率", "反光率", "reflectance", "transmittance"),
     0, 100, "反射/透射/吸收率是能量占比，不可能为负，也不会超过入射能量"),
    (("概率", "probability", "prob"), 0, 1, "概率必须落在 0~1"),
    (("占比", "比例", "百分比", "百分数", "percent", "pct"),
     0, None, "占比不能为负"),
    (("浓度", "密度", "concentration", "density"), 0, None, "浓度/密度不能为负"),
    (("质量", "重量", "mass", "weight"), 0, None, "质量不能为负"),
    (("长度", "距离", "半径", "直径", "高度", "深度", "厚度", "身高",
      "length", "distance", "radius", "height", "depth"), 0, None, "几何尺寸不能为负"),
    (("时间", "时长", "耗时", "duration", "elapsed"), 0, None, "时长不能为负"),
    (("速率", "速度", "speed"), 0, None, "速率(标量)不能为负；若是有向速度分量则可为负，需人工确认"),
    (("频率", "波数", "frequency", "wavenumber"), 0, None, "频率/波数不能为负"),
    (("次数", "数量", "个数", "计数", "count"), 0, None, "计数不能为负"),
    (("年龄", "age"), 0, 150, "年龄的合理范围"),
    (("温度(k", "绝对温度", "kelvin"), 0, None, "绝对温标不能低于 0 K"),
    (("湿度", "humidity"), 0, 100, "相对湿度是百分比"),
    (("效率", "efficiency"), 0, None, "效率不能为负"),
]

# 表头里的单位 → 附加约束
UNIT_RULES = [
    (("%", "％"), 0, 100, "表头标注单位为 %，按百分数解释时应落在 0~100"),
]

AXIS_HINT = ("波数", "波长", "频率", "时间", "时刻", "距离", "位置", "深度", "角度",
             "序号", "编号", "index", "time", "wavelength", "wavenumber", "freq")


def header_unit(col: str) -> str | None:
    """从 '反射率 (%)' 里取出 '%'"""
    mo = re.search(r"[（(]\s*([^（()）]{1,12})\s*[)）]\s*$", str(col).strip())
    return mo.group(1).strip() if mo else None


def match_rules(col: str):
    c = str(col).lower()
    out = []
    for keys, lo, hi, why in RULES:
        if any(k.lower() in c for k in keys):
            out.append((lo, hi, why))
    u = header_unit(col)
    if u:
        for keys, lo, hi, why in UNIT_RULES:
            if any(k in u for k in keys):
                out.append((lo, hi, why))
    return out


# ---------------------------------------------------------------- 载入
def load_any(p: Path) -> dict[str, pd.DataFrame]:
    if p.suffix.lower() in {".csv", ".txt", ".tsv"}:
        for enc in ("utf-8-sig", "gbk", "utf-8", "latin1"):
            try:
                sep = "\t" if p.suffix.lower() == ".tsv" else None
                return {p.stem: pd.read_csv(p, encoding=enc, sep=sep, engine="python")}
            except UnicodeDecodeError:
                continue
        return {}
    d = pd.read_excel(p, sheet_name=None)
    return {(k if len(d) > 1 else p.stem): v for k, v in d.items()}


# ---------------------------------------------------------------- 检查
def check_bounds(tag, df, out):
    for c in df.columns:
        s = df[c]
        if not pd.api.types.is_numeric_dtype(s):
            continue
        v = s.dropna()
        if v.empty:
            continue

        # 同一列可能同时命中"词"规则和"单位"规则(如 反射率 + %), 会给出同一个界。
        # 按界去重, 只保留最先命中(更具体)的那条依据, 避免同一问题报两遍。
        seen = set()
        for lo, hi, why in match_rules(c):
            # 单位是 % 但数据明显是小数(最大值 <= 1.5), 说明存的是小数不是百分数
            if hi == 100 and float(v.max()) <= 1.5:
                continue
            for bound, op, k, ext in (
                (lo, "<", int((v < lo).sum()) if lo is not None else 0, f"{v.min():.6g}"),
                (hi, ">", int((v > hi).sum()) if hi is not None else 0, f"{v.max():.6g}"),
            ):
                if bound is None or not k or (op, bound) in seen:
                    continue
                seen.add((op, bound))
                out.append(dict(文件=tag, 列=str(c), 违反=f"{op} {bound}",
                                个数=k, 极值=ext, 依据=why))


def check_axis(tag, df, notes):
    """自变量轴: 是否单调、是否等间隔、有无重复"""
    for c in df.columns:
        if not any(k.lower() in str(c).lower() for k in AXIS_HINT):
            continue
        s = df[c]
        if not pd.api.types.is_numeric_dtype(s):
            continue
        v = s.dropna().values
        if len(v) < 3:
            continue
        d = np.diff(v)
        info = []
        if not (np.all(d > 0) or np.all(d < 0)):
            info.append("非单调")
        dup = len(v) - len(np.unique(v))
        if dup:
            info.append(f"{dup} 个重复值")
        if len(d) and np.all(d != 0):
            rel = (d.max() - d.min()) / abs(np.median(d))
            if rel > 1e-6:
                info.append(f"步长不均匀 ({d.min():.6g}~{d.max():.6g})")
        notes.append(dict(文件=tag, 轴=str(c), 点数=len(v),
                          范围=f"{v.min():.6g}~{v.max():.6g}",
                          情况="；".join(info) if info else "单调且等间隔"))


def check_alignment(tables, aligns):
    """多个文件里同名的轴列, 取值是否完全一致 —— 决定能不能直接横向合并"""
    axes: dict[str, list] = {}
    for tag, df in tables:
        for c in df.columns:
            if not any(k.lower() in str(c).lower() for k in AXIS_HINT):
                continue
            if pd.api.types.is_numeric_dtype(df[c]):
                axes.setdefault(str(c).strip(), []).append((tag, df[c].dropna().values))
    for name, items in axes.items():
        if len(items) < 2:
            continue
        base_tag, base = items[0]
        same = all(len(v) == len(base) and np.array_equal(v, base) for _, v in items[1:])
        if same:
            aligns.append(dict(轴=name, 涉及文件=len(items), 结论="完全一致，可直接按行合并"))
        else:
            lens = {t: len(v) for t, v in items}
            aligns.append(dict(轴=name, 涉及文件=len(items),
                               结论=f"不一致，需插值到统一网格后再合并；各文件点数 {lens}"))


# ---------------------------------------------------------------- 报告
def write_report(paths, bad, notes, aligns, out: Path):
    L = ["# 物理量合理性检查", "", "**检查的文件**：", ""]
    for p in paths:
        L.append(f"- `{p}`")
    L.append("")

    L += ["## 1. 物理上讲不通的数值", ""]
    if not bad:
        L += ["没有发现。所有能识别出物理含义的列都落在合理范围内。", ""]
    else:
        L += [f"共 {len(bad)} 处。**这些必须在论文里交代，不能默默改掉。**", "",
              "| 文件 | 列 | 违反 | 个数 | 极值 | 为什么不可能 |", "|---|---|---|---|---|---|"]
        for r in bad:
            L.append(f"| {r['文件']} | {r['列']} | {r['违反']} | **{r['个数']}** | {r['极值']} | {r['依据']} |")
        L += ["", "> 处理建议：先查题面有没有解释（比如 C 题就写明了 X 染色体浓度可能为负）。",
              "> 题面解释过 → 保留，论文里引用题面说明。",
              "> 题面没解释 → 是测量误差还是仪器基线问题？决定截断、剔除还是保留，",
              "> 并写清楚影响了多少个点、对结论有没有实质影响。", ""]

    if notes:
        L += ["## 2. 自变量轴", "", "| 文件 | 轴 | 点数 | 范围 | 情况 |", "|---|---|---|---|---|"]
        for r in notes:
            L.append(f"| {r['文件']} | {r['轴']} | {r['点数']} | {r['范围']} | {r['情况']} |")
        L += ["", "> 步长不均匀会影响插值、求导、傅里叶变换和积分。用到这些方法时先重采样到均匀网格。", ""]

    if aligns:
        L += ["## 3. 多文件能否直接合并", "", "| 轴 | 涉及文件 | 结论 |", "|---|---|---|"]
        for r in aligns:
            L.append(f"| {r['轴']} | {r['涉及文件']} | {r['结论']} |")
        L.append("")

    p = out / "sanity_report.md"
    p.write_text("\n".join(L), encoding="utf-8")
    return p


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="物理量合理性检查")
    ap.add_argument("paths", nargs="+", help="xlsx/csv 文件，支持通配符")
    ap.add_argument("-o", "--out", default="sanity_out")
    a = ap.parse_args()

    files = []
    for pat in a.paths:
        hit = [Path(x) for x in glob.glob(pat)]
        files += hit if hit else ([Path(pat)] if Path(pat).exists() else [])
    files = sorted(set(files))
    if not files:
        raise SystemExit("没有匹配到任何文件")

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    tables, bad, notes = [], [], []
    for f in files:
        for sh, df in load_any(f).items():
            if df.empty:
                continue
            tag = f.stem if sh == f.stem else f"{f.stem}/{sh}"
            tables.append((tag, df))
            check_bounds(tag, df, bad)
            check_axis(tag, df, notes)

    aligns = []
    check_alignment(tables, aligns)

    rp = write_report([str(f) for f in files], bad, notes, aligns, out)
    if bad:
        pd.DataFrame(bad).to_csv(out / "violations.csv", index=False, encoding="utf-8-sig")

    print(f"检查 {len(tables)} 张表，物理上讲不通的数值 {len(bad)} 处")
    for r in bad[:6]:
        print(f"  · {r['文件']} · {r['列']} {r['违反']} 共 {r['个数']} 个（极值 {r['极值']}）")
    print(f"报告: {rp}")


if __name__ == "__main__":
    main()
