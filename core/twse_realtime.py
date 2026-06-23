# core/twse_realtime.py
# =====================================================================
# 台灣證券交易所官方即時報價模組
# 資料來源：mis.twse.com.tw（證交所官網，交易時間每 5 秒更新）
# 職責：只負責抓取台股即時報價，不做任何 UI 渲染
# 積木說明：此模組獨立，不影響美股、期貨、AI 分析任何邏輯
# =====================================================================

import json
import ssl
import urllib.request
import datetime

# 建立 SSL Context（跳過憑證驗證）
_SSL_CTX = ssl._create_unverified_context()
_HEADERS  = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


# ── 市場交易時間判斷（台灣時區 UTC+8）────────────────────────────────
def _is_tw_market_open() -> bool:
    """判斷台灣股市是否在盤中（週一至週五 09:00~13:30）"""
    now_tw = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    if now_tw.weekday() >= 5:          # 週六 = 5, 週日 = 6
        return False
    market_open  = now_tw.replace(hour=9,  minute=0,  second=0,  microsecond=0)
    market_close = now_tw.replace(hour=13, minute=30, second=0,  microsecond=0)
    return market_open <= now_tw <= market_close


def _detect_exchange(stock_id: str) -> str:
    """
    判斷股票掛牌市場：上市(tse) 或 上櫃(otc)。
    ETF / 大部分股票為上市；少數中小型股為上櫃。
    規則：4 碼數字且首碼 6 → 通常為上櫃；其餘預設上市。
    此函式僅為初始猜測，fetch 時若 tse 失敗會自動 fallback 到 otc。
    """
    sid = stock_id.strip()
    if sid.startswith("6") and len(sid) == 4:
        return "otc"
    return "tse"


def _parse_twse_response(item: dict, stock_id: str, exchange: str) -> dict:
    """
    解析 TWSE API 回傳的 msgArray[0]，轉成統一格式。

    TWSE 關鍵欄位：
      z  = 最新成交價（盤中，盤後為 "-"）
      y  = 昨日收盤價
      o  = 今日開盤價
      h  = 今日最高價
      l  = 今日最低價
      v  = 累積成交量（張）
      t  = 最後更新時間 (HH:MM:SS)
      n  = 股票簡稱
      a  = 五檔賣掛 (價格_價格_...)
      b  = 五檔買掛
      f  = 五檔賣量
      g  = 五檔買量
    """
    def _safe_float(val, default=0.0) -> float:
        try:
            if val in ("-", "", None):
                return default
            return float(str(val).replace(",", ""))
        except Exception:
            return default

    # 最新成交價：盤中用 z，盤後用 y（昨收）
    z_raw    = item.get("z", "-")
    prev_raw = item.get("y", "-")
    open_raw = item.get("o", "-")
    high_raw = item.get("h", "-")
    low_raw  = item.get("l", "-")

    prev_close = _safe_float(prev_raw)
    open_price = _safe_float(open_raw)
    high_price = _safe_float(high_raw)
    low_price  = _safe_float(low_raw)

    if z_raw not in ("-", "", None):
        price = _safe_float(z_raw, prev_close)
        is_intraday = True
    else:
        # 盤後或盤前：顯示昨收
        price = prev_close
        is_intraday = False

    change  = round(price - prev_close, 2) if prev_close else 0.0
    chg_pct = round((change / prev_close) * 100, 2) if prev_close else 0.0

    # 五檔掛單解析（取最佳買賣各一）
    def _parse_orders(price_str: str, qty_str: str):
        prices = [_safe_float(p) for p in price_str.split("_") if p.strip() and p != "-"]
        qtys   = [int(_safe_float(q)) for q in qty_str.split("_") if q.strip() and q != "-"]
        return list(zip(prices, qtys))

    ask_raw = item.get("a", "-")
    bid_raw = item.get("b", "-")
    ask_qty = item.get("f", "-")
    bid_qty = item.get("g", "-")

    asks = _parse_orders(ask_raw, ask_qty)  # 賣方（從低到高）
    bids = _parse_orders(bid_raw, bid_qty)  # 買方（從高到低）

    best_ask = asks[0][0] if asks else None   # 最低賣價
    best_bid = bids[0][0] if bids else None   # 最高買價

    update_time = item.get("t", "--:--:--")
    volume      = int(_safe_float(item.get("v", 0)))

    return {
        "success":      True,
        "source":       "TWSE_REALTIME",
        "is_intraday":  is_intraday,
        "market_open":  _is_tw_market_open(),
        "stock_id":     stock_id,
        "name":         item.get("n", stock_id),
        "exchange":     exchange,
        "price":        round(price, 2),
        "prev_close":   round(prev_close, 2),
        "open":         round(open_price, 2),
        "high":         round(high_price, 2),
        "low":          round(low_price, 2),
        "change":       change,
        "change_percent": chg_pct,
        "volume":       volume,
        "best_ask":     best_ask,
        "best_bid":     best_bid,
        "asks":         asks[:5],   # 五檔賣
        "bids":         bids[:5],   # 五檔買
        "update_time":  update_time,
        "currency":     "TWD",
        "market":       "TW",
    }


def fetch_tw_realtime(stock_id: str) -> dict:
    """
    主入口：抓取台股即時報價。
    策略：先試 tse（上市），失敗或無資料則試 otc（上櫃）。

    Parameters
    ----------
    stock_id : str  e.g. "0050", "2330", "6282"

    Returns
    -------
    dict 包含：success, price, prev_close, change, change_percent,
               open, high, low, volume, best_ask, best_bid,
               asks/bids (五檔), update_time, is_intraday, market_open
    """
    sid = stock_id.strip()

    # 嘗試順序：根據首碼猜測，失敗再換
    exchanges = ["otc", "tse"] if _detect_exchange(sid) == "otc" else ["tse", "otc"]

    for ex in exchanges:
        try:
            url = (
                f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp"
                f"?ex_ch={ex}_{sid}.tw&json=1&delay=0"
            )
            req = urllib.request.Request(url, headers=_HEADERS)
            with urllib.request.urlopen(req, context=_SSL_CTX, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            if data.get("rtcode") != "0000":
                continue

            msg_arr = data.get("msgArray", [])
            if not msg_arr:
                continue

            item = msg_arr[0]
            # 有效資料檢查：至少需要昨收價 y
            if not item.get("y") or item.get("y") == "-":
                continue

            return _parse_twse_response(item, sid, ex)

        except Exception:
            continue

    return {
        "success": False,
        "error": f"無法從 TWSE 取得 {stock_id} 的即時報價",
        "stock_id": stock_id,
    }


def fetch_tw_realtime_batch(stock_ids: list) -> dict:
    """
    批次抓取多支台股即時報價（一次 HTTP 請求，效率更高）。

    Parameters
    ----------
    stock_ids : list  e.g. ["0050", "2330", "0878"]

    Returns
    -------
    dict  {stock_id: result_dict}
    """
    if not stock_ids:
        return {}

    # 把所有股票組成一個查詢字串
    # TWSE API 支援：ex_ch=tse_0050.tw_tse_2330.tw_otc_6282.tw
    # 先全部用 tse 嘗試，失敗的再個別用 otc retry
    parts_tse = [f"tse_{sid}.tw" for sid in stock_ids]
    parts_otc = [f"otc_{sid}.tw" for sid in stock_ids]
    query = "_".join(parts_tse + parts_otc)

    results = {}
    try:
        url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch={query}&json=1&delay=0"
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, context=_SSL_CTX, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        for item in data.get("msgArray", []):
            sid  = item.get("c", "")
            if not sid:
                # 嘗試從 ch 欄位解析
                ch = item.get("ch", "")
                sid = ch.replace(".tw", "") if ch else ""
            if not sid:
                continue
            ex   = item.get("ex", "tse")
            if item.get("y") and item.get("y") != "-":
                results[sid] = _parse_twse_response(item, sid, ex)

    except Exception as e:
        # 批次失敗，回傳空 dict（呼叫方可改用逐一抓取）
        return {}

    return results


def get_market_status() -> dict:
    """
    回傳台股市場目前狀態資訊。
    """
    now_tw = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    is_open = _is_tw_market_open()
    is_weekday = now_tw.weekday() < 5

    if not is_weekday:
        status = "休市（假日）"
        status_en = "Closed (Weekend)"
    elif is_open:
        status = f"盤中 {now_tw.strftime('%H:%M')}"
        status_en = f"Open {now_tw.strftime('%H:%M')}"
    elif now_tw.hour < 9:
        status = f"開盤前 ({now_tw.strftime('%H:%M')})"
        status_en = f"Pre-Market ({now_tw.strftime('%H:%M')})"
    else:
        status = f"收盤後 ({now_tw.strftime('%H:%M')})"
        status_en = f"After-Hours ({now_tw.strftime('%H:%M')})"

    return {
        "is_open": is_open,
        "status_zh": status,
        "status_en": status_en,
        "time_tw": now_tw.strftime("%Y-%m-%d %H:%M:%S"),
    }
