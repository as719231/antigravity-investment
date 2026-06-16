#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Find where the CSS block ends in app.py"""

with open('app.py', encoding='utf-8') as f:
    content = f.read()

# Find the big CSS closing tag inside app.py
idx = content.find('</style>\n    """')
if idx >= 0:
    line_no = content[:idx].count('\n') + 1
    print(f"Found </style> closing at line ~{line_no}")
    print("Context:", repr(content[idx-50:idx+30]))
else:
    # Try alternative
    idx2 = content.find('</style>')
    if idx2 >= 0:
        line_no = content[:idx2].count('\n') + 1
        print(f"Found </style> at line ~{line_no}")
        print("Context:", repr(content[idx2-30:idx2+50]))
    else:
        print("No </style> found at all!")
