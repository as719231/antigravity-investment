#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix Unicode issue in patch_memory_ui"""

with open('app.py', encoding='utf-8') as f:
    content = f.read()

# Fix the problematic join lines
# The issue is Chinese character used as separator in f-string
OLD1 = "st.caption(f\"\u5e38\u770b\u80a1\u7968\uff1a{\u3001.join(f'{s}({n}\u6b21)' for s,n in top_stocks_list)}\")"
NEW1 = "st.caption(\"\u5e38\u770b\u80a1\u7968\uff1a\" + \"\u3001\".join(f\"{s}({n}\u6b21)\" for s,n in top_stocks_list))"

OLD2 = "st.caption(f\"\u6163\u7528\u6307\u6a19\uff1a{\u3001.join(indicators_list[:6])}\")"
NEW2 = "st.caption(\"\u6163\u7528\u6307\u6a19\uff1a\" + \"\u3001\".join(indicators_list[:6]))"

if OLD1 in content:
    content = content.replace(OLD1, NEW1, 1)
    print("Fixed caption 1")
else:
    # Try to find by partial match
    idx = content.find('\u3001.join(f\'{s}({n}\u6b21)\'')
    if idx < 0:
        idx = content.find("join(f'{s}({n}")
    print(f"Searching for join pattern at {idx}")
    if idx >= 0:
        # Find the full line
        line_start = content.rfind('\n', 0, idx) + 1
        line_end   = content.find('\n', idx)
        print(f"  Line: {repr(content[line_start:line_end])}")

if OLD2 in content:
    content = content.replace(OLD2, NEW2, 1)
    print("Fixed caption 2")
else:
    idx2 = content.find("\u3001.join(indicators_list")
    print(f"Caption 2 search at {idx2}")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Done")
