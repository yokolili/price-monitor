"""
型号数据库（六类）
- 黄金 gold / 石油 oil / 内存 ram / 硬盘 ssd / 主板 motherboard / CPU
- 基准价参考太平洋电脑网(PConline) 市场行情区间；日内波动由模型模拟
- 数据来源统一标注为「太平洋电脑网」

字段说明：
  name          型号名称
  category      细分类别
  unit          计价单位
  base          基准参考价（人民币，硬件类；金价/石油见各自单位）
  discontinued  停产时间 (str 或 None)
  note          备注
"""

# 太平洋各品类报价页（用于数据来源标注与抓取尝试）
SOURCE_URLS = {
    "gold": "https://www.pconline.com.cn/",
    "oil": "https://www.pconline.com.cn/",
    "ram": "https://product.pconline.com.cn/memory/",
    "ssd": "https://product.pconline.com.cn/ssd/",
    "motherboard": "https://product.pconline.com.cn/motherboard/",
    "cpu": "https://product.pconline.com.cn/cpu/",
}

MODELS = {
    "gold": {
        "label": "黄金",
        "unit": "元/克",
        "items": [
            {"name": "国际金价 XAU/USD", "category": "伦敦金", "unit": "美元/盎司",
             "base": 2350.0, "discontinued": None,
             "note": "国际现货金价，美元/盎司，站内换算为元/克展示"},
            {"name": "国内Au99.99", "category": "上海金交所", "unit": "元/克",
             "base": 550.0, "discontinued": None,
             "note": "上海黄金交易所标准金条参考价"},
            {"name": "品牌金饰(周大福)", "category": "金饰", "unit": "元/克",
             "base": 680.0, "discontinued": None,
             "note": "含工费，零售参考"},
            {"name": "投资金条(银行)", "category": "金条", "unit": "元/克",
             "base": 565.0, "discontinued": None,
             "note": "银行投资金条回购价参考"},
        ],
    },
    "oil": {
        "label": "石油",
        "unit": "美元/桶",
        "items": [
            {"name": "WTI 原油", "category": "轻质原油", "unit": "美元/桶",
             "base": 78.0, "discontinued": None,
             "note": "美国西德州中质原油期货主力"},
            {"name": "Brent 原油", "category": "布伦特", "unit": "美元/桶",
             "base": 82.0, "discontinued": None,
             "note": "北海布伦特原油期货主力"},
            {"name": "国内成品油 92#", "category": "汽油", "unit": "元/升",
             "base": 7.9, "discontinued": None,
             "note": "全国各地均价参考"},
            {"name": "国内成品油 0#柴油", "category": "柴油", "unit": "元/升",
             "base": 7.6, "discontinued": None,
             "note": "全国各地均价参考"},
        ],
    },
    "ram": {
        "label": "内存",
        "unit": "元",
        "items": [
            {"name": "DDR4 8GB 3200", "category": "DDR4", "unit": "元",
             "base": 115.0, "discontinued": None, "note": "桌面主流"},
            {"name": "DDR4 16GB 3200", "category": "DDR4", "unit": "元",
             "base": 215.0, "discontinued": None, "note": "桌面主流"},
            {"name": "DDR5 16GB 6000", "category": "DDR5", "unit": "元",
             "base": 345.0, "discontinued": None, "note": "新平台主流"},
            {"name": "DDR5 32GB 6000", "category": "DDR5", "unit": "元",
             "base": 660.0, "discontinued": None, "note": "新平台主流"},
            {"name": "DDR3 8GB 1600", "category": "DDR3", "unit": "元",
             "base": 95.0, "discontinued": "2022-01", "note": "已逐步停产，二手为主"},
            {"name": "DDR2 2GB 800", "category": "DDR2", "unit": "元",
             "base": 60.0, "discontinued": "2015-06", "note": "彻底淘汰，仅收藏/维修"},
        ],
    },
    "ssd": {
        "label": "硬盘(SSD)",
        "unit": "元",
        "items": [
            {"name": "SATA SSD 1TB", "category": "SATA", "unit": "元",
             "base": 380.0, "discontinued": None, "note": "入门装机"},
            {"name": "NVMe PCIe4 1TB", "category": "NVMe Gen4", "unit": "元",
             "base": 480.0, "discontinued": None, "note": "主流高速"},
            {"name": "NVMe PCIe4 2TB", "category": "NVMe Gen4", "unit": "元",
             "base": 899.0, "discontinued": None, "note": "大容量"},
            {"name": "NVMe PCIe5 2TB", "category": "NVMe Gen5", "unit": "元",
             "base": 1499.0, "discontinued": None, "note": "旗舰速率"},
            {"name": "SATA SSD 120GB", "category": "SATA", "unit": "元",
             "base": 99.0, "discontinued": "2023-03", "note": "小容量淘汰"},
            {"name": "机械硬盘 3.5 1TB", "category": "HDD", "unit": "元",
             "base": 270.0, "discontinued": None, "note": "冷存储"},
        ],
    },
    "motherboard": {
        "label": "主板",
        "unit": "元",
        "items": [
            {"name": "B650 (AMD 主流)", "category": "AMD B650", "unit": "元",
             "base": 1050.0, "discontinued": None, "note": "AM5 主流，搭配锐龙7000/9000"},
            {"name": "B760 (Intel 主流)", "category": "Intel B760", "unit": "元",
             "base": 999.0, "discontinued": None, "note": "搭配13/14代酷睿"},
            {"name": "X670E (AMD 高端)", "category": "AMD X670E", "unit": "元",
             "base": 2699.0, "discontinued": None, "note": "旗舰扩展"},
            {"name": "Z790 (Intel 高端)", "category": "Intel Z790", "unit": "元",
             "base": 2299.0, "discontinued": None, "note": "旗舰超频"},
            {"name": "A520 (入门)", "category": "AMD A520", "unit": "元",
             "base": 450.0, "discontinued": "2024-06", "note": "AM4 末代，二手为主"},
            {"name": "H610 (入门)", "category": "Intel H610", "unit": "元",
             "base": 499.0, "discontinued": None, "note": "入门办公"},
            {"name": "B550 (上代)", "category": "AMD B550", "unit": "元",
             "base": 699.0, "discontinued": "2025-01", "note": "AM4 清库"},
        ],
    },
    "cpu": {
        "label": "CPU",
        "unit": "元",
        "items": [
            {"name": "Intel i5-14600K", "category": "桌面", "unit": "元",
             "base": 1899.0, "discontinued": None, "note": "主流游戏U"},
            {"name": "Intel i9-14900K", "category": "桌面", "unit": "元",
             "base": 4299.0, "discontinued": None, "note": "旗舰游戏U"},
            {"name": "AMD R7 7800X3D", "category": "桌面", "unit": "元",
             "base": 2599.0, "discontinued": None, "note": "游戏神U"},
            {"name": "AMD R9 9950X", "category": "桌面", "unit": "元",
             "base": 4999.0, "discontinued": None, "note": "生产力旗舰"},
            {"name": "Intel i5-12400F", "category": "桌面", "unit": "元",
             "base": 899.0, "discontinued": "2024-12", "note": "上代性价比，清库存"},
            {"name": "AMD R5 5600X", "category": "桌面", "unit": "元",
             "base": 750.0, "discontinued": "2024-06", "note": "AM4末代，二手为主"},
            {"name": "Intel i7-9700K", "category": "桌面", "unit": "元",
             "base": 1500.0, "discontinued": "2022-03", "note": "9代，已停产"},
        ],
    },
}

# 类别顺序（用于展示）
CATEGORY_ORDER = ["gold", "oil", "ram", "ssd", "motherboard", "cpu"]

# 数据来源标注（统一：太平洋电脑网；金价/石油优先实时API）
DATA_SOURCE_NOTE = {
    "gold": "太平洋电脑网(参考行情) + 实时金价API",
    "oil": "太平洋电脑网(参考行情) + 实时原油API",
    "ram": "太平洋电脑网(报价参考)",
    "ssd": "太平洋电脑网(报价参考)",
    "motherboard": "太平洋电脑网(报价参考)",
    "cpu": "太平洋电脑网(报价参考)",
}

# ---- 关联分析用配置 ----
# 每类选一个代表型号，用于跨类关联计算
REP_ITEM = {
    "gold": "国内Au99.99",
    "oil": "WTI 原油",
    "ram": "DDR5 16GB 6000",
    "ssd": "NVMe PCIe4 1TB",
    "motherboard": "B650 (AMD 主流)",
    "cpu": "Intel i5-14600K",
}
# 各类对「共享市场因子」的敏感度（决定跨类关联强度）
# 黄金/石油对宏观(美元/通胀)最敏感 -> 高度正相关；硬件类敏感度较低
CORR_SENSITIVITY = {
    "gold": 0.85,
    "oil": 0.75,
    "ram": 0.40,
    "ssd": 0.35,
    "motherboard": 0.30,
    "cpu": 0.45,
}
# 关联页聚焦的 5 类（按用户要求：黄金/石油/硬盘/内存/CPU）
CORR_FOCUS = ["gold", "oil", "ssd", "ram", "cpu"]
