# core/margin_provider.py
# =====================================================================
# 功能：融資/融券餘額資料提供模組
# 資料來源：FinMind TaiwanStockMarginPurchaseShortSale API
# 涵蓋：融資餘額、融券餘額、融資增減趨勢、融券增減趨勢
# =====================================================================

import datetime
import warnings
warnings.filterwarnings("ignore")

_CACHE: dict = {}
_CACHE_DATE: str = ""


def _today() -> str:
    return datetime.date.today().strftime("%Y-%m-%d")


def fetch_margin_data(stock_id: str, days: int = 15) -> dict:
    """
    取得個股近 N 天的融資融券數據。

    Returns dict:
      available, margin_balance (融資餘額張數), margin_change (融資增減),
      short_balance (融券餘額張數), short_change (融券增減),
      margin_trend (趨勢描述), short_trend, updated
    """
    global _CACHE, _CACHE_DATE

    cache_key = f"{stock_id}_{days}"
    if _CACHE_DATE == _today() and cache_key in _CACHE:
        return _CACHE[cache_key]

    result = {
        "available":      False,
        "margin_balance": 0,
        "margin_change":  0,
        "margin_change_5d": 0,
        "short_balance":  0,
        "short_change":   0,
        "margin_trend":   "",
        "short_trend":    "",
    }

    try:
        from FinMind.data import DataLoader
        dl = DataLoader()

        end_date   = _today()
        start_date = (datetime.date.today() - datetime.timedelta(days=days + 15)).strftime("%Y-%m-%d")

        df = dl.taiwan_stock_margin_purchase_short_sale(
            stock_id=stock_id,
            start_date=start_date,
            end_date=end_date,
        )

        if df is None or df.empty:
            return result

        df = df.sort_values("date").tail(days)

        # 最新數據
        latest = df.iloc[-1]
        prev5  = df.iloc[-6] if len(df) >= 6 else df.iloc[0]
        prev1  = df.iloc[-2] if len(df) >= 2 else df.iloc[-1]

        margin_bal  = int(latest.get("MarginPurchaseTodayBalance", 0))
        margin_prev = int(prev1.get("MarginPurchaseTodayBalance", 0))
        margin_chg  = margin_bal - margin_prev

        margin_bal_5d_ago = int(prev5.get("MarginPurchaseTodayBalance", margin_bal))
        margin_chg_5d     = margin_bal - margin_bal_5d_ago

        short_bal   = int(latest.get("ShortSaleTodayBalance", 0))
        short_prev  = int(prev1.get("ShortSaleTodayBalance", 0))
        short_chg   = short_bal - short_prev

        # 融資趨勢判斷（融資增加代表散戶積極，但也意味籌碼浮動）
        if margin_chg_5d > 500:
            margin_trend = "融資大幅增加（散戶追高，籌碼浮動增加，注意風險）"
        elif margin_chg_5d > 0:
            margin_trend = "融資小幅增加（散戶偏多）"
        elif margin_chg_5d < -500:
            margin_trend = "融資大幅減少（籌碼轉乾淨，對後市偏正面）"
        else:
            margin_trend = "融資小幅減少（籌碼逐漸乾淨）"

        # 融券趨勢判斷
        if short_chg > 100:
            short_trend = "融券增加（空頭佈局增加）"
        elif short_chg < -100:
            short_trend = "融券減少（軋空動能存在）"
        else:
            short_trend = "融券變動不大"

        result.update({
            "available":        True,
            "margin_balance":   margin_bal,
            "margin_change":    margin_chg,
            "margin_change_5d": margin_chg_5d,
            "short_balance":    short_bal,
            "short_change":     short_chg,
            "margin_trend":     margin_trend,
            "short_trend":      short_trend,
            "updated":          latest["date"] if "date" in latest else _today(),
        })

    except Exception as e:
        print(f"[margin] {stock_id} 融資融券取得失敗: {e}")

    # 快取（當日有效）
    _CACHE[cache_key] = result
    _CACHE_DATE = _today()
    return result


def format_margin_for_ai(margin: dict, stock_id: str = "") -> str:
    """格式化融資融券數據為 AI Prompt 文字"""
    if not margin.get("available"):
        return ""

    sid_label = f"（{stock_id}）" if stock_id else ""
    lines = [f"====== 💰 融資融券籌碼數據 {sid_label}======"]
    lines.append(f"- 融資餘額: {margin['margin_balance']:,} 張  當日變化: {margin['margin_change']:+,} 張")
    lines.append(f"- 融資近5日淨增減: {margin['margin_change_5d']:+,} 張  → {margin['margin_trend']}")
    lines.append(f"- 融券餘額: {margin['short_balance']:,} 張  當日變化: {margin['short_change']:+,} 張  → {margin['short_trend']}")
    lines.append("")
    lines.append("請在分析中引用融資融券數據：融資高代表籌碼浮動，")
    lines.append("融資持續減少代表籌碼轉乾淨（對後市相對有利）；融券多代表有軋空潛力。")
    lines.append("=============================================")
    return "\n".join(lines)
