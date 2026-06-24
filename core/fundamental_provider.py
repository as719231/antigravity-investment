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
        ebitda_m   = info.get("ebitdaMargins")         # 0~1 小數
        rev_growth = info.get("revenueGrowth")         # 0~1 小數（年增率）
        earn_grow  = info.get("earningsGrowth")        # 0~1 小數
        debt_eq    = info.get("debtToEquity")          # 已是 % 形式
        div_yield  = info.get("dividendYield")         # 0~1 小數
        hi52       = info.get("fiftyTwoWeekHigh")
        lo52       = info.get("fiftyTwoWeekLow")
        cur_price  = info.get("currentPrice")
        mktcap     = info.get("marketCap")
        # 資產負債表
        curr_ratio = info.get("currentRatio")
        quick_rat  = info.get("quickRatio")
        total_debt = info.get("totalDebt")
        total_cash = info.get("totalCash")
        # 現金流
        fcf        = info.get("freeCashflow")
        ocf        = info.get("operatingCashflow")
        # 额外估値
        pb         = info.get("priceToBook")
        peg        = info.get("pegRatio")
        roa        = info.get("returnOnAssets")        # 0~1 小數

        if eps is not None or pe is not None or curr_ratio is not None:
            result["available"] = True

        result.update({
            "trailing_eps":      round(eps, 2)           if eps        is not None else None,
            "forward_eps":       round(fwd_eps, 2)       if fwd_eps    is not None else None,
            "trailing_pe":       round(pe, 2)            if pe         is not None else None,
            "forward_pe":        round(fwd_pe, 2)        if fwd_pe     is not None else None,
            "roe_pct":           round(roe * 100, 1)     if roe        is not None else None,
            "roa_pct":           round(roa * 100, 1)     if roa        is not None else None,
            "gross_margin_pct":  round(gross_m * 100, 1) if gross_m   is not None else None,
            "op_margin_pct":     round(op_m * 100, 1)   if op_m       is not None else None,
            "ebitda_margin_pct": round(ebitda_m * 100,1) if ebitda_m  is not None else None,
            "revenue_growth_pct":round(rev_growth*100,1) if rev_growth is not None else None,
            "earnings_growth_pct":round(earn_grow*100,1) if earn_grow  is not None else None,
            "debt_to_equity":    round(debt_eq, 1)       if debt_eq    is not None else None,
            "dividend_yield_pct":round(div_yield*100, 2) if div_yield  is not None else None,
            "week52_high":       hi52,
            "week52_low":        lo52,
            "current_price":     cur_price,
            # 資產負債表
            "current_ratio":     round(curr_ratio, 2)   if curr_ratio is not None else None,
            "quick_ratio":       round(quick_rat, 2)    if quick_rat  is not None else None,
            "total_debt_b":      round(total_debt/1e8,1) if total_debt is not None else None,  # 億元
            "total_cash_b":      round(total_cash/1e8,1) if total_cash is not None else None,
            "net_cash_b":        round((total_cash - total_debt)/1e8,1) if (total_cash and total_debt) else None,
            # 現金流
            "fcf_b":             round(fcf/1e8, 1)      if fcf        is not None else None,
            "ocf_b":             round(ocf/1e8, 1)      if ocf        is not None else None,
            # 额外估値
            "price_to_book":     round(pb, 2)            if pb         is not None else None,
            "peg_ratio":         round(peg, 2)           if peg        is not None else None,
        })

        # PE 相對估値判斷
        if pe is not None:
            if pe < 10:
                result["pe_status"] = f"低估（PE={pe:.1f}，低於一般合理區間）"
            elif pe < 20:
                result["pe_status"] = f"合理（PE={pe:.1f}，在合理估値區間）"
            elif pe < 30:
                result["pe_status"] = f"略高（PE={pe:.1f}，需要較高成長支撑）"
            elif pe < 50:
                result["pe_status"] = f"偏貴（PE={pe:.1f}，成長預期已充分反映）"
            else:
                result["pe_status"] = f"極度偏貴（PE={pe:.1f}，需極高成長率支撑）"

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
                result["position_52w_label"] = "接近年低點（低檔，存在價値機會）"

        # 財務健康綜合評分 (0~100)
        health_score = 50
        health_items = []
        if curr_ratio is not None:
            if curr_ratio >= 2:     health_score += 15; health_items.append("流動比优紀")
            elif curr_ratio >= 1.5: health_score += 8
            elif curr_ratio < 1:    health_score -= 15; health_items.append("流動性差")
        if fcf is not None:
            if fcf > 0:   health_score += 10; health_items.append("自由現金流正")
            else:         health_score -= 10; health_items.append("自由現金流負")
        if total_cash and total_debt:
            if total_cash > total_debt:  health_score += 10; health_items.append("現金多於負債")
            elif total_debt > total_cash*3: health_score -= 15; health_items.append("負債偏高")
        if roe is not None:
            if roe >= 0.20:  health_score += 10; health_items.append("ROE高")
            elif roe < 0.05: health_score -= 10
        if roa is not None:
            if roa >= 0.10:  health_score += 5
        health_score = max(0, min(100, health_score))
        if health_score >= 75:
            health_label = "🟢 財務健康"
        elif health_score >= 55:
            health_label = "🟡 財務穩定"
        elif health_score >= 40:
            health_label = "🟠 財務一般"
        else:
            health_label = "🔴 財務需注意"
        result["health_score"] = health_score
        result["health_label"] = health_label
        result["health_items"] = health_items

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

    pe   = fund.get("trailing_pe")
    fpe  = fund.get("forward_pe")
    eps  = fund.get("trailing_eps")
    feps = fund.get("forward_eps")
    roe  = fund.get("roe_pct")
    roa  = fund.get("roa_pct")
    gm   = fund.get("gross_margin_pct")
    om   = fund.get("op_margin_pct")
    em   = fund.get("ebitda_margin_pct")
    rg   = fund.get("revenue_growth_pct")
    eg   = fund.get("earnings_growth_pct")
    dy   = fund.get("dividend_yield_pct")
    de   = fund.get("debt_to_equity")
    hi   = fund.get("week52_high")
    lo   = fund.get("week52_low")
    pos  = fund.get("position_52w_pct")
    pb   = fund.get("price_to_book")
    peg  = fund.get("peg_ratio")
    cr   = fund.get("current_ratio")
    qr   = fund.get("quick_ratio")
    fcf  = fund.get("fcf_b")
    ocf  = fund.get("ocf_b")
    net_cash = fund.get("net_cash_b")

    _pb_ok   = '✅ 合理' if pb and pb < 3 else ('⚠️ 偏高' if pb and pb < 8 else '❌ 極高')
    _peg_ok  = '✅ 低估成長股' if peg and peg < 1 else ('⚠️ 合理' if peg and peg < 2 else '❌ 高估')
    _roe_ok  = '✅ 優秀' if roe and roe >= 15 else ('⚠️ 普通' if roe and roe >= 8 else '❌ 偏低')
    _roa_ok  = '✅ 優秀' if roa and roa >= 10 else '⚠️ 普通'
    _gm_ok   = '✅ 高護城河' if gm and gm >= 40 else ('➡️ 正常' if gm and gm >= 20 else '⚠️ 偏低')
    _rg_ok   = '✅ 成長加速' if rg and rg > 15 else ('➡️ 穩定成長' if rg and rg > 0 else '⚠️ 衰退')
    _dy_ok   = '✅ 高息股' if dy and dy >= 5 else ''
    _cr_ok   = '✅ 充裕' if cr and cr >= 2 else ('⚠️ 需注意' if cr and cr >= 1 else '❌ 偏低')
    _de_ok   = '✅ 財務穩健' if de and de < 50 else ('⚠️ 需注意' if de and de < 100 else '❌ 高負債')

    if eps  is not None: lines.append(f"- 每股盈餘(EPS): {eps} 元（追蹤）{f'| 預估EPS: {feps} 元' if feps else ''}")
    if pe   is not None: lines.append(f"- 本益比(PE): {pe} 倍  {fund.get('pe_status', '')}")
    if fpe  is not None: lines.append(f"- 預估本益比(Forward PE): {fpe} 倍")
    if pb   is not None: lines.append(f"- 股價淨值比(P/B): {pb}x  {_pb_ok}")
    if peg  is not None: lines.append(f"- PEG成長比率: {peg}  {_peg_ok}")
    if roe  is not None: lines.append(f"- ROE股東權益報酬: {roe}%  {_roe_ok}")
    if roa  is not None: lines.append(f"- ROA資產報酬率: {roa}%  {_roa_ok}")
    if gm   is not None: lines.append(f"- 毛利率: {gm}%  {_gm_ok}")
    if em   is not None: lines.append(f"- EBITDA利潤率: {em}%")
    if om   is not None: lines.append(f"- 營業利益率: {om}%")
    if rg   is not None: lines.append(f"- 營收年增率: {rg:+.1f}%  {_rg_ok}")
    if eg   is not None: lines.append(f"- 獲利年增率: {eg:+.1f}%")
    if dy   is not None: lines.append(f"- 股息殖利率: {dy}%  {_dy_ok}")
    if cr   is not None: lines.append(f"- 流動比率: {cr}x  {_cr_ok}")
    if qr   is not None: lines.append(f"- 速動比率: {qr}x")
    if fcf  is not None:
        fcf_label = '✅ 現金流充裕' if fcf > 0 else '❌ 現金流為負'
        lines.append(f"- 自由現金流(FCF): {fcf:+.1f}億元  {fcf_label}")
    if ocf  is not None: lines.append(f"- 營業現金流(OCF): {ocf:.1f}億元")
    if net_cash is not None:
        nc_label = '✅ 淨現金存影，財務健康' if net_cash > 0 else '⚠️ 負債大於現金'
        lines.append(f"- 淨現金(現金-負債): {net_cash:+.1f}億元  {nc_label}")
    if de   is not None: lines.append(f"- 負債股東權益比: {de}%  {_de_ok}")
    if hi and lo and pos is not None:
        lines.append(f"- 52週高低點: {lo} ~ {hi} 元  目前位置: {pos}%  → {fund.get('position_52w_label', '')}")
    # 財務健康評分
    hs = fund.get("health_score")
    hl = fund.get("health_label")
    if hs is not None:
        lines.append(f"- 財務健康綜合評分: {hs}/100  {hl}")

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
