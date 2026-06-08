import urllib.request
import json
import ssl
import re

def _fetch_tw_realtime_scrape(stock_id: str) -> dict:
    """
    爬取 Yahoo 奇摩股市 HTML 網頁，取得無延遲的即時成交價與漲跌幅
    """
    url = f"https://tw.stock.yahoo.com/quote/{stock_id}"
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    )
    try:
        context = ssl._create_unverified_context()
        with urllib.request.urlopen(req, context=context) as response:
            html = response.read().decode('utf-8')
            
            # 1. 抓取價格與趨勢方向
            price = None
            trend = "flat"
            price_match = re.search(r'class="[^"]*Fz\(32px\)[^"]*(C\(\$c-trend-\w+\))[^"]*">([^<]+)</span>', html)
            if price_match:
                trend_class = price_match.group(1)
                price = float(price_match.group(2).replace(",", ""))
                if "up" in trend_class:
                    trend = "up"
                elif "down" in trend_class:
                    trend = "down"
            else:
                price_match_simple = re.search(r'class="[^"]*Fz\(32px\)[^"]*">([^<]+)</span>', html)
                if price_match_simple:
                    price = float(price_match_simple.group(1).replace(",", ""))
            
            if price is None:
                return {"success": False, "error": "Price not found in HTML"}
                
            # 2. 抓取漲跌值
            change = 0.0
            change_match = re.search(r'class="[^"]*Fz\(20px\)[^"]*(C\(\$c-trend-\w+\))[^"]*">(?:<span[^>]*></span>)?\s*([^<]+)</span>', html)
            if change_match:
                change = float(change_match.group(2).replace(",", ""))
                if trend == "down":
                    change = -change
                    
            # 3. 抓取漲跌百分比
            change_percent = 0.0
            pct_match = re.search(r'class="[^"]*Fz\(20px\)[^"]*C\(\$c-trend-\w+\)[^"]*">\(([^%]+)%\)</span>', html)
            if pct_match:
                change_percent = float(pct_match.group(1))
                if trend == "down":
                    change_percent = -change_percent
                    
            # 4. 反推昨收價
            prev_close = price - change
            
            return {
                "success": True,
                "price": round(price, 2),
                "prev_close": round(prev_close, 2),
                "change": round(change, 2),
                "change_percent": round(change_percent, 2),
                "currency": "TWD",
                "symbol": f"{stock_id}.TW"
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


def fetch_realtime_price(stock_id: str) -> dict:
    """
    從 Yahoo Finance 抓取指定台股代號的盤中即時成交價與漲跌幅
    對於台股優先採用奇摩網頁解析（取得無延遲價格），若失敗或非台股則以 JSON API 做為備用
    """
    clean_id = stock_id.strip()
    
    # 如果是台股（純數字），優先進行網頁即時報價解析
    if clean_id.isdigit():
        res = _fetch_tw_realtime_scrape(clean_id)
        if res.get("success"):
            return res
            
    # --- 備用方案：使用 Yahoo Chart JSON API ---
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
