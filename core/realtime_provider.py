import urllib.request
import json
import ssl

def fetch_realtime_price(stock_id: str) -> dict:
    """
    從 Yahoo Finance API 抓取指定台股代號的盤中即時成交價與漲跌幅
    """
    # 整理代號格式：若為純數字（例如 2330），自動加上 .TW 字尾
    clean_id = stock_id.strip()
    if clean_id.isdigit():
        symbol = f"{clean_id}.TW"
    else:
        symbol = clean_id
        
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    )
    
    try:
        # 忽略 SSL 憑證驗證，確保在各種 Python 環境下皆可正常請求
        context = ssl._create_unverified_context()
        with urllib.request.urlopen(req, context=context) as response:
            data = json.loads(response.read().decode('utf-8'))
            if not data.get('chart', {}).get('result'):
                return {"success": False, "error": "No result found"}
                
            meta = data['chart']['result'][0]['meta']
            price = meta.get('regularMarketPrice')
            prev_close = meta.get('previousClose')
            
            if price is None or prev_close is None:
                # 嘗試從 indicators 取得最新的成交價
                try:
                    quotes = data['chart']['result'][0]['indicators']['quote'][0]
                    closes = [c for c in quotes.get('close', []) if c is not None]
                    if closes:
                        price = closes[-1]
                except Exception:
                    pass
            
            if price is None:
                return {"success": False, "error": "Price not available"}
                
            # 計算漲跌幅
            prev_close_val = prev_close if prev_close else price
            change = price - prev_close_val
            change_percent = (change / prev_close_val) * 100 if prev_close_val else 0.0
            
            return {
                "success": True,
                "price": round(price, 2),
                "prev_close": round(prev_close_val, 2),
                "change": round(change, 2),
                "change_percent": round(change_percent, 2),
                "currency": meta.get('currency', 'TWD'),
                "symbol": symbol
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
