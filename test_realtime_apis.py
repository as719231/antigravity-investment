#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test TWSE and alternative real-time APIs"""
import sys, io, json, urllib.request, ssl
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ctx = ssl._create_unverified_context()

# Test 1: TWSE official API
print("=== Test 1: TWSE Official API ===")
try:
    url = 'https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_0050.tw&json=1&delay=0'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
        data = json.loads(r.read())
    print(json.dumps(data, indent=2, ensure_ascii=False)[:1500])
except Exception as e:
    print(f"TWSE API failed: {e}")

# Test 2: TWSE Alternative (TPEx for OTC)
print("\n=== Test 2: MIS TWSE for 6282 (OTC) ===")
try:
    url2 = 'https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=otc_6282.tw&json=1&delay=0'
    req2 = urllib.request.Request(url2, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req2, context=ctx, timeout=8) as r2:
        data2 = json.loads(r2.read())
    print(json.dumps(data2, indent=2, ensure_ascii=False)[:1000])
except Exception as e:
    print(f"OTC API failed: {e}")

# Test 3: Yahoo Finance v8 API (checking marketState)
print("\n=== Test 3: Yahoo Finance v8 for 0050.TW ===")
try:
    url3 = 'https://query1.finance.yahoo.com/v8/finance/chart/0050.TW?interval=1m&range=1d'
    req3 = urllib.request.Request(url3, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req3, context=ctx, timeout=8) as r3:
        data3 = json.loads(r3.read())
    meta = data3['chart']['result'][0]['meta']
    print(f"price: {meta.get('regularMarketPrice')}")
    print(f"prevClose: {meta.get('previousClose')}")
    print(f"marketState: {meta.get('marketState')}")
    print(f"regularMarketTime: {meta.get('regularMarketTime')}")
except Exception as e:
    print(f"Yahoo v8 failed: {e}")
