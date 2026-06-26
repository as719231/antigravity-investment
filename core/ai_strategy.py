try:
    from google import genai as google_genai
    _genai_available = True
except ImportError:
    try:
        import google.generativeai as google_genai
        _genai_available = True
    except ImportError:
        google_genai = None
        _genai_available = False
import config

# 設定 Gemini API Key
if _genai_available and config.GEMINI_API_KEY:
    try:
        google_genai.configure(api_key=config.GEMINI_API_KEY)
    except Exception:
        pass

def get_ai_decision_report(stock_id: str, action: str, metrics: dict, details: str = "") -> str:
    """
    呼叫 Gemini 1.5 Flash 產生一段溫暖且專業的繁體中文投資分析報告，字數控制在 150-200 字以內，適合手機閱讀。
    
    action: 'BUY' (建議買入時), 'SELL' (建議賣出時), 'STATUS' (查詢狀態時)
    metrics: risk_calculator.py 計算出來的指標字典
    details: 其他需要傳入的輔助資訊（如：賣出目標價、帳戶餘額等）
    """
    if not config.GEMINI_API_KEY or not _genai_available:
        return "⚠️ 未設定 Gemini API Key，無法產生 AI 分析。"

    try:
        model = google_genai.GenerativeModel('gemini-1.5-flash')
    except AttributeError:
        return "⚠️ Gemini SDK 版本不相容，請檢查 requirements.txt。"
    
    # 建立系統 Prompt 語意
    action_chinese = {
        "BUY": "評估當前是否適合作為被動收入定期定額買入點",
        "SELL": "評估是否已達高點，適合執行停利賣出點",
        "STATUS": "日常帳戶狀態與市場概況分析"
    }.get(action, "投資決策分析")
    
    prompt = f"""
    你是一位專業且溫暖的理財小助手。你的主人正在實行「每月定期定額被動收入計畫」，核心標的是 {stock_id} (國泰永續高股息)。
    
    現在的分析情境是：【{action_chinese}】。
    
    目前的市場數據如下：
    - 收盤價：{metrics.get('close')} 元
    - RSI 指標：{metrics.get('rsi')}
    - KD 指標：K={metrics.get('k')}, D={metrics.get('d')}
    - 風險評估分：{metrics.get('risk_score')}/100 (風險等級為：{metrics.get('risk_level')})
    - 預估年化股息殖利率：{metrics.get('est_yield')}%
    {f"- 額外資訊：{details}" if details else ""}
    
    請撰寫一段給主人的分析報告，包含：
    1. 針對目前數據，提供專業、理性但口吻溫柔的解讀。
    2. 給予主人持續累積被動收入的正能量打氣。
    
    規則：
    * 必須使用繁體中文。
    * 字數大約 150 到 180 字之間。
    * 口吻要像好朋友一樣，讓人感到安心與放心。
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"🤖 AI 分析產生時發生錯誤：{str(e)}\n\n(已為您切換為指標純文字模式)\n當前股價為 {metrics.get('close')}，RSI 數值為 {metrics.get('rsi')}，風險等級為 {metrics.get('risk_level')}。"
