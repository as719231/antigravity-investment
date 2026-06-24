# core/macro_provider.py
# =====================================================================
# 功能：總體經濟數據提供模組
# 資料來源：Yahoo Finance API (yfinance)
# 涵蓋：VIX、費城半導體指數(SOX)、台幣匯率、NASDAQ、S&P500
# =====================================================================

import yfinance as yf
import datetime
import warnings
warnings.filterwarnings("ignore")

_CACHE: dict = {}
_CACHE_TIME: datetime.datetime | None = None
_CACHE_TTL_MINUTES = 30  # 總經數據每 30 分鐘刷新一次


def _is_cache_valid() -> bool:
    if _CACHE_TIME is None:
        return False
    return (datetime.datetime.now() - _CACHE_TIME).seconds < _CACHE_TTL_MINUTES * 60


def _fetch_ticker(symbol: str) -> dict:
    """安全地抓取單一 ticker 的最新價格與漲跌幅"""
    try:
        t = yf.Ticker(symbol)
        h = t.history(period="2d")
        if h.empty:
            return {}
        price = float(h["Close"].iloc[-1])
        prev  = float(h["Close"].iloc[-2]) if len(h) > 1 else price
        chg   = (price - prev) / prev * 100 if prev else 0
        return {"price": price, "change_pct": chg}
    except Exception:
        return {}


def fetch_macro_context() -> dict:
    """
    取得總體經濟環境數據。
    返回 dict，可直接傳入 ai_agent.get_system_instruction。

    Keys:
      vix, sox, usd_twd, nasdaq, sp500, dji,
      sox_trend (看多/看空), vix_level (低/中/高恐慌)
    """
    global _CACHE, _CACHE_TIME

    if _is_cache_valid() and _CACHE:
        return _CACHE

    tickers = {
        "vix":     "^VIX",
        "sox":     "^SOX",
        "usd_twd": "TWD=X",
        "nasdaq":  "^IXIC",
        "sp500":   "^GSPC",
        "dji":     "^DJI",
    }

    result = {"available": False}
    success_count = 0

    for key, symbol in tickers.items():
        data = _fetch_ticker(symbol)
        if data:
            result[key] = data
            success_count += 1

    if success_count >= 2:
        result["available"] = True

        # VIX 恐慌等級判斷
        vix_val = result.get("vix", {}).get("price", 20)
        if vix_val < 15:
            result["vix_level"] = "極低恐慌（市場樂觀）"
        elif vix_val < 20:
            result["vix_level"] = "低恐慌（正常偏樂觀）"
        elif vix_val < 25:
            result["vix_level"] = "中等恐慌（觀望）"
        elif vix_val < 35:
            result["vix_level"] = "高恐慌（市場不安）"
        else:
            result["vix_level"] = "極高恐慌（恐慌拋售）"

        # SOX 走勢判斷（費半是台灣半導體的領先指標）
        sox_chg = result.get("sox", {}).get("change_pct", 0)
        if sox_chg > 1.5:
            result["sox_trend"] = "強勢上漲，台灣半導體族群看多"
        elif sox_chg > 0:
            result["sox_trend"] = "小幅上漲，半導體族群偏多"
        elif sox_chg > -1.5:
            result["sox_trend"] = "小幅下跌，半導體族群偏空"
        else:
            result["sox_trend"] = "大跌，台灣半導體族群壓力大"

        # 台幣走勢判斷（台幣升值 → 外資有意願匯入）
        twd_chg = result.get("usd_twd", {}).get("change_pct", 0)
        # 注意：TWD=X 是 USD/TWD，價格下跌代表台幣升值
        if twd_chg < -0.3:
            result["twd_trend"] = "台幣升值，外資匯入意願高"
        elif twd_chg > 0.3:
            result["twd_trend"] = "台幣貶值，外資匯出壓力"
        else:
            result["twd_trend"] = "台幣匯率穩定"

        result["updated"] = datetime.datetime.now().strftime("%H:%M")

    _CACHE = result
    _CACHE_TIME = datetime.datetime.now()
    return result


def format_macro_for_ai(macro: dict) -> str:
    """
    將總經數據格式化成 AI Prompt 文字區塊。
    """
    if not macro.get("available"):
        return ""

    lines = ["====== 🌐 總體經濟環境數據（即時）======"]

    vix = macro.get("vix", {})
    if vix:
        lines.append(f"- VIX 恐慌指數: {vix['price']:.2f}  {vix['change_pct']:+.2f}%  → {macro.get('vix_level', '')}")

    sox = macro.get("sox", {})
    if sox:
        lines.append(f"- 費城半導體指數(SOX): {sox['price']:,.2f}  {sox['change_pct']:+.2f}%  → {macro.get('sox_trend', '')}")

    twd = macro.get("usd_twd", {})
    if twd:
        lines.append(f"- 美元/台幣匯率: {twd['price']:.3f}  {twd['change_pct']:+.2f}%  → {macro.get('twd_trend', '')}")

    nq = macro.get("nasdaq", {})
    if nq:
        lines.append(f"- NASDAQ 指數: {nq['price']:,.2f}  {nq['change_pct']:+.2f}%")

    sp = macro.get("sp500", {})
    if sp:
        lines.append(f"- S&P 500 指數: {sp['price']:,.2f}  {sp['change_pct']:+.2f}%")

    dji = macro.get("dji", {})
    if dji:
        lines.append(f"- 道瓊工業指數(DJI): {dji['price']:,.2f}  {dji['change_pct']:+.2f}%")

    lines.append("")
    lines.append("請在分析中引用上述總體經濟數據：")
    lines.append("① VIX 決定整體市場風險偏好；② SOX 是台灣半導體股的重要領先指標；")
    lines.append("③ 台幣走勢影響外資匯入意願；④ 美股走勢影響台股隔日開盤方向。")
    lines.append("======================================")

    return "\n".join(lines)
