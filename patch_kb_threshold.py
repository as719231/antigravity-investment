#!/usr/bin/env python3
"""Fix KB auto-save threshold"""
with open('core/knowledge_base.py', encoding='utf-8') as f:
    c = f.read()

c = c.replace(
    'if len(ai_text) < 150:\n        return   # \u56de\u7b54\u592a\u77ed\uff0c\u4e0d\u5024\u5f97\u5b58',
    'if len(ai_text) < 80:\n        return   # \u4e2d\u6587 80 \u5b57 \u2248 \u82f1\u6587 150 \u5b57\uff0c\u4e0d\u5024\u5f97\u5b58'
)
with open('core/knowledge_base.py', 'w', encoding='utf-8') as f:
    f.write(c)
print("Fixed threshold to 80")
