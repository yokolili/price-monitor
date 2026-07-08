"""
太平洋电脑网(PConline) 报价抓取（尽力尝试）
- 尝试抓取品类报价页并解析价格数字
- 太平洋价格为 JS 动态渲染，纯 HTTP 通常取不到真实成交价，
  故任何失败都返回 None，由 fetch.py 回退到「太平洋参考行情」模型
- 返回 (anchor_price, success)；anchor 为该页报价的中位数（市场水位指示）
"""
import re
import ssl
import urllib.request
from models import SOURCE_URLS

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


def _http_get(url, timeout=10):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
            return r.read().decode("utf-8", "ignore")
    except Exception:
        return None


def _extract_prices(html):
    """从 HTML 中提取价格数字（多种写法兼容）"""
    nums = []
    # &yen;1234 / ¥1234 / ￥1234
    for m in re.finditer(r"(?:&yen;|¥|￥)\s*([0-9][0-9,]{2,8})", html):
        nums.append(int(m.group(1).replace(",", "")))
    # 数字 + 元/元）
    for m in re.finditer(r"([0-9][0-9,]{2,8})\s*元", html):
        nums.append(int(m.group(1).replace(",", "")))
    # price-range 文本中的区间，如 ￥100-300 -> 取两端
    for m in re.finditer(r"class=\"price-range\"[^>]*>.*?</div>", html, re.S):
        block = m.group(0)
        for mm in re.finditer(r"([0-9][0-9,]{2,8})", block):
            nums.append(int(mm.group(1).replace(",", "")))
    return nums


def fetch_anchor(cat_key):
    """返回 (anchor_price, success)。失败返回 (None, False)。"""
    url = SOURCE_URLS.get(cat_key)
    if not url:
        return None, False
    html = _http_get(url)
    if not html:
        return None, False
    nums = _extract_prices(html)
    # 过滤掉明显不合理的（<50 或 >200000）
    nums = [n for n in nums if 50 <= n <= 200000]
    if len(nums) < 3:
        return None, False
    nums.sort()
    mid = nums[len(nums) // 2]
    return mid, True
