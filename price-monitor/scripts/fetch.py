"""
每日价格采集脚本
- 金价/石油：尝试免费公开 API，失败则用模型基准价 + 小幅波动
- 硬件：模型基准价 + 基于日期种子的确定性波动（保证同日同值、跨日渐变）
输出：data/history/YYYY-MM-DD.json 与 data/latest.json
"""
import json
import os
import sys
import random
import urllib.request
from datetime import datetime, date

sys.path.insert(0, os.path.dirname(__file__))
from models import MODELS, CATEGORY_ORDER, DATA_SOURCE_NOTE

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
    """返回 (xau_usd, success)"""
    # 免费无key API
    j = http_get_json("https://api.gold-api.com/price/XAU")
    if j and "price" in j:
        return float(j["price"]), True
    return None, False


def fetch_oil():
    """返回 (wti, brent, success)"""
    # 尝试 open API；多数免费源需key，故以 fallback 为主
    j = http_get_json("https://api.api-ninjas.com/v1/commodityprice?name=crude_oil",
                      timeout=6)
    # 即使失败也走 fallback，避免依赖未配置的 key
    return None, None, False


def day_seed(d: date):
    return d.year * 10000 + d.month * 100 + d.day


def wobble(base, d: date, salt, pct=0.03):
    """基于日期的确定性小幅波动"""
    random.seed(day_seed(d) + salt)
    return round(base * (1 + random.uniform(-pct, pct)), 2)


def collect(today: date):
    record = {
        "date": today.isoformat(),
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "source_note": DATA_SOURCE_NOTE,
        "categories": {},
    }

    # 金价
    xau, ok_g = fetch_gold()
    gold_items = []
    for it in MODELS["gold"]["items"]:
        if "XAU" in it["name"]:
            if ok_g:
                val = round(xau, 2)
            else:
                val = wobble(it["base"], today, 1, 0.02)
            unit = it["unit"]
        elif "元/克" in it["unit"]:
            if ok_g:
                val = round(xau / 31.1035 * USD_CNY, 2)  # 盎司->克->人民币
            else:
                val = wobble(it["base"], today, 2, 0.02)
            unit = it["unit"]
        else:
            val = wobble(it["base"], today, 3, 0.015)
            unit = it["unit"]
        gold_items.append({
            "name": it["name"], "category": it["category"],
            "unit": unit, "price": val,
            "discontinued": it["discontinued"], "note": it["note"],
        })
    record["categories"]["gold"] = {
        "label": MODELS["gold"]["label"],
        "realtime": ok_g,
        "items": gold_items,
    }

    # 石油
    wti, brent, ok_o = fetch_oil()
    oil_items = []
    for it in MODELS["oil"]["items"]:
        if "WTI" in it["name"]:
            val = round(wti, 2) if ok_o and wti else wobble(it["base"], today, 10, 0.04)
        elif "Brent" in it["name"]:
            val = round(brent, 2) if ok_o and brent else wobble(it["base"], today, 11, 0.04)
        else:
            val = wobble(it["base"], today, 12, 0.02)
        oil_items.append({
            "name": it["name"], "category": it["category"],
            "unit": it["unit"], "price": val,
            "discontinued": it["discontinued"], "note": it["note"],
        })
    record["categories"]["oil"] = {
        "label": MODELS["oil"]["label"],
        "realtime": ok_o,
        "items": oil_items,
    }

    # 硬件：确定性波动（模拟参考价）
    for cat in ["ram", "ssd", "cpu"]:
        items = []
        for idx, it in enumerate(MODELS[cat]["items"]):
            val = wobble(it["base"], today, 100 + idx, 0.03)
            items.append({
                "name": it["name"], "category": it["category"],
                "unit": it["unit"], "price": val,
                "discontinued": it["discontinued"], "note": it["note"],
            })
        record["categories"][cat] = {
            "label": MODELS[cat]["label"],
            "realtime": False,
            "items": items,
        }

    return record


def main():
    today = date.today()
    rec = collect(today)
    os.makedirs(HISTORY_DIR, exist_ok=True)
    # 每日快照
    snap = os.path.join(HISTORY_DIR, f"{today.isoformat()}.json")
    with open(snap, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=2)
    # 最新
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=2)

    rt = sum(1 for c in rec["categories"].values() if c["realtime"])
    print(f"[{today}] 采集完成：5类 {sum(len(c['items']) for c in rec['categories'].values())}项，"
          f"实时源 {rt} 类 → {snap}")
    return rec


if __name__ == "__main__":
    main()
