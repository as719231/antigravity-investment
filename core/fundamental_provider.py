# core/fundamental_provider.py
# =====================================================================
# 功能：基本面數據提供模組
# 資料來源：yfinance（EPS/ROE/毛利率/本益比）+ TWSE 月營收 API
# =====================================================================

import yfinance as yf
import requests
import datetime
import re
import warnings
warnings.filterwarnings("ignore")

_CACHE: dict = {}
_CACHE_DATE: str = ""
_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def _today() -> str:
    return datetime.date.today().strftime("%Y-%m-%d")


def fetch_fundamentals(stock_id: str) -> dict:
    """
    取得個股基本面數據。

    Returns dict:
      trailing_eps, forward_eps, trailing_pe, forward_pe,
      roe, gross_margin, operating_margin, revenue_growth,
      earnings_growth, debt_ratio, dividend_yield,
      week52_high, week52_low, market_cap,
      pe_status (相對估值判斷)
    """
    global _CACHE, _CACHE_DATE

    cache_key = stock_id
    if _CACHE_DATE == _today() and cache_key in _CACHE:
        return _CACHE[cache_key]

    result = {"available": False, "stock_id": stock_id}

    # yfinance: 加 .TW 後綴查台股
    ticker_str = stock_id + ".TW"
    try:
        t    = yf.Ticker(ticker_str)
        info = t.info or {}

        eps        = info.get("trailingEps")
        fwd_eps    = info.get("forwardEps")
        pe         = info.get("trailingPE")
        fwd_pe     = info.get("forwardPE")
        roe        = info.get("returnOnEquity")        # 0~1 小數
        gross_m    = info.get("grossMargins")          # 0~1 小數
        op_m       = info.get("operatingMargins")      # 0~1 小數
        rev_growth = info.get("revenueGrowth")         # 0~1 小數（年增率）
        earn_grow  = info.get("earningsGrowth")        # 0~1 小數
        debt_eq    = info.get("debtToEquity")          # 已是 % 形式
        div_yield  = info.get("dividendYield")         # 0~1 小數
        hi52       = info.get("fiftyTwoWeekHigh")
        lo52       = info.get("fiftyTwoWeekLow")
        cur_price  = info.get("currentPrice")
        mktcap     = info.get("marketCap")

        if eps is not None or pe is not None:
            result["available"] = True

        result.update({
            "trailing_eps":     round(eps, 2)          if eps        is not None else None,
            "forward_eps":      round(fwd_eps, 2)      if fwd_eps    is not None else None,
            "trailing_pe":      round(pe, 2)           if pe         is not None else None,
            "forward_pe":       round(fwd_pe, 2)       if fwd_pe     is not None else None,
            "roe_pct":          round(roe * 100, 1)    if roe        is not None else None,
            "gross_margin_pct": round(gross_m * 100, 1) if gross_m  is not None else None,
            "op_margin_pct":    round(op_m * 100, 1)  if op_m       is not None else None,
            "revenue_growth_pct": round(rev_growth * 100, 1) if rev_growth is not None else None,
            "earnings_growth_pct": round(earn_grow * 100, 1) if earn_grow is not None else None,
            "debt_to_equity":   round(debt_eq, 1)      if debt_eq    is not None else None,
            "dividend_yield_pct": round(div_yield * 100, 2) if div_yield is not None else None,
            "week52_high":      hi52,
            "week52_low":       lo52,
            "current_price":    cur_price,
        })

        # PE 相對估值判斷
        if pe is not None:
            if pe < 10:
                result["pe_status"] = f"低估（PE={pe:.1f}，低於一般合理區間）"
            elif pe < 20:
                result["pe_status"] = f"合理（PE={pe:.1f}，在合理估值區間）"
            elif pe < 30:
                result["pe_status"] = f"略高（PE={pe:.1f}，需要較高成長支撐）"
            elif pe < 50:
                result["pe_status"] = f"偏貴（PE={pe:.1f}，成長預期已充分反映）"
            else:
                result["pe_status"] = f"極度偏貴（PE={pe:.1f}，需極高成長率支撐）"

        # 52週位置判斷
        if hi52 and lo52 and cur_price:
            pct_in_range = (cur_price - lo52) / (hi52 - lo52) * 100
            result["position_52w_pct"] = round(pct_in_range, 1)
            if pct_in_range > 80:
                result["position_52w_label"] = "接近年高點（強勢，但需注意壓力）"
            elif pct_in_range > 50:
                result["position_52w_label"] = "年區間中上段（偏強）"
            elif pct_in_range > 20:
                result["position_52w_label"] = "年區間中下段（偏弱）"
            else:
                result["position_52w_label"] = "接近年低點（低檔，存在價值機會）"

    except Exception as e:
        print(f"[fundamental] {stock_id} yfinance 失敗: {e}")

    # 快取當日
    _CACHE[cache_key] = result
    _CACHE_DATE = _today()
    return result


def fetch_monthly_revenue(stock_id: str) -> dict:
    """
    取得個股最近 3 個月的月營收資料。
    資料來源：TWSE MOPS 或 FinMind API
    返回 dict: months (list), revenues (list), yoy_pct (年增率)
    """
    result = {"available": False, "months": [], "revenues": [], "yoy_avg_pct": None}

    try:
        from FinMind.data import DataLoader
        dl = DataLoader()
        end_date   = _today()
        start_date = (datetime.date.today() - datetime.timedelta(days=150)).strftime("%Y-%m-%d")

        df = dl.taiwan_stock_month_revenue(
            stock_id=stock_id,
            start_date=start_date,
            end_date=end_date,
        )

        if df is None or df.empty:
            return result

        df = df.sort_values("date").tail(6)

        months   = df["date"].astype(str).tolist()
        revenues = df["revenue"].tolist()

        # 年增率（比較今年同期 vs 去年）
        yoy_pcts = []
        if "revenue_year" in df.columns and "revenue_month" in df.columns:
            yoy_col = df.get("revenue_year") if "revenue_year" in df.columns else None

        # 簡易計算最近月份 YoY（用 revenueyoy if exists）
        if "revenue_year" in df.columns:
            for _, row in df.iterrows():
                try:
                    yoy_pcts.append(float(row.get("revenue_year", 0)))
                except Exception:
                    pass

        result.update({
            "available": True,
            "months":    months[-3:],
            "revenues":  [int(r) for r in revenues[-3:]],
            "yoy_avg_pct": round(sum(yoy_pcts[-3:]) / len(yoy_pcts[-3:]), 1) if yoy_pcts else None,
        })

    except Exception as e:
        print(f"[fundamental] {stock_id} 月營收失敗: {e}")

    return result


def format_fundamental_for_ai(fund: dict, rev: dict = None, stock_id: str = "") -> str:
    """格式化基本面數據為 AI Prompt 文字"""
    if not fund.get("available"):
        return ""

    sid_label = f"（{stock_id}）" if stock_id else ""
    lines = [f"====== 📊 基本面數據 {sid_label}======"]

    pe = fund.get("trailing_pe")
    fpe = fund.get("forward_pe")
    eps = fund.get("trailing_eps")
    feps = fund.get("forward_eps")
    roe = fund.get("roe_pct")
    gm  = fund.get("gross_margin_pct")
    om  = fund.get("op_margin_pct")
    rg  = fund.get("revenue_growth_pct")
    eg  = fund.get("earnings_growth_pct")
    dy  = fund.get("dividend_yield_pct")
    de  = fund.get("debt_to_equity")
    hi  = fund.get("week52_high")
    lo  = fund.get("week52_low")
    pos = fund.get("position_52w_pct")

    if eps  is not None: lines.append(f"- 每股盈餘(EPS): {eps} 元（追蹤）{f'| 預估EPS: {feps} 元' if feps else ''}")
    if pe   is not None: lines.append(f"- 本益比(PE): {pe} 倍  {fund.get('pe_status', '')}")
    if fpe  is not None: lines.append(f"- 預估本益比(Forward PE): {fpe} 倍")
    if roe  is not None: lines.append(f"- 股東權益報酬率(ROE): {roe}%  {'✅ 優秀' if roe >= 15 else ('⚠️ 普通' if roe >= 8 else '❌ 偏低')}")
    if gm   is not None: lines.append(f"- 毛利率: {gm}%  {'✅ 高護城河' if gm >= 40 else ('➡️ 正常' if gm >= 20 else '⚠️ 偏低')}")
    if om   is not None: lines.append(f"- 營業利益率: {om}%")
    if rg   is not None: lines.append(f"- 營收年增率: {rg:+.1f}%  {'✅ 成長加速' if rg > 15 else ('➡️ 穩定成長' if rg > 0 else '⚠️ 衰退')}")
    if eg   is not None: lines.append(f"- 獲利年增率: {eg:+.1f}%")
    if dy   is not None: lines.append(f"- 股息殖利率: {dy}%  {'✅ 高息股' if dy >= 5 else ''}")
    if de   is not None: lines.append(f"- 負債股東權益比: {de}%  {'✅ 財務穩健' if de < 50 else ('⚠️ 需注意' if de < 100 else '❌ 高負債')}")
    if hi and lo and pos is not None:
        lines.append(f"- 52週高低點: {lo} ~ {hi} 元  目前位置: {pos}%  → {fund.get('position_52w_label', '')}")

    # 月營收
    if rev and rev.get("available"):
        months   = rev.get("months", [])
        revenues = rev.get("revenues", [])
        yoy      = rev.get("yoy_avg_pct")
        if months and revenues:
            rev_pairs = "、".join(f"{m}:{r:,}" for m, r in zip(months[-3:], revenues[-3:]))
            lines.append(f"- 近期月營收(千元): {rev_pairs}")
        if yoy is not None:
            lines.append(f"- 月營收平均年增率: {yoy:+.1f}%")

    lines.append("")
    lines.append("請在分析中自然引用以上基本面數據，與技術面結合給出完整評估：")
    lines.append("① 本益比判斷估值貴貴/合理；② ROE/毛利率判斷公司競爭力；")
    lines.append("③ 營收成長趨勢判斷基本面動能；④ 殖利率判斷存股吸引力。")
    lines.append("=======================================")
    return "\n".join(lines)
