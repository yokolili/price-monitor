"""
型号数据库（五类）
- 金价 (gold): 以克/元计，记录国际金价与国内金价参考
- 石油 (oil): 以桶/美元计，WTI / Brent
- 内存 (ram): DDR 代际与主流型号
- 硬盘 (ssd): SSD 型号
- CPU: 桌面/服务器主流型号

字段说明：
  name      型号名称
  category  细分类别
  unit      计价单位
  base      基准参考价（人民币，硬件类；金价/石油见各自单位）
  discontinued  停产时间 (str 或 None)
  note      备注
"""

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
CATEGORY_ORDER = ["gold", "oil", "ram", "ssd", "cpu"]

# 数据性质标注
DATA_SOURCE_NOTE = {
    "gold": "实时API(金价) + 参考换算",
    "oil": "实时API(原油) + 参考换算",
    "ram": "预置型号库 + 参考价(标注模拟)",
    "ssd": "预置型号库 + 参考价(标注模拟)",
    "cpu": "预置型号库 + 参考价(标注模拟)",
}
