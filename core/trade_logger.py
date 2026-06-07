import os
import csv
from datetime import datetime
import config

def log_trade(action: str, price: float, shares: int, amount: float, message: str, mode: str):
    """
    將交易紀錄寫入 CSV 檔案
    """
    file_path = config.TRADE_HISTORY_FILE
    
    # 確保資料夾存在
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    file_exists = os.path.exists(file_path)
    
    headers = ["timestamp", "stock_id", "action", "price", "shares", "amount", "message", "mode"]
    
    row = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "stock_id": config.STOCK_ID,
        "action": action,
        "price": price,
        "shares": shares,
        "amount": amount,
        "message": message,
        "mode": mode
    }
    
    try:
        with open(file_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)
    except Exception as e:
        print(f"寫入交易紀錄 CSV 失敗: {str(e)}")
