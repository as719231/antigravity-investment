import pandas as pd
import numpy as np

def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    計算技術指標：MA20, MA60, RSI, KD, Volatility
    """
    df = df.copy()
    if len(df) < 20:
        return df

    # 1. 移動平均線 (MA)
    df['ma20'] = df['close'].rolling(window=20).mean()
    df['ma60'] = df['close'].rolling(window=60).mean()

    # 2. RSI (14天，Wilder Smoothing 網格法)
    delta = df['close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    
    avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()
    
    # 避免除以 0
    avg_loss = avg_loss.replace(0, 1e-9)
    rs = avg_gain / avg_loss
    df['rsi'] = 100 - (100 / (1 + rs))

    # 3. KD指標 (9天)
    df['low_9'] = df['low'].rolling(window=9).min()
    df['high_9'] = df['high'].rolling(window=9).max()
    
    # 計算 RSV
    denom = df['high_9'] - df['low_9']
    denom = denom.replace(0, 1e-9)
    df['rsv'] = (df['close'] - df['low_9']) / denom * 100
    
    k_list = []
    d_list = []
    current_k = 50.0
    current_d = 50.0
    for rsv in df['rsv']:
        if pd.isna(rsv):
            k_list.append(50.0)
            d_list.append(50.0)
        else:
            current_k = (2/3) * current_k + (1/3) * rsv
            current_d = (2/3) * current_d + (1/3) * current_k
            k_list.append(current_k)
            d_list.append(current_d)
            
    df['k'] = k_list
    df['d'] = d_list

    # 4. 歷史波動度 (20天日報酬率標準差 * 252開盤日的年化波動度)
    df['returns'] = df['close'].pct_change()
    df['volatility'] = df['returns'].rolling(window=20).std() * np.sqrt(252)

    return df

def evaluate_risk_and_yield(df: pd.DataFrame) -> dict:
    """
    評估目前最新的風險等級與預期配息收益率
    返回：
      - risk_score: 0~100 的數值
      - risk_level: '🟢 低風險', '🟡 中風險', '🔴 高風險'
      - est_yield: 預估年化股息率 (%)
      - rsi: 目前 RSI 數值
      - k: 目前 K 值
      - d: 目前 D 值
      - close: 最新收盤價
    """
    if df.empty:
        return {"error": "無歷史數據"}
        
    df_ind = calculate_indicators(df)
    latest = df_ind.iloc[-1]
    
    # 讀取當前數據
    close_price = float(latest['close'])
    rsi = float(latest['rsi']) if not pd.isna(latest['rsi']) else 50.0
    k_val = float(latest['k']) if not pd.isna(latest['k']) else 50.0
    d_val = float(latest['d']) if not pd.isna(latest['d']) else 50.0
    vol = float(latest['volatility']) if not pd.isna(latest['volatility']) else 0.15
    ma20 = float(latest['ma20']) if not pd.isna(latest['ma20']) else close_price
    
    # --- 風險分數評估模型 (0 ~ 100 分) ---
    # 基準分 50 分
    score = 50.0
    
    # 1. RSI 因子 (RSI > 70 屬超買高風險，RSI < 30 屬超賣安全區)
    if rsi > 80:
        score += (rsi - 70) * 1.2  # 極度超買加重懲罰 (+12~+36)
    elif rsi > 70:
        score += (rsi - 70) * 0.8  # 超買區溫和懲罰 (+0~+8)
    elif rsi < 30:
        score -= (30 - rsi) * 0.8  # 超賣區降低風險
        
    # 2. 均線位移因子 (相對於月線 MA20) - 校正版本
    price_to_ma = (close_price - ma20) / ma20 * 100
    if price_to_ma > 0:
        # 股價在月線之上：正常上漲 <=8% 只輕微加分；超過 8% 才顯著懲罰
        if price_to_ma <= 8.0:
            score += price_to_ma * 0.5   # 溫和上漲 最高 +4 分
        else:
            score += 4.0 + (price_to_ma - 8.0) * 1.5  # 超漲懲罰
    else:
        # 股價在月線之下：跌破月線本身就有下行風險，最多僅降低 5 分
        score += max(price_to_ma * 0.3, -5.0)
    
    # 3. KD 黃金/死亡交叉與趨勢
    if k_val > d_val:
        score -= 5.0  # 黃金交叉，偏向看多，進場風險微降
    else:
        score += 5.0  # 死亡交叉，下行風險增加
        
    # 4. 波動度因子 (平滑分級，避免正常個股被過度懲罰)
    if vol > 0.55:
        score += 12.0  # 極高波動 (>55%)，例如題材股
    elif vol > 0.35:
        score += 5.0   # 中高波動 (35~55%)
    elif vol <= 0.15:
        score -= 5.0   # 低波動 (<=15%)，例如 0050、00878 等大型 ETF
    # 正常波動 (15~35%) 不加分也不扣分
        
    # 限制分數在 0 ~ 100 之間
    score = max(0.0, min(100.0, score))
    
    # 風險分級
    if score < 35.0:
        risk_level = "🟢 低風險"
    elif score < 65.0:
        risk_level = "🟡 中風險"
    else:
        risk_level = "🔴 高風險"
        
    # --- 預估年化股息殖利率 ---
    # 00878 的近幾年每股配息大約在 1.2 到 1.4 元台幣之間
    # 我們以 1.35 元的常態化年配息金額，來動態估算目前的股息殖利率
    est_yield = (1.35 / close_price) * 100
    
    return {
        "close": round(close_price, 2),
        "rsi": round(rsi, 2),
        "k": round(k_val, 2),
        "d": round(d_val, 2),
        "volatility": round(vol, 4),
        "risk_score": round(score, 1),
        "risk_level": risk_level,
        "est_yield": round(est_yield, 2)
    }
