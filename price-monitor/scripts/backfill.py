"""
回填历史数据：本地确定性生成（不联网）
- 使用「共享市场因子」模型，使跨类关联真实可比
- 让周/月/年对比报告与关联分析页首次即有数据可比
- 页面会标注回填数据为「历史回溯(模拟)」
"""
import json
import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(__file__))
from models import MODELS, DATA_SOURCE_NOTE, CATEGORY_ORDER
import market

ROOT = os.path.dirname(os.path.dirname(__file__))
HISTORY_DIR = os.path.join(ROOT, "data", "history")


def make_record(d: date):
    rec = {
        "date": d.isoformat(),
        "updated_at": d.isoformat() + "T00:00:00",
        "backfilled": True,
        "source_note": DATA_SOURCE_NOTE,
        "categories": {},
    }
    for cat in CATEGORY_ORDER:
        items = []
        for idx, it in enumerate(MODELS[cat]["items"]):
            val = market.price(cat, it["base"], d, idx)
            items.append({
                "name": it["name"], "category": it["category"],
                "unit": it["unit"], "price": val,
                "discontinued": it["discontinued"], "note": it["note"],
                "source": "太平洋参考行情",
            })
        rec["categories"][cat] = {
            "label": MODELS[cat]["label"],
            "realtime": False,
            "source": "太平洋电脑网(参考行情)",
            "items": items,
        }
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
