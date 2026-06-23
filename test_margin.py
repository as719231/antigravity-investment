#!/usr/bin/env python3
import sys, io, requests
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
HEADERS = {'User-Agent': 'Mozilla/5.0'}

# Test 1: TWSE 個股融資融券 API
def test_margin(stock_id='0050'):
    url = f'https://www.twse.com.tw/rwd/zh/marginTrading/TWT93U?response=json&stockNo={stock_id}'
    r = requests.get(url, headers=HEADERS, timeout=10)
    print(f'Individual margin ({stock_id}): {r.status_code}')
    if r.ok:
        d = r.json()
        print('Keys:', list(d.keys()))
        print('stat:', d.get('stat'))
        rows = d.get('data', [])
        print('rows:', len(rows))
        if rows:
            print('fields:', d.get('fields', []))
            print('sample:', rows[-1])

# Test 2: TWSE 信用交易 by stock - using FinMind
def test_finmind_margin(stock_id='0050'):
    try:
        from FinMind.data import DataLoader
        import datetime
        dl = DataLoader()
        end = datetime.date.today().strftime('%Y-%m-%d')
        start = (datetime.date.today() - datetime.timedelta(days=30)).strftime('%Y-%m-%d')
        df = dl.taiwan_stock_margin_purchase_short_sale(
            stock_id=stock_id,
            start_date=start,
            end_date=end
        )
        print(f'FinMind margin ({stock_id}): {len(df)} rows')
        if not df.empty:
            print('Columns:', list(df.columns))
            print('Latest:', df.tail(2).to_string())
    except Exception as e:
        print(f'FinMind margin error: {e}')

test_margin('0050')
print()
test_finmind_margin('0050')
