import pandas as pd
import numpy as np
import datetime
from FinMind.data import DataLoader
from core.risk_calculator import calculate_indicators


def _get_dataloader() -> DataLoader:
    """取得已登入 Token 的 DataLoader"""
    dl = DataLoader()
    try:
        import config
        token = getattr(config, 'FINMIND_TOKEN', '')
        if token:
            dl.login_by_token(api_token=token)
    except Exception:
        pass
    return dl

def fetch_stock_data(stock_id: str, days: int = 120) -> pd.DataFrame:
    """
    抓取指定台股代號的歷史K線資料
    """
    dl = _get_dataloader()
    end_date = datetime.date.today().strftime('%Y-%m-%d')
    start_date = (datetime.date.today() - datetime.timedelta(days=days)).strftime('%Y-%m-%d')
    
    try:
        df = dl.taiwan_stock_daily(stock_id=stock_id, start_date=start_date, end_date=end_date)
        if not df.empty:
            df = df.rename(columns={'max': 'high', 'min': 'low'})
        return df
    except Exception as e:
        print(f"抓取 {stock_id} 數據失敗: {str(e)}")
        return pd.DataFrame()

def fetch_institutional_investors(stock_id: str, days: int = 30) -> dict:
    """
    抓取三大法人（投信、外資、自營商）近期买賣超​超​資料
    回傳 dict 包含: foreign_net, investment_trust_net, dealer_net, 各日明細
    """
    dl = DataLoader()
    end_date = datetime.date.today().strftime('%Y-%m-%d')
    start_date = (datetime.date.today() - datetime.timedelta(days=days)).strftime('%Y-%m-%d')
    
    result = {
        "available": False,
        "foreign_net": 0,       # 外資近N日净买賣超
        "investment_trust_net": 0,  # 投信近N日净买賣超
        "dealer_net": 0,        # 自營商近N日净买賣超
        "total_net": 0,         # 三大法人合計净买超
        "consecutive_buy": 0,   # 外資連續買超日數
        "consecutive_sell": 0,  # 外資連續賣超日數
        "recent_days": []
    }
    
    try:
        df = dl.taiwan_stock_institutional_investors(
            stock_id=stock_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if df.empty:
            return result
        
        # FinMind API 的 name 欄位為英文：
        # Foreign_Investor, Foreign_Dealer_Self → 外資
        # Investment_Trust → 投信
        # Dealer_self, Dealer_Hedging → 自營商
        df_foreign = df[df['name'].isin(['Foreign_Investor', 'Foreign_Dealer_Self'])].copy()
        df_trust   = df[df['name'] == 'Investment_Trust'].copy()
        df_dealer  = df[df['name'].isin(['Dealer_self', 'Dealer_Hedging'])].copy()
        
        def safe_net(df_sub):
            if df_sub.empty:
                return 0
            if 'buy' in df_sub.columns and 'sell' in df_sub.columns:
                return int((df_sub['buy'] - df_sub['sell']).sum())
            return 0
        
        foreign_net = safe_net(df_foreign)
        trust_net   = safe_net(df_trust)
        dealer_net  = safe_net(df_dealer)
        total_net   = foreign_net + trust_net + dealer_net
        
        # 計算外資連續買超或賣超日數（以 Foreign_Investor 為主）
        consecutive_buy = 0
        consecutive_sell = 0
        df_fi = df[df['name'] == 'Foreign_Investor'].copy()
        if not df_fi.empty:
            df_fi_sorted = df_fi.sort_values('date', ascending=False).copy()
            df_fi_sorted['net'] = df_fi_sorted['buy'] - df_fi_sorted['sell']
            for _, row in df_fi_sorted.iterrows():
                if row['net'] > 0:
                    if consecutive_sell > 0:
                        break
                    consecutive_buy += 1
                elif row['net'] < 0:
                    if consecutive_buy > 0:
                        break
                    consecutive_sell += 1
                else:
                    break
        
        # 建立最近天數明細（合計外資、投信、自營）
        all_dates = sorted(df['date'].unique(), reverse=True)[:10]
        recent = []
        for d in all_dates:
            day_df = df[df['date'] == d]
            day_f = day_df[day_df['name'].isin(['Foreign_Investor', 'Foreign_Dealer_Self'])]
            day_t = day_df[day_df['name'] == 'Investment_Trust']
            day_d = day_df[day_df['name'].isin(['Dealer_self', 'Dealer_Hedging'])]
            recent.append({
                "date": str(d),
                "foreign": int((day_f['buy'] - day_f['sell']).sum()) if not day_f.empty else 0,
                "trust":   int((day_t['buy'] - day_t['sell']).sum()) if not day_t.empty else 0,
                "dealer":  int((day_d['buy'] - day_d['sell']).sum()) if not day_d.empty else 0,
            })
        result.update({
            "available": True,
            "foreign_net": foreign_net,
            "investment_trust_net": trust_net,
            "dealer_net": dealer_net,
            "total_net": total_net,
            "consecutive_buy": consecutive_buy,
            "consecutive_sell": consecutive_sell,
            "recent_days": recent
        })
        return result
        
    except Exception as e:
        print(f"抓取三大法人資料失敗: {str(e)}")
        return result

# ============================================================
# 三大法人五大規則分析引擎
# ============================================================

def _inst_day_label(wan: float) -> tuple:
    """一、單日買賣超分級（單位：萬元）→ (label, type, grade)"""
    if wan > 10000:
        return "極強買超", "bullish", 4
    elif wan > 5000:
        return "強勢買超", "bullish", 3
    elif wan > 1000:
        return "中度買超", "bullish", 2
    elif wan > 0:
        return "弱勢買超", "bullish", 1
    elif wan < -10000:
        return "極強賣超", "bearish", -4
    elif wan < -5000:
        return "強勢賣超", "bearish", -3
    elif wan < -1000:
        return "中度賣超", "bearish", -2
    elif wan < 0:
        return "弱勢賣超", "bearish", -1
    else:
        return "法人持平", "neutral", 0

def _inst_consec_label(buy: int, sell: int) -> tuple:
    """二、連續性判定→ (label, type)"""
    if buy > 0:
        if buy >= 10: return f"法人高度認同（連買{buy}日）", "bullish"
        if buy >= 6:  return f"主升段觀察期（連買{buy}日）", "bullish"
        if buy >= 4:  return f"明顯偏多（連買{buy}日）", "bullish"
        if buy >= 2:  return f"短線偏多（連買{buy}日）", "bullish"
        return f"初步轉強（連買{buy}日）", "bullish"
    elif sell > 0:
        if sell >= 10: return f"法人大幅撤退（連賣{sell}日）", "bearish"
        if sell >= 6:  return f"主跌段觀察期（連賣{sell}日）", "bearish"
        if sell >= 4:  return f"明顯偏空（連賣{sell}日）", "bearish"
        if sell >= 2:  return f"短線偏空（連賣{sell}日）", "bearish"
        return f"初步轉弱（連賣{sell}日）", "bearish"
    return "法人中性", "neutral"

def analyze_institutional_signals(institutional: dict, metrics: dict, df: pd.DataFrame) -> dict:
    """
    三大法人五大規則分析：
      1. 單日買賣超分級  2. 連續性判定  3. 法人結構判定
      4. 進場評分         5. 警訊規則
    """
    if not institutional.get("available"):
        return {"available": False}

    close    = metrics.get("close", 0.0)
    ma20     = metrics.get("ma20", 0.0)
    recent   = institutional.get("recent_days", [])
    consec_buy  = institutional.get("consecutive_buy", 0)
    consec_sell = institutional.get("consecutive_sell", 0)

    # ----- 最新一日資料 -----
    if recent:
        d0 = recent[0]
        d0_foreign  = d0["foreign"]
        d0_trust    = d0["trust"]
        d0_dealer   = d0["dealer"]
        d0_total    = d0_foreign + d0_trust + d0_dealer
    else:
        d0_foreign = d0_trust = d0_dealer = d0_total = 0

    def to_wan(shares):
        return (shares * close) / 10000.0 if close > 0 else 0.0

    d0_total_wan   = to_wan(d0_total)
    d0_foreign_wan = to_wan(d0_foreign)
    d0_trust_wan   = to_wan(d0_trust)
    d0_dealer_wan  = to_wan(d0_dealer)

    # ===== 一、單日分級 =====
    day_label, day_type, day_grade = _inst_day_label(d0_total_wan)

    # ===== 二、連續性 (外資) =====
    consec_label, consec_type = _inst_consec_label(consec_buy, consec_sell)

    # 投信連續買賣超日數
    trust_buy = trust_sell = 0
    for r in recent:
        if r["trust"] > 0:
            if trust_sell > 0: break
            trust_buy += 1
        elif r["trust"] < 0:
            if trust_buy > 0: break
            trust_sell += 1
        else:
            break
    trust_consec_label, trust_consec_type = _inst_consec_label(trust_buy, trust_sell)

    # ===== 三、法人結構判定 =====
    if d0_foreign > 0 and d0_trust > 0:
        struct_level = 1
        struct_label = "第一級：外資 + 投信 同步買超"
        struct_type  = "bullish"
    elif consec_buy >= 2:
        struct_level = 2
        struct_label = "第二級：外資連續買超"
        struct_type  = "bullish"
    elif trust_buy >= 2:
        struct_level = 3
        struct_label = "第三級：投信連續買超"
        struct_type  = "bullish"
    elif d0_dealer > 0 and d0_foreign <= 0 and d0_trust <= 0:
        struct_level = 4
        struct_label = "第四級：僅自營商買超"
        struct_type  = "neutral"
    else:
        struct_level = 0
        struct_label = "法人結構偏空或持平"
        struct_type  = "bearish" if consec_sell > 0 else "neutral"

    # ===== 四、進場評分 =====
    score = 0
    score_details = []

    if consec_buy >= 5:
        score += 30
        score_details.append(("外資連續買超≥5日", 30))
    elif consec_buy >= 3:
        score += 20
        score_details.append(("外資連續買超≥3日", 20))

    if trust_buy >= 3:
        score += 15
        score_details.append(("投信連續買超≥3日", 15))

    if d0_total_wan >= 10000:
        score += 20
        score_details.append(("三大法人單日買超≥1億", 20))
    elif d0_total_wan >= 5000:
        score += 10
        score_details.append(("三大法人單日買超≥5000萬", 10))

    if close > 0 and ma20 > 0 and close > ma20:
        score += 20
        score_details.append(("股價站上20日均線", 20))

    if not df.empty and "volume" in df.columns and len(df) >= 6:
        latest_vol  = float(df["volume"].iloc[-1])
        avg_vol5    = float(df["volume"].iloc[-6:-1].mean())
        if avg_vol5 > 0 and latest_vol > avg_vol5:
            score += 15
            score_details.append(("成交量>乙5日均量", 15))

    if   score >= 80: score_label, score_type = "強烈看多", "bullish"
    elif score >= 60: score_label, score_type = "偏多",     "bullish"
    elif score >= 40: score_label, score_type = "中性",     "neutral"
    elif score >= 20: score_label, score_type = "偏空",     "bearish"
    else:             score_label, score_type = "強烈偏空", "bearish"

    # ===== 五、警訊規則 =====
    warnings = []

    # 警訊一：股價上漲但法人連續賣超 3 天
    if consec_sell >= 3 and not df.empty and len(df) >= 4:
        ref_price = float(df["close"].iloc[-4])
        if close > ref_price:
            warnings.append("⚠️ 股價上漲但法人連續賣超 3 天 → 主力出貨警訊")

    # 警訊二：股價下跌但法人連續買超 3 天
    if consec_buy >= 3 and not df.empty and len(df) >= 4:
        ref_price = float(df["close"].iloc[-4])
        if close < ref_price:
            warnings.append("📊 股價下跌但法人連續買超 3 天 → 法人逢低布局")

    # 警訊三：外資連續賣超 5 天以上
    if consec_sell >= 5:
        warnings.append("🔴 外資連續賣超 5 天以上 → 建議降低持股評級一級")

    # 警訊四：投信連續買超 10 天以上
    if trust_buy >= 10:
        warnings.append("📈 投信連續買超 10 天以上 → 列入波段觀察名單")

    return {
        "available": True,
        "day_label":   day_label,
        "day_type":    day_type,
        "day_grade":   day_grade,
        "d0_total_wan":   round(d0_total_wan, 0),
        "d0_foreign_wan": round(d0_foreign_wan, 0),
        "d0_trust_wan":   round(d0_trust_wan, 0),
        "d0_dealer_wan":  round(to_wan(d0_dealer), 0),
        "consec_label":  consec_label,
        "consec_type":   consec_type,
        "consec_buy":    consec_buy,
        "consec_sell":   consec_sell,
        "trust_buy":     trust_buy,
        "trust_sell":    trust_sell,
        "trust_consec_label": trust_consec_label,
        "struct_level":  struct_level,
        "struct_label":  struct_label,
        "struct_type":   struct_type,
        "score":         score,
        "score_label":   score_label,
        "score_type":    score_type,
        "score_details": score_details,
        "warnings":      warnings,
    }
def calculate_price_targets(df: pd.DataFrame, metrics: dict) -> dict:
    """
    依據均線支撐/壓力與近期高低點，計算參考買進與賣出價位
    """
    close = metrics.get('close', 0.0)
    latest = df.iloc[-1]
    ma5 = float(df['ma5'].iloc[-1]) if 'ma5' in df and not pd.isna(df['ma5'].iloc[-1]) else close
    ma20 = float(df['ma20'].iloc[-1]) if 'ma20' in df and not pd.isna(df['ma20'].iloc[-1]) else close
    ma60 = float(df['ma60'].iloc[-1]) if 'ma60' in df and not pd.isna(df['ma60'].iloc[-1]) else close
    
    # 近 20 天高低點
    recent_20 = df.tail(20)
    high_20 = float(recent_20['high'].max())
    low_20 = float(recent_20['low'].min())
    
    # 近 5 天高低點
    recent_5 = df.tail(5)
    high_5 = float(recent_5['high'].max())
    low_5 = float(recent_5['low'].min())
    
    # 主要支擐位：取 MA5, MA20, MA60 和近期低點中最靠近現價的下方安全區
    support_levels = sorted([x for x in [ma5, ma20, ma60, low_5, low_20] if x < close], reverse=True)
    resistance_levels = sorted([x for x in [ma5, ma20, ma60, high_5, high_20] if x > close])
    
    # 主要壓力位
    primary_support = support_levels[0] if support_levels else low_20
    secondary_support = support_levels[1] if len(support_levels) > 1 else low_20
    primary_resistance = resistance_levels[0] if resistance_levels else high_20
    secondary_resistance = resistance_levels[1] if len(resistance_levels) > 1 else high_20
    
    # 買進參考價位：主要支擐位上方 0~0.5%，避免追高主要壓力低於第二支擐
    buy_ideal = round(primary_support * 1.002, 2)  # 第一批买進參考（貼近支擐紐上方）
    buy_dip = round(secondary_support * 0.998, 2)  # 確認破支擐就追輸第二批
    
    # 止損位：突破主要支擐就出
    stop_loss = round(primary_support * 0.97, 2)   # 主要支擐倒帰 3% 為止損線
    
    # 賣出目標價位
    take_profit_1 = round(primary_resistance * 0.998, 2)    # 第一目標（接近主要壓力）
    take_profit_2 = round(secondary_resistance * 0.995, 2)  # 第二目標（確認突破後）
    
    return {
        "close": close,
        "buy_ideal": buy_ideal,
        "buy_dip": buy_dip,
        "stop_loss": stop_loss,
        "take_profit_1": take_profit_1,
        "take_profit_2": take_profit_2,
        "primary_support": round(primary_support, 2),
        "secondary_support": round(secondary_support, 2),
        "primary_resistance": round(primary_resistance, 2),
        "secondary_resistance": round(secondary_resistance, 2),
        "high_20": round(high_20, 2),
        "low_20": round(low_20, 2),
        "ma5": round(ma5, 2),
        "ma20": round(ma20, 2),
        "ma60": round(ma60, 2),
    }

def detect_crossovers(df: pd.DataFrame) -> list:
    """
    偵測最新一天的均線交叉狀態 (例如 MA5 與 MA20)
    """
    signals = []
    if len(df) < 21:
        return signals

    # 取得最新兩天
    today = df.iloc[-1]
    yesterday = df.iloc[-2]

    # MA5 vs MA20
    if yesterday['ma5'] <= yesterday['ma20'] and today['ma5'] > today['ma20']:
        signals.append({
            "name": "均線黃金交叉 (5MA / 20MA)",
            "type": "bullish",
            "strength": "80%",
            "desc": "5MA（短期均線）向上突破 20MA（月線），多頭轉強訊號。"
        })
    elif yesterday['ma5'] >= yesterday['ma20'] and today['ma5'] < today['ma20']:
        signals.append({
            "name": "均線死亡交叉 (5MA / 20MA)",
            "type": "bearish",
            "strength": "80%",
            "desc": "5MA（短期均線）向下跌破 20MA（月線），空頭轉強訊號。"
        })

    # MA20 vs MA60 (月線與季線)
    if 'ma60' in today and not pd.isna(today['ma20']) and not pd.isna(today['ma60']):
        if yesterday['ma20'] <= yesterday['ma60'] and today['ma20'] > today['ma60']:
            signals.append({
                "name": "中長期黃金交叉 (20MA / 60MA)",
                "type": "bullish",
                "strength": "100%",
                "desc": "20MA（月線）向上突破 60MA（季線），中長期多頭趨勢確立。"
            })
        elif yesterday['ma20'] >= yesterday['ma60'] and today['ma20'] < today['ma60']:
            signals.append({
                "name": "中長期死亡交叉 (20MA / 60MA)",
                "type": "bearish",
                "strength": "100%",
                "desc": "20MA（月線）向下跌破 60MA（季線），中長期趨勢轉空。"
            })

    return signals

def detect_kline_patterns(df: pd.DataFrame) -> list:
    """
    利用規則引擎辨識最新日K的特定K線型態
    """
    patterns = []
    if len(df) < 5:
        return patterns

    # 取出最新三天的數據
    # df 依 date 排序，-1 為最新一天，-2 為前一天，-3 為大前天
    day1 = df.iloc[-3]
    day2 = df.iloc[-2]
    day3 = df.iloc[-1]  # 最新一天

    # 輔助計算函數 (最新一天 day3)
    c3, o3, h3, l3 = float(day3['close']), float(day3['open']), float(day3['high']), float(day3['low'])
    body3 = abs(c3 - o3)
    range3 = max(h3 - l3, 1e-9)
    upper_shadow3 = h3 - max(o3, c3)
    lower_shadow3 = min(o3, c3) - l3
    is_red3 = c3 > o3  # 上漲 (陽線)
    is_green3 = c3 < o3 # 下跌 (陰線)

    # 前一天 day2
    c2, o2, h2, l2 = float(day2['close']), float(day2['open']), float(day2['high']), float(day2['low'])
    body2 = abs(c2 - o2)
    range2 = max(h2 - l2, 1e-9)
    is_red2 = c2 > o2
    is_green2 = c2 < o2

    # 大前天 day1
    c1, o1, h1, l1 = float(day1['close']), float(day1['open']), float(day1['high']), float(day1['low'])
    body1 = abs(c1 - o1)
    range1 = max(h1 - l1, 1e-9)
    is_green1 = c1 < o1
    is_red1 = c1 > o1

    # 判斷近期的波段趨勢 (以20MA斜率簡單代表)
    trend_rising = df['ma20'].iloc[-1] > df['ma20'].iloc[-5] if 'ma20' in df and not pd.isna(df['ma20'].iloc[-5]) else True

    # ---------------- 1. 單根 K 線 ----------------
    # 十字星
    if body3 / range3 < 0.1:
        patterns.append({
            "name": "十字星",
            "type": "neutral",
            "strength": "50%",
            "desc": "開盤價幾乎等於收盤價，多空雙方勢均力敵。出現在高低檔常預示趨勢即將變天。"
        })
    
    # 錘子線 (下跌段出現) & 上吊線 (上漲段出現)
    elif (lower_shadow3 / body3 > 2.0) and (upper_shadow3 / range3 < 0.15) and (body3 / range3 > 0.15):
        if not trend_rising:
            patterns.append({
                "name": "錘子線 (Hammer)",
                "type": "bullish",
                "strength": "65%",
                "desc": "長下影小實體，出現在下跌趨勢中。代表下方承接力道極強，可能止跌反彈。"
            })
        else:
            patterns.append({
                "name": "上吊線 (Hanging Man)",
                "type": "bearish",
                "strength": "65%",
                "desc": "長下影小實體，出現在上漲趨勢高檔。警告買盤追高力道枯竭，主力高位出貨。"
            })

    # 倒錘子線 (下跌段出現) & 射擊之星 (上漲段出現)
    elif (upper_shadow3 / body3 > 2.0) and (lower_shadow3 / range3 < 0.15) and (body3 / range3 > 0.15):
        if not trend_rising:
            patterns.append({
                "name": "倒錘子線 (Inverted Hammer)",
                "type": "bullish",
                "strength": "65%",
                "desc": "長上影小實體，出現在下跌趨勢中。顯示買方已展開試探性進攻，可能反轉看漲。"
            })
        else:
            patterns.append({
                "name": "射擊之星 (Shooting Star)",
                "type": "bearish",
                "strength": "80%",
                "desc": "長上影小實體，出現在上漲高位。顯示衝高受阻並遭空頭強力摜壓，為見頂訊號。"
            })

    # 墓碑十字星
    elif (body3 / range3 < 0.1) and (upper_shadow3 / range3 > 0.7) and (lower_shadow3 / range3 < 0.1) and trend_rising:
        patterns.append({
            "name": "墓碑十字星 (Gravestone Doji)",
            "type": "bearish",
            "strength": "100%",
            "desc": "長上影無下影且收在最低。上漲高檔出現，為極度強烈的看跌見頂訊號。"
        })

    # ---------------- 2. 雙根 K 線 ----------------
    # 看漲吞沒
    if is_green2 and is_red3 and (o3 <= c2) and (c3 >= o2) and (body3 > body2):
        patterns.append({
            "name": "看漲吞沒 (Bullish Engulfing)",
            "type": "bullish",
            "strength": "80%",
            "desc": "前一日為綠K，今日為大紅K且實體完全包覆前一日，為多頭強勢反攻、趨勢看漲訊號。"
        })
    # 看跌吞沒
    elif is_red2 and is_green3 and (o3 >= c2) and (c3 <= o2) and (body3 > body2):
        patterns.append({
            "name": "看跌吞沒 (Bearish Engulfing)",
            "type": "bearish",
            "strength": "80%",
            "desc": "前一日為紅K，今日為大綠K且實體完全包覆前一日，為空頭大舉摜壓、趨勢看跌訊號。"
        })
    
    # 穿刺線
    elif is_green2 and is_red3 and (o3 < l2) and (c3 > (o2 + c2)/2) and (c3 < o2):
        patterns.append({
            "name": "穿刺線 (Piercing Pattern)",
            "type": "bullish",
            "strength": "65%",
            "desc": "紅K開盤價跌破前一日低點，但收盤價收復前一日陰線實體的一半以上，多頭反彈力道顯著。"
        })
    # 烏雲蓋頂
    elif is_red2 and is_green3 and (o3 > h2) and (c3 < (o2 + c2)/2) and (c3 > o2):
        patterns.append({
            "name": "烏雲蓋頂 (Dark Cloud Cover)",
            "type": "bearish",
            "strength": "65%",
            "desc": "綠K開盤價開在高點上方，但收盤價跌破前一日紅K實體的一半以下，顯示漲勢受阻將回檔。"
        })

    # 鑷子底
    if abs(l3 - l2) / l3 < 0.0015:
        patterns.append({
            "name": "鑷子底 (Tweezer Bottom)",
            "type": "bullish",
            "strength": "65%",
            "desc": "連續兩日最低點幾乎相同，顯示該價格支撐力道極強，不易跌破，屬看漲訊號。"
        })
    # 鑷子頂
    elif abs(h3 - h2) / h3 < 0.0015:
        patterns.append({
            "name": "鑷子頂 (Tweezer Top)",
            "type": "bearish",
            "strength": "65%",
            "desc": "連續兩日最高點幾乎相同，顯示上方壓力沉重，難以突破，屬看跌訊號。"
        })

    # ---------------- 3. 三根 K 線 ----------------
    # 晨星
    if is_green1 and (body1/range1 > 0.4) and (body2/range2 < 0.35) and (max(o2, c2) < c1) and is_red3 and (c3 > (o1+c1)/2):
        patterns.append({
            "name": "晨星 (Morning Star)",
            "type": "bullish",
            "strength": "100%",
            "desc": "下跌末端出現長陰K -> 跳空小K線 -> 長陽K線且收在首日陰線中點以上。預示黎明將至，極強看漲訊號。"
        })
    # 黃昏星
    elif is_red1 and (body1/range1 > 0.4) and (body2/range2 < 0.35) and (min(o2, c2) > c1) and is_green3 and (c3 < (o1+c1)/2):
        patterns.append({
            "name": "黃昏星 (Evening Star)",
            "type": "bearish",
            "strength": "100%",
            "desc": "上漲高檔出現長陽K -> 跳空小K線 -> 長陰K線且收在首日陽線中點以下。預示黃昏降臨，極強看跌訊號。"
        })

    # 三白兵 (三根連漲紅K)
    if is_red3 and is_red2 and is_red1 and (c3 > c2 > c1) and (o3 > o2 > o1):
        # 且收盤都接近當天高點
        if (h3 - c3)/range3 < 0.15 and (h2 - c2)/range2 < 0.15:
            patterns.append({
                "name": "三白兵 (Three White Soldiers)",
                "type": "bullish",
                "strength": "80%",
                "desc": "連續出現三根實體飽滿且持續墊高的紅K線，表示多頭主力強勢發動，後續看漲。"
            })
    # 三烏鴉 (三根連跌綠K)
    elif is_green3 and is_green2 and is_green1 and (c3 < c2 < c1) and (o3 < o2 < o1):
        if (c3 - l3)/range3 < 0.15 and (c2 - l2)/range2 < 0.15:
            patterns.append({
                "name": "三烏鴉 (Three Black Crows)",
                "type": "bearish",
                "strength": "80%",
                "desc": "連續出現三根實體飽滿且持續下探的綠K線，表示空頭掌控局勢，後續看跌。"
            })

    return patterns

def get_action_recommendation(df: pd.DataFrame, metrics: dict, signals: list) -> dict:
    """
    依據量化指標與 K 線型態，產生具體的交易操盤建議。
    使用「淨訊號邏輯」：多頭數量 - 空頭數量，讓強勢多頭訊號能夠觸發買入建議。
    """
    risk_score = metrics.get('risk_score', 50.0)
    close_price = metrics.get('close', 0.0)
    ma20 = df['ma20'].iloc[-1] if 'ma20' in df and not pd.isna(df['ma20'].iloc[-1]) else close_price
    
    # 統計訊號類型
    bullish_signals = [s for s in signals if s['type'] == 'bullish']
    bearish_signals = [s for s in signals if s['type'] == 'bearish']
    
    # 計算淨訊號情緒（多頭數量 - 空頭數量）
    net_signals = len(bullish_signals) - len(bearish_signals)
    
    action = "watch"
    reason_zh = "目前技術面趨於穩定，多空訊號尚無明顯壓倒性，建議續抱觀望，等待更明確的進出場訊號。"
    reason_en = "Technical indicators are relatively stable with no dominant signals. Recommend holding and watching for a clearer entry or exit signal."
    reason_ja = "テクニカル指標は比較的安定しており、明確なシグナルはまだ出ていません。保有継続で様子見を推奨します。"
    reason_th = "ตัวชี้วัดทางเทคนิคค่อนข้างเสถียร ยังไม่มีสัญญาณที่ชัดเจน แนะนำให้ถือไว้และรอสัญญาณที่ชัดขึ้น"
    reason_vi = "Các chỉ số kỹ thuật tương đối ổn định, chưa có tín hiệu rõ ràng. Đề xuất giữ nguyên và theo dõi thêm."

    # 1. 直接清倉 (風險極高，或中高風險時空頭訊號明確壓制多頭)
    if risk_score >= 85.0 or (risk_score >= 70.0 and net_signals < 0) or (close_price < ma20 and net_signals < 0):
        action = "liquidate"
        if risk_score >= 85.0:
            reason_zh = "當前大腦風險評分過高，處於極度超買或波動劇烈區間，為保護本金安全，建議執行清倉避險。若預期大盤或板塊持續走弱，可考慮現股買進「反向 ETF（例如台灣50反1 00632R，或美股 SH）」以在下跌中安全獲利，無融資融券破產風險。"
            reason_en = "Current risk score is extremely high. To protect capital, spot liquidation is recommended. If you expect a downtrend, consider buying inverse ETFs (e.g. 00632R for Taiwan market or SH for US market) with 100% cash to safely profit from the drop without margin or leverage."
            reason_ja = "現在のリスクスコアが極めて高い状態です。資本を保護するため、現物売却による避難を推奨します。下落が続くと予想される場合は、レバレッジを使わず現物資金でインバースETF（00632Rや米国株SHなど）の購入を検討し、安全に下落局面で利益を狙ってください。"
            reason_th = "คะแนนความเสี่ยงสูงเกินไป เพื่อความปลอดภัยของเงินต้น แนะนำให้ขายล้างพอร์ตป้องกันความเสี่ยง หากคาดว่าตลาดจะปรับตัวลงต่อเนื่อง สามารถพิจารณาซื้อ Inverse ETF (เช่น 00632R หรือ SH) ด้วยเงินสด 100%"
            reason_vi = "Điểm rủi ro hiện tại quá cao. Để bảo vệ vốn, đề xuất bán hết tiền mặt phòng vệ. Nếu dự kiến thị trường giảm tiếp, hãy cân nhắc mua Inverse ETF bằng tiền mặt 100%."
        else:
            reason_zh = "股價已跌破月線支撐，且淨技術訊號偏向空方。短期趨勢轉弱，建議清倉現股避險；亦可使用現金買入「反向 ETF」作為替代避險方式。"
            reason_en = "Price has broken below the 20MA with net bearish signals. Short-term trend weakening. Recommend liquidating or hedging via cash-only inverse ETFs."
            reason_ja = "株価が20MAを下回り、弱気シグナルが優勢です。現物売却か、現金でのインバースETF購入によるヘッジを推奨します。"
            reason_th = "ราคาหลุด 20MA และสัญญาณเชิงลบมีน้ำหนักมากกว่า แนะนำให้ขายหรือป้องกันความเสี่ยงผ่าน Inverse ETF ด้วยเงินสด"
            reason_vi = "Giá thủng 20MA và tín hiệu thiên về giảm. Đề xuất bán phòng vệ hoặc mua Inverse ETF bằng tiền mặt."

    # 2. 分倉出貨 (中高風險且多空均衡，或空頭訊號稍佔優)
    elif (70.0 <= risk_score < 85.0 and net_signals <= 0) or (net_signals < 0 and risk_score >= 55.0):
        action = "sell_partial"
        reason_zh = "股價處於相對高檔區，或空頭技術訊號稍佔優勢。建議分批落袋為安，逐步縮小倉位以防止利潤回吐。"
        reason_en = "Price is in a relatively high zone or bearish signals slightly dominate. Recommend scaling out in batches to lock in profits."
        reason_ja = "株価が高値圏にあるか、弱気シグナルが若干優勢です。一部利益確定を行い、リスクを段階的に縮小することを推奨します。"
        reason_th = "ราคาอยู่ในโซนค่อนข้างสูง หรือสัญญาณเชิงลบมีน้ำหนักพอสมควร แนะนำให้ทยอยขายทำกำไรบางส่วน"
        reason_vi = "Giá đang ở vùng tương đối cao hoặc tín hiệu giảm nhỉnh hơn. Đề xuất chốt lời từng phần để bảo vệ thành quả."

    # 3. 分批補倉買進 (安全區或多頭訊號明確佔優且風險 < 70)
    elif (risk_score <= 35.0) or (net_signals > 0 and risk_score < 70.0):
        if close_price >= ma20 or risk_score <= 35.0 or net_signals >= 2:
            action = "buy"
            reason_zh = "指標處於安全區間，或多頭技術訊號明確佔優（如黃金交叉、看漲吞沒等），且股價獲均線支撐，為良好的分批加碼時機。"
            reason_en = "Indicators are in the safe zone or bullish signals are clearly dominant (Golden Cross, Bullish Engulfing, etc.) with MA support. Good opportunity to accumulate in batches."
            reason_ja = "指標が安全圏にあるか、強気シグナル（ゴールデンクロスや陽線包み足など）が明確に優勢で均線に支えられています。分割買いの好機です。"
            reason_th = "ตัวชี้วัดอยู่ในโซนปลอดภัย หรือสัญญาณเชิงบวกมีน้ำหนักมากกว่า (เช่น Golden Cross, Bullish Engulfing) พร้อมแนวรับจากเส้นค่าเฉลี่ย เป็นจังหวะดีในการทยอยซื้อสะสม"
            reason_vi = "Các chỉ số nằm trong vùng an toàn hoặc tín hiệu kỹ thuật tăng chiếm ưu thế (như Giao cắt vàng, Nhấn chìm tăng) và có hỗ trợ từ đường MA. Thời điểm tốt để gom thêm từng phần."
        else:
            action = "watch"
            reason_zh = "多頭訊號已出現，但股價仍未站回均線支撐區，建議暫時觀望，等待回測均線確立後再行分批加碼。"
            reason_en = "Bullish signals detected but price has not yet reclaimed MA support. Wait for a pullback to the moving average before accumulating."
            reason_ja = "強気シグナルが出ていますが、均線のサポートがまだ確認できません。押し目買いのタイミングを待ちましょう。"
            reason_th = "มีสัญญาณขาขึ้นแต่ราคายังไม่ยืนเหนือแนวรับค่าเฉลี่ย ควรรอยืนยันก่อนทยอยซื้อ"
            reason_vi = "Có tín hiệu tăng nhưng giá chưa lấy lại vùng hỗ trợ MA. Chờ xác nhận trước khi gom thêm."

    return {
        "action": action,
        "reason": {
            "繁體中文": reason_zh,
            "English": reason_en,
            "日本語": reason_ja,
            "ไทย": reason_th,
            "Tiếng Việt": reason_vi
        }
    }

def evaluate_stock_signals(stock_id: str) -> dict:
    """
    整合函數：抓取數據、計算指標，並偵測所有訊號與風險
    """
    df = fetch_stock_data(stock_id)
    if df.empty:
        return {"error": "查無此股票代號資料或網路錯誤。"}

    # 1. 計算基本技術指標 (ma5, ma20, ma60, rsi, kd, volatility)
    df['ma5'] = df['close'].rolling(window=5).mean()
    df_ind = calculate_indicators(df)
    
    # 2. 評估風險與殖利率
    from core.risk_calculator import evaluate_risk_and_yield
    metrics = evaluate_risk_and_yield(df_ind)
    
    # 3. 偵測均線交叉訊號
    crossovers = detect_crossovers(df_ind)
    
    # 4. 偵測 K 線圖形形態
    kline_patterns = detect_kline_patterns(df_ind)
    
    # 合併所有訊號
    all_signals = crossovers + kline_patterns
    
    # 5. 評估交易操盤建議
    recommendation = get_action_recommendation(df_ind, metrics, all_signals)
    
    # 6. 計算買進/賣出參考價位
    price_targets = calculate_price_targets(df_ind, metrics)
    
    # 7. 抓取三大法人資料
    institutional = fetch_institutional_investors(stock_id)
    
    # 8. 三大法人五大規則分析
    inst_analysis = analyze_institutional_signals(institutional, metrics, df_ind)
    
    # 9. 股票類型自動判定（額外資訊層，不影響以上任何分析邏輯）
    stock_type: dict = {}
    try:
        from core.stock_classifier import classify_stock
        stock_type = classify_stock(stock_id)
    except Exception as e:
        print(f"股票分類失敗（不影響主要分析）: {e}")
    
    return {
        "df":             df_ind,
        "metrics":        metrics,
        "signals":        all_signals,
        "recommendation": recommendation,
        "price_targets":  price_targets,
        "institutional":  institutional,
        "inst_analysis":  inst_analysis,
        "stock_type":     stock_type,   # 新增：類型分析（額外層，不影響原有邏輯）
    }
