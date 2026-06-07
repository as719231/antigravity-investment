import os
import google.generativeai as genai
from FinMind.data import DataLoader
import datetime
from dotenv import load_dotenv

# 加載 .env 檔案
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

# 初始化 Gemini
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def ai_analyze_stock(stock_id="00878"):
    print(f"\n--- [抗重力 AI 大腦] 正在分析 {stock_id} ---")
    
    # 1. 抓取數據
    dl = DataLoader()
    end_date = datetime.date.today().strftime('%Y-%m-%d')
    start_date = (datetime.date.today() - datetime.timedelta(days=30)).strftime('%Y-%m-%d')
    
    try:
        df = dl.taiwan_stock_daily(stock_id=stock_id, start_date=start_date, end_date=end_date)
        if df.empty:
            print("無法抓取數據，請稍後再試。")
            return
            
        latest_price = df.iloc[-1]['close']
        price_change = latest_price - df.iloc[0]['close']
        
        # 2. 構建 Prompt 餵給 AI
        prompt = f"""
        你是一位專業且溫暖的投資理財機器人，你的主人是一位每月薪水5萬、剛開始投資、追求「被動收入」的新手。
        
        目前的市場數據如下：
        - 標的：{stock_id} (國泰永續高股息)
        - 今日收盤價：{latest_price} 元
        - 過去一個月的價格變動：{price_change:.2f} 元
        - 每月投入金額：5,000 元 (定期定額)
        
        請根據以上數據，給主人一段約 150 字的建議：
        1. 分析目前的價格算不算貴？
        2. 針對「被動收入」的目標，給予正向的鼓勵。
        3. 用淺顯易懂、像好朋友一樣的口吻。
        """
        
        # 3. 呼叫 Gemini
        response = model.generate_content(prompt)
        
        print("\n" + "="*50)
        print(f"🤖 Gemini AI 的分析報告：")
        print("-" * 50)
        print(response.text)
        print("="*50)
        
    except Exception as e:
        print(f"分析過程發生錯誤：{e}")
        if "API_KEY" in str(e):
            print("💡 提醒：請檢查 .env 檔案中的 GEMINI_API_KEY 是否填寫正確！")

if __name__ == "__main__":
    if not API_KEY or "YOUR_API_KEY" in API_KEY:
        print("❌ 錯誤：尚未設定 API Key。請先修改 .env 檔案！")
    else:
        ai_analyze_stock()
