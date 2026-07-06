"""
回填历史数据：纯本地确定性生成（不联网，模拟历史）
让周/月/年对比报告首次即有数据可比。
页面会标注回填数据为"历史回溯(模拟)"。
"""
import json
import os
import sys
import random
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(__file__))
from models import MODELS, DATA_SOURCE_NOTE, CATEGORY_ORDER

ROOT = os.path.dirname(os.path.dirname(__file__))
HISTORY_DIR = os.path.join(ROOT, "data", "history")
USD_CNY = 7.15


def day_seed(d: date):
    return d.year * 10000 + d.month * 100 + d.day


def wobble(base, d: date, salt, pct=0.03):
    random.seed(day_seed(d) + salt)
    return round(base * (1 + random.uniform(-pct, pct)), 2)


def make_record(d: date):
    rec = {
        "date": d.isoformat(),
        "updated_at": d.isoformat() + "T00:00:00",
        "backfilled": True,
        "source_note": DATA_SOURCE_NOTE,
        "categories": {},
    }
    # 金价（含 XAU 换算）
    xau_base = 2350.0
    gold_items = []
    for idx, it in enumerate(MODELS["gold"]["items"]):
        if "XAU" in it["name"]:
            val = wobble(xau_base, d, 1, 0.02)
        elif "元/克" in it["unit"]:
            val = round(wobble(xau_base, d, 1, 0.02) / 31.1035 * USD_CNY, 2)
        else:
            val = wobble(it["base"], d, 2 + idx, 0.02)
        gold_items.append({"name": it["name"], "category": it["category"],
                            "unit": it["unit"], "price": val,
                            "discontinued": it["discontinued"], "note": it["note"]})
    rec["categories"]["gold"] = {"label": MODELS["gold"]["label"], "realtime": False, "items": gold_items}

    for cat in ["oil", "ram", "ssd", "cpu"]:
        items = []
        for idx, it in enumerate(MODELS[cat]["items"]):
            val = wobble(it["base"], d, 100 + idx, 0.03)
            items.append({"name": it["name"], "category": it["category"],
                          "unit": it["unit"], "price": val,
                          "discontinued": it["discontinued"], "note": it["note"]})
        rec["categories"][cat] = {"label": MODELS[cat]["label"], "realtime": False, "items": items}
    return rec


def backfill(days=365, end=None):
    end = end or date.today()
    created = 0
    for i in range(1, days):
        d = end - timedelta(days=i)
        fn = os.path.join(HISTORY_DIR, f"{d.isoformat()}.json")
        if os.path.exists(fn):
            continue
        rec = make_record(d)
        with open(fn, "w", encoding="utf-8") as f:
            json.dump(rec, f, ensure_ascii=False, indent=2)
        created += 1
    print(f"回填完成：新增 {created} 天历史快照")


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 365
    backfill(n)
