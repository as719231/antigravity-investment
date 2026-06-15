# core/futures_provider.py
# =====================================================================
# 期貨市場即時報價抓取模組（純看盤用，不追蹤持倉）
# 資料來源：Yahoo Finance API（期貨符號）
# 積木職責：只負責抓取報價資料，不做任何 UI 渲染
# =====================================================================

import urllib.request
import json
import ssl


# 常用期貨合約符號對照表（Yahoo Finance Ticker）
FUTURES_CATALOG = {
    # === 台灣期貨 ===
    "TWF":  {"name_zh": "台指期", "name_en": "Taiwan TAIEX Futures", "symbol": "TWF=F", "currency": "TWD", "flag": "🇹🇼"},
    "STXF": {"name_zh": "小台指", "name_en": "Mini TAIEX Futures",   "symbol": "STXF=F","currency": "TWD", "flag": "🇹🇼"},

    # === 美國主要期貨 ===
    "ES":   {"name_zh": "S&P 500 期貨",      "name_en": "S&P 500 Futures",      "symbol": "ES=F",  "currency": "USD", "flag": "🇺🇸"},
    "NQ":   {"name_zh": "NASDAQ 100 期貨",   "name_en": "NASDAQ 100 Futures",   "symbol": "NQ=F",  "currency": "USD", "flag": "🇺🇸"},
    "YM":   {"name_zh": "道瓊期貨",          "name_en": "Dow Jones Futures",    "symbol": "YM=F",  "currency": "USD", "flag": "🇺🇸"},
    "RTY":  {"name_zh": "羅素2000期貨",      "name_en": "Russell 2000 Futures", "symbol": "RTY=F", "currency": "USD", "flag": "🇺🇸"},
    "VX":   {"name_zh": "VIX 波動率指數",    "name_en": "VIX Volatility Index", "symbol": "^VIX",  "currency": "USD", "flag": "🇺🇸"},

    # === 商品期貨 ===
    "GC":   {"name_zh": "黃金期貨",          "name_en": "Gold Futures",         "symbol": "GC=F",  "currency": "USD", "flag": "🥇"},
    "SI":   {"name_zh": "白銀期貨",          "name_en": "Silver Futures",       "symbol": "SI=F",  "currency": "USD", "flag": "⚪"},
    "CL":   {"name_zh": "原油期貨 (WTI)",    "name_en": "Crude Oil WTI",        "symbol": "CL=F",  "currency": "USD", "flag": "🛢️"},
    "BZ":   {"name_zh": "布蘭特原油",        "name_en": "Brent Crude Oil",      "symbol": "BZ=F",  "currency": "USD", "flag": "🛢️"},

    # === 外匯期貨 ===
    "DX":   {"name_zh": "美元指數",          "name_en": "US Dollar Index",      "symbol": "DX=F",  "currency": "USD", "flag": "💵"},
    "6E":   {"name_zh": "歐元兌美元",        "name_en": "EUR/USD Futures",      "symbol": "6E=F",  "currency": "USD", "flag": "🇪🇺"},
    "6J":   {"name_zh": "日圓兌美元",        "name_en": "JPY/USD Futures",      "symbol": "6J=F",  "currency": "USD", "flag": "🇯🇵"},
}


def _yahoo_quote(symbol: str) -> dict:
    """從 Yahoo Finance JSON API 取得期貨即時報價"""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=1d"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    )
    try:
        context = ssl._create_unverified_context()
        with urllib.request.urlopen(req, context=context, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            result = data.get("chart", {}).get("result", [])
            if not result:
                return {"success": False, "error": "No data returned"}

            meta = result[0]["meta"]
            price = meta.get("regularMarketPrice")
            prev_close = meta.get("previousClose") or meta.get("chartPreviousClose")

            if price is None:
                return {"success": False, "error": "Price unavailable"}

            prev_val = prev_close if prev_close else price
            change = price - prev_val
            change_pct = (change / prev_val) * 100 if prev_val else 0.0

            return {
                "success": True,
                "price": round(price, 2),
                "prev_close": round(prev_val, 2),
                "change": round(change, 2),
                "change_percent": round(change_pct, 2),
                "market_state": meta.get("marketState", "UNKNOWN"),
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


def fetch_futures_price(contract_key: str) -> dict:
    """
    取得期貨即時報價。

    Parameters
    ----------
    contract_key : str
        期貨代號（例如 'ES', 'NQ', 'TWF', 'GC'）

    Returns
    -------
    dict
        包含 success, price, change, change_percent, currency, name_zh, name_en, flag
    """
    info = FUTURES_CATALOG.get(contract_key.upper())
    if info is None:
        # 直接用輸入的 symbol 查詢
        symbol = contract_key if "=" in contract_key or "^" in contract_key else f"{contract_key}=F"
        info = {"name_zh": contract_key, "name_en": contract_key, "symbol": symbol, "currency": "USD", "flag": "📊"}

    result = _yahoo_quote(info["symbol"])
    if result.get("success"):
        result["name_zh"] = info["name_zh"]
        result["name_en"] = info["name_en"]
        result["currency"] = info["currency"]
        result["flag"] = info["flag"]
        result["contract_key"] = contract_key
    return result


def fetch_multiple_futures(contract_keys: list) -> list:
    """批量取得多個期貨報價，回傳 list of dict"""
    results = []
    for key in contract_keys:
        r = fetch_futures_price(key)
        r["key"] = key
        results.append(r)
    return results


def get_default_watchlist() -> list:
    """回傳預設的看盤監控清單（關鍵期貨）"""
    return ["ES", "NQ", "YM", "VX", "GC", "CL", "DX"]
