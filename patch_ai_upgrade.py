#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patch ai_agent.py:
1. Add indicators, macro, margin, fundamental parameters to get_system_instruction()
2. Add format functions to build new context blocks
3. Update generate_advisor_response() signature to pass new params
"""

with open('core/ai_agent.py', encoding='utf-8') as f:
    content = f.read()

# ── PATCH 1: Update function signature ─────────────────────────────
OLD_SIG = 'def get_system_instruction(selected_lang: str = "繁體中文", price_targets: dict = None, institutional: dict = None, stock_type: dict = None) -> str:'
NEW_SIG = 'def get_system_instruction(selected_lang: str = "繁體中文", price_targets: dict = None, institutional: dict = None, stock_type: dict = None, indicators: dict = None, macro: dict = None, margin: dict = None, fundamental: dict = None) -> str:'

if OLD_SIG in content:
    content = content.replace(OLD_SIG, NEW_SIG, 1)
    print('PATCH 1: signature updated')
else:
    print('ERROR: PATCH 1 signature not found')

# ── PATCH 2: Add new context blocks after type_ctx block ────────────
OLD_BLOCK = '''    instruction = f"""
你是一位溫暖、貼心、專業的「專屬 AI 股市理財專員」，負責輔助你的主人（Akira）進行理財規劃與股市分析。'''

NEW_BLOCK = '''    # 技術指標精確數值區塊
    ind_ctx = ""
    if indicators and indicators.get("available"):
        from core.indicator_extractor import format_indicators_for_ai
        stock_id_label = price_targets.get("stock_id", "") if price_targets else ""
        ind_ctx = format_indicators_for_ai(indicators, stock_id=stock_id_label)

    # 總體經濟環境區塊
    macro_ctx = ""
    if macro and macro.get("available"):
        from core.macro_provider import format_macro_for_ai
        macro_ctx = format_macro_for_ai(macro)

    # 融資融券區塊
    margin_ctx = ""
    if margin and margin.get("available"):
        from core.margin_provider import format_margin_for_ai
        stock_id_label = price_targets.get("stock_id", "") if price_targets else ""
        margin_ctx = format_margin_for_ai(margin, stock_id=stock_id_label)

    # 基本面數據區塊
    fund_ctx = ""
    if fundamental and fundamental.get("available"):
        from core.fundamental_provider import format_fundamental_for_ai
        stock_id_label = price_targets.get("stock_id", "") if price_targets else ""
        fund_ctx = format_fundamental_for_ai(fundamental, stock_id=stock_id_label)

    instruction = f"""
你是一位溫暖、貼心、專業的「專屬 AI 股市理財專員」，負責輔助你的主人（Akira）進行理財規劃與股市分析。'''

if OLD_BLOCK in content:
    content = content.replace(OLD_BLOCK, NEW_BLOCK, 1)
    print('PATCH 2: new context blocks added')
else:
    print('ERROR: PATCH 2 block not found')

# ── PATCH 3: Add new contexts into the instruction f-string ─────────
OLD_INJECT = '''{type_ctx}
"""

    # 將三層記憶注入'''

NEW_INJECT = '''{type_ctx}

{ind_ctx}

{macro_ctx}

{margin_ctx}

{fund_ctx}

【分析師指令】
你現在擁有完整的五維分析數據：技術面（精確指標數值）、籌碼面（法人+融資融券）、
基本面（EPS/ROE/毛利率）、總體經濟（VIX/費半/匯率）、個人持股狀況。
當主人詢問個股分析時，請盡量整合以上數據給出完整的多維度分析，
像一位資深分析師那樣，用精確的數字支撐你的每一個觀點。
"""

    # 將三層記憶注入'''

if OLD_INJECT in content:
    content = content.replace(OLD_INJECT, NEW_INJECT, 1)
    print('PATCH 3: context injection updated')
else:
    print('ERROR: PATCH 3 not found')
    idx = content.find('{type_ctx}')
    print(f'Found type_ctx at char {idx}')
    print(repr(content[idx:idx+150]))

# ── PATCH 4: Update generate_advisor_response signature ─────────────
OLD_GEN = 'def generate_advisor_response(chat_history: list, user_query: str, model_name: str = "gemini-2.5-flash", selected_lang: str = "繁體中文", price_targets: dict = None, institutional: dict = None, stock_type: dict = None) -> str:'
NEW_GEN = 'def generate_advisor_response(chat_history: list, user_query: str, model_name: str = "gemini-2.5-flash", selected_lang: str = "繁體中文", price_targets: dict = None, institutional: dict = None, stock_type: dict = None, indicators: dict = None, macro: dict = None, margin: dict = None, fundamental: dict = None) -> str:'

if OLD_GEN in content:
    content = content.replace(OLD_GEN, NEW_GEN, 1)
    print('PATCH 4: generate_advisor_response signature updated')
else:
    print('ERROR: PATCH 4 not found')

# ── PATCH 5: Update the internal call to get_system_instruction ─────
OLD_CALL = 'system_instruction=get_system_instruction(selected_lang, price_targets=price_targets, institutional=institutional, stock_type=stock_type),'
NEW_CALL = 'system_instruction=get_system_instruction(selected_lang, price_targets=price_targets, institutional=institutional, stock_type=stock_type, indicators=indicators, macro=macro, margin=margin, fundamental=fundamental),'

if OLD_CALL in content:
    content = content.replace(OLD_CALL, NEW_CALL, 1)
    print('PATCH 5: internal call updated')
else:
    print('ERROR: PATCH 5 not found')

with open('core/ai_agent.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Saved core/ai_agent.py')
