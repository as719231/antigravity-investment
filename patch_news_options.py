#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from core.us_data_provider import fetch_us_stock_analysis, fetch_institutional_data, fetch_market_indices

print("=== Testing AAPL analysis ===")
result = fetch_us_stock_analysis('AAPL', days=30)
if 'error' in result:
    print("ERROR:", result['error'])
else:
    m = result['metrics']
    print("close:", m['close'])
    print("RSI:", m['rsi'])
    print("K:", m['k'], "D:", m['d'])
    print("volatility:", m['volatility'])
    print("est_yield:", m['est_yield'])
    print("signals:", len(result['signals']))
    for s in result['signals']:
        print("  -", s['name'], s['type'])
    print("price_targets:", result['price_targets'])

print()
print("=== Testing institutional data ===")
inst = fetch_institutional_data('AAPL')
print("available:", inst.get('available'))
print("inst_pct:", inst.get('inst_pct'))
print("short_pct:", inst.get('short_pct'))
print("short_ratio:", inst.get('short_ratio'))

print()
print("=== Testing market indices ===")
indices = fetch_market_indices()
for k, v in indices.items():
    if v.get('success'):
        print(k, v['price'], v['change_pct'])
    else:
        print(k, "FAILED:", v.get('error',''))
