"""
网站生成器：读取 latest.json + 历史，生成纯文字静态站点
输出 public/ 下：
  index.html            首页（今日价格 + 导航）
  archive/YYYY-MM-DD.html  每日页
  weekly/index.html  monthly/index.html  yearly/index.html  周期报告
安全：无外部资源、输出转义、无用户可控输入
"""
import json
import os
import html
import sys
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(__file__))
from models import MODELS, CATEGORY_ORDER
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
.wrap{max-width:920px;margin:0 auto}
h1{font-size:22px;color:var(--gold);border-bottom:1px solid var(--border);padding-bottom:12px;margin-bottom:6px}
h2{font-size:18px;color:var(--accent);margin:24px 0 10px}
h3{font-size:15px;color:var(--text);margin:14px 0 6px}
.sub{color:var(--muted);font-size:12px;margin-bottom:18px}
nav{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0}
nav a{color:var(--accent);text-decoration:none;border:1px solid var(--border);
  padding:6px 12px;border-radius:6px;font-size:13px}
nav a:hover{background:var(--panel)}
.card{background:var(--panel);border:1px solid var(--border);border-radius:8px;
  padding:14px 16px;margin-bottom:12px}
table{width:100%;border-collapse:collapse;margin-top:8px;font-size:13px}
th,td{text-align:left;padding:7px 8px;border-bottom:1px solid var(--border)}
th{color:var(--muted);font-weight:600}
.up{color:var(--up)} .down{color:var(--down)} .flat{color:var(--muted)}
.disc{color:var(--down);font-size:11px;border:1px solid var(--down);
  border-radius:4px;padding:1px 5px;margin-left:6px}
.spark{color:var(--accent);letter-spacing:1px;font-size:13px;white-space:nowrap;overflow:hidden}
.tag{display:inline-block;font-size:10px;padding:1px 6px;border-radius:4px;
  background:#21262d;color:var(--muted);margin-left:6px}
.note{color:var(--muted);font-size:11px;margin-top:4px}
.meta{color:var(--muted);font-size:11px;margin-top:24px;border-top:1px solid var(--border);padding-top:12px}
ul{list-style:none;padding-left:0}
li{padding:4px 0;border-bottom:1px solid var(--border)}
.pred{color:var(--gold)}
footer{color:var(--muted);font-size:11px;text-align:center;margin-top:30px}
"""

SITE_TITLE = "价格观察站"
SITE_DESC = "黄金 · 石油 · 内存 · 硬盘 · CPU 每日价格跟踪与周期分析"


def esc(s):
    return html.escape(str(s))


def page(title, body, base=""):
    nav = f"""
    <nav>
      <a href="{base}index.html">首页</a>
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
        rows.append(
            f"<tr><td>{esc(it['name'])}{disc}{rt}</td>"
            f"<td>{esc(it['category'])}</td>"
            f"<td class='{cls}'>{price:,.2f} {esc(it['unit'])} {delta}</td></tr>"
        )
    note = cat_data.get("source_note", {})
    return f"""<div class="card">
<h3>{esc(cat_data['label'])}</h3>
<table><thead><tr><th>型号</th><th>类别</th><th>今日价格</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table>
</div>"""


def build_index(latest, history):
    # 找前一天用于涨跌
    dates = sorted(history.keys())
    prev_rec = history[dates[-2]] if len(dates) > 1 else None
    blocks = []
    for cat in CATEGORY_ORDER:
        c = latest["categories"].get(cat)
        if c:
            blocks.append(category_block(cat, c, prev_rec.get(cat) if prev_rec else None))
    src_note = latest.get("source_note", {})
    note_html = "<div class='note'>数据来源：" + " · ".join(
        f"{MODELS[k]['label']}={esc(v)}" for k, v in src_note.items()) + "。硬件类为参考价(模拟波动)，金价实时。</div>"
    body = f"""<div class="sub">更新时间：{esc(latest['updated_at'])}</div>
{note_html}
{''.join(blocks)}
<div class="meta">说明：本页价格每日自动生成。已停产型号标注红色「停产」标签。周期分析报告见上方导航。</div>"""
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
    # 转 HTML
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


def main():
    with open(os.path.join(ROOT, "data", "latest.json"), encoding="utf-8") as f:
        latest = json.load(f)
    history = A.load_history()

    # 确保输出目录存在（GitHub 全新检出时无 public/）
    os.makedirs(PUBLIC, exist_ok=True)

    # 首页
    with open(os.path.join(PUBLIC, "index.html"), "w", encoding="utf-8") as f:
        f.write(build_index(latest, history))

    # 归档索引
    os.makedirs(os.path.join(PUBLIC, "archive"), exist_ok=True)
    with open(os.path.join(PUBLIC, "archive", "index.html"), "w", encoding="utf-8") as f:
        f.write(build_archive_page(history))

    # 每日页
    for d, rec in history.items():
        with open(os.path.join(PUBLIC, "archive", f"{d}.html"), "w", encoding="utf-8") as f:
            f.write(build_daily_page(d, rec))

    # 周期报告
    for period, title, folder in [
        ("week", "近一周价格对比报告", "weekly"),
        ("month", "近一月价格对比报告", "monthly"),
        ("year", "近一年价格对比报告", "yearly"),
    ]:
        os.makedirs(os.path.join(PUBLIC, folder), exist_ok=True)
        with open(os.path.join(PUBLIC, folder, "index.html"), "w", encoding="utf-8") as f:
            f.write(build_report_page(period, title, base="../"))

    n_archive = len(history)
    print(f"站点生成完成：首页 + 归档{n_archive}页 + 周/月/年报告")


if __name__ == "__main__":
    main()
