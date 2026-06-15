# core/realtime_provider.py
# =====================================================================
# 即時股價抓取模組（台股 + 美股）
# - 台股：優先 Yahoo 奇摩 HTML 爬取（無延遲）→ 備用 JSON API
# - 美股：Yahoo Finance JSON API（15分鐘延遲，免費方案）
# 積木職責：只負責抓取報價，不做任何 UI 渲染
# =====================================================================

import urllib.request
import json
import ssl
import re


# 美股常用股票中英文名稱對照表
US_STOCK_NAMES = {
    "AAPL":  {"zh": "蘋果公司",     "en": "Apple Inc."},
    "MSFT":  {"zh": "微軟",         "en": "Microsoft Corp."},
    "NVDA":  {"zh": "輝達",         "en": "NVIDIA Corp."},
    "TSLA":  {"zh": "特斯拉",       "en": "Tesla Inc."},
    "AMZN":  {"zh": "亞馬遜",       "en": "Amazon.com Inc."},
    "GOOGL": {"zh": "谷歌(A股)",    "en": "Alphabet Inc. (Class A)"},
    "GOOG":  {"zh": "谷歌(C股)",    "en": "Alphabet Inc. (Class C)"},
    "META":  {"zh": "Meta元宇宙",   "en": "Meta Platforms Inc."},
    "AMSL":  {"zh": "艾司摩爾",     "en": "ASML Holding NV"},
    "NFLX":  {"zh": "Netflix",      "en": "Netflix Inc."},
    "AMD":   {"zh": "超微",         "en": "Advanced Micro Devices"},
    "INTC":  {"zh": "英特爾",       "en": "Intel Corp."},
    "QCOM":  {"zh": "高通",         "en": "Qualcomm Inc."},
    "AVGO":  {"zh": "博通",         "en": "Broadcom Inc."},
    "TSM":   {"zh": "台積電ADR",    "en": "TSMC (ADR)"},
    "VOO":   {"zh": "先鋒S&P500",   "en": "Vanguard S&P 500 ETF"},
    "QQQ":   {"zh": "納指100 ETF",  "en": "Invesco QQQ Trust"},
    "SPY":   {"zh": "SPDR S&P500",  "en": "SPDR S&P 500 ETF"},
    "IWM":   {"zh": "羅素2000 ETF", "en": "iShares Russell 2000 ETF"},
    "GLD":   {"zh": "黃金 ETF",     "en": "SPDR Gold Shares"},
    "ARKK":  {"zh": "ARK創新 ETF",  "en": "ARK Innovation ETF"},
    "SOXX":  {"zh": "費城半導體ETF","en": "iShares Semiconductor ETF"},
    "XLK":   {"zh": "科技股 ETF",   "en": "Technology Select Sector SPDR"},
    "BRK-B": {"zh": "波克夏(B股)", "en": "Berkshire Hathaway Inc."},
    "JPM":   {"zh": "摩根大通",     "en": "JPMorgan Chase & Co."},
    "V":     {"zh": "VISA",         "en": "Visa Inc."},
    "JNJ":   {"zh": "嬌生",         "en": "Johnson & Johnson"},
    "WMT":   {"zh": "沃爾瑪",       "en": "Walmart Inc."},
    "UNH":   {"zh": "聯合健康",     "en": "UnitedHealth Group"},
}


def _fetch_tw_realtime_scrape(stock_id: str) -> dict:
    """
    爬取 Yahoo 奇摩股市 HTML 網頁，取得無延遲的即時成交價與漲跌幅
    """
    url = f"https://tw.stock.yahoo.com/quote/{stock_id}"
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    )
    try:
        context = ssl._create_unverified_context()
        with urllib.request.urlopen(req, context=context) as response:
            html = response.read().decode('utf-8')

            price = None
            trend = "flat"
            price_match = re.search(r'class="[^"]*Fz\(32px\)[^"]*(C\(\$c-trend-\w+\))[^"]*">([^<]+)</span>', html)
            if price_match:
                trend_class = price_match.group(1)
                price = float(price_match.group(2).replace(",", ""))
                if "up" in trend_class:
                    trend = "up"
                elif "down" in trend_class:
                    trend = "down"
            else:
                price_match_simple = re.search(r'class="[^"]*Fz\(32px\)[^"]*">([^<]+)</span>', html)
                if price_match_simple:
                    price = float(price_match_simple.group(1).replace(",", ""))

            if price is None:
                return {"success": False, "error": "Price not found in HTML"}

            change = 0.0
            change_match = re.search(r'class="[^"]*Fz\(20px\)[^"]*(C\(\$c-trend-\w+\))[^"]*">(?:<span[^>]*></span>)?\s*([^<]+)</span>', html)
            if change_match:
                change = float(change_match.group(2).replace(",", ""))
                if trend == "down":
                    change = -change

            change_percent = 0.0
            pct_match = re.search(r'class="[^"]*Fz\(20px\)[^"]*C\(\$c-trend-\w+\)[^"]*">\(([^%]+)%\)</span>', html)
            if pct_match:
                change_percent = float(pct_match.group(1))
                if trend == "down":
                    change_percent = -change_percent

            prev_close = price - change

            return {
                "success": True,
                "price": round(price, 2),
                "prev_close": round(prev_close, 2),
                "change": round(change, 2),
                "change_percent": round(change_percent, 2),
                "currency": "TWD",
                "symbol": f"{stock_id}.TW",
                "market": "TW"
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


def _fetch_yahoo_json_api(symbol: str, currency_default: str = "TWD") -> dict:
    """使用 Yahoo Finance JSON API 抓取報價（備用，約有15分鐘延遲）"""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    )
    try:
        context = ssl._create_unverified_context()
        with urllib.request.urlopen(req, context=context, timeout=8) as response:
            data = json.loads(response.read().decode('utf-8'))
            if not data.get('chart', {}).get('result'):
                return {"success": False, "error": "No result found"}

            meta = data['chart']['result'][0]['meta']
            price = meta.get('regularMarketPrice')
            prev_close = meta.get('previousClose')

            if price is None or prev_close is None:
                try:
                    quotes = data['chart']['result'][0]['indicators']['quote'][0]
                    closes = [c for c in quotes.get('close', []) if c is not None]
                    if closes:
                        price = closes[-1]
                except Exception:
                    pass

            if price is None:
                return {"success": False, "error": "Price not available"}

            prev_close_val = prev_close if prev_close else price
            change = price - prev_close_val
            change_percent = (change / prev_close_val) * 100 if prev_close_val else 0.0

            return {
                "success": True,
                "price": round(price, 2),
                "prev_close": round(prev_close_val, 2),
                "change": round(change, 2),
                "change_percent": round(change_percent, 2),
                "currency": meta.get('currency', currency_default),
                "symbol": symbol,
                "market_state": meta.get("marketState", "UNKNOWN"),
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


def fetch_realtime_price(stock_id: str) -> dict:
    """
    台股即時報價入口（維持向下相容）。
    優先使用奇摩 HTML 爬取（無延遲），失敗則使用 JSON API。
    """
    clean_id = stock_id.strip()

    if clean_id.isdigit():
        res = _fetch_tw_realtime_scrape(clean_id)
        if res.get("success"):
            return res
        # 備用 JSON API
        return _fetch_yahoo_json_api(f"{clean_id}.TW", currency_default="TWD")

    # 非數字直接用 JSON API
    return _fetch_yahoo_json_api(clean_id, currency_default="USD")


def fetch_us_stock_price(ticker: str) -> dict:
    """
    美股即時報價（Yahoo Finance API，約15分鐘延遲）。

    Parameters
    ----------
    ticker : str
        美股代號，例如 'AAPL', 'TSLA', 'NVDA', 'VOO'

    Returns
    -------
    dict
        包含 success, price, change, change_percent, currency='USD',
        name_zh, name_en, market_state
    """
    ticker = ticker.strip().upper()
    result = _fetch_yahoo_json_api(ticker, currency_default="USD")

    if result.get("success"):
        name_info = US_STOCK_NAMES.get(ticker, {"zh": ticker, "en": ticker})
        result["name_zh"] = name_info["zh"]
        result["name_en"] = name_info["en"]
        result["ticker"] = ticker
        result["market"] = "US"
    return result


def get_us_watchlist_default() -> list:
    """回傳預設美股監控清單（常見科技龍頭 + ETF）"""
    return ["AAPL", "NVDA", "TSLA", "MSFT", "AMZN", "TSM", "QQQ", "VOO"]
