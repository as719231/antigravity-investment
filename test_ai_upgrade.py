#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Full integration test: all 4 new AI data providers"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print('=' * 60)
print('AI 分析師升級 — 全面整合測試')
print('=' * 60)

STOCK = '2330'

# ── 任務 1: 技術指標 ───────────────────────────────────────────
print('\n[Task 1] 技術指標精確數值注入...')
try:
    from core.pattern_detector import fetch_stock_data
    from core.indicator_extractor import extract_technical_indicators, format_indicators_for_ai
    df = fetch_stock_data(STOCK, days=120)
    ind = extract_technical_indicators(df)
    print(f'  RSI: {ind.get("rsi")} → {ind.get("rsi_label")}')
    print(f'  KD: K={ind.get("k_val")} D={ind.get("d_val")} → {ind.get("kd_cross")}')
    print(f'  MACD: {ind.get("macd_label")}')
    print(f'  Boll: {ind.get("boll_label")}')
    print(f'  Volume: {ind.get("vol_label")}')
    txt = format_indicators_for_ai(ind, STOCK)
    print(f'  Prompt text: {len(txt)} chars')
    print('  ✅ 任務 1 PASS')
except Exception as e:
    print(f'  ❌ 任務 1 FAIL: {e}')

# ── 任務 2: 總體經濟 ──────────────────────────────────────────
print('\n[Task 2] 總體經濟環境（VIX/SOX/台幣）...')
try:
    from core.macro_provider import fetch_macro_context, format_macro_for_ai
    macro = fetch_macro_context()
    if macro.get('available'):
        vix = macro.get('vix', {})
        sox = macro.get('sox', {})
        twd = macro.get('usd_twd', {})
        print(f'  VIX: {vix.get("price", "N/A"):.2f} → {macro.get("vix_level")}')
        print(f'  SOX: {sox.get("price", "N/A"):,.2f} → {macro.get("sox_trend")}')
        print(f'  USD/TWD: {twd.get("price", "N/A"):.3f} → {macro.get("twd_trend")}')
        txt = format_macro_for_ai(macro)
        print(f'  Prompt text: {len(txt)} chars')
        print('  ✅ 任務 2 PASS')
    else:
        print('  ⚠️ 任務 2 PARTIAL: macro not available')
except Exception as e:
    print(f'  ❌ 任務 2 FAIL: {e}')

# ── 任務 3: 融資融券 ──────────────────────────────────────────
print('\n[Task 3] 融資融券籌碼數據...')
try:
    from core.margin_provider import fetch_margin_data, format_margin_for_ai
    margin = fetch_margin_data(STOCK)
    if margin.get('available'):
        print(f'  融資餘額: {margin["margin_balance"]:,} 張 ({margin["margin_change"]:+,})')
        print(f'  融資5日: {margin["margin_change_5d"]:+,} 張 → {margin["margin_trend"]}')
        print(f'  融券餘額: {margin["short_balance"]:,} 張 → {margin["short_trend"]}')
        txt = format_margin_for_ai(margin, STOCK)
        print(f'  Prompt text: {len(txt)} chars')
        print('  ✅ 任務 3 PASS')
    else:
        print('  ⚠️ 任務 3: not available (FinMind may need token)')
except Exception as e:
    print(f'  ❌ 任務 3 FAIL: {e}')

# ── 任務 4: 基本面 ─────────────────────────────────────────────
print('\n[Task 4] 基本面數據（EPS/ROE/毛利率）...')
try:
    from core.fundamental_provider import fetch_fundamentals, fetch_monthly_revenue, format_fundamental_for_ai
    fund = fetch_fundamentals(STOCK)
    rev  = fetch_monthly_revenue(STOCK)
    if fund.get('available'):
        print(f'  EPS(trailing): {fund.get("trailing_eps")} 元')
        print(f'  PE: {fund.get("trailing_pe")}x → {fund.get("pe_status")}')
        print(f'  ROE: {fund.get("roe_pct")}%')
        print(f'  毛利率: {fund.get("gross_margin_pct")}%')
        print(f'  營收年增率: {fund.get("revenue_growth_pct")}%')
        print(f'  殖利率: {fund.get("dividend_yield_pct")}%')
        print(f'  52週位置: {fund.get("position_52w_pct")}% → {fund.get("position_52w_label")}')
        if rev.get('available'):
            print(f'  月營收: {rev.get("months")} - {rev.get("revenues")}')
        txt = format_fundamental_for_ai(fund, rev, STOCK)
        print(f'  Prompt text: {len(txt)} chars')
        print('  ✅ 任務 4 PASS')
    else:
        print('  ⚠️ 任務 4: not available')
except Exception as e:
    print(f'  ❌ 任務 4 FAIL: {e}')

# ── 模組編譯驗證 ───────────────────────────────────────────────
print('\n[Compile Check] 所有模組...')
import subprocess
mods = ['core/ai_agent.py', 'core/indicator_extractor.py',
        'core/macro_provider.py', 'core/margin_provider.py',
        'core/fundamental_provider.py', 'app.py']
all_ok = True
for m in mods:
    r = subprocess.run(['python', '-m', 'py_compile', m], capture_output=True, text=True)
    if r.returncode == 0:
        print(f'  ✅ {m}')
    else:
        print(f'  ❌ {m}: {r.stderr}')
        all_ok = False

print()
print('=' * 60)
print('測試完成！' if all_ok else '有部分測試失敗，請檢查')
print('=' * 60)
