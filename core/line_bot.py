import os
import json
import hmac
import hashlib
import base64
import requests
import logging
import config
from core.broker import ShioajiBroker
from core.ai_strategy import get_ai_decision_report
from core.risk_calculator import evaluate_risk_and_yield
import core.trade_logger as trade_logger

logger = logging.getLogger("LineBot")
USER_ID_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "user_id.txt")
broker = ShioajiBroker()

# --- 用戶 ID 儲存與讀取 ---
def save_user_id(user_id: str):
    os.makedirs(os.path.dirname(USER_ID_FILE), exist_ok=True)
    with open(USER_ID_FILE, "w", encoding="utf-8") as f:
        f.write(user_id)

def get_user_id() -> str:
    if os.path.exists(USER_ID_FILE):
        with open(USER_ID_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""

# --- 驗證 LINE Webhook 簽章 ---
def verify_signature(body: bytes, signature: str) -> bool:
    if not config.LINE_CHANNEL_SECRET:
        return True # 若未設定金鑰則跳過（開發用）
    hash_val = hmac.new(
        config.LINE_CHANNEL_SECRET.encode('utf-8'),
        body,
        hashlib.sha256
    ).digest()
    computed_signature = base64.b64encode(hash_val).decode('utf-8')
    return computed_signature == signature

# --- REST API 通訊 (發送 LINE 訊息) ---
def send_reply(reply_token: str, message_obj: dict):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.LINE_CHANNEL_ACCESS_TOKEN}"
    }
    payload = {
        "replyToken": reply_token,
        "messages": [message_obj]
    }
    res = requests.post("https://api.line.me/v2/bot/message/reply", headers=headers, data=json.dumps(payload))
    return res.status_code == 200

def send_push(user_id: str, message_obj: dict):
    if not user_id:
        logger.warning("嘗試發送 Push 訊息，但 user_id 為空！")
        return False
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.LINE_CHANNEL_ACCESS_TOKEN}"
    }
    payload = {
        "to": user_id,
        "messages": [message_obj]
    }
    res = requests.post("https://api.line.me/v2/bot/message/push", headers=headers, data=json.dumps(payload))
    return res.status_code == 200

def make_text_message(text: str) -> dict:
    return {"type": "text", "text": text}

# --- 互動式 Flex Message 產生器 ---
def make_decision_card(action: str, current_price: float, metrics: dict, ai_report: str) -> dict:
    """
    建立精美的 Flex Message 卡片
    action: 'BUY' 或 'SELL'
    """
    is_buy = action == "BUY"
    header_title = "🚀 抗重力投資建議：建議買進" if is_buy else "🚨 抗重力投資建議：達到賣出門檻"
    header_color = "#0F8294" if is_buy else "#E05B5B"
    
    action_text = f"買進 {config.get_buy_amount():,} 元 (零股)" if is_buy else "賣出全部持股"
    
    # 建立 Flex Message 結構
    bubble = {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": header_title,
                    "weight": "bold",
                    "color": "#FFFFFF",
                    "size": "md"
                }
            ],
            "backgroundColor": header_color
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                # 標的名稱
                {
                    "type": "text",
                    "text": f"標的：{config.STOCK_ID} (國泰永續高股息)",
                    "weight": "bold",
                    "size": "md",
                    "margin": "sm"
                },
                {
                    "type": "separator",
                    "margin": "md"
                },
                # 數據表格
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "md",
                    "spacing": "sm",
                    "contents": [
                        {"type": "box", "layout": "horizontal", "contents": [
                            {"type": "text", "text": "建議動作", "color": "#aaaaaa", "size": "sm"},
                            {"type": "text", "text": action_text, "align": "end", "size": "sm", "weight": "bold"}
                        ]},
                        {"type": "box", "layout": "horizontal", "contents": [
                            {"type": "text", "text": "當前股價", "color": "#aaaaaa", "size": "sm"},
                            {"type": "text", "text": f"{current_price} 元", "align": "end", "size": "sm", "weight": "bold"}
                        ]},
                        {"type": "box", "layout": "horizontal", "contents": [
                            {"type": "text", "text": "風險評估", "color": "#aaaaaa", "size": "sm"},
                            {"type": "text", "text": f"{metrics.get('risk_level')} ({metrics.get('risk_score')}/100)", "align": "end", "size": "sm", "weight": "bold"}
                        ]},
                        {"type": "box", "layout": "horizontal", "contents": [
                            {"type": "text", "text": "預估年配息率", "color": "#aaaaaa", "size": "sm"},
                            {"type": "text", "text": f"{metrics.get('est_yield')}%", "align": "end", "size": "sm", "weight": "bold"}
                        ]}
                    ]
                },
                {
                    "type": "separator",
                    "margin": "md"
                },
                # AI 分析內容
                {
                    "type": "text",
                    "text": "🤖 AI 指揮官分析：",
                    "weight": "bold",
                    "size": "sm",
                    "margin": "md",
                    "color": "#888888"
                },
                {
                    "type": "text",
                    "text": ai_report,
                    "wrap": True,
                    "size": "sm",
                    "margin": "xs",
                    "color": "#333333",
                    "style": "italic"
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "horizontal",
            "spacing": "sm",
            "contents": [
                # 確認按鈕
                {
                    "type": "button",
                    "style": "primary",
                    "height": "sm",
                    "color": "#1DB446",
                    "action": {
                        "type": "postback",
                        "label": "✅ 確認執行",
                        "data": f"action={action.lower()}&price={current_price}"
                    }
                },
                # 取消按鈕
                {
                    "type": "button",
                    "style": "secondary",
                    "height": "sm",
                    "action": {
                        "type": "postback",
                        "label": "❌ 暫緩/取消",
                        "data": "action=cancel"
                    }
                }
            ]
        }
    }
    
    return {
        "type": "flex",
        "altText": "抗重力投資決策報告",
        "contents": bubble
    }

# --- LINE Webhook 核心處理器 ---
def process_webhook_events(events: list):
    """
    解析 Webhook 事件列表
    """
    for event in events:
        event_type = event.get("type")
        source = event.get("source", {})
        user_id = source.get("userId")
        
        # 儲存使用者 ID，以便排程器推送訊息
        if user_id:
            save_user_id(user_id)
            
        # 1. 處理純文字命令
        if event_type == "message":
            message = event.get("message", {})
            msg_type = message.get("type")
            reply_token = event.get("replyToken")
            
            if msg_type == "text" and reply_token:
                text_content = message.get("text", "").strip()
                handle_text_commands(reply_token, text_content, user_id)
                
        # 2. 處理按鈕點擊事件 (Postback)
        elif event_type == "postback":
            reply_token = event.get("replyToken")
            postback_data = event.get("postback", {}).get("data", "")
            if reply_token and postback_data:
                handle_postback_commands(reply_token, postback_data, user_id)

def handle_text_commands(reply_token: str, text: str, user_id: str):
    """
    處理文字指令，例如：/status, /set_sell, /set_buy
    """
    # 隱藏金鑰等測試模式，防止無防備輸出
    if text == "/status":
        send_reply(reply_token, make_text_message("⏳ 正在取得您的資產與市場狀態，請稍候..."))
        
        # 模擬從 FinMind 取得最新價格與歷史數據以評估指標
        from FinMind.data import DataLoader
        import datetime
        dl = DataLoader()
        end_date = datetime.date.today().strftime('%Y-%m-%d')
        start_date = (datetime.date.today() - datetime.timedelta(days=90)).strftime('%Y-%m-%d')
        
        try:
            df = dl.taiwan_stock_daily(stock_id=config.STOCK_ID, start_date=start_date, end_date=end_date)
            metrics = evaluate_risk_and_yield(df)
            current_price = metrics["close"]
            
            # 取得庫存狀態
            status = broker.get_account_status()
            
            # 呼叫 AI 產生日常簡報
            details = f"當前可用資金：{status.get('balance', 0):,.0f} 元，目前庫存持有股數：{status.get('shares', 0)} 股，平均持股成本：{status.get('avg_cost', 0.0)} 元。模擬交易模式為：{status.get('mode', 'N/A')}。"
            ai_report = get_ai_decision_report(config.STOCK_ID, "STATUS", metrics, details)
            
            # 組裝回覆訊息
            status_text = (
                f"📊 【抗重力投資助理狀態回報】\n"
                f"────────────────\n"
                f"🔹 標的：{config.STOCK_ID} (國泰永續高股息)\n"
                f"🔹 當前股價：{current_price} 元\n"
                f"🔹 風險評估：{metrics['risk_level']} ({metrics['risk_score']}/100)\n"
                f"🔹 預估年化股息率：{metrics['est_yield']}%\n"
                f"────────────────\n"
                f"💰 運作模式：{status.get('mode')}\n"
                f"💰 帳戶餘額：{status.get('balance', 0.0):,.1f} 元\n"
                f"💰 持有股數：{status.get('shares', 0)} 股\n"
                f"💰 平均持股成本：{status.get('avg_cost', 0.0)} 元\n"
                f"🎯 賣出目標價設定：{config.get_sell_threshold()} 元\n"
                f"💵 每次購買預算：{config.get_buy_amount():,} 元\n"
                f"────────────────\n"
                f"🤖 AI 分析官點評：\n{ai_report}"
            )
            # 發送給用戶
            send_push(user_id, make_text_message(status_text))
        except Exception as e:
            send_push(user_id, make_text_message(f"❌ 查詢失敗，錯誤原因：{str(e)}"))
            
    elif text.startswith("/set_sell"):
        parts = text.split()
        if len(parts) < 2:
            send_reply(reply_token, make_text_message("⚠️ 格式錯誤！正確格式為：\n`/set_sell [價格]` (例如: `/set_sell 24.5`)"))
            return
        try:
            target_price = float(parts[1])
            settings = config.load_settings()
            settings["sell_threshold"] = target_price
            config.save_settings(settings)
            send_reply(reply_token, make_text_message(f"✅ 成功將賣出提示門檻設定為：{target_price} 元。當 00878 股價突破此價格時，將會發送 LINE 提醒賣出。"))
        except ValueError:
            send_reply(reply_token, make_text_message("⚠️ 請輸入正確的數字格式。"))
            
    elif text.startswith("/set_buy"):
        parts = text.split()
        if len(parts) < 2:
            send_reply(reply_token, make_text_message("⚠️ 格式錯誤！正確格式為：\n`/set_buy [金額]` (例如: `/set_buy 5000`)"))
            return
        try:
            amount = int(parts[1])
            settings = config.load_settings()
            settings["buy_amount"] = amount
            config.save_settings(settings)
            send_reply(reply_token, make_text_message(f"✅ 成功將每次下單金額設定為：{amount:,} 元。"))
        except ValueError:
            send_reply(reply_token, make_text_message("⚠️ 請輸入正確的整數金額。"))

    elif text.startswith("/mode"):
        parts = text.split()
        if len(parts) < 2 or parts[1].lower() not in ["live", "simulation"]:
            send_reply(reply_token, make_text_message("⚠️ 格式錯誤！正確格式為：\n`/mode [live/simulation]`\n(live: 實盤下單，simulation: 模擬交易)"))
            return
        
        mode_str = parts[1].lower()
        is_sim = mode_str == "simulation"
        
        settings = config.load_settings()
        settings["simulation_mode"] = is_sim
        config.save_settings(settings)
        
        mode_chinese = "模擬交易 (Simulation)" if is_sim else "🔥 正式實盤交易 (LIVE)"
        send_reply(reply_token, make_text_message(f"✅ 交易模式已成功切換為：\n{mode_chinese}\n\n*注意：若切換為實盤，請確保已在 .env 中填寫憑證密碼與身分證字號！*"))

    else:
        # 提示指令說明
        help_text = (
            "🙋‍♂️ 您好！我是抗重力投資助理機器人，您可以輸入以下指令來控制我：\n\n"
            "💬 `/status` ： 查詢目前帳戶餘額、庫存與 AI 市場點評。\n"
            "💬 `/set_sell [價格]` ： 設定高價賣出提示（例：`/set_sell 24.5`）。\n"
            "💬 `/set_buy [金額]` ： 設定每次定額購買預算（例：`/set_buy 5000`）。\n"
            "💬 `/mode [live/simulation]` ： 切換實盤或模擬交易。\n\n"
            "💡 我將會在每天盤中 09:30、12:30、13:30 自動看盤並通知您是否執行買賣喔！"
        )
        send_reply(reply_token, make_text_message(help_text))

def handle_postback_commands(reply_token: str, postback_data: str, user_id: str):
    """
    處理按鈕點擊，例如 action=buy&price=21.45 或 action=cancel
    """
    params = {}
    for item in postback_data.split("&"):
        if "=" in item:
            k, v = item.split("=", 1)
            params[k] = v
            
    action = params.get("action")
    
    if action == "cancel":
        send_reply(reply_token, make_text_message("❌ 已取消本次交易建議。我會繼續為您監控市場！"))
        return
        
    price = float(params.get("price", 0.0))
    if not price:
        send_reply(reply_token, make_text_message("⚠️ 錯誤：交易資料缺少價格資訊，無法執行。"))
        return
        
    if action == "buy":
        send_reply(reply_token, make_text_message("⏳ 收到指令，正在為您送出買入委託..."))
        result = broker.place_buy_order(price)
        
        if result["status"] == "SUCCESS":
            mode_name = "模擬" if config.is_simulation_mode() else "實盤"
            trade_logger.log_trade(
                action="BUY",
                price=price,
                shares=result["shares"],
                amount=result["total_cost"] if "total_cost" in result else (price * result["shares"]),
                message=result["message"],
                mode=mode_name
            )
            # 通知下單成功
            send_push(user_id, make_text_message(f"🎉 下單成功！\n{result['message']}"))
        else:
            send_push(user_id, make_text_message(f"❌ 買入交易失敗：\n{result['message']}"))
            
    elif action == "sell":
        send_reply(reply_token, make_text_message("⏳ 收到指令，正在為您送出賣出委託..."))
        result = broker.place_sell_order(price)
        
        if result["status"] == "SUCCESS":
            mode_name = "模擬" if config.is_simulation_mode() else "實盤"
            trade_logger.log_trade(
                action="SELL",
                price=price,
                shares=result["shares"],
                amount=result.get("revenue", price * result["shares"]),
                message=result["message"],
                mode=mode_name
            )
            send_push(user_id, make_text_message(f"🎉 賣出交易完成！\n{result['message']}"))
        else:
            send_push(user_id, make_text_message(f"❌ 賣出交易失敗：\n{result['message']}"))
