from FinMind.data import DataLoader
import datetime

def get_latest_stock_price(stock_id="00878"):
    dl = DataLoader()
    
    # 抓取最近 10 天的資料
    end_date = datetime.date.today().strftime('%Y-%m-%d')
    start_date = (datetime.date.today() - datetime.timedelta(days=10)).strftime('%Y-%m-%d')
    
    print("\n--- [抗重力監控] 正在抓取 {} 的最新數據 ---".format(stock_id))
    
    try:
        df = dl.taiwan_stock_daily(
            stock_id=stock_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if df.empty:
            print("無法抓取資料，可能是開盤時間尚未更新或 API 限制。")
            return
            
        latest_data = df.iloc[-1]
        
        print("-" * 50)
        print("標的名稱：{} (國泰永續高股息)".format(stock_id))
        print("日期：{}".format(latest_data['date']))
        print("收盤價：{} 元".format(latest_data['close']))
        print("成交量：{:,} 股".format(int(latest_data['Trading_Volume'])))
        print("-" * 50)
        
        # 簡單的 AI 分析模擬
        if latest_data['close'] < 20: 
             print("AI 小建議：目前價格似乎在您設定的甜蜜點，可以考慮小額加碼！")
        else:
             print("AI 小建議：目前價格平穩，維持每月的 5,000 元定期定額即可。")
             
    except Exception as e:
        print("發生錯誤：{}".format(str(e)))

if __name__ == "__main__":
    get_latest_stock_price()
