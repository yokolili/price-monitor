"""
分析 + 预测模块
- 读取历史快照，计算周期（周/月/年）对比
- 生成 ASCII 趋势图
- 原因分析（基于波动方向与已知常识的规则模板）
- 价格预测（移动平均 + 趋势外推，保守区间）
"""
import json
import os
import statistics
from datetime import datetime, date, timedelta

ROOT = os.path.dirname(os.path.dirname(__file__))
HISTORY_DIR = os.path.join(ROOT, "data", "history")


def load_history(days=400):
    """加载历史快照，返回 {date_str: record}"""
    data = {}
    for fn in os.listdir(HISTORY_DIR):
        if fn.endswith(".json"):
            d = fn[:-5]
            try:
                with open(os.path.join(HISTORY_DIR, fn), encoding="utf-8") as f:
                    data[d] = json.load(f)
            except Exception:
                pass
    return dict(sorted(data.items()))


def series_for(data, cat, item_name):
    """返回 [(date, price)] 序列"""
    out = []
    for d, rec in data.items():
        c = rec["categories"].get(cat)
        if not c:
            continue
        for it in c["items"]:
            if it["name"] == item_name:
                out.append((d, it["price"]))
    return out


def ascii_chart(series, width=48, height=8):
    """纯文字 ASCII 走势图（折线示意）"""
    if len(series) < 2:
        return ["(数据不足)"]
    vals = [v for _, v in series]
    lo, hi = min(vals), max(vals)
    if hi == lo:
        hi = lo + 1
    lines = []
    n = len(series)
    for row in range(height, 0, -1):
        threshold = lo + (hi - lo) * (row - 0.5) / height
        line = []
        for i, v in enumerate(vals):
            # 采样到 width 列
            col = int(i / max(1, n - 1) * (width - 1))
            line.append(" " * (col - len(line)) + ("*" if abs(v - threshold) < (hi - lo) / height else ""))
        s = "".join(line)
        # 简化：网格 + 折线
        bar = ""
        for i, v in enumerate(vals):
            pos = int((v - lo) / (hi - lo) * (height - 1))
            # 只画采样列避免过密
            if i % max(1, n // width) == 0 or i == n - 1:
                pass
        lines.append(s if s.strip() else " " * width)
    # 用更清晰的柱状 sparkline 方式
    return sparkline(vals, width)


def sparkline(vals, width=48):
    """生成 sparkline 文本"""
    chars = " ▁▂▃▄▅▆▇█"
    lo, hi = min(vals), max(vals)
    if hi == lo:
        return ["".join([chars[-1]] * min(width, len(vals)))]
    step = max(1, len(vals) / width)
    out = []
    for i in range(width):
        idx = min(len(vals) - 1, int(i * step))
        v = vals[idx]
        level = int((v - lo) / (hi - lo) * (len(chars) - 1))
        out.append(chars[level])
    return ["".join(out)]


def trend_info(series):
    """返回趋势描述与变化率"""
    if len(series) < 2:
        return "数据不足", 0.0
    first = series[0][1]
    last = series[-1][1]
    change = (last - first) / first * 100 if first else 0
    if change > 1:
        trend = "上升 ↑"
    elif change < -1:
        trend = "下降 ↓"
    else:
        trend = "平稳 →"
    return trend, round(change, 2)


def moving_average(vals, w=7):
    if len(vals) < w:
        return vals[-1] if vals else 0
    return round(statistics.mean(vals[-w:]), 2)


def predict(series, horizon=30):
    """简单线性外推 + MA，返回 (预测值, 区间下限, 区间上限)"""
    if len(series) < 3:
        return None, None, None
    vals = [v for _, v in series]
    # 线性回归斜率
    n = len(vals)
    xs = list(range(n))
    xm = statistics.mean(xs)
    ym = statistics.mean(vals)
    num = sum((x - xm) * (y - ym) for x, y in zip(xs, vals))
    den = sum((x - xm) ** 2 for x in xs)
    slope = num / den if den else 0
    last = vals[-1]
    pred = last + slope * horizon
    # 波动带宽
    residuals = [abs(v - (ym + slope * (i - xm))) for i, v in enumerate(vals)]
    band = statistics.mean(residuals) * 1.5 + abs(slope) * horizon * 0.3
    return round(pred, 2), round(pred - band, 2), round(pred + band, 2)


# 原因分析模板（基于类别常识）
REASON_TEMPLATES = {
    "gold": [
        "美联储货币政策与美元指数波动直接影响金价；避险情绪升温时金价走强。",
        "地缘局势与通胀预期是黄金核心驱动，央行购金提供中长期支撑。",
    ],
    "oil": [
        "OPEC+ 减产/增产决议、全球需求预期与地缘供应风险主导油价。",
        "美国库存数据与宏观经济景气度变化是短期油价主要变量。",
    ],
    "ram": [
        "DRAM 厂商产能调控与 AI 服务器需求挤占，DDR5 价格受供需影响。",
        "代际更替期旧制程清库存，新平台普及推高 DDR5 需求。",
    ],
    "ssd": [
        "NAND 闪存 wafer 价格周期与旺季备货影响 SSD 报价。",
        "PCIe5.0 新品溢价明显，Gen4 主流容量价格随颗粒成本波动。",
    ],
    "cpu": [
        "新架构发布与竞品定价博弈影响 CPU 行情，旧型号清库降价。",
        "桌面需求平稳，高端型号受产能与渠道策略影响。",
    ],
}


def reason_text(cat, change):
    templates = REASON_TEMPLATES.get(cat, ["受市场供需与宏观环境影响。"])
    if change > 1:
        return templates[0]
    elif change < -1:
        return templates[1] if len(templates) > 1 else templates[0]
    return "近期多空因素均衡，" + templates[0]


# ---------- 关联分析（黄金/石油/硬盘/内存/CPU）----------

def _rep_prices(data, cat):
    """返回 {date: price} 代表型号序列"""
    from models import REP_ITEM
    ser = series_for(data, cat, REP_ITEM[cat])
    return dict(ser)


def _returns_map(data, cats):
    prices = {c: _rep_prices(data, c) for c in cats}
    dates = sorted(set().union(*[set(p.keys()) for p in prices.values()]))
    ret = {}
    for c in cats:
        r = {}
        prev = None
        for d in dates:
            if d in prices[c]:
                p = prices[c][d]
                if prev:
                    r[d] = (p - prev) / prev if prev else 0.0
                prev = p
        ret[c] = r
    return ret, dates


def _pearson(x, y):
    n = len(x)
    if n < 2:
        return 0.0
    mx = statistics.mean(x)
    my = statistics.mean(y)
    num = sum((a - mx) * (b - my) for a, b in zip(x, y))
    dx = sum((a - mx) ** 2 for a in x) ** 0.5
    dy = sum((b - my) ** 2 for b in y) ** 0.5
    return num / (dx * dy) if dx and dy else 0.0


def correlation_matrix(data, cats):
    """返回 (matrix, common_dates)。matrix[cat][cat2] = 皮尔逊相关系数"""
    ret, dates = _returns_map(data, cats)
    common = sorted(set.intersection(*[set(ret[c].keys()) for c in cats]))
    mat = {c: {c2: None for c2 in cats} for c in cats}
    for i, a in enumerate(cats):
        for b in cats[i:]:
            if a == b:
                mat[a][b] = 1.0
            else:
                xa = [ret[a][d] for d in common]
                xb = [ret[b][d] for d in common]
                v = round(_pearson(xa, xb), 3)
                mat[a][b] = v
                mat[b][a] = v
    return mat, common


def impact_nodes(data, cats, threshold=0.018):
    """返回 [(date, cat, change)]：代表型号日涨幅超阈值的时点（影响节点）"""
    ret, dates = _returns_map(data, cats)
    out = []
    for d in dates:
        for c in cats:
            if d in ret[c] and abs(ret[c][d]) >= threshold:
                out.append((d, c, ret[c][d]))
    out.sort()
    return out


# 真实世界关联点（因果叙述），与数值关联互为补充
CORR_POINTS = [
    ("黄金 ↔ 石油", "正相关", "二者同受美元指数与通胀预期驱动；避险/通胀升温时往往同向波动。"),
    ("石油 → 硬盘/内存", "弱正相关", "油价影响石化原料(封装胶材)与制造能源成本，间接传导至 NAND/DRAM 报价。"),
    ("内存 ↔ CPU", "正相关", "新平台(如 DDR5 配合新接口 CPU)同期发布，需求与换代节奏联动。"),
    ("黄金 ↔ 硬盘/CPU", "弱/不相关", "黄金属避险资产，硬件属工业消费品，驱动因子不同，关联较弱。"),
]


def correlation_report(data):
    """结构化关联报告，供 build 生成关联页"""
    from models import CORR_FOCUS, CATEGORY_ORDER
    cats = CORR_FOCUS
    mat, common = correlation_matrix(data, cats)
    # 配对排序
    pairs = []
    for i, a in enumerate(cats):
        for b in cats[i + 1:]:
            pairs.append((a, b, mat[a][b]))
    pairs.sort(key=lambda x: x[2], reverse=True)
    nodes = impact_nodes(data, cats)
    return {
        "cats": cats,
        "matrix": mat,
        "common_days": len(common),
        "pairs": pairs,
        "impact": nodes,
        "points": CORR_POINTS,
    }


def build_period_report(period, data):
    """period: 'week'|'month'|'year'"""
    dates = list(data.keys())
    if period == "week":
        cutoff = (date.today() - timedelta(days=7)).isoformat()
        title = "近一周"
    elif period == "month":
        cutoff = (date.today() - timedelta(days=30)).isoformat()
        title = "近一月"
    else:
        cutoff = (date.today() - timedelta(days=365)).isoformat()
        title = "近一年"

    window = {d: r for d, r in data.items() if d >= cutoff}
    if not window:
        window = data

    sections = []
    summary_points = []
    for cat in ["gold", "oil", "ram", "ssd", "cpu"]:
        c = window[list(window.keys())[-1]]["categories"].get(cat)
        if not c:
            continue
        sec_lines = [f"### {c['label']}"]
        for it in c["items"]:
            ser = series_for(window, cat, it["name"])
            if len(ser) < 2:
                continue
            spark = ascii_chart(ser)[0]
            trend, chg = trend_info(ser)
            pred, lo, hi = predict(ser, 30)
            disc = f" [停产 {it['discontinued']}]" if it["discontinued"] else ""
            sec_lines.append(f"- {it['name']}{disc} ({it['unit']})")
            sec_lines.append(f"  今日 {it['price']} | 趋势 {trend} ({chg:+}%)")
            sec_lines.append(f"  走势: {spark}")
            if pred:
                sec_lines.append(f"  30日预测: {pred} (区间 {lo}~{hi})")
            sec_lines.append(f"  分析: {reason_text(cat, chg)}")
            summary_points.append(f"{c['label']}-{it['name']}: {trend}({chg:+}%)")
        sections.append("\n".join(sec_lines))

    summary = "## 周期总结\n" + "\n".join(f"- {p}" for p in summary_points[:12])
    body = f"# {title}价格对比报告\n\n生成时间: {datetime.now().isoformat(timespec='seconds')}\n\n" + \
           "\n\n".join(sections) + "\n\n" + summary
    return body


if __name__ == "__main__":
    data = load_history()
    print(f"历史天数: {len(data)}")
    for p in ["week", "month", "year"]:
        rep = build_period_report(p, data)
        print(f"\n===== {p} =====")
        print(rep[:600])
