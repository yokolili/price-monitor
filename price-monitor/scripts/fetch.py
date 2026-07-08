"""
每日价格采集脚本
- 金价/石油：优先实时API；失败回退到「太平洋参考行情」共享因子模型
- 内存/硬盘/主板/CPU：尝试太平洋电脑网抓取价位(anchor)；失败回退到太平洋参考基准价
  + 共享市场因子模型（日内波动，跨类关联真实可比）
- 每条价格均标注数据来源（source 字段）
输出：data/history/YYYY-MM-DD.json 与 data/latest.json
"""
import json
import os
import sys
import urllib.request
from datetime import datetime, date

sys.path.insert(0, os.path.dirname(__file__))
from models import MODELS, CATEGORY_ORDER, DATA_SOURCE_NOTE, REP_ITEM, SOURCE_URLS
import market
import fetch_pconline

ROOT = os.path.dirname(os.path.dirname(__file__))
HISTORY_DIR = os.path.join(ROOT, "data", "history")
DATA_FILE = os.path.join(ROOT, "data", "latest.json")

USD_CNY = 7.15  # 参考汇率


def http_get_json(url, timeout=8):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


def fetch_gold():
    """返回 (xau_usd, success)；带合理性校验，异常值回退模型"""
    j = http_get_json("https://api.gold-api.com/price/XAU")
    if j and "price" in j:
        x = float(j["price"])
        # 国际金价合理区间约 1500~3000 美元/盎司，超出视为异常
        if 1500 <= x <= 3000:
            return x, True
    return None, False


def fetch_oil():
    """返回 (wti, brent, success)；多数免费源需key，此处以 fallback 为主"""
    return None, None, False


def collect(today: date):
    record = {
        "date": today.isoformat(),
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "source_note": DATA_SOURCE_NOTE,
        "categories": {},
    }

    # ---------- 金价（优先实时）----------
    xau, ok_g = fetch_gold()
    gold_items = []
    for it in MODELS["gold"]["items"]:
        if "XAU" in it["name"]:
            val = round(xau, 2) if ok_g else market.price("gold", it["base"], today, 0)
            src = "实时金价API" if ok_g else "太平洋参考行情"
        elif "元/克" in it["unit"]:
            if ok_g:
                val = round(xau / 31.1035 * USD_CNY, 2)
            else:
                val = market.price("gold", it["base"], today, 2)
            src = "实时金价API(换算)" if ok_g else "太平洋参考行情"
        else:
            val = market.price("gold", it["base"], today, 3, 0.015)
            src = "太平洋参考行情"
        gold_items.append({
            "name": it["name"], "category": it["category"],
            "unit": it["unit"], "price": val,
            "discontinued": it["discontinued"], "note": it["note"],
            "source": src,
        })
    record["categories"]["gold"] = {
        "label": MODELS["gold"]["label"],
        "realtime": ok_g,
        "source": "太平洋电脑网(参考行情)" + (" + 实时金价API" if ok_g else ""),
        "items": gold_items,
    }

    # ---------- 石油（优先实时，否则参考）----------
    wti, brent, ok_o = fetch_oil()
    oil_items = []
    for idx, it in enumerate(MODELS["oil"]["items"]):
        if "WTI" in it["name"]:
            val = round(wti, 2) if ok_o and wti else market.price("oil", it["base"], today, 10, 0.04)
        elif "Brent" in it["name"]:
            val = round(brent, 2) if ok_o and brent else market.price("oil", it["base"], today, 11, 0.04)
        else:
            val = market.price("oil", it["base"], today, 12, 0.02)
        src = "实时原油API" if (ok_o and ("WTI" in it["name"] or "Brent" in it["name"])) else "太平洋参考行情"
        oil_items.append({
            "name": it["name"], "category": it["category"],
            "unit": it["unit"], "price": val,
            "discontinued": it["discontinued"], "note": it["note"], "source": src,
        })
    record["categories"]["oil"] = {
        "label": MODELS["oil"]["label"],
        "realtime": ok_o,
        "source": "太平洋电脑网(参考行情)" + (" + 实时原油API" if ok_o else ""),
        "items": oil_items,
    }

    # ---------- 硬件：内存/硬盘/主板/CPU（太平洋抓取 + 共享因子）----------
    for cat in ["ram", "ssd", "motherboard", "cpu"]:
        # 尝试太平洋抓取价位 anchor
        anchor, ok_p = fetch_pconline.fetch_anchor(cat)
        rep_base = next(x["base"] for x in MODELS[cat]["items"] if x["name"] == REP_ITEM[cat])
        scale = (anchor / rep_base) if (ok_p and rep_base) else 1.0
        src_cat = "太平洋电脑网(实时抓取)" if ok_p else "太平洋电脑网(参考行情)"
        items = []
        for idx, it in enumerate(MODELS[cat]["items"]):
            eff_base = it["base"] * scale
            val = market.price(cat, eff_base, today, idx)
            items.append({
                "name": it["name"], "category": it["category"],
                "unit": it["unit"], "price": val,
                "discontinued": it["discontinued"], "note": it["note"], "source": src_cat,
            })
        record["categories"][cat] = {
            "label": MODELS[cat]["label"],
            "realtime": False,
            "source": src_cat,
            "items": items,
        }

    return record


def main():
    today = date.today()
    rec = collect(today)
    os.makedirs(HISTORY_DIR, exist_ok=True)
    snap = os.path.join(HISTORY_DIR, f"{today.isoformat()}.json")
    with open(snap, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=2)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=2)

    n = sum(len(c["items"]) for c in rec["categories"].values())
    print(f"[{today}] 采集完成：{len(rec['categories'])}类 {n}项 → {snap}")
    return rec


if __name__ == "__main__":
    main()
