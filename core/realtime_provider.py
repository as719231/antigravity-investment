# core/realtime_provider.py
# =====================================================================
# 即時股價抓取模組（台股 + 美股）統一入口
#
# 台股：優先使用 core/twse_realtime.py（證交所官方，交易時間每 5 秒更新）
#        備用：Yahoo 奇摩 HTML 爬取
# 美股：Yahoo Finance JSON API（fast_info，約 2~5 分鐘延遲）
#
# 積木職責：只負責報價路由，不做任何 UI 渲染
# v2.3 改動：整合 TWSE 真即時 API，台股延遲從 15 分鐘縮短至 ≤5 秒
# =====================================================================

import urllib.request
import json
import ssl
import re
import datetime

from core.twse_realtime import fetch_tw_realtime, get_market_status

# ── SSL Context ──────────────────────────────────────────────────────
_SSL_CTX = ssl._create_unverified_context()
_HEADERS  = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


# ── 美股中英文名稱對照表 ─────────────────────────────────────────────
US_STOCK_NAMES = {
    "AAPL":  {"zh": "蘋果公司",     "en": "Apple Inc."},
    "MSFT":  {"zh": "微軟",         "en": "Microsoft Corp."},
    "NVDA":  {"zh": "輝達",         "en": "NVIDIA Corp."},
    "TSLA":  {"zh": "特斯拉",       "en": "Tesla Inc."},
    "AMZN":  {"zh": "亞馬遜",       "en": "Amazon.com Inc."},
    "GOOGL": {"zh": "谷歌(A股)",    "en": "Alphabet Inc. (Class A)"},
    "GOOG":  {"zh": "谷歌(C股)",    "en": "Alphabet Inc. (Class C)"},
    "META":  {"zh": "Meta元宇宙",   "en": "Meta Platforms Inc."},
    "ASML":  {"zh": "艾司摩爾",     "en": "ASML Holding NV"},
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


# ── 備用：Yahoo 奇摩 HTML 爬取（台股）───────────────────────────────
def _fetch_tw_yahoo_scrape(stock_id: str) -> dict:
    """備用方案：爬取 Yahoo 奇摩股市 HTML"""
    url = f"https://tw.stock.yahoo.com/quote/{stock_id}"
    req = urllib.request.Request(url, headers=_HEADERS)
    try:
        with urllib.request.urlopen(req, context=_SSL_CTX) as response:
            html = response.read().decode("utf-8")

            price = None
            trend = "flat"
            price_match = re.search(
                r'class="[^"]*Fz\(32px\)[^"]*(C\(\$c-trend-\w+\))[^"]*">([^<]+)</span>', html
            )
            if price_match:
                trend_class = price_match.group(1)
                price = float(price_match.group(2).replace(",", ""))
                trend = "up" if "up" in trend_class else ("down" if "down" in trend_class else "flat")
            else:
                simple = re.search(r'class="[^"]*Fz\(32px\)[^"]*">([^<]+)</span>', html)
                if simple:
                    price = float(simple.group(1).replace(",", ""))

            if price is None:
                return {"success": False, "error": "Yahoo HTML 解析失敗"}

            change = 0.0
            chg_m = re.search(
                r'class="[^"]*Fz\(20px\)[^"]*(C\(\$c-trend-\w+\))[^"]*">(?:<span[^>]*></span>)?\s*([^<]+)</span>',
                html,
            )
            if chg_m:
                change = float(chg_m.group(2).replace(",", ""))
                if trend == "down":
                    change = -change

            chg_pct = 0.0
            pct_m = re.search(
                r'class="[^"]*Fz\(20px\)[^"]*C\(\$c-trend-\w+\)[^"]*">\(([^%]+)%\)</span>', html
            )
            if pct_m:
                chg_pct = float(pct_m.group(1))
                if trend == "down":
                    chg_pct = -chg_pct

            now_str = datetime.datetime.now().strftime("%H:%M:%S")
            return {
                "success":        True,
                "source":         "YAHOO_SCRAPE",
                "is_intraday":    True,
                "market_open":    True,
                "price":          round(price, 2),
                "prev_close":     round(price - change, 2),
                "change":         round(change, 2),
                "change_percent": round(chg_pct, 2),
                "currency":       "TWD",
                "symbol":         f"{stock_id}.TW",
                "market":         "TW",
                "update_time":    now_str,
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── 備用：Yahoo Finance JSON API ─────────────────────────────────────
def _fetch_yahoo_json_api(symbol: str, currency_default: str = "TWD") -> dict:
    """Yahoo Finance JSON API（備用，美股約 2~5 分鐘延遲）"""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    req = urllib.request.Request(url, headers=_HEADERS)
    try:
        with urllib.request.urlopen(req, context=_SSL_CTX, timeout=8) as response:
            data = json.loads(response.read().decode("utf-8"))
            if not data.get("chart", {}).get("result"):
                return {"success": False, "error": "No result"}

            meta = data["chart"]["result"][0]["meta"]
            price      = meta.get("regularMarketPrice")
            prev_close = meta.get("previousClose")

            if price is None:
                try:
                    closes = data["chart"]["result"][0]["indicators"]["quote"][0].get("close", [])
                    closes = [c for c in closes if c is not None]
                    if closes:
                        price = closes[-1]
                except Exception:
                    pass

            if price is None:
                return {"success": False, "error": "Price not available"}

            prev_val   = prev_close or price
            change     = round(price - prev_val, 4)
            chg_pct    = round((change / prev_val) * 100, 2) if prev_val else 0.0
            market_ts  = meta.get("regularMarketTime", 0)
            now_str    = datetime.datetime.now().strftime("%H:%M:%S")

            return {
                "success":         True,
                "source":          "YAHOO_JSON",
                "price":           round(price, 4),
                "prev_close":      round(prev_val, 4),
                "change":          change,
                "change_percent":  chg_pct,
                "currency":        meta.get("currency", currency_default),
                "symbol":          symbol,
                "market_state":    meta.get("marketState", "UNKNOWN"),
                "market_time":     market_ts,
                "update_time":     now_str,
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ════════════════════════════════════════════════════════════════════
# 公開入口函式
# ════════════════════════════════════════════════════════════════════

def fetch_realtime_price(stock_id: str) -> dict:
    """
    台股即時報價統一入口（v2.3 升級版）。

    優先順序：
      1. TWSE 官方 API（mis.twse.com.tw）← 最快，交易時間 ≤5 秒更新
      2. Yahoo 奇摩 HTML 爬取             ← 備用
      3. Yahoo Finance JSON API            ← 最後手段

    Parameters
    ----------
    stock_id : str  e.g. "0050", "2330", "0878", "6282"
    """
    clean_id = stock_id.strip()

    # 台股（純數字代號）
    if clean_id.isdigit() or (clean_id.endswith(".TW") and clean_id.split(".")[0].isdigit()):
        sid = clean_id.replace(".TW", "").replace(".tw", "")

        # ① TWSE 官方即時（最佳）
        result = fetch_tw_realtime(sid)
        if result.get("success"):
            return result

        # ② Yahoo 奇摩 HTML（備用）
        result2 = _fetch_tw_yahoo_scrape(sid)
        if result2.get("success"):
            return result2

        # ③ Yahoo JSON API（最後手段）
        return _fetch_yahoo_json_api(f"{sid}.TW", currency_default="TWD")

    # 非數字代號（美股 / ETF）直接用 Yahoo JSON
    return _fetch_yahoo_json_api(clean_id, currency_default="USD")


def fetch_us_stock_price(ticker: str) -> dict:
    """
    美股即時報價（Yahoo Finance API）。

    Parameters
    ----------
    ticker : str  e.g. "AAPL", "TSLA", "NVDA", "VOO"
    """
    ticker = ticker.strip().upper()
    result = _fetch_yahoo_json_api(ticker, currency_default="USD")

    if result.get("success"):
        name_info = US_STOCK_NAMES.get(ticker, {"zh": ticker, "en": ticker})
        result["name_zh"]  = name_info["zh"]
        result["name_en"]  = name_info["en"]
        result["ticker"]   = ticker
        result["market"]   = "US"
    return result


def get_us_watchlist_default() -> list:
    """回傳預設美股監控清單"""
    return ["AAPL", "NVDA", "TSLA", "MSFT", "AMZN", "TSM", "QQQ", "VOO"]
