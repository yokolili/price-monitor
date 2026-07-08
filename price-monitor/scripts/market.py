"""
共享市场因子模型（确定性）
- daily_common(d)：全市场每日共同冲击，所有品类共享 -> 决定跨类联动方向与强度
- daily_idio(d,cat,idx)：品类/型号自身噪声（固定种子，不跨品类碰撞）
- trend：长期缓慢漂移，避免价格水平扁平
- 价格日收益 = 敏感度*共同冲击 + (1-敏感度)*自身噪声
  敏感度高的品类（黄金/石油）联动强；硬件类敏感度低，联动弱但为正
- 全部按日期+固定种子确定性生成，保证：同日同值、跨日渐变、跨进程一致
"""
import math
import random
from datetime import date

from models import CORR_SENSITIVITY

# 固定类别种子（避免 hash() 随机化导致跨进程不一致）
CAT_SEED = {
    "gold": 11, "oil": 23, "ram": 37,
    "ssd": 41, "motherboard": 53, "cpu": 67,
}


def day_seed(d: date):
    return d.year * 10000 + d.month * 100 + d.day


def daily_common(d: date):
    """全市场每日共同冲击，范围约 [-1,1]，所有品类共享"""
    random.seed(day_seed(d) + 777)
    return random.uniform(-1, 1)


def daily_idio(d: date, cat: str, idx: int):
    """品类/型号自身噪声"""
    random.seed(day_seed(d) + CAT_SEED.get(cat, 7) * 131 + idx * 17 + 3)
    return random.uniform(-1, 1)


def price(cat: str, base: float, d: date, idx: int = 0, pct: float = 0.025):
    sens = CORR_SENSITIVITY.get(cat, 0.4)
    s = day_seed(d)
    # 长期趋势：类别间相位不同，制造缓慢漂移
    phase = CAT_SEED.get(cat, 7) / 15.0
    trend = 0.5 * math.sin(s / 60.0) + 0.3 * math.sin(s / 23.0 + phase)
    common = daily_common(d)
    idio = daily_idio(d, cat, idx)
    # 日收益：共享冲击按敏感度加权 + 自身噪声；叠加缓慢趋势
    daily_ret = pct * (sens * common + (1 - sens) * idio) + 0.004 * trend
    return round(base * (1 + daily_ret), 2)
