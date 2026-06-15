# core/us_data_provider.py
# =====================================================================
# 美股資料提供者（積木：只負責資料，不做 UI）
# - 歷史 OHLCV + 技術指標（yfinance）
# - 機構持股比 + 做空比例（Option A）
# - 大盤指數背景（S&P500 / 道瓊 / NASDAQ / 費半）（Option C）
# =====================================================================

import pandas as pd
import numpy as np
import datetime

try:
    import yfinance as yf
    _YFINANCE_OK = True
except ImportError:
    _YFINANCE_OK = False


# ── 大盤指數符號對照 ─────────────────────────────────────────────────
MARKET_INDICES = {
    "SP500": {"symbol": "^GSPC", "name_zh": "S&P 500",        "name_en": "S&P 500",         "flag": "🇺🇸"},
    "DJI":   {"symbol": "^DJI",  "name_zh": "道瓊指數",         "name_en": "Dow Jones",        "flag": "🏛️"},
    "IXIC":  {"symbol": "^IXIC", "name_zh": "那斯達克",         "name_en": "NASDAQ",           "flag": "💻"},
    "SOX":   {"symbol": "SOXX",  "name_zh": "費城半導體 (SOXX)", "name_en": "PHLX Semiconductor","flag": "🔬"},
}


# ──────────────────────────────────────────────────────────────────────
#  指標計算（共用 risk_calculator 相同算法，格式與台股對齊）
# ──────────────────────────────────────────────────────────────────────

def _calc_ma(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["ma5"]  = df["close"].rolling(5).mean()
    df["ma20"] = df["close"].rolling(20).mean()
    df["ma60"] = df["close"].rolling(60).mean()
    return df


def _calc_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    delta = df["close"].diff()
    gain  = delta.clip(lower=0)
    loss  = -delta.clip(upper=0)
    avg_g = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_l = loss.ewm(alpha=1/period, adjust=False).mean()
    avg_l = avg_l.replace(0, 1e-9)
    df["rsi"] = 100 - (100 / (1 + avg_g / avg_l))
    return df


def _calc_kd(df: pd.DataFrame, period: int = 9) -> pd.DataFrame:
    df["low_9"]  = df["low"].rolling(period).min()
    df["high_9"] = df["high"].rolling(period).max()
    denom        = (df["high_9"] - df["low_9"]).replace(0, 1e-9)
    df["rsv"]    = (df["close"] - df["low_9"]) / denom * 100
    k_list, d_list = [], []
    ck, cd = 50.0, 50.0
    for rsv in df["rsv"]:
        if pd.isna(rsv):
            k_list.append(50.0); d_list.append(50.0)
        else:
            ck = (2/3)*ck + (1/3)*rsv
            cd = (2/3)*cd + (1/3)*ck
            k_list.append(ck); d_list.append(cd)
    df["k"] = k_list
    df["d"] = d_list
    return df


def _calc_volatility(df: pd.DataFrame) -> pd.DataFrame:
    df["returns"]    = df["close"].pct_change()
    df["volatility"] = df["returns"].rolling(20).std() * np.sqrt(252)
    return df


def _calc_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = _calc_ma(df)
    df = _calc_rsi(df)
    df = _calc_kd(df)
    df = _calc_volatility(df)
    return df


def _calc_price_targets(df: pd.DataFrame, close: float) -> dict:
    """計算買賣參考價位（與台股 pattern_detector 同邏輯）"""
    ma5  = float(df["ma5"].iloc[-1])  if not pd.isna(df["ma5"].iloc[-1])  else close
    ma20 = float(df["ma20"].iloc[-1]) if not pd.isna(df["ma20"].iloc[-1]) else close
    ma60 = float(df["ma60"].iloc[-1]) if not pd.isna(df["ma60"].iloc[-1]) else close

    recent_20 = df.tail(20)
    high_20   = float(recent_20["high"].max())
    low_20    = float(recent_20["low"].min())
    recent_5  = df.tail(5)
    high_5    = float(recent_5["high"].max())
    low_5     = float(recent_5["low"].min())

    support_levels    = sorted([x for x in [ma5, ma20, ma60, low_5, low_20]  if x < close], reverse=True)
    resistance_levels = sorted([x for x in [ma5, ma20, ma60, high_5, high_20] if x > close])

    primary_support     = support_levels[0]    if support_levels    else low_20
    secondary_support   = support_levels[1]    if len(support_levels) > 1  else low_20
    primary_resistance  = resistance_levels[0] if resistance_levels else high_20
    secondary_resistance= resistance_levels[1] if len(resistance_levels) > 1 else high_20

    return {
        "buy_ideal":          round(primary_support * 1.002, 2),
        "buy_dip":            round(secondary_support * 0.998, 2),
        "stop_loss":          round(primary_support * 0.97, 2),
        "take_profit_1":      round(primary_resistance * 0.998, 2),
        "take_profit_2":      round(secondary_resistance * 0.998, 2),
        "primary_support":    round(primary_support, 2),
        "primary_resistance": round(primary_resistance, 2),
    }


def _detect_patterns(df: pd.DataFrame) -> list:
    """簡化版 K 線形態偵測（用於美股）"""
    signals = []
    if len(df) < 5:
        return signals

    # 均線交叉
    if len(df) >= 21:
        ma5_now  = df["ma5"].iloc[-1]
        ma5_prev = df["ma5"].iloc[-2]
        ma20_now  = df["ma20"].iloc[-1]
        ma20_prev = df["ma20"].iloc[-2]
        if pd.notna(ma5_now) and pd.notna(ma20_now):
            if ma5_now > ma20_now and ma5_prev <= ma20_prev:
                signals.append({"name": "均線黃金交叉 (5MA / 20MA)", "type": "bullish"})
            elif ma5_now < ma20_now and ma5_prev >= ma20_prev:
                signals.append({"name": "均線死亡交叉 (5MA / 20MA)", "type": "bearish"})

    if len(df) >= 61:
        ma20_now  = df["ma20"].iloc[-1]
        ma20_prev = df["ma20"].iloc[-2]
        ma60_now  = df["ma60"].iloc[-1]
        ma60_prev = df["ma60"].iloc[-2]
        if pd.notna(ma60_now):
            if ma20_now > ma60_now and ma20_prev <= ma60_prev:
                signals.append({"name": "中長期黃金交叉 (20MA / 60MA)", "type": "bullish"})
            elif ma20_now < ma60_now and ma20_prev >= ma60_prev:
                signals.append({"name": "中長期死亡交叉 (20MA / 60MA)", "type": "bearish"})

    # 單根形態（最後一根 K 棒）
    r = df.iloc[-1]
    o, h, l, c = float(r["open"]), float(r["high"]), float(r["low"]), float(r["close"])
    body = abs(c - o)
    upper_shadow = h - max(c, o)
    lower_shadow = min(c, o) - l
    full_range   = h - l if h != l else 1e-9

    if body / full_range < 0.1 and lower_shadow / full_range > 0.6:
        signals.append({"name": "錘子線 (Hammer)", "type": "bullish"})
    elif body / full_range < 0.1 and upper_shadow / full_range > 0.6:
        signals.append({"name": "射擊之星 (Shooting Star)", "type": "bearish"})
    elif body / full_range < 0.1:
        signals.append({"name": "十字星", "type": "neutral"})

    # 吞沒形態
    if len(df) >= 2:
        r_prev = df.iloc[-2]
        o_p, c_p = float(r_prev["open"]), float(r_prev["close"])
        if c_p < o_p and c > o and c > o_p and o < c_p:
            signals.append({"name": "看漲吞沒 (Bullish Engulfing)", "type": "bullish"})
        elif c_p > o_p and c < o and c < o_p and o > c_p:
            signals.append({"name": "看跌吞沒 (Bearish Engulfing)", "type": "bearish"})

    return signals


def _calc_risk(close: float, ma20: float, rsi: float, k: float, d: float, vol: float) -> dict:
    """風險分數評估（與台股 risk_calculator 同邏輯）"""
    score = 50.0
    if rsi > 80:   score += (rsi - 70) * 1.2
    elif rsi > 70: score += (rsi - 70) * 0.8
    elif rsi < 30: score -= (30 - rsi) * 0.8
    price_to_ma = (close - ma20) / ma20 * 100 if ma20 else 0
    if price_to_ma > 0:
        score += 4.0 + (price_to_ma - 8.0) * 1.5 if price_to_ma > 8 else price_to_ma * 0.5
    else:
        score += max(price_to_ma * 0.3, -5.0)
    if k > d: score -= 5.0
    else:      score += 5.0
    if vol > 0.55:   score += 12.0
    elif vol > 0.35: score += 5.0
    elif vol <= 0.15: score -= 5.0
    score = max(0.0, min(100.0, score))
    risk_level = "🟢 低風險" if score < 35 else "🟡 中風險" if score < 65 else "🔴 高風險"
    return {"risk_score": round(score, 1), "risk_level": risk_level}


# ──────────────────────────────────────────────────────────────────────
#  主要公開 API
# ──────────────────────────────────────────────────────────────────────

def fetch_us_stock_analysis(ticker: str, days: int = 120) -> dict:
    """
    抓取美股歷史 K 線並計算全套技術指標，格式與台股 analysis dict 對齊。

    Returns dict with keys:
      df, metrics, signals, price_targets, institutional, error(可選)
    """
    if not _YFINANCE_OK:
        return {"error": "yfinance 未安裝，請執行 pip install yfinance"}

    try:
        end   = datetime.date.today()
        start = end - datetime.timedelta(days=int(days * 1.8))  # 多抓一些確保 60MA 夠資料

        t = yf.Ticker(ticker.upper())
        raw = t.history(start=str(start), end=str(end), auto_adjust=True)

        if raw is None or raw.empty:
            return {"error": f"無法取得 {ticker} 的歷史資料，請確認代號是否正確。"}

        # ── 格式化成標準 DataFrame ────────────────────────────────
        df = raw[["Open", "High", "Low", "Close", "Volume"]].copy()
        df.columns = ["open", "high", "low", "close", "volume"]
        df.index = pd.to_datetime(df.index).tz_localize(None)
        df = df.reset_index().rename(columns={"index": "date", "Date": "date"})
        df["date"] = pd.to_datetime(df["date"]).dt.date
        df = df.dropna(subset=["close"]).sort_values("date").reset_index(drop=True)

        # 保留最近 N 個交易日
        df = df.tail(days).reset_index(drop=True)

        if len(df) < 20:
            return {"error": f"{ticker} 資料不足（僅有 {len(df)} 天），無法進行技術分析。"}

        # ── 計算所有指標 ─────────────────────────────────────────
        df = _calc_all_indicators(df)
        latest = df.iloc[-1]

        close    = float(latest["close"])
        rsi      = float(latest["rsi"])   if not pd.isna(latest["rsi"])   else 50.0
        k_val    = float(latest["k"])     if not pd.isna(latest["k"])     else 50.0
        d_val    = float(latest["d"])     if not pd.isna(latest["d"])     else 50.0
        vol      = float(latest["volatility"]) if not pd.isna(latest["volatility"]) else 0.2
        ma5      = float(latest["ma5"])   if not pd.isna(latest["ma5"])   else close
        ma20     = float(latest["ma20"])  if not pd.isna(latest["ma20"])  else close

        risk = _calc_risk(close, ma20, rsi, k_val, d_val, vol)

        # ── 殖利率（來自 yfinance info）────────────────────────────
        est_yield = 0.0
        try:
            info = t.info
            # trailingAnnualDividendYield is reliable (actual decimal, e.g. 0.0036 = 0.36%)
            dy = info.get("trailingAnnualDividendYield") or 0
            est_yield = round(float(dy) * 100, 2)
        except Exception:
            pass

        metrics = {
            "close":      round(close, 2),
            "rsi":        round(rsi, 2),
            "k":          round(k_val, 2),
            "d":          round(d_val, 2),
            "volatility": round(vol, 4),
            "risk_score": risk["risk_score"],
            "risk_level": risk["risk_level"],
            "est_yield":  est_yield,
            "ma5":  round(ma5, 2),
            "ma20": round(ma20, 2),
        }

        # ── 形態偵測 ─────────────────────────────────────────────
        signals = _detect_patterns(df)

        # ── 買賣參考價位 ─────────────────────────────────────────
        price_targets = _calc_price_targets(df, close)

        # ── AI 操盤建議（簡版，不需聯網）────────────────────────
        recommendation = _quick_recommendation(rsi, k_val, d_val, risk["risk_score"], signals)

        return {
            "df":             df,
            "metrics":        metrics,
            "signals":        signals,
            "price_targets":  price_targets,
            "recommendation": recommendation,
            "ticker":         ticker.upper(),
        }

    except Exception as e:
        return {"error": f"分析 {ticker} 時發生錯誤：{str(e)}"}


def _quick_recommendation(rsi: float, k: float, d: float, risk_score: float, signals: list) -> dict:
    """根據技術指標給出快速操作建議"""
    bullish_signals = sum(1 for s in signals if s["type"] == "bullish")
    bearish_signals = sum(1 for s in signals if s["type"] == "bearish")

    if risk_score >= 70 or (rsi > 75 and k > 80):
        action = "sell_partial"
        reason_zh = f"RSI={rsi:.0f} 超買區，風險分={risk_score:.0f}，建議考慮減倉或停利。"
        reason_en = f"RSI={rsi:.0f} overbought, risk score={risk_score:.0f}. Consider partial profit-taking."
    elif risk_score <= 30 or (rsi < 30 and bullish_signals >= 1):
        action = "buy"
        reason_zh = f"RSI={rsi:.0f} 超賣區，出現 {bullish_signals} 個看漲形態，可考慮分批建倉。"
        reason_en = f"RSI={rsi:.0f} oversold with {bullish_signals} bullish pattern(s). Consider staged entry."
    elif bearish_signals >= 2 or risk_score >= 60:
        action = "watch"
        reason_zh = f"出現 {bearish_signals} 個看跌形態，風險分={risk_score:.0f}，建議觀望。"
        reason_en = f"{bearish_signals} bearish pattern(s), risk score={risk_score:.0f}. Watch and wait."
    else:
        action = "watch"
        reason_zh = f"技術面中性，RSI={rsi:.0f}，風險分={risk_score:.0f}，可持倉觀察。"
        reason_en = f"Neutral technicals, RSI={rsi:.0f}, risk={risk_score:.0f}. Hold and monitor."

    return {
        "action": action,
        "reason": {
            "繁體中文": reason_zh,
            "English":  reason_en,
            "日本語":   reason_zh,
            "ไทย":      reason_zh,
            "Tiếng Việt": reason_zh,
        }
    }


def fetch_institutional_data(ticker: str) -> dict:
    """
    抓取美股機構持股比 + 做空比例（Option A）
    來源：yfinance info
    """
    if not _YFINANCE_OK:
        return {"available": False}
    try:
        info = yf.Ticker(ticker.upper()).info
        inst_pct   = info.get("institutionalOwnershipPercent") or info.get("heldPercentInstitutions") or 0
        insider_pct= info.get("heldPercentInsiders") or 0
        short_pct  = info.get("shortPercentOfFloat") or 0
        short_ratio= info.get("shortRatio") or 0   # 空頭回補天數

        return {
            "available":       True,
            "inst_pct":        round(float(inst_pct) * 100, 1),    # 機構持股比 %
            "insider_pct":     round(float(insider_pct) * 100, 1), # 內部人持股比 %
            "retail_pct":      round(max(0, 100 - float(inst_pct)*100 - float(insider_pct)*100), 1),
            "short_pct":       round(float(short_pct) * 100, 1),   # 做空比 %
            "short_ratio":     round(float(short_ratio), 1),        # 空頭回補天數
        }
    except Exception:
        return {"available": False}


def fetch_market_indices() -> dict:
    """
    抓取四大指數即時報價（Option C）：
    S&P500 / 道瓊 / NASDAQ / 費城半導體 SOXX
    """
    if not _YFINANCE_OK:
        return {}

    results = {}
    for key, info in MARKET_INDICES.items():
        try:
            t = yf.Ticker(info["symbol"])
            hist = t.history(period="2d", auto_adjust=True)
            if hist is None or hist.empty or len(hist) < 1:
                results[key] = {"success": False, **info}
                continue
            close_today = float(hist["Close"].iloc[-1])
            close_prev  = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else close_today
            change      = close_today - close_prev
            change_pct  = (change / close_prev) * 100 if close_prev else 0
            results[key] = {
                "success":      True,
                "price":        round(close_today, 2),
                "change":       round(change, 2),
                "change_pct":   round(change_pct, 2),
                "name_zh":      info["name_zh"],
                "name_en":      info["name_en"],
                "flag":         info["flag"],
            }
        except Exception as e:
            results[key] = {"success": False, "error": str(e), **info}
    return results
