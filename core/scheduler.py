import pandas as pd
import datetime
import os
import csv
import logging
import config
from core.risk_calculator import evaluate_risk_and_yield
from core.ai_strategy import get_ai_decision_report
from core.line_bot import get_user_id, send_push, make_decision_card, make_text_message
from core.broker import ShioajiBroker
from FinMind.data import DataLoader

logger = logging.getLogger("Scheduler")
broker = ShioajiBroker()

def has_bought_this_month() -> bool:
    """
    檢查 trade_history.csv，確認本月是否已經有買入(BUY)紀錄
    """
    file_path = config.TRADE_HISTORY_FILE
    if not os.path.exists(file_path):
        return False
        
    current_month = datetime.datetime.now().strftime("%Y-%m") # 例如 "2026-06"
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 檢查時間戳記是否在本月，且 action 為 BUY
                timestamp = row.get("timestamp", "")
                action = row.get("action", "")
                mode = row.get("mode", "")
                
                # 排除不同交易模式的干擾 (例如模擬模式不影響實盤額度，反之亦然)
                current_mode_name = "模擬" if config.is_simulation_mode() else "實盤"
                
                if timestamp.startswith(current_month) and action == "BUY" and mode == current_mode_name:
                    return True
    except Exception as e:
        logger.error("讀取交易紀錄判斷本月買入狀態出錯: %s", str(e))
        
    return False

def check_market_and_notify():
    """
    排程核心任務：自動看盤，評估買賣機會並發送 LINE 通知
    """
    user_id = get_user_id()
    if not user_id:
        logger.warning("排程器啟動，但目前沒有儲存任何用戶的 LINE User ID，無法發送通知！請先在 LINE 對話隨意輸入訊息。")
        return
        
    logger.info("📅 排程看盤任務啟動: %s", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    # 1. 抓取 FinMind 股價歷史
    dl = DataLoader()
    end_date = datetime.date.today().strftime('%Y-%m-%d')
    start_date = (datetime.date.today() - datetime.timedelta(days=90)).strftime('%Y-%m-%d')
    
    try:
        df = dl.taiwan_stock_daily(stock_id=config.STOCK_ID, start_date=start_date, end_date=end_date)
        if df.empty:
            logger.warning("FinMind 抓取不到資料。")
            return
            
        # 2. 計算技術分析與風險
        metrics = evaluate_risk_and_yield(df)
        current_price = metrics["close"]
        
        # 3. 取得目前庫存狀況
        status = broker.get_account_status()
        shares = status.get("shares", 0)
        
        # --- 賣出決策評估 ---
        sell_threshold = config.get_sell_threshold()
        if shares > 0 and current_price >= sell_threshold:
            logger.info("👉 觸發賣出條件！當前股價 %s >= 賣出門檻 %s", current_price, sell_threshold)
            ai_report = get_ai_decision_report(config.STOCK_ID, "SELL", metrics, f"目前庫存股數：{shares} 股，設定賣出目標價：{sell_threshold} 元。")
            card = make_decision_card("SELL", current_price, metrics, ai_report)
            send_push(user_id, card)
            return  # 觸發賣出就不再評估買入

        # --- 買進決策評估 ---
        # 規則 A：本月如果已經買過，就絕對不重複買
        if has_bought_this_month():
            logger.info("👉 本月已經執行過買入定期定額，本月跳過買入評估。")
            return
            
        # 規則 B：本月還沒買過，進行進場點評估
        today = datetime.datetime.now()
        # 判斷是不是接近月底 (25號之後)
        is_end_of_month = today.day >= 25
        
        # 買入觸發訊號：
        # 1. 或是處於低風險區 (risk_score < 40)
        # 2. 或是已經到月底了 (強制執行定期定額，防錯過)
        should_buy = (metrics["risk_score"] < 40.0) or is_end_of_month
        
        if should_buy:
            logger.info("👉 觸發買入條件！風險分數: %s, 是否月底: %s", metrics["risk_score"], is_end_of_month)
            details = f"每次預算：{config.get_buy_amount()} 元。本月尚未交易。{'已屆月底，執行定期定額強迫儲蓄。' if is_end_of_month else '技術指標處於低風險便宜區，適合作為本月扣款點。'}"
            ai_report = get_ai_decision_report(config.STOCK_ID, "BUY", metrics, details)
            card = make_decision_card("BUY", current_price, metrics, ai_report)
            send_push(user_id, card)
        else:
            logger.info("👉 未達買入標準 (風險分數 %s >= 40 且尚未到月底 25 號)。繼續監控。", metrics["risk_score"])
            
    except Exception as e:
        logger.error("排程看盤與通知執行失敗: %s", str(e))
        send_push(user_id, make_text_message(f"⚠️ 盤中自動看盤發生錯誤：{str(e)}"))
