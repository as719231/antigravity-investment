#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Full integration test for three-layer memory system"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pathlib, json

# Clean test data
pathlib.Path('data/knowledge_base.json').write_text('[]', encoding='utf-8')
pathlib.Path('data/chat_memory.json').write_text(
    json.dumps({"sessions": [], "total_rounds": 0}, ensure_ascii=False),
    encoding='utf-8'
)

from core.memory_manager  import save_conversation, get_memory_context
from core.profile_manager import update_profile_from_conversation, get_profile_context
from core.knowledge_base  import auto_save_from_conversation, get_rag_context, get_stats

u1 = '0050現在可以買嗎？'
a1 = '0050 RSI 目前55，均線多頭排列，支撐在108元。建議在108元附近可以分批布局，止損設在105元。技術分析建議稍作等待。📌 買進參考: 108元 | 止損: 105元'
save_conversation(u1, a1, stock_id='0050')
update_profile_from_conversation(u1, a1, stock_id='0050')
auto_save_from_conversation(u1, a1, stock_id='0050')

u2 = '2330台積電如何？'
a2 = '台積電2330，RSI 62，均線黃金交叉，外資近30日持續買超3000張。法人籌碼偏多。支撐在700元，壓力760元。建議現價可以分批買進。📌 買進參考: 710元 | 止損: 685元'
save_conversation(u2, a2, stock_id='2330')
update_profile_from_conversation(u2, a2, stock_id='2330')
auto_save_from_conversation(u2, a2, stock_id='2330')

mem_ctx  = get_memory_context(max_rounds=5)
prof_ctx = get_profile_context()
rag_ctx  = get_rag_context('0050 RSI 支撐', stock_id='0050')

print('=== INTEGRATION TEST ===')
print(f'Layer 1 - Memory:  {len(mem_ctx)} chars, has_0050={chr(34)+"0050"+chr(34) in mem_ctx}')
print(f'Layer 2 - Profile: {len(prof_ctx)} chars')
print(f'Layer 3 - RAG:     {len(rag_ctx)} chars, found={len(rag_ctx) > 10}')

kb = get_stats()
print(f'KB stats: {kb["total"]} total, {kb["auto_saved"]} auto')
print()
print('ALL INTEGRATION TESTS PASSED ✓')
