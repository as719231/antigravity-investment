#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patch app.py:
1. Add new data fetching (indicators, macro, margin, fundamental) before the chat tab
2. Update all generate_advisor_response() calls to pass new params
"""

with open('app.py', encoding='utf-8') as f:
    content = f.read()

# ── PATCH A: Add data fetching before first generate_advisor_response call ──────
# Find the spinner+call block and insert fetching before it
OLD_FETCH = '''        # 呼叫理財專員 API
        with st.spinner(LANG_DICT[selected_lang]["chat_spinner"]):
            from core.ai_agent import generate_advisor_response
            response_text = generate_advisor_response(
                st.session_state.chat_history[:-1], 
                user_query, 
                model_name=selected_model_name,
                selected_lang=selected_lang,
                price_targets=price_targets,
                institutional=institutional,
                stock_type=stock_type
            )'''

NEW_FETCH = '''        # ── 準備分析數據（技術指標/總經/融資融券/基本面）──
        _ai_indicators  = None
        _ai_macro       = None
        _ai_margin      = None
        _ai_fundamental = None

        _current_stock_id = price_targets.get("stock_id", stock_id) if price_targets else stock_id
        try:
            # 任務1：技術指標精確數值（從已下載的 K 線算）
            from core.pattern_detector import fetch_stock_data
            from core.indicator_extractor import extract_technical_indicators
            _df_for_ai = fetch_stock_data(_current_stock_id, days=120)
            if not _df_for_ai.empty:
                _ai_indicators = extract_technical_indicators(_df_for_ai)
        except Exception:
            pass

        try:
            # 任務2：總體經濟（VIX/SOX/台幣/美股）
            from core.macro_provider import fetch_macro_context
            _ai_macro = fetch_macro_context()
        except Exception:
            pass

        try:
            # 任務3：融資融券
            from core.margin_provider import fetch_margin_data
            _ai_margin = fetch_margin_data(_current_stock_id)
        except Exception:
            pass

        try:
            # 任務4：基本面（EPS/ROE/毛利率/PE）
            from core.fundamental_provider import fetch_fundamentals, fetch_monthly_revenue
            _fund = fetch_fundamentals(_current_stock_id)
            _rev  = fetch_monthly_revenue(_current_stock_id)
            if _fund.get("available"):
                _fund["monthly_revenue"] = _rev
                _ai_fundamental = _fund
        except Exception:
            pass

        # 呼叫理財專員 API
        with st.spinner(LANG_DICT[selected_lang]["chat_spinner"]):
            from core.ai_agent import generate_advisor_response
            response_text = generate_advisor_response(
                st.session_state.chat_history[:-1], 
                user_query, 
                model_name=selected_model_name,
                selected_lang=selected_lang,
                price_targets=price_targets,
                institutional=institutional,
                stock_type=stock_type,
                indicators=_ai_indicators,
                macro=_ai_macro,
                margin=_ai_margin,
                fundamental=_ai_fundamental
            )'''

if OLD_FETCH in content:
    content = content.replace(OLD_FETCH, NEW_FETCH, 1)
    print('PATCH A: data fetching + main call updated')
else:
    print('ERROR: PATCH A not found')

# ── PATCH B: Update shortcut Q1 call ────────────────────────────────
OLD_Q1 = '''                resp = generate_advisor_response(
                    st.session_state.chat_history[:-1], 
                    q1_text, 
                    model_name=selected_model_name,
                    selected_lang=selected_lang,
                    price_targets=price_targets,
                    institutional=institutional,
                    stock_type=stock_type
                )
                st.session_state.chat_history.append({"role": "model", "text": resp})
            st.rerun()
            
    with c_q2:'''

NEW_Q1 = '''                resp = generate_advisor_response(
                    st.session_state.chat_history[:-1], 
                    q1_text, 
                    model_name=selected_model_name,
                    selected_lang=selected_lang,
                    price_targets=price_targets,
                    institutional=institutional,
                    stock_type=stock_type,
                    indicators=_ai_indicators if "_ai_indicators" in dir() else None,
                    macro=_ai_macro if "_ai_macro" in dir() else None,
                    margin=_ai_margin if "_ai_margin" in dir() else None,
                    fundamental=_ai_fundamental if "_ai_fundamental" in dir() else None
                )
                st.session_state.chat_history.append({"role": "model", "text": resp})
            st.rerun()
            
    with c_q2:'''

if OLD_Q1 in content:
    content = content.replace(OLD_Q1, NEW_Q1, 1)
    print('PATCH B: Q1 shortcut updated')
else:
    print('ERROR: PATCH B not found')

# ── PATCH C: Update shortcut Q2 call ────────────────────────────────
OLD_Q2 = '''                resp = generate_advisor_response(
                    st.session_state.chat_history[:-1], 
                    q2_text, 
                    model_name=selected_model_name,
                    selected_lang=selected_lang,
                    price_targets=price_targets,
                    institutional=institutional,
                    stock_type=stock_type
                )
                st.session_state.chat_history.append({"role": "model", "text": resp})
            st.rerun()
            
    with c_q3:'''

NEW_Q2 = '''                resp = generate_advisor_response(
                    st.session_state.chat_history[:-1], 
                    q2_text, 
                    model_name=selected_model_name,
                    selected_lang=selected_lang,
                    price_targets=price_targets,
                    institutional=institutional,
                    stock_type=stock_type,
                    indicators=_ai_indicators if "_ai_indicators" in dir() else None,
                    macro=_ai_macro if "_ai_macro" in dir() else None,
                    margin=_ai_margin if "_ai_margin" in dir() else None,
                    fundamental=_ai_fundamental if "_ai_fundamental" in dir() else None
                )
                st.session_state.chat_history.append({"role": "model", "text": resp})
            st.rerun()
            
    with c_q3:'''

if OLD_Q2 in content:
    content = content.replace(OLD_Q2, NEW_Q2, 1)
    print('PATCH C: Q2 shortcut updated')
else:
    print('ERROR: PATCH C not found')

# ── PATCH D: Update shortcut Q3 call ────────────────────────────────
OLD_Q3 = '''                resp = generate_advisor_response(
                    st.session_state.chat_history[:-1], 
                    q3_text, 
                    model_name=selected_model_name,
                    selected_lang=selected_lang,
                    price_targets=price_targets,
                    institutional=institutional,
                    stock_type=stock_type
                )
                st.session_state.chat_history.append({"role": "model", "text": resp})
            st.rerun()'''

NEW_Q3 = '''                resp = generate_advisor_response(
                    st.session_state.chat_history[:-1], 
                    q3_text, 
                    model_name=selected_model_name,
                    selected_lang=selected_lang,
                    price_targets=price_targets,
                    institutional=institutional,
                    stock_type=stock_type,
                    indicators=_ai_indicators if "_ai_indicators" in dir() else None,
                    macro=_ai_macro if "_ai_macro" in dir() else None,
                    margin=_ai_margin if "_ai_margin" in dir() else None,
                    fundamental=_ai_fundamental if "_ai_fundamental" in dir() else None
                )
                st.session_state.chat_history.append({"role": "model", "text": resp})
            st.rerun()'''

if OLD_Q3 in content:
    content = content.replace(OLD_Q3, NEW_Q3, 1)
    print('PATCH D: Q3 shortcut updated')
else:
    print('ERROR: PATCH D not found')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Saved app.py')
