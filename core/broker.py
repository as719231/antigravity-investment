import os
import json
import logging
import shioaji as sj
import config
from datetime import datetime

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Broker")

# 本地模擬數據檔案路徑
MOCK_PORTFOLIO_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "mock_portfolio.json")

def load_mock_portfolio():
    """載入本地模擬帳戶資料"""
    if os.path.exists(MOCK_PORTFOLIO_FILE):
        try:
            with open(MOCK_PORTFOLIO_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    
    # 預設模擬資料
    default_mock = {
        "balance": 100000.0,  # 預設有 10 萬模擬金
        "holdings": {}        # 儲存結構: { "00878": { "shares": 0, "cost": 0.0 } }
    }
    save_mock_portfolio(default_mock)
    return default_mock

def save_mock_portfolio(data):
    """儲存本地模擬帳戶資料"""
    os.makedirs(os.path.dirname(MOCK_PORTFOLIO_FILE), exist_ok=True)
    with open(MOCK_PORTFOLIO_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


class ShioajiBroker:
    def __init__(self):
        self.api = None
        self.is_logged_in = False
        
    def _login(self):
        """嘗試登入真實 Shioaji API"""
        if self.is_logged_in:
            return True
            
        if not config.SHIOAJI_API_KEY or not config.SHIOAJI_SECRET_KEY:
            logger.error("缺少 Shioaji API Key 或 Secret Key！")
            return False
            
        try:
            # 建立 Shioaji API 實例 (實盤)
            self.api = sj.Shioaji(simulation=False)
            self.api.login(
                api_key=config.SHIOAJI_API_KEY,
                secret_key=config.SHIOAJI_SECRET_KEY
            )
            
            # 設定預設帳戶
            accounts = self.api.list_accounts()
            if accounts:
                self.api.set_default_account(accounts[0])
                logger.info("Shioaji 登入成功，預設帳戶: %s", accounts[0])
                
                # 啟用憑證
                if config.SHIOAJI_CA_PATH and os.path.exists(config.SHIOAJI_CA_PATH):
                    self.api.activate_ca(
                        ca_path=config.SHIOAJI_CA_PATH,
                        ca_passwd=config.SHIOAJI_CA_PASSWORD,
                        person_id=config.SHIOAJI_PERSON_ID
                    )
                    logger.info("憑證啟用成功。")
                else:
                    logger.warning("未設定憑證或憑證檔案不存在，下單功能將受限！")
                    
                self.is_logged_in = True
                return True
            else:
                logger.error("Shioaji 找不到證券帳戶。")
                return False
        except Exception as e:
            logger.error("Shioaji 登入出錯: %s", str(e))
            return False

    def get_account_status(self) -> dict:
        """
        取得目前帳戶狀態 (可用餘額與持股數量)
        """
        # --- 模擬模式 ---
        if config.is_simulation_mode():
            data = load_mock_portfolio()
            holding_info = data["holdings"].get(config.STOCK_ID, {"shares": 0, "cost": 0.0})
            return {
                "mode": "模擬交易 (Simulation)",
                "balance": data["balance"],
                "shares": holding_info["shares"],
                "avg_cost": holding_info["cost"]
            }
            
        # --- 實盤模式 ---
        if not self._login():
            return {"error": "無法登入券商系統"}
            
        try:
            # 1. 查詢可用餘額
            balance_info = self.api.account_balance(account=self.api.stock_account)
            balance = getattr(balance_info, 'acc_balance', 0.0)
            
            # 2. 查詢庫存
            positions = self.api.list_positions(self.api.stock_account)
            shares = 0
            avg_cost = 0.0
            
            for p in positions:
                if p.code == config.STOCK_ID:
                    shares = p.quantity
                    avg_cost = p.price
                    break
                    
            return {
                "mode": "實盤交易 (Live)",
                "balance": balance,
                "shares": shares,
                "avg_cost": avg_cost
            }
        except Exception as e:
            logger.error("查詢帳戶狀態出錯: %s", str(e))
            return {"error": str(e)}

    def place_buy_order(self, current_price: float) -> dict:
        """
        執行買入 5000 元 (以當前股價限價買入零股)
        """
        buy_amount = config.get_buy_amount()
        # 計算可買進的股數 (無條件捨去，留一點手續費緩衝)
        target_shares = int((buy_amount - 20) // current_price) # 扣除最低手續費 20 元
        
        if target_shares <= 0:
            return {"status": "FAILED", "message": f"金額 {buy_amount} 元不足以購買任何一股 (股價 {current_price} 元)"}

        # --- 模擬模式 ---
        if config.is_simulation_mode():
            data = load_mock_portfolio()
            total_cost = round(target_shares * current_price + 20, 2) # 加上模擬手續費 20
            
            if data["balance"] < total_cost:
                return {"status": "FAILED", "message": f"模擬帳戶餘額不足！需要 {total_cost} 元，剩餘 {data['balance']:.2f} 元"}
            
            # 更新餘額
            data["balance"] = round(data["balance"] - total_cost, 2)
            
            # 更新持股
            holding = data["holdings"].get(config.STOCK_ID, {"shares": 0, "cost": 0.0})
            old_shares = holding["shares"]
            old_cost = holding["cost"]
            
            new_shares = old_shares + target_shares
            # 平均成本加權
            new_cost = round(((old_shares * old_cost) + (target_shares * current_price)) / new_shares, 2)
            
            data["holdings"][config.STOCK_ID] = {
                "shares": new_shares,
                "cost": new_cost
            }
            save_mock_portfolio(data)
            
            return {
                "status": "SUCCESS",
                "shares": target_shares,
                "price": current_price,
                "total_cost": total_cost,
                "message": f"【模擬】成功以限價 {current_price} 元買入 {target_shares} 股 00878，扣除手續費共花費 {total_cost} 元。"
            }

        # --- 實盤模式 ---
        if not self._login():
            return {"status": "FAILED", "message": "無法登入券商系統"}
            
        try:
            # 取得商品合約
            contract = self.api.Contracts.Stocks[config.STOCK_ID]
            # 建立盤中零股買單 (以目前的 close 價掛限價單)
            order = self.api.Order(
                action=sj.constant.Action.Buy,
                price=current_price,
                quantity=target_shares,
                price_type=sj.constant.StockPriceType.LMT,
                order_type=sj.constant.OrderType.ROD,
                order_lot=sj.constant.StockOrderLot.IntradayOdd,
                account=self.api.stock_account
            )
            # 送出委託
            trade = self.api.place_order(contract, order)
            logger.info("送出買入委託: %s", trade)
            
            return {
                "status": "SUCCESS",
                "shares": target_shares,
                "price": current_price,
                "trade_id": getattr(trade.status, 'id', 'N/A'),
                "message": f"已成功向永豐金證券送出買單：限價 {current_price} 元買入 {target_shares} 股 00878 盤中零股。"
            }
        except Exception as e:
            logger.error("實盤下買單出錯: %s", str(e))
            return {"status": "FAILED", "message": f"下單失敗: {str(e)}"}

    def place_sell_order(self, current_price: float) -> dict:
        """
        執行賣出 (將目前持有的所有股數全數賣出)
        """
        # 1. 取得當前持股
        status = self.get_account_status()
        if "error" in status:
            return {"status": "FAILED", "message": f"無法取得庫存狀態：{status['error']}"}
            
        total_shares = status["shares"]
        if total_shares <= 0:
            return {"status": "FAILED", "message": "目前帳戶內無任何持股，無需執行賣出。"}

        # --- 模擬模式 ---
        if config.is_simulation_mode():
            data = load_mock_portfolio()
            revenue = round(total_shares * current_price - 20, 2) # 扣除手續費/稅費 20 元
            
            # 更新持股與餘額
            data["balance"] = round(data["balance"] + revenue, 2)
            data["holdings"][config.STOCK_ID] = {"shares": 0, "cost": 0.0}
            save_mock_portfolio(data)
            
            pnl = round(revenue - (total_shares * status["avg_cost"]), 2)
            
            return {
                "status": "SUCCESS",
                "shares": total_shares,
                "price": current_price,
                "revenue": revenue,
                "pnl": pnl,
                "message": f"【模擬】成功以限價 {current_price} 元賣出 {total_shares} 股 00878，得款 {revenue} 元，估計實現損益: {pnl} 元。"
            }

        # --- 實盤模式 ---
        if not self._login():
            return {"status": "FAILED", "message": "無法登入券商系統"}
            
        try:
            # 取得商品合約
            contract = self.api.Contracts.Stocks[config.STOCK_ID]
            # 建立盤中零股賣單
            order = self.api.Order(
                action=sj.constant.Action.Sell,
                price=current_price,
                quantity=total_shares,
                price_type=sj.constant.StockPriceType.LMT,
                order_type=sj.constant.OrderType.ROD,
                order_lot=sj.constant.StockOrderLot.IntradayOdd,
                account=self.api.stock_account
            )
            # 送出委託
            trade = self.api.place_order(contract, order)
            logger.info("送出賣出委託: %s", trade)
            
            return {
                "status": "SUCCESS",
                "shares": total_shares,
                "price": current_price,
                "trade_id": getattr(trade.status, 'id', 'N/A'),
                "message": f"已成功向永豐金證券送出賣單：限價 {current_price} 元賣出所有持股 {total_shares} 股 00878 盤中零股。"
            }
        except Exception as e:
            logger.error("實盤下賣單出錯: %s", str(e))
            return {"status": "FAILED", "message": f"賣單下單失敗: {str(e)}"}
