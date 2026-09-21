#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
audit_data.py — 数模竞赛附件数据体检

用法:
    python audit_data.py <附件.xlsx|csv> [-p 题面.pdf] [-o 输出目录]

产出:
    <out>/data_audit_report.md      体检报告
    <out>/data_decision_log.csv     待决策清单(填"处理方式+理由", 直接进论文)
    <out>/fig_missing.png           缺失分布图

设计原则:
    1. 只报告事实, 绝不自动修数据 —— 论文里要写的是"为什么这么处理"。
    2. 宁可漏报不可刷屏: 同类问题聚合成一条, 误报会让人整份不看。
    3. 带 -p 时把题面里写死的约束(范围/阈值/分组)拿来和数据对账 ——
       "题面说的和数据给的不一致"是最容易写进论文的加分点。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

CRIT, WARN, INFO = "阻断", "警告", "提示"
SEV_ORDER = {CRIT: 0, WARN: 1, INFO: 2}


class Findings:
    def __init__(self):
        self.rows: list[dict] = []

    def add(self, sev, cat, sheet, col, desc, action=""):
        self.rows.append(dict(严重度=sev, 分类=cat, 表=sheet, 列=col, 发现=desc, 建议动作=action))

    def to_frame(self):
        df = pd.DataFrame(self.rows)
        if df.empty:
            return df
        df["_o"] = df["严重度"].map(SEV_ORDER)
        return df.sort_values(["_o", "分类", "表"]).drop(columns="_o").reset_index(drop=True)


# ============================================================ 载入
def load_tables(path: Path) -> dict[str, pd.DataFrame]:
    if path.suffix.lower() in {".csv", ".txt", ".tsv"}:
        for enc in ("utf-8-sig", "gbk", "utf-8", "latin1"):
            try:
                sep = "\t" if path.suffix.lower() == ".tsv" else None
                return {path.stem: pd.read_csv(path, encoding=enc, sep=sep, engine="python")}
            except UnicodeDecodeError:
                continue
        raise SystemExit(f"无法解码 {path}")
    return pd.read_excel(path, sheet_name=None)


def load_problem_text(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        try:
            import fitz
        except ImportError:
            print("[warn] 未装 pymupdf，跳过题面对照", file=sys.stderr)
            return ""
        with fitz.open(path) as doc:
            return "\n".join(pg.get_text() for pg in doc)
    for enc in ("utf-8", "gbk", "utf-8-sig"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return ""


# ============================================================ 列语义识别
ID_HINT = ("代码", "编号", "编码", "样本号", "样本序号", "序号", "id", "code", "no.")
CONST_PER_ID = ("身高", "年龄", "出生", "性别", "gender", "height", "birth")
TIME_HINT = ("孕周", "周数", "日期", "时间", "月经", "date", "time", "week")
NONNEG_HINT = ("浓度", "比例", "数量", "次数", "读段", "个数", "率", "年龄", "身高", "体重",
               "count", "num", "ratio", "rate")
RATIO_HINT = ("比例", "率", "含量", "浓度", "ratio", "rate", "pct", "百分")


def hits(col, keys) -> bool:
    c = str(col).lower()
    return any(k.lower() in c for k in keys)


def is_num(s: pd.Series) -> bool:
    return pd.api.types.is_numeric_dtype(s)


def is_id_col(name, s: pd.Series, n: int) -> bool:
    """ID 列: 名字像 ID, 且取值离散重复或全唯一"""
    if not hits(name, ID_HINT):
        return False
    u = s.nunique(dropna=True)
    return u >= 2


def datetime_ratio(s: pd.Series) -> float:
    v = s.dropna().astype(str).str.strip()
    v = v[v != ""]
    if v.empty:
        return 0.0
    with pd.option_context("mode.chained_assignment", None):
        ok = pd.to_datetime(v, errors="coerce", format="mixed")
    return float(ok.notna().mean())


def numeric_ratio(s: pd.Series) -> float:
    v = s.dropna().astype(str).str.strip()
    v = v[v != ""]
    if v.empty:
        return 0.0
    return float(pd.to_numeric(v, errors="coerce").notna().mean())


def looks_yyyymmdd(s: pd.Series) -> bool:
    if not is_num(s):
        return False
    v = s.dropna()
    if v.empty:
        return False
    return bool(((v >= 19000101) & (v <= 21001231)).mean() > 0.9 and (v % 1 == 0).all())


def classify_columns(df: pd.DataFrame) -> dict[str, str]:
    """给每列打一个语义标签, 后续检查据此分流(避免对 ID 列建议'转成数字'这类误报)"""
    n = len(df)
    out = {}
    for c in df.columns:
        s = df[c]
        if s.isna().all():
            out[c] = "空列"
        elif is_id_col(c, s, n):
            out[c] = "标识"
        elif looks_yyyymmdd(s):
            out[c] = "日期数值"
        elif is_num(s):
            out[c] = "数值"
        elif datetime_ratio(s) > 0.8:
            out[c] = "日期文本"
        elif s.nunique(dropna=True) <= 20 and numeric_ratio(s) < 0.5:
            out[c] = "类别"
        elif 0 < numeric_ratio(s) < 1:
            out[c] = "混合文本"
        else:
            out[c] = "待解析文本"
    return out


# ============================================================ 检查
def check_structure(name, df, kinds, F):
    for c in df.columns:
        if str(c) != str(c).strip():
            F.add(WARN, "列名", name, repr(str(c)), "列名首尾有空白字符",
                  "strip 列名；否则按名取列或跨表合并会静默失败")
        if re.fullmatch(r"Unnamed:\s*\d+", str(c)):
            F.add(INFO, "列名", name, str(c), "无表头列",
                  "确认是占位空列还是漏掉的表头")

    for c in pd.Index(df.columns)[pd.Index(df.columns).duplicated()].unique():
        F.add(CRIT, "列名", name, str(c), "存在同名列", "重命名，否则 df[col] 取到 DataFrame")

    k = int(df.duplicated().sum())
    if k:
        F.add(WARN, "重复", name, "-", f"整行完全重复 {k} 行", "确认是真重复还是有意义的多次记录")

    empt = [str(c) for c in df.columns if kinds[c] == "空列"]
    if empt:
        F.add(INFO, "空列", name, "、".join(empt[:8]), f"{len(empt)} 个整列为空",
              "若因本表天然无此字段(如女胎无 Y 染色体)属结构性缺失，论文中说明而非当缺失处理")

    for c in df.columns:
        s = df[c]
        if kinds[c] != "空列" and s.nunique(dropna=True) == 1:
            F.add(WARN, "常量列", name, str(c), f"全表只有一个取值: {s.dropna().iloc[0]!r}",
                  "不能作为特征；若这本该是标签列，则该表无法做有监督学习")


def check_types(name, df, kinds, F):
    for c in df.columns:
        k, s = kinds[c], df[c]
        if k in ("空列", "数值", "标识"):
            continue
        if k == "日期数值":
            F.add(WARN, "类型", name, str(c), "数值列形如 YYYYMMDD，实为日期",
                  "转 datetime；否则做差、排序、算间隔都会错")
        elif k == "日期文本":
            F.add(WARN, "类型", name, str(c), "日期以文本存储",
                  "统一 parse 成 datetime，并检查 parse 失败的行")
        elif k == "混合文本":
            bad = s.dropna().astype(str).str.strip()
            bad = bad[pd.to_numeric(bad, errors="coerce").isna() & (bad != "")]
            F.add(WARN, "类型", name, str(c),
                  f"{numeric_ratio(s):.0%} 可转数字，其余为文本，例: {sorted(bad.unique())[:5]}",
                  "定编码规则(如 '≥3'→3 并另开哑变量)，并在论文写明该规则")
        elif k == "待解析文本":
            F.add(WARN, "类型", name, str(c),
                  f"文本但结构化，需写解析函数，例: {sorted(s.dropna().astype(str).unique())[:4]}",
                  "写解析函数转数值，并统计解析失败行数")
        elif k == "类别":
            vc = s.value_counts(dropna=True)
            F.add(INFO, "类别列", name, str(c),
                  f"{len(vc)} 个类别: " + "、".join(f"{i}({v})" for i, v in vc.head(6).items()),
                  "确认类别是否需要合并；若为标签列，注意类别不平衡")


def check_missing(name, df, kinds, F):
    n = len(df)
    for c in df.columns:
        if kinds[c] == "空列":
            continue
        k = int(df[c].isna().sum())
        if k == 0:
            continue
        rate = k / n
        sev = CRIT if rate > 0.5 else (WARN if rate > 0.05 else INFO)
        extra = ""
        if rate > 0.5 and kinds[c] == "类别":
            extra = ("该列非空值是类别编码 —— 空白很可能表示'无此情况'而非'没记录'。"
                     "若如此，绝不能填补，应转成 有/无 的二值列。")
        F.add(sev, "缺失", name, str(c), f"缺失 {k}/{n} ({rate:.1%})",
              extra or "先判断是'没记录'还是'空白本身有含义'，后者不可填补")


def check_values(name, df, kinds, F):
    rows = []
    for c in df.columns:
        if kinds[c] not in ("数值",):
            continue
        v = df[c].dropna()
        if v.empty:
            continue

        neg = int((v < 0).sum())
        flagged_neg = False
        if neg and hits(c, NONNEG_HINT):
            F.add(WARN, "取值域", name, str(c),
                  f"名称暗示非负，却有 {neg} 个负值 (min={v.min():.4g})",
                  "先查题面是否解释了负值来源：有解释就保留并在论文说明，无解释才按异常处理")
            flagged_neg = True

        if hits(c, RATIO_HINT):
            hi = float(v.max())
            if hi <= 1.0:
                oob = int((v > 1).sum()) + (0 if flagged_neg else int((v < 0).sum()))
                if oob:
                    F.add(WARN, "取值域", name, str(c), f"比例类列 {oob} 个值超出 [0,1]", "核对量纲")
            elif 1 < hi <= 100:
                F.add(INFO, "量纲", name, str(c),
                      f"比例类列范围 {v.min():.4g}~{hi:.4g}，像百分数而非小数",
                      "全表统一量纲，否则与其他比例列相乘/比较会差 100 倍")

        q1, q3 = v.quantile(.25), v.quantile(.75)
        iqr = q3 - q1
        if iqr > 0:
            k = int(((v < q1 - 3 * iqr) | (v > q3 + 3 * iqr)).sum())
            if k:
                rows.append((str(c), k, k / len(v), float(v.min()), float(v.max())))

    if rows:
        rows.sort(key=lambda r: -r[2])
        top = "；".join(f"{c} {k}个({p:.1%})" for c, k, p, _, _ in rows[:5])
        sev = WARN if rows[0][2] > 0.01 else INFO
        F.add(sev, "离群", name, f"{len(rows)} 列",
              f"IQR 3 倍界外点，最多的: {top}",
              "离群≠错误。逐列判断是录入错误、真实极端值，还是有意义的子群；详见报告附录")
    return rows


def check_identity(name, df, F):
    cols = {str(c).strip(): c for c in df.columns}
    h = next((cols[k] for k in cols if "身高" in k or "height" in k.lower()), None)
    w = next((cols[k] for k in cols if "体重" in k or "weight" in k.lower()), None)
    b = next((cols[k] for k in cols if "bmi" in k.lower()), None)
    if not (h and w and b) or not all(is_num(df[x]) for x in (h, w, b)):
        return
    hv = df[h].astype(float)
    hv = hv / 100 if hv.median() > 3 else hv
    d = (df[b].astype(float) - df[w].astype(float) / hv**2).abs()
    k = int((d > 0.5).sum())
    if k:
        F.add(CRIT, "恒等式", name, f"{b} ← {h},{w}",
              f"{k} 行 BMI 与身高体重不自洽 (最大偏差 {d.max():.2f})",
              "决定以哪一方为准并说明理由；不一致行多为录入错误")
    else:
        F.add(INFO, "恒等式", name, f"{b} ← {h},{w}",
              f"BMI 与身高体重自洽 (最大偏差 {d.max():.4f})", "可直接使用，无需重算")


def check_repeated_measures(name, df, kinds, F):
    n = len(df)
    ids = [c for c in df.columns if kinds[c] == "标识" and 1 < df[c].nunique(dropna=True) < n]
    for c in ids:
        g = df.groupby(c).size()
        if g.max() <= 1:
            continue
        F.add(CRIT, "独立性", name, str(c),
              f"{g.size} 个个体 / {n} 条记录，每个体 {g.min()}~{g.max()} 条 (均值 {g.mean():.2f})",
              "同一个体多次测量不是独立样本。按行做回归/检验会高估显著性和 R²，"
              "应改用混合效应模型(个体随机效应)或先按个体聚合，并在论文中明确说明")

        # 判断每列在个体内是"恒定属性"还是"随次变化的观测":
        # 绝大多数个体只有一个取值 → 本该恒定, 少数不一致的就是录入矛盾;
        # 普遍多值 → 是观测量, 可以拿来当复合键查重复。
        for col in df.columns:
            if col == c or kinds[col] == "空列":
                continue
            nu = df.groupby(c)[col].nunique(dropna=True)
            const_frac = float((nu <= 1).mean())
            bad = int((nu > 1).sum())

            if const_frac == 1.0:
                continue                                   # 完全恒定, 正常
            if const_frac >= 0.85 or hits(col, CONST_PER_ID):
                if bad:
                    F.add(WARN, "一致性", name, f"{c} → {col}",
                          f"{bad}/{nu.size} 个个体的「{col}」前后取值不一致"
                          f"（{const_frac:.0%} 的个体是唯一值，说明该字段本应恒定）",
                          "属录入矛盾。定统一规则(取众数/取首次/整条剔除)，"
                          "写进论文并说明影响了多少样本")
            elif hits(col, TIME_HINT):
                k = int(df.duplicated(subset=[c, col]).sum())
                if k:
                    F.add(WARN, "重复", name, f"{c}+{col}",
                          f"同一个体在同一「{col}」下出现 {k} 条重复记录",
                          "查是一次采血多次检测还是录入重复；前者需决定取哪条或取均值，并说明")


def check_cross_sheet(sheets, kinds_all, F):
    if len(sheets) < 2:
        return
    norm = {k: {str(c).strip() for c in v.columns} for k, v in sheets.items()}
    names = list(sheets)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            oa, ob = sorted(norm[a] - norm[b]), sorted(norm[b] - norm[a])
            if oa or ob:
                F.add(INFO, "跨表", f"{a} vs {b}", "-",
                      f"列名不一致；仅「{a}」有: {oa[:6]}；仅「{b}」有: {ob[:6]}",
                      "区分是业务性差异(该表天然无此字段)还是表头写法不同")
            for c in sorted(norm[a] & norm[b]):
                ca = next(x for x in sheets[a].columns if str(x).strip() == c)
                cb = next(x for x in sheets[b].columns if str(x).strip() == c)
                if kinds_all[a][ca] != kinds_all[b][cb]:
                    F.add(WARN, "跨表", f"{a} vs {b}", c,
                          f"同名列语义类型不一致: {kinds_all[a][ca]} vs {kinds_all[b][cb]}",
                          "合并前统一类型，否则 concat 后整列退化成 object")


# ============================================================ 题面对照
UNIT_COL_HINT = {
    "周": ("孕周", "周数", "week"),
    "%": ("比例", "率", "含量", "浓度", "pct"),
    "岁": ("年龄", "age"),
    "kg": ("体重", "weight"),
    "cm": ("身高", "height"),
}
CMP = {"达到或高于": ">=", "不低于": ">=", "至少": ">=", "高于": ">", "大于": ">", "超过": ">",
       "≥": ">=", ">=": ">=", "不超过": "<=", "低于": "<", "小于": "<", "≤": "<=", "<=": "<="}

RANGE_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(周|%|岁|kg|cm)?\s*[~～\-—－至到]\s*(\d+(?:\.\d+)?)\s*(周|%|岁|kg|cm)?")
THRESH_RE = re.compile(
    r"(达到或高于|不低于|不超过|至少|高于|低于|大于|小于|超过|≥|≤|>=|<=)\s*(\d+(?:\.\d+)?)\s*(周|%|岁|kg|cm)?")


# 列名里没有区分度的通用词, 匹配前先剥掉, 否则"XX的比例"会被任何提到比例的句子命中
GENERIC = ("孕妇", "检测", "染色体的", "的", "占总", "总", "原始", "数据",
           "比例", "含量", "浓度", "数量", "个数", "次数", "读段数", "指标", "值", "率")


def _core(colname: str) -> str:
    """取列名中有区分度的部分"""
    s = str(colname).strip()
    for g in GENERIC:
        s = s.replace(g, "")
    return re.sub(r"[\s（）()、，,:：]", "", s)


def _overlap(ctx: str, core: str) -> float:
    """core 的字符有多大比例出现在上下文里"""
    ch = set(core)
    if not ch:
        return 0.0
    return len(ch & set(ctx)) / len(ch)


def _match_column(ctx: str, unit: str, sheets, kinds_all, min_chars=2, min_frac=0.6):
    """
    按 单位类别 + 列名核心词与上下文的字符重合度 找目标列。

    只靠单位会把「GC 含量 40%~60%」套到所有带"比例"的列上, 所以要求列名剥掉
    通用词后剩下的核心词, 至少 min_chars 个字符出现在题面上下文中, 且覆盖率
    不低于 min_frac。宁可漏配也不错配。
    """
    hints = UNIT_COL_HINT.get(unit, ())
    out = []
    for sn, df in sheets.items():
        for c in df.columns:
            if kinds_all[sn][c] not in ("数值", "待解析文本", "混合文本"):
                continue
            cn = str(c).strip()
            if hints and not hits(cn, hints):
                continue
            core = _core(cn)
            if len(set(core) & set(ctx)) >= min_chars and _overlap(ctx, core) >= min_frac:
                out.append((sn, c))
    return out


def _series_numeric(df, col, kinds):
    """把列取成数值 Series；'11w+6' 这类按 周+天/7 解析"""
    s = df[col]
    if kinds[col] == "数值":
        return s.dropna().astype(float)
    v = s.dropna().astype(str)
    p = v.str.extract(r"^\s*(\d+)\s*w(?:\+(\d+))?\s*$")
    if p[0].notna().mean() > 0.8:
        return (p[0].astype(float) + p[1].fillna(0).astype(float) / 7).dropna()
    return pd.to_numeric(v, errors="coerce").dropna()


MAX_MATCH = 4  # 一条约束匹配到超过这么多列, 判定为匹配不可靠, 只提示不断言


def check_against_problem(text, sheets, kinds_all, F):
    """把题面里写死的数值约束拿来和数据对账。返回 (对账明细, 未匹配约束)"""
    if not text.strip():
        return [], []
    flat = re.sub(r"\s+", "", text)
    checked, unmatched = [], []
    seen_range, seen_thresh = set(), set()

    def ctx_of(mo, before=28, after=18):
        return flat[max(0, mo.start() - before): mo.end() + after]

    # --- 区间约束: 题面写了范围, 看数据有多少落在外面 ---
    for mo in RANGE_RE.finditer(flat):
        unit = mo.group(4) or mo.group(2)
        if not unit:
            continue
        lo, hi = float(mo.group(1)), float(mo.group(3))
        if hi <= lo or (lo, hi, unit) in seen_range:
            continue
        seen_range.add((lo, hi, unit))
        ctx = ctx_of(mo)
        cand = _match_column(ctx, unit, sheets, kinds_all)
        if not cand:
            unmatched.append(("区间", f"{lo:g}~{hi:g}{unit}", ctx))
            continue
        if len(cand) > MAX_MATCH:
            unmatched.append(("区间(匹配过宽)", f"{lo:g}~{hi:g}{unit}",
                              f"{ctx}  → 命中 {len(cand)} 列，未自动判定"))
            continue
        for sn, col in cand:
            v = _series_numeric(sheets[sn], col, kinds_all[sn])
            if v.empty:
                continue
            pct = unit == "%" and v.max() <= 1.5
            L, H = (lo / 100, hi / 100) if pct else (lo, hi)
            k = int(((v < L) | (v > H)).sum())
            checked.append((f"{lo:g}~{hi:g}{unit}", sn, str(col), len(v), k,
                            f"{v.min():.4g}~{v.max():.4g}"))
            if k:
                sev = WARN if k / len(v) > 0.01 else INFO
                F.add(sev, "题面对照", sn, str(col),
                      f"题面写「{lo:g}~{hi:g}{unit}」，实际 {k}/{len(v)} 行 ({k/len(v):.1%}) 在区间外"
                      f"，数据范围 {v.min():.4g}~{v.max():.4g}",
                      "题面与数据不一致。别直接按题面裁剪 —— 先判断是题面表述宽泛还是数据有异常；"
                      "无论取哪种，论文里都要写出这个差异和你的处理依据")

    # --- 阈值约束: 题面给了判定线, 算达标比例 ---
    for mo in THRESH_RE.finditer(flat):
        word, num, unit = mo.group(1), float(mo.group(2)), mo.group(3)
        op = CMP.get(word)
        if not unit or not op:
            continue
        # 阈值句里主语通常在数值之前("Y染色体浓度达到或高于4%"), 后窗开大会把
        # 下一个分句的主语("、女胎的X染色体浓度…")也吃进来, 造成错配。
        ctx = ctx_of(mo, before=28, after=6)
        cand = _match_column(ctx, unit, sheets, kinds_all)
        if not cand:
            if (word, num, unit) not in seen_thresh:
                seen_thresh.add((word, num, unit))
                unmatched.append(("阈值", f"{word}{num:g}{unit}", ctx))
            continue
        if len(cand) > MAX_MATCH:
            continue
        for sn, col in cand:
            key = (sn, str(col), num, unit)   # 同一列同一数值只报一次, 不分 >= 还是 >
            if key in seen_thresh:
                continue
            seen_thresh.add(key)
            v = _series_numeric(sheets[sn], col, kinds_all[sn])
            if v.empty:
                continue
            thr = num / 100 if unit == "%" and v.max() <= 1.5 else num
            frac = float((v >= thr).mean() if op == ">=" else
                         (v > thr).mean() if op == ">" else
                         (v <= thr).mean() if op == "<=" else (v < thr).mean())
            F.add(INFO, "题面对照", sn, str(col),
                  f"题面阈值「{word}{num:g}{unit}」→ 满足占 {frac:.1%}（{len(v)} 行）",
                  "这个比例往往就是解题要用的关键量，可直接引用；"
                  "若是 0% 或 100%，先确认量纲和列匹配对不对")

    return checked, unmatched


# ============================================================ 图 & 报告
def plot_missing(sheets, out: Path):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
        plt.rcParams["axes.unicode_minus"] = False
    except Exception:
        return None
    k = len(sheets)
    fig, axes = plt.subplots(k, 1, figsize=(11, max(3.2, 3.2 * k)), squeeze=False)
    for ax, (nm, df) in zip(axes[:, 0], sheets.items()):
        r = df.isna().mean().sort_values(ascending=False)
        ax.bar(range(len(r)), r.values,
               color=["#c0392b" if x > .5 else "#e67e22" if x > .05 else "#95a5a6" for x in r])
        ax.set_xticks(range(len(r)))
        ax.set_xticklabels([str(c)[:14] for c in r.index], rotation=90, fontsize=7)
        ax.set_ylabel("缺失率"); ax.set_ylim(0, 1)
        ax.set_title(f"{nm} — 各列缺失率 (n={len(df)})", fontsize=10)
        ax.axhline(.05, ls="--", lw=.8, c="#7f8c8d")
    fig.tight_layout()
    p = out / "fig_missing.png"
    fig.savefig(p, dpi=130); plt.close(fig)
    return p


def write_report(src, prob, sheets, kinds_all, fdf, outliers, checked, unmatched, out: Path, fig):
    L = ["# 数据体检报告", "", f"**数据**: `{src}`"]
    if prob:
        L.append(f"**题面**: `{prob}`")
    L += ["", "## 0. 概览", "", "| 表 | 行 | 列 | 数值 | 标识 | 类别 | 待解析 | 空列 |",
          "|---|---|---|---|---|---|---|---|"]
    for nm, df in sheets.items():
        k = pd.Series(list(kinds_all[nm].values())).value_counts()
        L.append(f"| {nm} | {len(df)} | {len(df.columns)} | {k.get('数值',0)} | {k.get('标识',0)} | "
                 f"{k.get('类别',0)} | {k.get('待解析文本',0)+k.get('混合文本',0)+k.get('日期文本',0)} | "
                 f"{k.get('空列',0)} |")
    L.append("")

    if fdf.empty:
        L += ["## 1. 发现", "", "未发现问题。", ""]
    else:
        c = fdf["严重度"].value_counts()
        L += ["## 1. 发现", "",
              f"共 {len(fdf)} 条：**{CRIT} {c.get(CRIT,0)}** / {WARN} {c.get(WARN,0)} / {INFO} {c.get(INFO,0)}", ""]
        for sev in (CRIT, WARN, INFO):
            sub = fdf[fdf["严重度"] == sev]
            if sub.empty:
                continue
            L += [f"### {sev}（{len(sub)}）", ""]
            for _, r in sub.iterrows():
                L.append(f"- **[{r['分类']}] {r['表']} · {r['列']}** — {r['发现']}")
                if r["建议动作"]:
                    L.append(f"  - → {r['建议动作']}")
            L.append("")

    if checked or unmatched:
        L += ["## 2. 题面约束对账", ""]
    if checked:
        L += ["| 题面写的 | 表 | 列 | 有效行 | 越界行 | 数据实际范围 |", "|---|---|---|---|---|---|"]
        for a, sn, col, n, k, rng in checked:
            L.append(f"| {a} | {sn} | {col} | {n} | {'**'+str(k)+'**' if k else 0} | {rng} |")
        L.append("")
    if unmatched:
        L += ["**以下约束没能自动对上列，请人工确认**（漏配比错配安全，但别忽略）：", "",
              "| 类型 | 题面写的 | 上下文 |", "|---|---|---|"]
        for kind, expr, ctx in unmatched:
            L.append(f"| {kind} | {expr} | …{ctx[:70]}… |")
        L.append("")

    if outliers:
        L += ["## 3. 离群点明细", "", "| 表 | 列 | 界外点 | 占比 | 数据范围 |", "|---|---|---|---|---|"]
        for nm, rows in outliers.items():
            for c, k, p, lo, hi in rows:
                L.append(f"| {nm} | {c} | {k} | {p:.1%} | {lo:.4g} ~ {hi:.4g} |")
        L.append("")

    if fig:
        L += ["## 4. 缺失分布", "", f"![缺失率]({fig.name})", ""]

    L += ["## 5. 下一步", "",
          "1. 打开 `data_decision_log.csv`，对每条**阻断**和**警告**填 `处理方式` 与 `理由`。",
          "2. 理由要能直接抄进论文的数据预处理小节 —— 评委扣的是「删了没说为什么」。",
          "3. 决策定完再写清洗脚本，不要边看边改数据。", ""]
    p = out / "data_audit_report.md"
    p.write_text("\n".join(L), encoding="utf-8")
    return p


def write_decision_log(fdf, out: Path):
    p = out / "data_decision_log.csv"
    cols = ["严重度", "分类", "表", "列", "发现", "建议动作", "处理方式", "理由", "影响行数"]
    if fdf.empty:
        pd.DataFrame(columns=cols).to_csv(p, index=False, encoding="utf-8-sig")
        return p
    d = fdf[fdf["严重度"].isin([CRIT, WARN])].copy()
    for x in ("处理方式", "理由", "影响行数"):
        d[x] = ""
    d[cols].to_csv(p, index=False, encoding="utf-8-sig")
    return p


# ============================================================ main
def main():
    ap = argparse.ArgumentParser(description="数模竞赛附件数据体检")
    ap.add_argument("path", help="附件 xlsx/csv")
    ap.add_argument("-p", "--problem", help="题面 pdf/txt，给了就做题面-数据对账")
    ap.add_argument("-o", "--out", default="data_audit")
    a = ap.parse_args()

    src = Path(a.path)
    if not src.exists():
        raise SystemExit(f"找不到文件: {src}")
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)

    sheets = {k: v for k, v in load_tables(src).items() if not v.empty}
    if not sheets:
        raise SystemExit("文件里没有非空表")

    kinds_all = {nm: classify_columns(df) for nm, df in sheets.items()}
    F = Findings()
    outliers = {}
    for nm, df in sheets.items():
        k = kinds_all[nm]
        check_structure(nm, df, k, F)
        check_types(nm, df, k, F)
        check_missing(nm, df, k, F)
        rows = check_values(nm, df, k, F)
        if rows:
            outliers[nm] = rows
        check_identity(nm, df, F)
        check_repeated_measures(nm, df, k, F)
    check_cross_sheet(sheets, kinds_all, F)

    checked, unmatched = [], []
    prob = None
    if a.problem:
        prob = Path(a.problem)
        if prob.exists():
            checked, unmatched = check_against_problem(load_problem_text(prob), sheets, kinds_all, F)
        else:
            print(f"[warn] 题面不存在: {prob}", file=sys.stderr)
            prob = None

    fdf = F.to_frame()
    fig = plot_missing(sheets, out)
    rp = write_report(src, prob, sheets, kinds_all, fdf, outliers, checked, unmatched, out, fig)
    dl = write_decision_log(fdf, out)

    c = fdf["严重度"].value_counts() if not fdf.empty else {}
    print(f"表 {len(sheets)} 个，发现 {len(fdf)} 条 "
          f"({CRIT} {c.get(CRIT,0)} / {WARN} {c.get(WARN,0)} / {INFO} {c.get(INFO,0)})"
          + (f"，题面对账 {len(checked)} 项，未匹配 {len(unmatched)} 项" if prob else ""))
    print(f"报告: {rp}\n决策清单: {dl}" + (f"\n图: {fig}" if fig else ""))


if __name__ == "__main__":
    main()
