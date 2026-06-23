#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Patch app.py Phase 3: inject stock_id + real-time price into price_targets"""

with open('app.py', encoding='utf-8') as f:
    content = f.read()

# Find anchor after stock_type line
ANCHOR = 'stock_type     = analysis.get("stock_type",     {})   # \u80a1\u7968\u985e\u578b\u81ea\u52d5\u5224\u5b9a\u7d50\u679c'

if ANCHOR not in content:
    print("ERROR: anchor not found")
else:
    INSERT = '''
# \u2500\u2500 \u5c07 stock_id \u6ce8\u5165 price_targets\uff08\u4f9b\u8a18\u61b6\u7cfb\u7d71\u6a19\u8a18\u7528\uff09\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
price_targets["stock_id"] = stock_id

# \u2500\u2500 \u6ce8\u5165\u5373\u6642\u5831\u50f9\u5230 price_targets\uff08AI \u6c38\u9060\u77e5\u9053\u6700\u65b0\u50f9\u683c\uff09\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
try:
    from core.realtime_provider import fetch_realtime_price as _fetch_rt
    _rt_now = _fetch_rt(stock_id)
    if _rt_now.get("success"):
        price_targets["realtime_price"]    = _rt_now["price"]
        price_targets["realtime_change"]   = _rt_now.get("change", 0)
        price_targets["realtime_pct"]      = _rt_now.get("change_percent", 0)
        price_targets["realtime_time"]     = _rt_now.get("update_time", "--")
        price_targets["realtime_source"]   = _rt_now.get("source", "")
        price_targets["realtime_intraday"] = _rt_now.get("is_intraday", False)
except Exception:
    pass  # \u5373\u6642\u5831\u50f9\u5931\u6557\u4e0d\u5f71\u97ff\u4e3b\u8981\u5206\u6790\u6d41\u7a0b
'''
    content = content.replace(ANCHOR, ANCHOR + INSERT, 1)
    print("Injected stock_id + realtime into price_targets")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Done")
