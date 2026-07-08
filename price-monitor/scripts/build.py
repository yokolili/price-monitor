"""
网站生成器：读取 latest.json + 历史，生成纯文字静态站点
输出 public/ 下：
  index.html            首页（今日价格 + 导航）
  archive/YYYY-MM-DD.html  每日页
  weekly/index.html  monthly/index.html  yearly/index.html  周期报告
  correlation/index.html  黄金/石油/硬盘/内存/CPU 关联分析
安全：无外部资源、输出转义、无用户可控输入
"""
import json
import os
import html
import sys
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(__file__))
from models import MODELS, CATEGORY_ORDER, SOURCE_URLS, REP_ITEM
import analyze as A

ROOT = os.path.dirname(os.path.dirname(__file__))
PUBLIC = os.path.join(ROOT, "public")
HISTORY_DIR = os.path.join(ROOT, "data", "history")

CSS = """
:root{
  --bg:#0d1117; --panel:#161b22; --border:#30363d; --text:#c9d1d9;
  --muted:#8b949e; --accent:#58a6ff; --gold:#e3b341; --up:#3fb950; --down:#f85149;
  --mono:'SF Mono',Consolas,'Liberation Mono',Menlo,monospace;
}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:var(--mono);line-height:1.6;
  padding:24px 16px 60px;font-size:14px}
.wrap{max-width:960px;margin:0 auto}
h1{font-size:22px;color:var(--gold);border-bottom:1px solid var(--border);padding-bottom:12px;margin-bottom:6px;
  animation:fadeIn .6s ease both}
h2{font-size:18px;color:var(--accent);margin:24px 0 10px}
h3{font-size:15px;color:var(--text);margin:14px 0 6px}
.sub{color:var(--muted);font-size:12px;margin-bottom:18px}
nav{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0}
nav a{color:var(--accent);text-decoration:none;border:1px solid var(--border);
  padding:6px 12px;border-radius:6px;font-size:13px;transition:.2s}
nav a:hover{background:var(--panel);transform:translateY(-1px)}
.card{background:var(--panel);border:1px solid var(--border);border-radius:8px;
  padding:14px 16px;margin-bottom:12px;animation:fadeIn .5s ease both}
.src{color:var(--muted);font-size:11px;margin-top:4px}
.src a{color:var(--accent);text-decoration:none}
table{width:100%;border-collapse:collapse;margin-top:8px;font-size:13px}
th,td{text-align:left;padding:7px 8px;border-bottom:1px solid var(--border)}
th{color:var(--muted);font-weight:600}
.up{color:var(--up)} .down{color:var(--down)} .flat{color:var(--muted)}
.up{animation:pulseUp 2.4s ease-in-out infinite}
.disc{color:var(--down);font-size:11px;border:1px solid var(--down);
  border-radius:4px;padding:1px 5px;margin-left:6px}
.spark{color:var(--accent);letter-spacing:1px;font-size:13px;white-space:nowrap;overflow:hidden;
  background:linear-gradient(90deg,var(--accent),#79c0ff,var(--accent));background-size:40px 100%;
  -webkit-background-clip:text;background-clip:text;color:transparent;animation:slideSpark 3s linear infinite}
.tag{display:inline-block;font-size:10px;padding:1px 6px;border-radius:4px;
  background:#21262d;color:var(--muted);margin-left:6px}
.note{color:var(--muted);font-size:11px;margin-top:4px}
.meta{color:var(--muted);font-size:11px;margin-top:24px;border-top:1px solid var(--border);padding-top:12px}
ul{list-style:none;padding-left:0}
li{padding:4px 0;border-bottom:1px solid var(--border)}
.pred{color:var(--gold)}
footer{color:var(--muted);font-size:11px;text-align:center;margin-top:30px}
.heat td,.heat th{padding:6px 4px;font-size:12px}
.corrpt{border-left:3px solid var(--accent);padding:6px 10px;margin:8px 0;background:var(--panel);border-radius:4px}
.impact{font-size:12px;padding:3px 0}
@keyframes fadeIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
@keyframes pulseUp{0%,100%{opacity:1}50%{opacity:.5}}
@keyframes slideSpark{from{background-position:0 0}to{background-position:40px 0}}
"""

SITE_TITLE = "价格观察站"
SITE_DESC = "黄金 · 石油 · 内存 · 硬盘 · 主板 · CPU 每日价格跟踪与周期分析"

CAT_COLORS = {
    "gold": "#e3b341", "oil": "#f0883e", "ssd": "#58a6ff",
    "ram": "#79c0ff", "motherboard": "#56d364", "cpu": "#bc8cff",
}


def esc(s):
    return html.escape(str(s))


def page(title, body, base=""):
    nav = f"""
    <nav>
      <a href="{base}index.html">首页</a>
      <a href="{base}correlation/index.html">关联分析</a>
      <a href="{base}weekly/index.html">周报</a>
      <a href="{base}monthly/index.html">月报</a>
      <a href="{base}yearly/index.html">年报</a>
      <a href="{base}archive/index.html">每日归档</a>
    </nav>"""
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} - {SITE_TITLE}</title>
<style>{CSS}</style></head>
<body><div class="wrap">
<h1>{SITE_TITLE}</h1>
<div class="sub">{SITE_DESC}</div>
{nav}
{body}
<footer>纯文字静态站点 · 无图片 · 数据每日自动更新 · 生成于 {datetime.now().isoformat(timespec='seconds')}</footer>
</div></body></html>"""


def category_block(cat_key, cat_data, prev=None):
    rows = []
    for it in cat_data["items"]:
        price = it["price"]
        cls = "flat"
        delta = ""
        if prev:
            pitem = next((x for x in prev["items"] if x["name"] == it["name"]), None)
            if pitem:
                d = (price - pitem["price"]) / pitem["price"] * 100 if pitem["price"] else 0
                delta = f"{d:+.2f}%"
                cls = "up" if d > 0.05 else ("down" if d < -0.05 else "flat")
        disc = f'<span class="disc">停产 {esc(it["discontinued"])}</span>' if it["discontinued"] else ""
        rt = '<span class="tag">实时</span>' if cat_data.get("realtime") else '<span class="tag">参考</span>'
        src = f'<span class="tag">来源:{esc(it.get("source","太平洋"))}</span>'
        rows.append(
            f"<tr><td>{esc(it['name'])}{disc}{rt}{src}</td>"
            f"<td>{esc(it['category'])}</td>"
            f"<td class='{cls}'>{price:,.2f} {esc(it['unit'])} {delta}</td></tr>"
        )
    note = cat_data.get("source_note", {})
    src_url = SOURCE_URLS.get(cat_key, "#")
    src_html = f'<div class="src">数据来源：{esc(cat_data.get("source","太平洋电脑网"))} · ' \
               f'<a href="{esc(src_url)}" target="_blank" rel="noopener">太平洋电脑网</a></div>'
    return f"""<div class="card">
<h3>{esc(cat_data['label'])}</h3>
{src_html}
<table><thead><tr><th>型号</th><th>类别</th><th>今日价格</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table>
</div>"""


def build_index(latest, history):
    dates = sorted(history.keys())
    prev_rec = history[dates[-2]] if len(dates) > 1 else None
    blocks = []
    for cat in CATEGORY_ORDER:
        c = latest["categories"].get(cat)
        if c:
            blocks.append(category_block(cat, c, prev_rec.get(cat) if prev_rec else None))
    src_note = latest.get("source_note", {})
    note_html = "<div class='note'>数据来源：" + " · ".join(
        f"{MODELS[k]['label']}={esc(v)}" for k, v in src_note.items()) + "。硬件类基准参考太平洋电脑网行情，日内波动为模型模拟。</div>"
    body = f"""<div class="sub">更新时间：{esc(latest['updated_at'])}</div>
{note_html}
{''.join(blocks)}
<div class="meta">说明：本页价格每日自动生成。已停产型号标注红色「停产」标签。新增「关联分析」页可查看黄金/石油/硬盘/内存/CPU 的跨类联动。</div>"""
    return page("今日价格", body, base="")


def build_archive_page(history):
    items = []
    for d in sorted(history.keys(), reverse=True)[:60]:
        rec = history[d]
        items.append(f"<li><a href='{esc(d)}.html'>{esc(d)}</a> · 更新 {esc(rec['updated_at'][:10])}"
                     f"{' · 回填' if rec.get('backfilled') else ''}</li>")
    body = f"<h2>每日价格归档</h2><ul>{''.join(items)}</ul>"
    return page("每日归档", body, base="../")


def build_daily_page(d, rec):
    blocks = []
    for cat in CATEGORY_ORDER:
        c = rec["categories"].get(cat)
        if c:
            blocks.append(category_block(cat, c, None))
    body = f"<div class='sub'>{esc(d)}{' (历史回溯/模拟)' if rec.get('backfilled') else ''}</div>{''.join(blocks)}"
    return page(f"每日价格 {d}", body, base="../")


def build_report_page(period, title, base="../"):
    data = A.load_history()
    body = A.build_period_report(period, data)
    html_parts = []
    for line in body.split("\n"):
        if line.startswith("### "):
            html_parts.append(f"<h3>{esc(line[4:])}</h3>")
        elif line.startswith("## "):
            html_parts.append(f"<h2>{esc(line[3:])}</h2>")
        elif line.startswith("# "):
            html_parts.append(f"<h1 style='font-size:18px'>{esc(line[2:])}</h1>")
        elif line.startswith("- "):
            html_parts.append(f"<div style='padding:3px 0'>{esc(line[2:])}</div>")
        elif line.strip().startswith("今日 ") or line.strip().startswith("走势") or line.strip().startswith("30日") or line.strip().startswith("分析"):
            cls = "spark" if "走势" in line else ("pred" if "30日" in line else "note")
            html_parts.append(f"<div class='{cls}'>{esc(line)}</div>")
        elif line.strip() == "":
            pass
        else:
            html_parts.append(f"<div>{esc(line)}</div>")
    return page(title, "\n".join(html_parts), base=base)


# ---------------- 关联分析页 ----------------

def _svg_corr_chart(history, cats, w=680, h=220):
    series = {c: A._rep_prices(history, c) for c in cats}
    common = sorted(set.intersection(*[set(s.keys()) for s in series.values()]))
    if len(common) < 2:
        return "<div class='note'>历史数据不足，无法绘制走势。</div>"
    norm = {}
    for c in cats:
        vals = [series[c][d] for d in common]
        lo, hi = min(vals), max(vals)
        norm[c] = [(v - lo) / (hi - lo) if hi > lo else 0.5 for v in vals]
    n = len(common)
    parts = [f'<svg viewBox="0 0 {w} {h}" width="100%" preserveAspectRatio="none" '
             f'style="background:#0d1117;border:1px solid #30363d;border-radius:8px">']
    pad = 10
    for c in cats:
        pts = []
        for i, v in enumerate(norm[c]):
            x = pad + i / (n - 1) * (w - 2 * pad)
            y = pad + (1 - v) * (h - 2 * pad)
            pts.append(f"{x:.1f},{y:.1f}")
        parts.append(f'<polyline fill="none" stroke="{CAT_COLORS.get(c,"#58a6ff")}" '
                     f'stroke-width="2" points="{" ".join(pts)}"/>')
    parts.append("</svg>")
    legend = " ".join(
        f'<span style="color:{CAT_COLORS.get(c,"#58a6ff")}">■</span> {esc(MODELS[c]["label"])}'
        for c in cats)
    return "".join(parts) + f'<div class="note" style="margin-top:6px">{legend}</div>'


def build_correlation_page(history, base="../"):
    rep = A.correlation_report(history)
    cats = rep["cats"]
    labels = {c: MODELS[c]["label"] for c in cats}
    colors = {c: CAT_COLORS.get(c, "#58a6ff") for c in cats}

    # 1) 叠加走势图
    chart = _svg_corr_chart(history, cats)
    chart_block = f"<h2>代表型号归一化走势（同屏对比）</h2>{chart}" \
                  f"<div class='note'>各序列按自身区间归一化到 0~1，用于观察联动节奏，非真实价格比例。</div>"

    # 2) 相关系数热力图
    heat_rows = []
    for a in cats:
        cells = [f"<th>{esc(labels[a])}</th>"]
        for b in cats:
            v = rep["matrix"][a][b]
            if v is None:
                cells.append("<td style='background:#21262d;text-align:center'>—</td>")
            else:
                if v >= 0.3:
                    bg = "rgba(63,185,80,.55)"
                elif v >= -0.3:
                    bg = "rgba(139,148,158,.30)"
                else:
                    bg = "rgba(248,81,73,.55)"
                cells.append(f"<td style='background:{bg};text-align:center'>{v:+.2f}</td>")
        heat_rows.append("<tr>" + "".join(cells) + "</tr>")
    heat_head = "<tr><th></th>" + "".join(f"<th>{esc(labels[c])}</th>" for c in cats) + "</tr>"
    heat = f"<h2>相关系数矩阵（日收益率皮尔逊相关）</h2>" \
           f"<table class='heat'>{heat_head}{''.join(heat_rows)}</table>" \
           f"<div class='note'>取值 -1~+1：接近 +1 同向变动，接近 -1 反向变动，接近 0 基本无关。" \
           f"基于约 {rep['common_days']} 天历史。</div>"

    # 3) 强关联 / 弱关联配对
    pair_lines = []
    for a, b, v in rep["pairs"]:
        tag = "强正相关" if v >= 0.3 else ("强负相关" if v <= -0.3 else "弱/无显著相关")
        pair_lines.append(
            f"<div class='corrpt'><b style='color:{colors[a]}'>{esc(labels[a])}</b> ↔ "
            f"<b style='color:{colors[b]}'>{esc(labels[b])}</b>："
            f"<span class='{'up' if v>=0.3 else ('down' if v<=-0.3 else 'flat')}'>{v:+.2f}</span> "
            f"— {tag}</div>")
    pairs_block = f"<h2>关联配对排序</h2>{''.join(pair_lines)}"

    # 4) 关联点（因果叙述）
    pt_lines = []
    for pair, relation, desc in rep["points"]:
        pt_lines.append(f"<li><b>{esc(pair)}</b> 〔{esc(relation)}〕：{esc(desc)}</li>")
    points_block = f"<h2>关联点（传导逻辑）</h2><ul>{''.join(pt_lines)}</ul>"

    # 5) 影响节点时间
    nodes = sorted(rep["impact"], key=lambda x: abs(x[2]), reverse=True)[:25]
    node_lines = []
    for d, c, ch in nodes:
        cls = "up" if ch > 0 else "down"
        node_lines.append(
            f"<div class='impact'><span class='{cls}'>{esc(labels[c])}</span> "
            f"于 <b>{esc(d)}</b> 单日变动 <span class='{cls}'>{ch*100:+.2f}%</span></div>")
    no_node = "<div class='note'>近期无显著单日波动节点。</div>"
    impact_inner = "".join(node_lines) if node_lines else no_node
    impact_block = (f"<h2>影响节点时间（单日波动显著时点，Top {len(node_lines)}）</h2>" + impact_inner)

    body = chart_block + heat + pairs_block + points_block + impact_block
    return page("跨类关联分析", body, base=base)


def main():
    with open(os.path.join(ROOT, "data", "latest.json"), encoding="utf-8") as f:
        latest = json.load(f)
    history = A.load_history()

    os.makedirs(PUBLIC, exist_ok=True)

    with open(os.path.join(PUBLIC, "index.html"), "w", encoding="utf-8") as f:
        f.write(build_index(latest, history))

    os.makedirs(os.path.join(PUBLIC, "archive"), exist_ok=True)
    with open(os.path.join(PUBLIC, "archive", "index.html"), "w", encoding="utf-8") as f:
        f.write(build_archive_page(history))

    for d, rec in history.items():
        with open(os.path.join(PUBLIC, "archive", f"{d}.html"), "w", encoding="utf-8") as f:
            f.write(build_daily_page(d, rec))

    for period, title, folder in [
        ("week", "近一周价格对比报告", "weekly"),
        ("month", "近一月价格对比报告", "monthly"),
        ("year", "近一年价格对比报告", "yearly"),
    ]:
        os.makedirs(os.path.join(PUBLIC, folder), exist_ok=True)
        with open(os.path.join(PUBLIC, folder, "index.html"), "w", encoding="utf-8") as f:
            f.write(build_report_page(period, title, base="../"))

    # 关联分析页
    os.makedirs(os.path.join(PUBLIC, "correlation"), exist_ok=True)
    with open(os.path.join(PUBLIC, "correlation", "index.html"), "w", encoding="utf-8") as f:
        f.write(build_correlation_page(history, base="../"))

    n_archive = len(history)
    print(f"站点生成完成：首页 + 关联分析页 + 归档{n_archive}页 + 周/月/年报告")


if __name__ == "__main__":
    main()
