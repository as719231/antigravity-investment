#!/usr/bin/env python3
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Test fundamentals via yfinance for Taiwan stocks
import yfinance as yf, warnings
warnings.filterwarnings('ignore')

tickers = ['0050.TW', '2330.TW', '6282.TW']
for ticker in tickers:
    try:
        t = yf.Ticker(ticker)
        info = t.info
        print(f'=== {ticker} ===')
        keys = ['trailingEps', 'forwardEps', 'trailingPE', 'forwardPE',
                'returnOnEquity', 'grossMargins', 'operatingMargins',
                'revenueGrowth', 'earningsGrowth', 'debtToEquity',
                'currentPrice', 'fiftyTwoWeekHigh', 'fiftyTwoWeekLow',
                'marketCap', 'dividendYield', 'payoutRatio']
        for k in keys:
            v = info.get(k)
            if v is not None:
                print(f'  {k}: {v}')
        print()
    except Exception as e:
        print(f'{ticker}: {e}')
        print()
