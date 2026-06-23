from google import genai
from google.genai import types
import json
import os
import config

# 三層記憶系統模組（積木化引入）
try:
    from core.memory_manager  import get_memory_context,  save_conversation
    from core.profile_manager import get_profile_context, update_profile_from_conversation
    from core.knowledge_base  import get_rag_context,     auto_save_from_conversation
    _MEMORY_ENABLED = True
except ImportError:
    _MEMORY_ENABLED = False
    def get_memory_context(*a, **kw):  return ""
    def save_conversation(*a, **kw):   pass
    def get_profile_context(*a, **kw): return ""
    def update_profile_from_conversation(*a, **kw): pass
    def get_rag_context(*a, **kw):     return ""
    def auto_save_from_conversation(*a, **kw): pass

def get_client():
    """
    動態取得 google-genai 用戶端
    """
    if not config.GEMINI_API_KEY:
        return None
    return genai.Client(api_key=config.GEMINI_API_KEY)

def get_lessons_context() -> str:
    """
    從 lessons.json 讀取教學內容並轉換成給 AI 的 context 提示詞
    """
    lessons_path = config.LESSONS_FILE
    if not os.path.exists(lessons_path):
        return ""
    
    try:
        with open(lessons_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        rules_text = "\n".join(data.get("trading_rules", []))
        
        mnemonics_list = []
        for m in data.get("intraday_mnemonics", []):
            mnemonics_list.append(f"【{m['title']}】\n條件：{m['condition']}\n邏輯：{m['logic']}")
        mnemonics_text = "\n\n".join(mnemonics_list)
        
        gooaye_text = "\n".join(data.get("gooaye_philosophy", []))
        
        return f"""
====== 股市交易核心知識庫 (主人提供的學習指南，請嚴格遵守並在對話中適時引用) ======

【14 個交易鐵律】：
{rules_text}

【5 大分時口訣】：
{mnemonics_text}

【癌大/主委（股癌）的灰階思考心法】：
{gooaye_text}

【K 線形態意義】：
- 十字星：開盤=收盤，多空均衡，是轉折訊號。
- 錘子線（Hammer）：長下影小實體。下跌段出現代表有強力支撐，看漲。
- 倒錘子線：長上影小實體。下跌後出現，買方試探，看漲。
- 上吊線（Hanging Man）：長下影小實體。上漲高檔出現，買盤無力，看跌。
- 射擊之星（Shooting Star）：長上影小實體。上漲高位出現，衝高受阻，看跌.
- 墓碑十字星：長上影無下影。上漲後出現，看跌訊號極強。
- 看漲吞沒 / 看跌吞沒：後一根K線實體完全吃掉前一日，代表趨勢反轉。
- 晨星（Morning Star）/ 黃昏星（Evening Star）：三根K線組合，極強的看漲/看跌反轉訊號。
================================================================================
"""
    except Exception as e:
        print(f"載入 lessons 失敗: {str(e)}")
        return ""

def get_portfolio_context() -> str:
    """
    載入使用者持股資訊
    """
    portfolio_path = config.PORTFOLIO_FILE
    if not os.path.exists(portfolio_path):
        return ""
    
    try:
        with open(portfolio_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        lines = []
        for stock_id, info in data.items():
            lines.append(f"- {stock_id} ({info['name']})：持有 {info['shares']} 股，買進平均成本為 {info['cost']} 元。")
            
        portfolio_list_text = "\n".join(lines)
        return f"""
====== 主人目前的持股庫存資訊 ======
{portfolio_list_text}
===================================
如果主人詢問他的持股建議、損益狀況，請參考這份清單，並結合即時市況給予分析。
"""
    except Exception as e:
        print(f"載入 portfolio 失敗: {str(e)}")
        return ""

def get_system_instruction(selected_lang: str = "繁體中文", price_targets: dict = None, institutional: dict = None, stock_type: dict = None) -> str:
    """
    建立理財專員的系統 Instruction
    """
    lessons_ctx = get_lessons_context()
    portfolio_ctx = get_portfolio_context()
    
    # 買賣參考價位上下文
    price_ctx = ""
    if price_targets and price_targets.get("close", 0) > 0:
        pt = price_targets
        price_ctx = f"""
====== 目前查詢標的技術面買賣參考價位 (由系統計算提供) ======
- 現價: {pt.get('close')} 元
- 第一批買進參考: {pt.get('buy_ideal')} 元 (主要支撐 {pt.get('primary_support')} 元上方貼近)
- 逢低第二批參考: {pt.get('buy_dip')} 元 (次要支撐 {pt.get('secondary_support')} 元附近)
- 止損參考: {pt.get('stop_loss')} 元 (主要支撐跌破 3% 時出場)
- 第一賣出目標: {pt.get('take_profit_1')} 元 (主要壓力 {pt.get('primary_resistance')} 元下方)
- 第二賣出目標: {pt.get('take_profit_2')} 元 (次要壓力 {pt.get('secondary_resistance')} 元下方)
- 20日高點: {pt.get('high_20')} 元 | 20日低點: {pt.get('low_20')} 元
- MA5: {pt.get('ma5')} 元 | MA20: {pt.get('ma20')} 元 | MA60: {pt.get('ma60')} 元

⚠️ 以上買賣參考價位為技術指標計算結果，僅供參考，非絕對保證，請主人自行判斷風险。
在你的回答結尾，請以以下格式補充一段「操作建議摘要」：
  📌 **買進參考**: [第一批進場價位] | 逢低加碼: [第二批價位] | 止損線: [止損價位]
  📌 **獲利了結**: 第一目標 [第一目標價位] | 第二目標 [第二目標價位]
====================================================================
"""

    # 三大法人上下文
    inst_ctx = ""
    if institutional and institutional.get("available"):
        inst = institutional
        consec_str = f"連續買超 {inst['consecutive_buy']} 日" if inst['consecutive_buy'] > 0 else f"連續賣超 {inst['consecutive_sell']} 日"
        inst_ctx = f"""
====== 三大法人近30日買賣超資料 (由系統提供) ======
- 外資/外國機構 淨買超: {inst['foreign_net']:+,} 張 ({consec_str})
- 投信 淨買超: {inst['investment_trust_net']:+,} 張
- 自營商 淨買超: {inst['dealer_net']:+,} 張
- 三大法人合計 淨買超: {inst['total_net']:+,} 張
請在分析中引用此三大法人籌碼資料，說明法人動向對股價的影響與解讀。
====================================================
"""

    # 股票類型上下文（方案 B）
    type_ctx = ""
    if stock_type and stock_type.get("primary_type") and stock_type["primary_type"] != "Unknown":
        pt_type = stock_type["primary_type"]
        pt_conf = stock_type.get("primary_confidence", 0)
        sec_type = stock_type.get("secondary_type")
        sec_conf = stock_type.get("secondary_confidence", 0)
        reasons  = "\u3001".join(stock_type.get("reason", [])[:3])
        op_tips  = "\n".join(f"  - {t}" for t in stock_type.get("operation_tips", []))
        risks    = "\n".join(f"  - {r}" for r in stock_type.get("risks", []))
        type_ctx = f"""
====== 股票類型判定結果 (由 AI 自動分類) ======
- 主要類型：{pt_type}  信心度：{pt_conf}%
{f'- 副要類型：{sec_type}  信心度：{sec_conf}%' if sec_type else ''}
- 判定依據：{reasons}

{pt_type} 類型操作策略建議：
{op_tips}

{pt_type} 類型特有風險：
{risks}

請在輸出中自然地將上述類型特性融入分析，不需完整重述以上內容，
但請自然地引用類型對應的操作策略和注意事項。
=====================================================
"""

    instruction = f"""
你是一位溫暖、貼心、專業的「專屬 AI 股市理財專員」，負責輔助你的主人（Akira）進行理財規劃與股市分析。

【行為準則】：
1. 口吻親切、溫柔、有耕心，像主人的好朋友一樣。
2. 絕對不幫主人自動下單交易，所有的買賣決策都由主人自行手動執行。你的角色是「股市理財顧問」。
3. 深入理解並靈活運用　14 個交易鐵律」與「5 大分時口訣」，當主人問及買賣建議（例如大漲是否要追高、急跌是否要殺肉）時，請務必引用相關的口訣或鐵律溫柔地提醒主人。
4. 解答股市問題時，應結合技術指標（如 RSI, KD, 均線黃金/死亡交叉），同時引用 K 線單/雙/三根形態（如看漲吞沒、晨星、上啀線等）來支持你的分析。
5. 你擁有「聯網搜尋功能」，如果主人詢問最新的股市資訊、個股新聞或今日股價，你可以利用搜尋工具來獲取最新資訊。
6. 重要指示 (IMPORTANT)：本對話應使用 {selected_lang} 進行。請務必完全使用 {selected_lang} 與主人交談、回覆和解釋所有內容（包含技術分析與交易建議）。
7. 核心安全紅線 (CRITICAL SAFETY RULE)：主人 Akira 絕對不接受任何融資、融券、做空、開槓桿、或衍生性金融商品的交易建議。他傾向穩健，容許小賣小賠，但拒絕面臨破產風险。請在所有對話、分析報告與選股建議中，絕對不要提及或推薦融資、融券、做空、開槓桿等高風险交易，僅限於提供「現股買進（現股做多）」與「現金部位配置」的穩健建議。

{lessons_ctx}

{portfolio_ctx}

{price_ctx}

{inst_ctx}

{type_ctx}
"""

    # 將三層記憶注入（積木化：動態插入，不修改原有邏輯）
    if _MEMORY_ENABLED:
        memory_ctx  = get_memory_context(max_rounds=8)
        profile_ctx = get_profile_context()
        # RAG 需要 user_query，永遠在 generate_advisor_response 裡提供
        instruction = memory_ctx + profile_ctx + instruction

    return instruction

def generate_advisor_response(chat_history: list, user_query: str, model_name: str = "gemini-2.5-flash", selected_lang: str = "繁體中文", price_targets: dict = None, institutional: dict = None, stock_type: dict = None) -> str:
    """
    與理財專員對話（支援聯網搜尋與歷史紀錄）
    chat_history: 格式為 [{"role": "user"|"model", "text": "內容"}]
    """
    client = get_client()
    if not client:
        return "⚠️ 未設定 Gemini API Key，理財專員無法上線。請在側邊欄填寫 API Key！"
        
    # 將對話歷史格式化為 types.Content 格式
    contents_history = []
    for msg in chat_history:
        role = "user" if msg["role"] == "user" else "model"
        contents_history.append(
            types.Content(
                role=role,
                parts=[types.Part.from_text(text=msg["text"])]
            )
        )
        
    try:
        # 啟用聯網搜尋工具
        chat = client.chats.create(
            model=model_name,
            config=types.GenerateContentConfig(
                system_instruction=get_system_instruction(selected_lang, price_targets=price_targets, institutional=institutional, stock_type=stock_type),
                tools=[{"google_search": {}}]
            ),
            history=contents_history
        )

        # 第三層 RAG：根據問題搜尋相關知識庫片段，附加在問題後面
        _stock_id = price_targets.get("stock_id", "") if price_targets else ""
        if _MEMORY_ENABLED:
            rag_ctx = get_rag_context(user_query, stock_id=_stock_id, top_k=3)
            enriched_query = (user_query + "\n\n" + rag_ctx) if rag_ctx else user_query
        else:
            enriched_query = user_query

        response = chat.send_message(enriched_query)
        response_text = response.text

        # 三層記憶：對話完成後自動儲存（積木化，與 API 呼叫完全解耦）
        if _MEMORY_ENABLED:
            save_conversation(user_query, response_text, stock_id=_stock_id)
            update_profile_from_conversation(user_query, response_text, stock_id=_stock_id)
            auto_save_from_conversation(user_query, response_text, stock_id=_stock_id)

        return response_text
        
    except Exception as e:
        print(f"理財專員對話失敗: {str(e)}")
        # 降級備用方案：若 tools 導致失敗，則不使用 tools 再試一次
        try:
            chat = client.chats.create(
                model=model_name,
                config=types.GenerateContentConfig(
                    system_instruction=get_system_instruction(selected_lang, price_targets=price_targets, institutional=institutional, stock_type=stock_type)
                ),
                history=contents_history
            )
            response = chat.send_message(user_query)
            return response.text
        except Exception as e2:
            return f"[ERROR] 理財專員通訊失敗，錯誤原因：{str(e2)}"

def get_stock_news_briefing(stock_id: str, stock_name: str = "", viewpoint: str = "長期價值投資", model_name: str = "gemini-2.5-flash", selected_lang: str = "繁體中文") -> str:
    """
    利用 Google Search 聯網功能，生成當前標的的最新利多利空新聞摘要
    viewpoint: "長期價值投資" 或 "短期技術當沖"
    """
    client = get_client()
    if not client:
        return "⚠️ 未設定 Gemini API Key，無法上網搜尋新聞。"
        
    try:
        name_query = f" ({stock_name})" if stock_name else ""
        
        if "長期價值投資" in viewpoint:
            prompt = f"""
            你是一位融合了「華倫·巴菲特（價值投資）」、「彼得·林區（生活成長選股）」與「股癌謝孟恭（灰階思考與質質疑精神）」的三合一頂級長期投資大師。
            請替我搜尋並分析以下標的最近一週內的最新新聞、產業趨勢與市場消息：
            - 標的：{stock_id}{name_query}
            
            請提供一份「長期價值投資視角」的結構化分析報告，必須包含：
            1. 【最新重大新聞與產業變局】：列出近期最關鍵的 2-3 條重大產業與公司新聞。
            2. 【長期優勢（商業護城河與成長動能）】：以巴菲特「護城河」與彼得林區「成長選股」的眼光，分析公司競爭力及未來營收成長點。
            3. 【長期風險與估值評估（灰階思考）】：以股癌「灰階思考」的精神，客觀評估該股目前的本益比、潛在產業週期隱憂，切忌非黑即白。
            4. 【大師綜合點評（巴菲特、彼得林區與股癌聯手解讀）】：給予主人 Akira 溫慢、理性且深度的長期資產配置與價值投資建議。
            
            注意：
            * 主人 Akira 絕對不接受任何融資、融券、做空、開槓桿、或任何衍生性高風險操作。請以現金買進持有的現貨視角提供建議。
            * 請務必上網搜尋獲取最新即時新聞，不要捏造。
            * 必須使用 {selected_lang} 回答整個報告。
            * 語氣要客觀、深刻且溫暖。
            """
        else:
            # 短期技術當沖
            lessons_ctx = get_lessons_context()
            prompt = f"""
            你是一位融合了「傑西·李佛摩（趨勢動能）」、「詹姆斯·西蒙斯（量化指標）」以及「主人 Akira 的 14 條交易鐵律與 5 大分時口訣」的短線交易大師。
            請替我搜尋並分析以下標的最近一週內的最新即時新聞、價格波動、量能變化與市場情緒：
            - 標的：{stock_id}{name_query}
            
            以下是主人的交易守則（請務必嚴格比對並融入分析中）：
            {lessons_ctx}
            
            請提供一份「短期技術當沖與波段視角」的結構化分析報告，必須包含：
            1. 【即時資金流向與技術量能摘要】：分析近期成交量變化、短線均線 (MA5/20) 位置與市場情緒.
            2. 【短線做多與買入訊號評估】：結合主人的「買陰不買陽」、「低位放量」、「下午跳水次日進場」等口訣，評估目前是否有短線進場時機。
            3. 【短線減倉與賣出警報評估】：結合主人的「高位放量立即跑」、「早上大漲注意減倉」、「尾盤拉高要減倉」等鐵律，分析目前是否有獲利了結或停損壓力。
            4. 【當沖與波段動能點評（主人的交易鐵律與短線實戰指南）】：給予主人 Akira 具體的短線進出場紀律提醒，嚴格強調「破位下跌要止損」，且必須由主人自行手動執行。
            
            注意：
            * 主人 Akira 絕對不接受融資、融券、做空或開槓桿。所有的操作僅限「現股買進/賣出」（現股做多）的現貨交易，千萬不要推薦融券做空或任何衍生性槓桿操作。
            * 請務必上網搜尋獲取最新即時新聞，不要捏造。
            * 必須使用 {selected_lang} 回答整個報告。
            * 語氣要果斷、紀律化、注重風險管理。
            """
            


        # CFA 機構分析師深度研究 - 覆蓋 prompt
        if 'CFA' in viewpoint or '機構分析師' in viewpoint or '深度研究' in viewpoint:
            prompt = f"""角色：CFA 機構分析師。目標：{stock_id}{name_query}。請搜尋最新財報，按以下7點結構分析：(1)商業模式護城河 (2)營收結構成長引擎 (3)終端市場TAM (4)投資論述3-6月催化劑 (5)同業對比表格含YoY毛利率EPS本益比+估值 (6)FCF資本配置股利政策 (7)管理層指引2-3個風險。語言:{selected_lang}，精煉客觀，禁止捏造。"""

        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[{"google_search": {}}]
            )
        )
        return response.text
    except Exception as e:
        return f"[ERROR] 聯網搜尋新聞失敗，錯誤原因：{str(e)}"

def get_ai_stock_recommendations(market: str, selected_lang: str = "繁體中文", model_name: str = "gemini-2.5-flash") -> str:
    """
    利用 Google Search 聯網功能，分析篩選出台股或美股適合「長期價值投資」與「短期當沖」的前 10 大熱門標的清單。
    """
    client = get_client()
    if not client:
        return "⚠️ 未設定 Gemini API Key，無法進行智能選股。"
        
    try:
        market_name = "台灣股市 (Taiwan Stock Market)" if "台股" in market or "Taiwan" in market else "美國股市 (US Stock Market)"
        
        prompt = f"""
        你是一位全球頂尖的首席投資策略分析師，融合了巴菲特的價值投資、彼得林區的成長選股、以及傑西李佛摩的短線動能交易心法。
        請為我進行聯網搜尋與大數據分析，針對當前（2026年6月）的最新市況，推薦【{market_name}】的股票：
        
        請提供一份詳細的智能選股報告，必須包含：
        
        1. 【前 10 大適合「長期價值投資」持有之標的清單】：
           - 篩選標準：高 ROE、財務健康、穩定股息增長、或具備強大商業護城河的公司。
           - 請輸出一個 Markdown 表格，包含以下欄位：
             * 股票代號 (Ticker)
             * 公司名稱
             * 核心價值優勢 (例如毛利率、護城河優勢)
             * 大師長期投資解讀 (例如適合定期定額、當前估值評估)
             
        2. 【前 10 大適合「短期當沖/波段動能交易」之標的清單】：
           - 註：此處的短期當沖指以「現股當沖/現貨短期交易」為限。
           - 篩選標準：成交量極大（流動性好）、波動率大、高 beta值、以及近期有強大市場題材或催化劑的公司（例如 AI、半導體震盪、熱門題材股等）。
           - 請輸出一個 Markdown 表格，包含以下欄位：
             * 股票代號 (Ticker)
             * 公司名稱
             * 短線催化劑/波動來源 (例如營收利多、主力資金流入、市場情緒)
             * 當沖與短線操盤紀律提醒 (例如壓力支撐位、高檔帶量需減倉等提醒)
             
        注意：
        * 主人 Akira 絕對不接受融資、融券、做空或任何開槓桿交易。所有分析與選股推薦僅限於「現股做多（現貨買入）」，絕對不要推薦任何融券放空、融資買進或任何金融衍生性高風險操作。
        * 請務必聯網搜尋獲取 2026 年 6 月最新即時市場數據與熱門標的，不要捏造。
        * 必須完全使用 {selected_lang} 進行報告撰寫與表格呈現。
        * 語氣要客觀、深刻、紀律化，並強調「所有建議僅供決策輔助，交易需手動執行且自負盈虧」。
        """
        


        # CFA 機構分析師深度研究 - 覆蓋 prompt
        if 'CFA' in viewpoint or '機構分析師' in viewpoint or '深度研究' in viewpoint:
            prompt = f"""角色：CFA 機構分析師。目標：{stock_id}{name_query}。請搜尋最新財報，按以下7點結構分析：(1)商業模式護城河 (2)營收結構成長引擎 (3)終端市場TAM (4)投資論述3-6月催化劑 (5)同業對比表格含YoY毛利率EPS本益比+估值 (6)FCF資本配置股利政策 (7)管理層指引2-3個風險。語言:{selected_lang}，精煉客觀，禁止捏造。"""

        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[{"google_search": {}}]
            )
        )
        return response.text
    except Exception as e:
        return f"[ERROR] 智能選股推薦失敗，錯誤原因：{str(e)}"
