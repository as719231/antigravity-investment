#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patch 1: 升級台股看盤分頁 (app.py)
在法人分析面板之後，插入：
  A) MACD + 布林通道 + 成交量深度指標面板
  B) 基本面快速面板 (PE / ROE / 毛利率 / EPS / 殖利率)
  C) 融資融券趨勢面板
"""

with open('app.py', encoding='utf-8') as f:
    content = f.read()

# ── 插入點：法人面板結束後，熱圖開始前 ─────────────────────────────
ANCHOR = '''# ==============================================================================
# 🚨 價格警示檢查（每次頁面重載時自動比對）'''

NEW_PANELS = '''# ==============================================================================
# 📈 深度技術指標面板 + 基本面 + 融資融券（注入台股看盤分頁）
# ==============================================================================
with tab_market:
    # ── A: MACD / 布林 / 成交量深度面板 ─────────────────────────
    try:
        from core.indicator_extractor import extract_technical_indicators
        _ind = extract_technical_indicators(df)
        if _ind.get("available"):
            st.markdown("---")
            st.markdown("#### 📊 深度技術指標")

            _ic1, _ic2, _ic3 = st.columns(3)

            # MACD
            _macd_hist = _ind.get("macd_hist", 0)
            _macd_color = "#EF4444" if _macd_hist >= 0 else "#10B981"
            _macd_sign  = "▲" if _macd_hist >= 0 else "▼"
            with _ic1:
                st.markdown(f"""<div class="glass-card" style="padding:14px; border-left:4px solid {_macd_color};">
<div style="font-size:0.72rem; color:#94A3B8; font-weight:600;">MACD</div>
<div style="font-size:0.95rem; font-weight:700; color:{_macd_color}; margin:4px 0;">DIF {_ind['macd']:+.3f}</div>
<div style="font-size:0.78rem; color:#94A3B8;">DEA {_ind['macd_signal']:+.3f} | 柱 {_macd_sign}{abs(_macd_hist):.3f}</div>
<div style="font-size:0.72rem; color:#64748B; margin-top:4px;">{_ind['macd_label'][:18]}</div>
</div>""", unsafe_allow_html=True)

            # 布林通道
            _boll_pos = _ind.get("boll_label", "")
            _boll_color = "#EF4444" if "上軌" in _boll_pos else "#10B981" if "下軌" in _boll_pos else "#F59E0B"
            with _ic2:
                st.markdown(f"""<div class="glass-card" style="padding:14px; border-left:4px solid {_boll_color};">
<div style="font-size:0.72rem; color:#94A3B8; font-weight:600;">布林通道 (20,2σ)</div>
<div style="font-size:0.95rem; font-weight:700; color:#F8FAFC; margin:4px 0;">上軌 {_ind['boll_upper']}</div>
<div style="font-size:0.78rem; color:#94A3B8;">中軌 {_ind['boll_mid']} | 下軌 {_ind['boll_lower']}</div>
<div style="font-size:0.72rem; color:{_boll_color}; margin-top:4px;">{_ind.get('boll_label','')[:20]}</div>
</div>""", unsafe_allow_html=True)

            # 成交量
            _vol_label = _ind.get("vol_label", "")
            _vol_color = "#F59E0B" if "爆量" in _vol_label else "#6366F1" if "放量" in _vol_label else "#10B981" if "縮量" in _vol_label else "#94A3B8"
            with _ic3:
                _vol_disp = f"{_ind['volume']:,}" if _ind.get('volume') else "--"
                _vma_disp = f"{_ind['vol_ma20']:,}" if _ind.get('vol_ma20') else "--"
                st.markdown(f"""<div class="glass-card" style="padding:14px; border-left:4px solid {_vol_color};">
<div style="font-size:0.72rem; color:#94A3B8; font-weight:600;">成交量 vs 均量</div>
<div style="font-size:0.95rem; font-weight:700; color:#F8FAFC; margin:4px 0;">{_vol_disp} 張</div>
<div style="font-size:0.78rem; color:#94A3B8;">20日均量 {_vma_disp} 張</div>
<div style="font-size:0.72rem; color:{_vol_color}; margin-top:4px;">{_vol_label[:20]}</div>
</div>""", unsafe_allow_html=True)

            # 均線排列
            _ma_color = "#EF4444" if "多頭" in _ind.get("ma_trend","") else "#10B981" if "空頭" in _ind.get("ma_trend","") else "#F59E0B"
            st.markdown(f"""<div style="margin-top:8px; padding:8px 14px; background:rgba(30,41,59,0.5); border-radius:8px; font-size:0.8rem; color:{_ma_color};">
📐 <b>均線排列</b>：{_ind.get('ma_trend','')} &nbsp;｜&nbsp; MA5={_ind.get('ma5','--')} &nbsp; MA20={_ind.get('ma20','--')} &nbsp; MA60={_ind.get('ma60','--')}
</div>""", unsafe_allow_html=True)

    except Exception as _te:
        pass

    # ── B: 基本面快速面板 ─────────────────────────────────────────
    try:
        from core.fundamental_provider import fetch_fundamentals, fetch_monthly_revenue
        _fund = fetch_fundamentals(stock_id)
        if _fund.get("available"):
            st.markdown("---")
            st.markdown("#### 💰 基本面速覽")

            _fc1, _fc2, _fc3, _fc4, _fc5 = st.columns(5)

            def _fund_card(col, title, value, sublabel, color="#F8FAFC"):
                col.markdown(f"""<div class="glass-card" style="padding:12px; text-align:center;">
<div style="font-size:0.68rem; color:#94A3B8;">{title}</div>
<div style="font-size:1.1rem; font-weight:800; color:{color}; margin:4px 0;">{value}</div>
<div style="font-size:0.68rem; color:#64748B;">{sublabel}</div>
</div>""", unsafe_allow_html=True)

            # PE
            pe_val = _fund.get("trailing_pe")
            pe_color = "#EF4444" if pe_val and pe_val > 40 else "#F59E0B" if pe_val and pe_val > 25 else "#10B981"
            _fund_card(_fc1, "本益比 PE", f"{pe_val:.1f}x" if pe_val else "--", _fund.get("pe_status","")[:12], pe_color)

            # ROE
            roe_val = _fund.get("roe_pct")
            roe_color = "#10B981" if roe_val and roe_val >= 15 else "#F59E0B" if roe_val and roe_val >= 8 else "#EF4444"
            _fund_card(_fc2, "ROE 股東報酬率", f"{roe_val:.1f}%" if roe_val else "--", "✅優秀" if roe_val and roe_val >= 15 else "⚠️普通", roe_color)

            # 毛利率
            gm_val = _fund.get("gross_margin_pct")
            gm_color = "#10B981" if gm_val and gm_val >= 40 else "#F59E0B" if gm_val and gm_val >= 20 else "#EF4444"
            _fund_card(_fc3, "毛利率", f"{gm_val:.1f}%" if gm_val else "--", "高護城河" if gm_val and gm_val >= 40 else "正常", gm_color)

            # EPS
            eps_val = _fund.get("trailing_eps")
            feps_val = _fund.get("forward_eps")
            eps_sub  = f"預估EPS {feps_val}" if feps_val else "trailing"
            _fund_card(_fc4, "EPS(元)", f"{eps_val}" if eps_val else "--", eps_sub, "#6366F1")

            # 殖利率
            dy_val = _fund.get("dividend_yield_pct")
            dy_color = "#10B981" if dy_val and dy_val >= 5 else "#94A3B8"
            _fund_card(_fc5, "殖利率", f"{dy_val:.2f}%" if dy_val else "--", "高息股✅" if dy_val and dy_val >= 5 else "一般", dy_color)

            # 52週位置條
            pos_pct = _fund.get("position_52w_pct", 50)
            pos_label = _fund.get("position_52w_label","")
            hi52 = _fund.get("week52_high","--")
            lo52 = _fund.get("week52_low","--")
            pos_color = "#EF4444" if pos_pct > 80 else "#F59E0B" if pos_pct > 50 else "#10B981"
            st.markdown(f"""<div style="margin-top:8px; padding:10px 14px; background:rgba(30,41,59,0.5); border-radius:8px;">
<div style="display:flex; justify-content:space-between; font-size:0.75rem; color:#94A3B8; margin-bottom:5px;">
  <span>52週低點 {lo52}</span><span style="color:{pos_color}; font-weight:700;">📍 目前位置 {pos_pct:.0f}%  {pos_label}</span><span>52週高點 {hi52}</span>
</div>
<div style="background:rgba(255,255,255,0.08); border-radius:6px; height:6px; overflow:hidden;">
  <div style="width:{pos_pct}%; height:100%; background:{pos_color}; border-radius:6px;"></div>
</div>
</div>""", unsafe_allow_html=True)

            # 月營收
            _rev = fetch_monthly_revenue(stock_id)
            if _rev.get("available") and _rev.get("months"):
                rg = _fund.get("revenue_growth_pct")
                rg_color = "#10B981" if rg and rg > 0 else "#EF4444"
                months = _rev.get("months",[])[-3:]
                revs   = [f"{r/1e6:.1f}M" if r >= 1e6 else f"{r/1e3:.0f}K" for r in _rev.get("revenues",[])[-3:]]
                rev_pairs = " → ".join(f"{m[-5:]} {v}" for m, v in zip(months, revs))
                st.markdown(f"""<div style="margin-top:6px; padding:7px 14px; background:rgba(30,41,59,0.4); border-radius:8px; font-size:0.78rem; color:#94A3B8;">
📅 <b>近期月營收</b>：{rev_pairs} &nbsp;｜&nbsp; <span style="color:{rg_color}; font-weight:700;">年增率 {rg:+.1f}%</span>
</div>""", unsafe_allow_html=True)

    except Exception as _fe:
        pass

    # ── C: 融資融券趨勢面板 ─────────────────────────────────────────
    try:
        from core.margin_provider import fetch_margin_data
        _mar = fetch_margin_data(stock_id)
        if _mar.get("available"):
            st.markdown("---")
            st.markdown("#### 🏦 融資融券籌碼")
            _mc1, _mc2, _mc3 = st.columns(3)

            _m5d_chg = _mar.get("margin_change_5d", 0)
            _m5d_color = "#F59E0B" if _m5d_chg > 300 else "#EF4444" if _m5d_chg > 0 else "#10B981"
            _sc = _mar.get("short_change", 0)
            _sc_color = "#EF4444" if _sc > 50 else "#10B981" if _sc < -50 else "#94A3B8"

            _mc1.markdown(f"""<div class="glass-card" style="padding:14px; border-left:4px solid {_m5d_color};">
<div style="font-size:0.72rem; color:#94A3B8;">融資餘額</div>
<div style="font-size:1.1rem; font-weight:800; color:#F8FAFC; margin:4px 0;">{_mar['margin_balance']:,} 張</div>
<div style="font-size:0.75rem; color:{_m5d_color};">5日 {_m5d_chg:+,} 張</div>
</div>""", unsafe_allow_html=True)

            _mc2.markdown(f"""<div class="glass-card" style="padding:14px; border-left:4px solid {_sc_color};">
<div style="font-size:0.72rem; color:#94A3B8;">融券餘額</div>
<div style="font-size:1.1rem; font-weight:800; color:#F8FAFC; margin:4px 0;">{_mar['short_balance']:,} 張</div>
<div style="font-size:0.75rem; color:{_sc_color};">當日 {_sc:+,} 張</div>
</div>""", unsafe_allow_html=True)

            _trend_txt = _mar.get("margin_trend","")
            _trend_color = "#F59E0B" if "增加" in _trend_txt and "大幅" in _trend_txt else "#10B981" if "減少" in _trend_txt else "#94A3B8"
            _mc3.markdown(f"""<div class="glass-card" style="padding:14px; border-left:4px solid {_trend_color};">
<div style="font-size:0.72rem; color:#94A3B8;">融資趨勢解讀</div>
<div style="font-size:0.78rem; color:{_trend_color}; margin-top:8px; line-height:1.4;">{_trend_txt}</div>
</div>""", unsafe_allow_html=True)

    except Exception as _me:
        pass

# ==============================================================================
# 🚨 價格警示檢查（每次頁面重載時自動比對）'''

if ANCHOR in content:
    content = content.replace(ANCHOR, NEW_PANELS, 1)
    print('PATCH 1: Taiwan tab panels injected')
else:
    print('ERROR: Anchor not found in app.py')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Saved app.py')
