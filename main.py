import threading
import time
import schedule
import datetime
import logging
import json
import os
from flask import Flask, request, jsonify
import config
from core.line_bot import verify_signature, process_webhook_events, make_text_message, send_push, get_user_id
from core.scheduler import check_market_and_notify

# 設定全域日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Main")

app = Flask(__name__)

# --- 背景排程執行緒 ---
def scheduler_loop():
    logger.info("⏰ 背景排程執行緒啟動！")
    
    # 週一到週五的盤中三個時段進行檢查
    def job_wrapper():
        today_weekday = datetime.datetime.today().weekday()
        if today_weekday < 5:  # 0~4 代表週一至週五
            logger.info("📊 偵測為交易日，執行看盤分析...")
            check_market_and_notify()
        else:
            logger.info("☕ 今天是週末，休市不進行自動看盤。")

    # 設定每日時間排程 (開盤盤中與尾盤)
    schedule.every().day.at("09:30").do(job_wrapper)
    schedule.every().day.at("12:30").do(job_wrapper)
    schedule.every().day.at("13:30").do(job_wrapper)

    while True:
        schedule.run_pending()
        time.sleep(10) # 每 10 秒檢查一次

# --- Flask 路由定義 ---

@app.route("/callback", methods=["POST"])
def callback():
    """
    LINE Webhook 回呼接收端
    """
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data()
    
    # 驗證簽章
    if not verify_signature(body, signature):
        logger.warning("❌ 簽章驗證失敗！")
        return "Invalid signature", 400
        
    try:
        body_text = body.decode("utf-8")
        data = json.loads(body_text)
        events = data.get("events", [])
        
        # 移交交給 LINE 控制中心處理非同步事件
        # 啟動新執行緒處理事件，避免 LINE Webhook 逾時 (LINE 要求 Webhook 必須在 1 秒內回傳 200 OK)
        threading.Thread(target=process_webhook_events, args=(events,)).start()
        
        return "OK", 200
    except Exception as e:
        logger.error("解析 Webhook 事件時發生錯誤: %s", str(e))
        return "Internal Error", 500

@app.route("/health", methods=["GET"])
def health():
    """
    UptimeRobot 定時喚醒與健康檢查端點
    """
    return jsonify({"status": "healthy", "time": datetime.datetime.now().isoformat()}), 200

@app.route("/trigger_check", methods=["GET"])
def trigger_check():
    """
    提供一個手動網頁觸發端點（測試用）
    您可以打開瀏覽器輸入 http://localhost:5000/trigger_check 來測試 AI 分析與發送卡片
    """
    logger.info("⚡ 接收到手動觸發看盤指令！")
    threading.Thread(target=check_market_and_notify).start()
    return jsonify({"status": "triggered", "message": "已啟動背景線程看盤分析任務，請查看 LINE 機器人訊息！"}), 200

# 輔助：若執行 `main.py` 直接啟動
if __name__ == "__main__":
    # 1. 啟動背景排程器執行緒
    sched_thread = threading.Thread(target=scheduler_loop, daemon=True)
    sched_thread.start()
    
    # 2. 啟動 Flask 網頁伺服器
    # 本地開發預設跑在 5000 port
    port = int(os.environ.get("PORT", 5000))
    
    logger.info("🚀 啟動 Flask Webhook 伺服器，Port: %s", port)
    # 在本機測試時使用 debug=False 以免執行緒重啟兩次導致排程重啟
    app.run(host="0.0.0.0", port=port, debug=False)
