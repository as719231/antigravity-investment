#!/usr/bin/env python3
import sys, io, requests
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

HEADERS = {'User-Agent': 'Mozilla/5.0'}

# The working one earlier had strDate=1140601&endDate=1140831 - let's try the exact same
url = 'https://www.twse.com.tw/rwd/zh/exRight/TWT49U?response=json&strDate=1140601&endDate=1140831'
r = requests.get(url, headers=HEADERS, timeout=10)
print('Test with 1140601-1140831:', r.status_code)
d = r.json()
print('Stat:', d.get('stat'))
print('Rows:', len(d.get('data', [])))

# The previous test ran with no strDate/endDate and got 18 rows - let's use just today + 90 days
# with the specific format that worked: 115xxxx
import datetime
now = datetime.date.today()
print('Today:', now, 'ROC year:', now.year - 1911)

# Try without any date param first
url2 = 'https://www.twse.com.tw/rwd/zh/exRight/TWT49U?response=json'
r2 = requests.get(url2, headers=HEADERS, timeout=10)
print()
print('No-date URL:', r2.status_code)
d2 = r2.json()
print('Stat2:', d2.get('stat'))
print('Rows2:', len(d2.get('data', [])))
if d2.get('data'):
    print('Fields:', d2.get('fields'))
    for row in d2['data'][:3]:
        print('  ', row[:7])

# The working test had exact URL format from test_sector_api.py earlier:
# https://www.twse.com.tw/rwd/zh/exRight/TWT49U?response=json&strDate=1140601&endDate=1140831
# but that returned 'stat=查詢結束日期小於92年5月5日' 
# The ONE that worked returned 18 rows was the NO-DATE version! Let's check again
