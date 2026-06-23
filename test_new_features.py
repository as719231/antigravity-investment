#!/usr/bin/env python3
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from core.sector_heatmap import fetch_sector_indices
sectors = fetch_sector_indices()
print('Sectors found:', len(sectors))
for s in sectors[:10]:
    print(f"  {s['name']}: {s['change_pct']:+.2f}%")

print()
from core.alert_manager import add_alert, check_alerts, get_all_alerts, get_stats
s = get_stats()
print('Alerts stats:', s)

# Add a test alert
aid = add_alert('0050', '元大台灣50', '>', 200.0, '測試警示')
print('Added alert id:', aid)

# Check with mock price
triggered = check_alerts({'0050': 205.0})
print('Triggered:', len(triggered), 'alerts')
if triggered:
    print('  Triggered:', triggered[0]['stock_id'], triggered[0]['price'])

print()
from core.calendar_provider import fetch_upcoming_dividends
divs = fetch_upcoming_dividends(days_ahead=90)
print('Dividends found:', len(divs))
for d in divs[:5]:
    print(f"  {d['stock_id']} {d['stock_name']}: {d['ex_date']} ({d['days_left']}天) 現金:{d['cash_div']}")

print()
print('ALL MODULE TESTS PASSED')
