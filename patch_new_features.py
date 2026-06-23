#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patch app.py: Inject three new features
1. Price Alert panel (into tab_market after existing content)
2. Sector Heatmap (into tab_market)
3. Dividend/Earnings Calendar (into tab_market)
"""

with open('app.py', encoding='utf-8') as f:
    content = f.read()

ANCHOR = "# ==============================================================================\n# TAB 2: \U0001f4bc \u5c08\u5c6c\u6301\u80a1\u8ffd\u8e64\u770b\u677f\n# =============================================================================="

NEW_SECTIONS = '''
# ==============================================================================
# \U0001f6a8 \u50f9\u683c\u8b66\u793a\u6aa2\u67e5\uff08\u6bcf\u6b21\u9801\u9762\u91cd\u8f09\u6642\u81ea\u52d5\u6bd4\u5c0d\uff09
# ==============================================================================
try:
    from core.alert_manager import check_alerts, get_all_alerts, add_alert, remove_alert, clear_triggered, get_stats as alert_stats
    # \u7528\u6301\u80a1\u5e93\u5b58\u7684\u73fe\u50f9\u4f86\u6bd4\u5c0d\u8b66\u793a
    _current_prices = {}
    try:
        from core.realtime_provider import fetch_realtime_price as _frp
        import json as _json
        _pf_path = config.PORTFOLIO_FILE
        if os.path.exists(_pf_path):
            with open(_pf_path, encoding="utf-8") as _f:
                _pf = _json.load(_f)
            for _sid in list(_pf.keys())[:5]:  # \u6700\u591a\u6aa2\u67e5 5 \u652f\uff0c\u907f\u514d\u592a\u6162
                _rt = _frp(_sid)
                if _rt.get("success"):
                    _current_prices[_sid] = _rt["price"]
    except Exception:
        pass

    _triggered = check_alerts(_current_prices) if _current_prices else []
    if _triggered:
        for _t in _triggered:
            _sign = "\u2191" if _t["condition"] == ">" else "\u2193"
            st.toast(
                f"\U0001f514 \u8b66\u793a\u89f8\u767c\uff01 {_t['stock_id']} {_t['stock_name']} "
                f"{'>\u6f32\u5230' if _t['condition'] == '>' else '<\u8dcc\u5230'} "
                f"{_t['price']} \u5143\uff0c\u73fe\u50f9: {_t.get('trigger_price', '--')} \u5143",
                icon="\U0001f514"
            )
except Exception:
    pass

# ==============================================================================
# \U0001f5fa\ufe0f \u53f0\u80a1\u677f\u584a\u71b1\u5716 (Sector Heatmap)
# ==============================================================================
with tab_market:
    st.markdown("---")
    st.markdown("### \U0001f5fa\ufe0f \u53f0\u80a1\u677f\u584a\u71b1\u5716 · Sector Heatmap")

    try:
        from core.sector_heatmap import fetch_sector_indices
        import plotly.graph_objects as go

        _sectors = fetch_sector_indices()
        if _sectors:
            # \u751f\u6210\u71b1\u5716\u8272\u5757\uff08\u7528 Plotly Treemap/Bar\uff09
            _names    = [s["name"] for s in _sectors if s["name"] != "\u5927\u76e4"]
            _changes  = [s["change_pct"] for s in _sectors if s["name"] != "\u5927\u76e4"]
            _closes   = [s["close"] for s in _sectors if s["name"] != "\u5927\u76e4"]
            _labels   = [f"{n}<br>{c:+.2f}%" for n, c in zip(_names, _changes)]

            _colors = []
            for c in _changes:
                if c >= 2:    _colors.append("#b91c1c")
                elif c >= 1:  _colors.append("#dc2626")
                elif c >= 0:  _colors.append("#ef4444")
                elif c >= -1: _colors.append("#16a34a")
                elif c >= -2: _colors.append("#15803d")
                else:         _colors.append("#166534")

            _fig_heat = go.Figure(go.Bar(
                x=_names,
                y=[abs(c) + 0.1 for c in _changes],
                text=_labels,
                textposition="inside",
                marker_color=_colors,
                hovertemplate="<b>%{x}</b><br>\u5206\u985e\u6307\u6578: %{customdata:.2f}<br>\u6f32\u8dcc: %{text}<extra></extra>",
                customdata=_closes,
            ))
            _fig_heat.update_layout(
                height=320,
                margin=dict(l=10, r=10, t=10, b=40),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(15,23,42,0.6)",
                font_color="white",
                xaxis=dict(showgrid=False, tickangle=-30, tickfont_size=10),
                yaxis=dict(showgrid=False, showticklabels=False),
                showlegend=False,
            )
            st.plotly_chart(_fig_heat, use_container_width=True, config={"displayModeBar": False})

            # \u5927\u76e4\u6307\u6578\u6f32\u8dcc
            _market = next((s for s in _sectors if s["name"] == "\u5927\u76e4"), None)
            if _market:
                _mc = _market["change_pct"]
                _color_m = "\U0001f534" if _mc > 0 else "\U0001f7e2"
                st.caption(f"{_color_m} \u5927\u76e4\u52a0\u6b0a\u6307\u6578: {_market['close']:,.2f}  {_mc:+.2f}%")
        else:
            st.info("\u76ee\u524d\u70ba\u975e\u4ea4\u6613\u6642\u9593\uff0c\u985e\u80a1\u8cc7\u6599\u5c07\u65bc\u76e4\u5f8c\u66f4\u65b0")

    except Exception as _he:
        st.caption(f"\u71b1\u5716\u8f09\u5165\u4e2d... ({str(_he)[:50]})")

# ==============================================================================
# \U0001f4c5 \u9664\u6b0a\u606f/\u8ca1\u5831\u884c\u4e8b\u66c6
# ==============================================================================
with tab_market:
    st.markdown("---")
    st.markdown("### \U0001f4c5 \u9664\u6b0a\u606f\u884c\u4e8b\u66c6\uff08\u672a\u4f86 60 \u5929\uff09")
    try:
        from core.calendar_provider import fetch_upcoming_dividends
        from core.profile_manager import get_profile_summary

        _prof      = get_profile_summary()
        _watched   = list(_prof.get("watched_stocks", {}).keys())
        _divs      = fetch_upcoming_dividends(days_ahead=60)

        if _divs:
            # \u82e5\u6709\u76e3\u770b\u80a1\u7968\uff0c\u5148\u986f\u793a\u76e3\u770b\u80a1\u7968\u7684\u9664\u6b0a\u606f\uff0c\u518d\u986f\u793a\u5176\u4ed6
            _divs_watched = [d for d in _divs if d["stock_id"] in _watched] if _watched else []
            _divs_other   = [d for d in _divs if d["stock_id"] not in _watched][:20]
            _divs_display = _divs_watched + _divs_other

            if _divs_watched:
                st.caption(f"\U0001f516 \u4f60\u7684\u76e3\u770b\u80a1\u7968\u5171\u6709 {len(_divs_watched)} \u652f\u5373\u5c07\u9664\u6b0a\u606f")

            _cal_cols = st.columns([2, 3, 2, 2, 2, 2])
            _headers  = ["\u4ee3\u865f", "\u540d\u7a31", "\u9664\u6b0a\u606f\u65e5", "\u5269\u5929", "\u73fe\u91d1\u80a1\u5229", "\u985e\u578b"]
            for col, h in zip(_cal_cols, _headers):
                col.markdown(f"**{h}**")
            st.markdown('<hr style="margin:4px 0; opacity:.2">', unsafe_allow_html=True)

            for d in _divs_display[:25]:
                c1, c2, c3, c4, c5, c6 = st.columns([2, 3, 2, 2, 2, 2])
                days_left = d["days_left"]
                urgency   = "\U0001f534" if days_left <= 7 else ("\U0001f7e1" if days_left <= 30 else "\U0001f7e2")
                is_mine   = d["stock_id"] in _watched
                name_str  = f"\u2b50 {d['stock_name']}" if is_mine else d["stock_name"]

                c1.write(d["stock_id"])
                c2.write(name_str)
                c3.write(d["ex_date"])
                c4.write(f"{urgency} {days_left}\u5929")
                c5.write(f"{d['cash_div']} \u5143" if d.get("cash_div") and d["cash_div"] != "0" else "-")
                c6.write(d.get("div_type", "-"))
        else:
            st.info("\u76ee\u524d\u8fd1 60 \u5929\u5167\u7121\u9664\u6b0a\u606f\u516c\u544a\uff0c\u6216\u8cc7\u6599\u8f09\u5165\u5931\u6557")
    except Exception as _ce:
        st.caption(f"\u884c\u4e8b\u66c6\u8f09\u5165\u4e2d... ({str(_ce)[:80]})")

# ==============================================================================
# \U0001f514 \u50f9\u683c\u8b66\u793a\u7ba1\u7406\u9762\u677f
# ==============================================================================
with tab_market:
    st.markdown("---")
    with st.expander("\U0001f514 \u50f9\u683c\u8b66\u793a\u7ba1\u7406", expanded=False):
        try:
            from core.alert_manager import (
                add_alert, remove_alert, get_all_alerts,
                clear_triggered, get_stats as alert_stats
            )
            _ast = alert_stats()
            st.caption(f"\u73fe\u6709\u8b66\u793a: {_ast['active']} \u500b\u6d3b\u8df3 | {_ast['triggered']} \u500b\u5df2\u89f8\u767c")

            # \u65b0\u589e\u8b66\u793a\u8868\u55ae
            with st.form("alert_form_main"):
                _af1, _af2, _af3, _af4 = st.columns([2, 2, 1.5, 3])
                with _af1:
                    _alert_sid  = st.text_input("\u80a1\u7968\u4ee3\u865f", value=stock_id, placeholder="e.g. 0050")
                with _af2:
                    _alert_name = st.text_input("\u540d\u7a31(\u53ef\u7565)", placeholder="e.g. \u5143\u5927\u53f0\u706350")
                with _af3:
                    _alert_cond = st.selectbox("\u689d\u4ef6", ["\u2191 \u6f32\u5230\uff08\u9ad8\u65bc\uff09", "\u2193 \u8dcc\u5230\uff08\u4f4e\u65bc\uff09"])
                with _af4:
                    _alert_price = st.number_input("\u76ee\u6a19\u50f9\u683c(\u5143)", min_value=0.0, step=0.5, format="%.2f")
                _alert_note  = st.text_input("\u5099\u8a3b(\u53ef\u7565)", placeholder="e.g. \u7b2c\u4e00\u6279\u8cb7\u9032\u50f9\u4f4d")
                if st.form_submit_button("\u2795 \u65b0\u589e\u8b66\u793a", use_container_width=True):
                    if _alert_sid and _alert_price > 0:
                        _cond_map = {"\u2191 \u6f32\u5230\uff08\u9ad8\u65bc\uff09": ">", "\u2193 \u8dcc\u5230\uff08\u4f4e\u65bc\uff09": "<"}
                        add_alert(
                            stock_id=_alert_sid.strip(),
                            stock_name=_alert_name.strip() or _alert_sid.strip(),
                            condition=_cond_map[_alert_cond],
                            price=_alert_price,
                            note=_alert_note.strip()
                        )
                        st.toast(f"\u8b66\u793a\u5df2\u8a2d\u5b9a\uff01{_alert_sid} {'>\u6f32\u5230' if '>' in _cond_map[_alert_cond] else '<\u8dcc\u5230'} {_alert_price}\u5143", icon="\U0001f514")
                        st.rerun()
                    else:
                        st.warning("\u8acb\u586b\u5beb\u80a1\u7968\u4ee3\u865f\u548c\u76ee\u6a19\u50f9\u683c")

            # \u73fe\u6709\u8b66\u793a\u6e05\u55ae
            _alerts = get_all_alerts()
            if _alerts:
                for _al in _alerts:
                    _acol1, _acol2, _acol3, _acol4 = st.columns([2, 3, 3, 1])
                    _acol1.write(_al["stock_id"])
                    _cond_label = f"{'>\u6f32\u5230' if _al['condition'] == '>' else '<\u8dcc\u5230'} {_al['price']}\u5143"
                    _acol2.write(_cond_label)
                    _status = "\u2705 \u5df2\u89f8\u767c" if _al["triggered"] else "\u23f3 \u76e3\u63a7\u4e2d"
                    _acol3.write(f"{_status} {_al.get('note', '')}")
                    if _acol4.button("\U0001f5d1\ufe0f", key=f"del_alert_{_al['id']}"):
                        remove_alert(_al["id"])
                        st.rerun()

                _ccol1, _ccol2 = st.columns(2)
                with _ccol1:
                    if st.button("\U0001f9f9 \u6e05\u9664\u5df2\u89f8\u767c", use_container_width=True):
                        clear_triggered()
                        st.rerun()
            else:
                st.info("\u5c1a\u7121\u8b66\u793a\uff0c\u8acb\u4e0a\u65b9\u65b0\u589e")

        except Exception as _ae:
            st.error(f"\u8b66\u793a\u6a21\u7d44\u9748: {_ae}")

# ==============================================================================
# TAB 2: \U0001f4bc \u5c08\u5c6c\u6301\u80a1\u8ffd\u8e64\u770b\u677f
# =============================================================================='''

if ANCHOR in content:
    content = content.replace(ANCHOR, NEW_SECTIONS, 1)
    print("SUCCESS: Injected heatmap + calendar + alert sections")
else:
    print("ERROR: Anchor not found")
    # Show what we looked for
    idx = content.find("TAB 2")
    print(f"'TAB 2' found at char {idx}")
    print(f"Context: {repr(content[idx-20:idx+100])}")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Saved app.py")
