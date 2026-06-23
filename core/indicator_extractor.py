# core/indicator_extractor.py
# =====================================================================
# 功能：從已計算的 DataFrame 中提取技術指標數值並格式化給 AI
# 職責：把已有的 RSI/KD/MACD/量/布林通道數值打包成 AI 可讀的文字
# =====================================================================

import pandas as pd
import numpy as np


def extract_technical_indicators(df: pd.DataFrame) -> dict:
    """
    從已計算指標的 DataFrame 提取最新技術指標數值。
    輸入：pattern_detector.py 或 risk_calculator.py 計算後的 DataFrame
    輸出：dict，包含所有指標的最新值與解讀標籤
    """
    if df is None or df.empty or len(df) < 5:
        return {"available": False}

    result = {"available": True}

    try:
        # ── 確保計算所有指標 ───────────────────────────────────────
        df = df.copy()

        # MA
        for win in [5, 20, 60]:
            col = f"ma{win}"
            if col not in df.columns:
                df[col] = df["close"].rolling(window=win).mean()

        # RSI (已在 risk_calculator 計算，若沒有重算)
        if "rsi" not in df.columns:
            delta = df["close"].diff()
            gain  = delta.clip(lower=0).ewm(alpha=1/14, adjust=False).mean()
            loss  = (-delta.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
            loss  = loss.replace(0, 1e-9)
            df["rsi"] = 100 - 100 / (1 + gain / loss)

        # KD (已在 risk_calculator 計算，若沒有重算)
        if "k" not in df.columns or "d" not in df.columns:
            lo9 = df["low"].rolling(9).min()
            hi9 = df["high"].rolling(9).max()
            denom = (hi9 - lo9).replace(0, 1e-9)
            rsv = (df["close"] - lo9) / denom * 100
            k_list, d_list, ck, cd = [], [], 50.0, 50.0
            for v in rsv:
                if pd.isna(v):
                    k_list.append(ck); d_list.append(cd)
                else:
                    ck = 2/3 * ck + 1/3 * v
                    cd = 2/3 * cd + 1/3 * ck
                    k_list.append(ck); d_list.append(cd)
            df["k"] = k_list
            df["d"] = d_list

        # MACD (12/26/9 EMA)
        if "macd" not in df.columns:
            ema12 = df["close"].ewm(span=12, adjust=False).mean()
            ema26 = df["close"].ewm(span=26, adjust=False).mean()
            df["macd"]        = ema12 - ema26
            df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
            df["macd_hist"]   = df["macd"] - df["macd_signal"]

        # 布林通道 (20, ±2σ)
        if "boll_upper" not in df.columns:
            mid = df["close"].rolling(20).mean()
            std = df["close"].rolling(20).std()
            df["boll_upper"] = mid + 2 * std
            df["boll_mid"]   = mid
            df["boll_lower"] = mid - 2 * std

        # 成交量均線
        if "vol_ma20" not in df.columns and "volume" in df.columns:
            df["vol_ma20"] = df["volume"].rolling(20).mean()

        # ── 取最新值 ──────────────────────────────────────────────
        last  = df.iloc[-1]
        prev  = df.iloc[-2] if len(df) >= 2 else last
        prev5 = df.iloc[-6] if len(df) >= 6 else df.iloc[0]

        close  = float(last["close"])
        rsi    = float(last.get("rsi", 50))
        k_val  = float(last.get("k", 50))
        d_val  = float(last.get("d", 50))
        ma5    = float(last.get("ma5", close))
        ma20   = float(last.get("ma20", close))
        ma60   = float(last.get("ma60", close))
        macd   = float(last.get("macd", 0))
        signal = float(last.get("macd_signal", 0))
        hist   = float(last.get("macd_hist", 0))
        prev_hist = float(prev.get("macd_hist", 0))
        boll_u = float(last.get("boll_upper", close * 1.05))
        boll_m = float(last.get("boll_mid", close))
        boll_l = float(last.get("boll_lower", close * 0.95))
        volume = int(last.get("volume", 0)) if "volume" in last.index else 0
        vol_ma = float(last.get("vol_ma20", volume)) if volume else 0

        # ── 指標解讀 ──────────────────────────────────────────────
        # RSI 解讀
        if rsi >= 80:
            rsi_label = "極度超買（高風險，短線拉回機率大）"
        elif rsi >= 70:
            rsi_label = "超買區（注意壓力）"
        elif rsi >= 50:
            rsi_label = "多方趨勢（健康偏多）"
        elif rsi >= 30:
            rsi_label = "弱勢區（偏空但非超賣）"
        else:
            rsi_label = "超賣區（短線反彈機率高）"

        # KD 解讀
        kd_cross = ""
        k_prev = float(prev.get("k", 50))
        d_prev = float(prev.get("d", 50))
        if k_val > d_val and k_prev <= d_prev:
            kd_cross = "✅ 剛發生黃金交叉（買進訊號）"
        elif k_val < d_val and k_prev >= d_prev:
            kd_cross = "❌ 剛發生死亡交叉（賣出訊號）"
        elif k_val > d_val:
            kd_cross = "黃金交叉狀態（持續看多）"
        else:
            kd_cross = "死亡交叉狀態（持續看空）"

        if k_val < 20:
            kd_level = "極低檔（超賣）"
        elif k_val < 40:
            kd_level = "低檔"
        elif k_val < 60:
            kd_level = "中段"
        elif k_val < 80:
            kd_level = "高檔"
        else:
            kd_level = "極高檔（超買）"

        # MACD 解讀
        if macd > signal:
            if hist > prev_hist:
                macd_label = "MACD 多頭排列且柱狀圖擴大（動能增強）"
            else:
                macd_label = "MACD 多頭排列但柱狀圖收縮（動能趨緩）"
        else:
            if hist < prev_hist:
                macd_label = "MACD 空頭排列且柱狀圖擴大（下跌動能增強）"
            else:
                macd_label = "MACD 空頭排列但柱狀圖收縮（下跌趨緩）"

        if macd > 0 and signal > 0:
            macd_label += "，整體在零軸上方（多方）"
        elif macd < 0 and signal < 0:
            macd_label += "，整體在零軸下方（空方）"

        # 布林通道位置
        boll_range = boll_u - boll_l
        if boll_range > 0:
            boll_pos = (close - boll_l) / boll_range * 100
        else:
            boll_pos = 50

        if boll_pos >= 90:
            boll_label = f"觸及上軌（極度超買，壓力 {boll_u:.2f} 元）"
        elif boll_pos >= 70:
            boll_label = f"上半部（偏多，壓力上軌 {boll_u:.2f} 元）"
        elif boll_pos >= 30:
            boll_label = f"中段（整理）"
        elif boll_pos >= 10:
            boll_label = f"下半部（偏空，支撐下軌 {boll_l:.2f} 元）"
        else:
            boll_label = f"觸及下軌（超賣，支撐 {boll_l:.2f} 元）"

        # 成交量解讀
        vol_label = ""
        if vol_ma > 0 and volume > 0:
            vol_ratio = volume / vol_ma
            if vol_ratio >= 2.0:
                vol_label = f"爆量（{vol_ratio:.1f}x 均量），籌碼換手積極"
            elif vol_ratio >= 1.5:
                vol_label = f"放量（{vol_ratio:.1f}x 均量）"
            elif vol_ratio >= 0.8:
                vol_label = f"正常量（{vol_ratio:.1f}x 均量）"
            else:
                vol_label = f"縮量（{vol_ratio:.1f}x 均量），觀望情緒重"

        # 均線排列
        if close > ma5 > ma20 > ma60:
            ma_trend = "多頭完美排列（短中長線全部看多）"
        elif close > ma20 > ma60:
            ma_trend = "多頭排列（股價站上月線季線）"
        elif close < ma5 < ma20 < ma60:
            ma_trend = "空頭完美排列（短中長線全部看空）"
        elif close < ma20 < ma60:
            ma_trend = "空頭排列（股價跌破月線季線）"
        elif close > ma20:
            ma_trend = "偏多（股價站上月線）"
        else:
            ma_trend = "偏空（股價跌破月線）"

        result.update({
            "close":      close,
            "rsi":        round(rsi, 1),
            "rsi_label":  rsi_label,
            "k_val":      round(k_val, 1),
            "d_val":      round(d_val, 1),
            "kd_cross":   kd_cross,
            "kd_level":   kd_level,
            "macd":       round(macd, 3),
            "macd_signal": round(signal, 3),
            "macd_hist":  round(hist, 3),
            "macd_label": macd_label,
            "boll_upper": round(boll_u, 2),
            "boll_mid":   round(boll_m, 2),
            "boll_lower": round(boll_l, 2),
            "boll_label": boll_label,
            "volume":     volume,
            "vol_ma20":   int(vol_ma),
            "vol_label":  vol_label,
            "ma5":        round(ma5, 2),
            "ma20":       round(ma20, 2),
            "ma60":       round(ma60, 2),
            "ma_trend":   ma_trend,
        })

    except Exception as e:
        print(f"[indicator_extractor] 提取失敗: {e}")
        result["available"] = False

    return result


def format_indicators_for_ai(ind: dict, stock_id: str = "") -> str:
    """格式化技術指標數值為 AI Prompt 文字"""
    if not ind.get("available"):
        return ""

    sid_label = f"（{stock_id}）" if stock_id else ""
    lines = [f"====== 📈 技術指標精確數值 {sid_label}（AI 請務必引用）======"]

    lines.append(f"- RSI(14): {ind['rsi']}  → {ind['rsi_label']}")
    lines.append(f"- KD 指標: K={ind['k_val']}  D={ind['d_val']}  位置:{ind['kd_level']}  → {ind['kd_cross']}")
    lines.append(f"- MACD: DIF={ind['macd']}  DEA={ind['macd_signal']}  柱={ind['macd_hist']}  → {ind['macd_label']}")
    lines.append(f"- 布林通道: 上軌={ind['boll_upper']}  中軌={ind['boll_mid']}  下軌={ind['boll_lower']}  → {ind['boll_label']}")
    if ind.get("vol_label"):
        lines.append(f"- 成交量: {ind['volume']:,} 張  均量(20日)={ind['vol_ma20']:,} 張  → {ind['vol_label']}")
    lines.append(f"- 均線: MA5={ind['ma5']}  MA20={ind['ma20']}  MA60={ind['ma60']}  → {ind['ma_trend']}")
    lines.append("")
    lines.append("⚠️ 重要：回答時請明確引用以上數值（如「RSI目前為XX，處於XX區」），")
    lines.append("不要籠統說『RSI偏高』，而是說『RSI=72.3，進入超買區』。")
    lines.append("====================================================")
    return "\n".join(lines)
