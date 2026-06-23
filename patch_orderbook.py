#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix order book HTML - replace table with div-flex"""

with open('app.py', encoding='utf-8') as f:
    content = f.read()

# Find the block to replace by unique anchors
START = '    if asks and bids:'
END   = '    st.markdown(f"""<div class="glass-card"'

idx_s = content.find(START)
idx_e = content.find(END, idx_s)
if idx_s < 0 or idx_e < idx_s:
    print(f"ERROR: START={idx_s} END={idx_e}")
else:
    old_block = content[idx_s:idx_e]
    print(f"Replacing {len(old_block)} chars from line ~{content[:idx_s].count(chr(10))+1}")

    new_block = """    if asks and bids:
        ask_rows_html = "".join(
            '<div style="display:flex;justify-content:space-between;padding:2px 0;">'
            '<span style="color:#10B981;font-size:0.72rem;font-family:monospace;">' + f'{p:.2f}' + '</span>'
            '<span style="color:#64748B;font-size:0.72rem;">' + f'{q}' + ' \u5f35</span></div>'
            for p, q in reversed(asks[:3])
        )
        bid_rows_html = "".join(
            '<div style="display:flex;justify-content:space-between;padding:2px 0;">'
            '<span style="color:#EF4444;font-size:0.72rem;font-family:monospace;">' + f'{p:.2f}' + '</span>'
            '<span style="color:#64748B;font-size:0.72rem;">' + f'{q}' + ' \u5f35</span></div>'
            for p, q in bids[:3]
        )
        ob_open  = '<div style="margin-top:10px;background:rgba(0,0,0,0.2);border-radius:8px;padding:8px 12px;">'
        ob_open += '<div style="display:flex;gap:16px;">'
        ob_sell  = '<div style="flex:1;"><div style="font-size:0.65rem;color:#64748B;font-weight:600;margin-bottom:3px;text-align:center;">\u8ce3\u51fa\u639b\u55ae</div>'
        ob_sep   = '</div><div style="width:1px;background:rgba(255,255,255,0.07);"></div>'
        ob_buy   = '<div style="flex:1;"><div style="font-size:0.65rem;color:#64748B;font-weight:600;margin-bottom:3px;text-align:center;">\u8cb7\u9032\u639b\u55ae</div>'
        ob_close = '</div></div></div>'
        order_book_html = ob_open + ob_sell + ask_rows_html + ob_sep + ob_buy + bid_rows_html + ob_close

"""
    # Fix the generator syntax (can't use f-string in generator with mixed quotes easily)
    # Use a proper approach
    new_block = '''    if asks and bids:
        def _ob_row(p, q, color):
            return (
                f\'<div style="display:flex;justify-content:space-between;padding:2px 0;">\' +
                f\'<span style="color:{color};font-size:0.72rem;font-family:monospace;">{p:.2f}</span>\' +
                f\'<span style="color:#64748B;font-size:0.72rem;">{q} \u5f35</span></div>\'
            )
        ask_rows_html = "".join(_ob_row(p, q, "#10B981") for p, q in reversed(asks[:3]))
        bid_rows_html = "".join(_ob_row(p, q, "#EF4444") for p, q in bids[:3])
        order_book_html = (
            \'<div style="margin-top:10px;background:rgba(0,0,0,0.2);border-radius:8px;padding:8px 12px;">\'
            \'<div style="display:flex;gap:16px;">\'
            \'<div style="flex:1;"><div style="font-size:0.65rem;color:#64748B;font-weight:600;margin-bottom:3px;text-align:center;">\u8ce3\u51fa\u639b\u55ae</div>\'
            + ask_rows_html +
            \'</div><div style="width:1px;background:rgba(255,255,255,0.07);"></div>\'
            \'<div style="flex:1;"><div style="font-size:0.65rem;color:#64748B;font-weight:600;margin-bottom:3px;text-align:center;">\u8cb7\u9032\u639b\u55ae</div>\'
            + bid_rows_html +
            \'</div></div></div>\'
        )

'''
    content = content[:idx_s] + new_block + content[idx_e:]
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Done: inserted {len(new_block)} chars")
