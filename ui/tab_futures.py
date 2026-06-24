# ui/tab_futures.py
# =====================================================================
# 期貨市場看盤分頁積木（純看盤，不追蹤持倉）
# 職責：顯示期貨即時報價，輔助分析台股/美股大盤走勢
# =====================================================================

import streamlit as st
from core.futures_provider import fetch_multiple_futures, FUTURES_CATALOG, get_default_watchlist


# --- 多語言文字 ---
_T = {
    "繁體中文": {
        "tab_title":     "📉 期貨市場看盤",
        "desc":          "追蹤全球關鍵期貨動態，分析大盤方向（純看盤，不記錄持倉）",
        "section_tw":    "🇹🇼 台灣期貨",
        "section_us_idx":"🇺🇸 美股指數期貨",
        "section_cmd":   "🥇 商品期貨",
        "section_fx":    "💵 外匯與指數",
        "vix_label":     "恐慌指數 VIX",
        "vix_low":       "市場情緒平穩（VIX < 20）",
        "vix_med":       "市場存在不安情緒（VIX 20-30）",
        "vix_high":      "⚠️ 市場恐慌（VIX > 30），注意風險！",
        "prev_close":    "昨收",
        "refresh_btn":   "🔄 刷新期貨報價",
        "na_text":       "資料不可用",
        "delay_note":    "⚠️ 期貨報價來源 Yahoo Finance，可能有 15 分鐘延遲",
        "analysis_note": "📊 看盤邏輯：ES/NQ 方向 → 預判隔日台股情緒；黃金/原油 → 風險偏好；VIX → 市場恐慌程度",
        "up_color":      "#EF4444",
        "down_color":    "#10B981",
    },
    "English": {
        "tab_title":     "📉 Futures Market Monitor",
        "desc":          "Track global key futures for market direction analysis (View-only, no position tracking)",
        "section_tw":    "🇹🇼 Taiwan Futures",
        "section_us_idx":"🇺🇸 US Index Futures",
        "section_cmd":   "🥇 Commodity Futures",
        "section_fx":    "💵 FX & Indices",
        "vix_label":     "Fear Index VIX",
        "vix_low":       "Market Calm (VIX < 20)",
        "vix_med":       "Some Anxiety (VIX 20-30)",
        "vix_high":      "⚠️ Market Fear (VIX > 30), watch risk!",
        "prev_close":    "Prev Close",
        "refresh_btn":   "🔄 Refresh Futures",
        "na_text":       "Data Unavailable",
        "delay_note":    "⚠️ Futures data from Yahoo Finance, may have ~15 min delay",
        "analysis_note": "📊 Reading the tape: ES/NQ direction → predict next-day Taiwan open; Gold/Oil → risk appetite; VIX → fear level",
        "up_color":      "#EF4444",
        "down_color":    "#10B981",
    },
    "日本語": {
        "tab_title":     "📉 先物市場モニター",
        "desc":          "グローバルな主要先物を追跡し、相場方向を分析（閲覧専用）",
        "section_tw":    "🇹🇼 台湾先物",
        "section_us_idx":"🇺🇸 米国株価指数先物",
        "section_cmd":   "🥇 商品先物",
        "section_fx":    "💵 為替・指数",
        "vix_label":     "恐怖指数 VIX",
        "vix_low":       "相場は落ち着いている（VIX < 20）",
        "vix_med":       "やや不安定（VIX 20-30）",
        "vix_high":      "⚠️ 相場パニック（VIX > 30）、リスク注意！",
        "prev_close":    "前日終値",
        "refresh_btn":   "🔄 更新",
        "na_text":       "データなし",
        "delay_note":    "⚠️ 先物データはYahoo Finance提供、約15分ディレイ",
        "analysis_note": "📊 読み方：ES/NQ方向→翌日台湾市場寄付き予測；金/原油→リスク嗜好；VIX→恐怖水準",
        "up_color":      "#EF4444",
        "down_color":    "#10B981",
    },
    "ไทย": {
        "tab_title":     "📉 ตลาดสัญญาฟิวเจอร์ส",
        "desc":          "ติดตามฟิวเจอร์สสำคัญทั่วโลกเพื่อวิเคราะห์ทิศทางตลาด",
        "section_tw":    "🇹🇼 ฟิวเจอร์สไต้หวัน",
        "section_us_idx":"🇺🇸 ฟิวเจอร์สดัชนีสหรัฐ",
        "section_cmd":   "🥇 สินค้าโภคภัณฑ์",
        "section_fx":    "💵 ฟอเร็กซ์และดัชนี",
        "vix_label":     "ดัชนีความกลัว VIX",
        "vix_low":       "ตลาดสงบ (VIX < 20)",
        "vix_med":       "ตลาดไม่แน่นอน (VIX 20-30)",
        "vix_high":      "⚠️ ตลาดตื่นตระหนก (VIX > 30)!",
        "prev_close":    "ราคาปิดก่อนหน้า",
        "refresh_btn":   "🔄 รีเฟรช",
        "na_text":       "ไม่มีข้อมูล",
        "delay_note":    "⚠️ ข้อมูลล่าช้าจาก Yahoo Finance",
        "analysis_note": "📊 การอ่านสัญญาณ: ES/NQ → คาดการณ์การเปิดตลาดไต้หวัน; ทอง/น้ำมัน → ความต้องการความเสี่ยง; VIX → ระดับความกลัว",
        "up_color":      "#EF4444",
        "down_color":    "#10B981",
    },
    "Tiếng Việt": {
        "tab_title":     "📉 Thị Trường Phái Sinh",
        "desc":          "Theo dõi hợp đồng tương lai toàn cầu để phân tích xu hướng thị trường",
        "section_tw":    "🇹🇼 Phái sinh Đài Loan",
        "section_us_idx":"🇺🇸 Phái sinh chỉ số Mỹ",
        "section_cmd":   "🥇 Hàng hóa",
        "section_fx":    "💵 Ngoại hối & Chỉ số",
        "vix_label":     "Chỉ số sợ hãi VIX",
        "vix_low":       "Thị trường bình ổn (VIX < 20)",
        "vix_med":       "Thị trường bất ổn (VIX 20-30)",
        "vix_high":      "⚠️ Hoảng loạn thị trường (VIX > 30)!",
        "prev_close":    "Đóng cửa trước",
        "refresh_btn":   "🔄 Làm mới",
        "na_text":       "Không có dữ liệu",
        "delay_note":    "⚠️ Dữ liệu từ Yahoo Finance, có thể trễ ~15 phút",
        "analysis_note": "📊 Cách đọc: ES/NQ → dự đoán mở cửa thị trường Đài Loan hôm sau; Vàng/Dầu → khẩu vị rủi ro; VIX → mức độ sợ hãi",
        "up_color":      "#EF4444",
        "down_color":    "#10B981",
    },
}


def _render_futures_card(result: dict, lang: str, width: str = "100%"):
    """渲染單個期貨報價卡片"""
    t = _T[lang]
    key = result.get("key", "")
    flag = result.get("flag", "📊")

    if not result.get("success"):
        name = FUTURES_CATALOG.get(key, {}).get("name_zh", key)
        st.markdown(f"""<div class="glass-card" style="padding:12px; border-left:4px solid #64748B; margin-bottom:8px;">
<span style="color:#94A3B8; font-size:0.85rem;">{flag} {name} — {t['na_text']}</span>
</div>""", unsafe_allow_html=True)
        return

    price     = result["price"]
    change    = result["change"]
    change_pct= result["change_percent"]
    name_zh   = result.get("name_zh", key)
    name_en   = result.get("name_en", key)
    currency  = result.get("currency", "USD")
    prev_close= result.get("prev_close", 0)

    if change > 0:
        color = t["up_color"]
        sign = "▲ +"
    elif change < 0:
        color = t["down_color"]
        sign = "▼ "
    else:
        color = "#94A3B8"
        sign = ""

    currency_symbol = "$" if currency == "USD" else ""

    st.markdown(f"""<div class="glass-card" style="padding:14px 16px; margin-bottom:8px; border-left:4px solid {color}; background:linear-gradient(135deg,rgba(20,25,50,0.75),rgba(10,12,30,0.9));">
<div style="display:flex; justify-content:space-between; align-items:center;">
<div>
<div style="font-size:0.72rem; color:#94A3B8; font-weight:600;">{flag} {name_zh} / {name_en}</div>
<div style="display:flex; align-items:baseline; gap:8px; margin-top:3px;">
<span style="font-size:1.6rem; font-weight:800; color:#F8FAFC; font-family:monospace;">{currency_symbol}{price:,.2f}</span>
<span style="font-size:0.95rem; font-weight:700; color:{color}; font-family:monospace;">{sign}{abs(change):.2f} ({change_pct:+.2f}%)</span>
</div>
</div>
<div style="text-align:right; font-size:0.75rem; color:#64748B;">
{t['prev_close']}<br>
<span style="color:#94A3B8; font-family:monospace;">{currency_symbol}{prev_close:,.2f}</span>
</div>
</div>
</div>""", unsafe_allow_html=True)


def _render_vix_gauge(vix_result: dict, lang: str):
    """VIX 恐慌指數量表"""
    t = _T[lang]
    if not vix_result.get("success"):
        return

    vix = vix_result["price"]
    if vix < 20:
        vix_color = "#10B981"
        vix_msg = t["vix_low"]
        bar_pct = max(5, int(vix / 50 * 100))
    elif vix < 30:
        vix_color = "#F59E0B"
        vix_msg = t["vix_med"]
        bar_pct = int(vix / 50 * 100)
    else:
        vix_color = "#EF4444"
        vix_msg = t["vix_high"]
        bar_pct = min(100, int(vix / 50 * 100))

    change = vix_result.get("change", 0)
    change_pct = vix_result.get("change_percent", 0)
    sign = "+" if change >= 0 else ""

    st.markdown(f"""<div class="glass-card" style="padding:16px 20px; margin-bottom:12px; border-left:5px solid {vix_color}; background:linear-gradient(135deg,rgba(20,25,50,0.85),rgba(10,12,30,0.95));">
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
<span style="font-size:0.85rem; font-weight:700; color:{vix_color};">⚡ {t['vix_label']}</span>
<span style="font-size:1.5rem; font-weight:800; color:{vix_color}; font-family:monospace;">{vix:.2f} &nbsp;<span style="font-size:0.9rem;">{sign}{change:.2f} ({change_pct:+.2f}%)</span></span>
</div>
<div style="background:rgba(30,41,59,0.6); border-radius:8px; height:8px; overflow:hidden; margin-bottom:8px;">
<div style="background:{vix_color}; height:100%; width:{bar_pct}%; border-radius:8px; transition:width 0.5s ease;"></div>
</div>
<div style="font-size:0.82rem; color:#E2E8F0;">{vix_msg}</div>
</div>""", unsafe_allow_html=True)


def render(lang: str):
    """
    渲染期貨市場看盤分頁。
    唯一對外接口：只需傳入語言設定。
    v2.9: 總體儀表板升級為6格（加道瓊 DJI）
    """
    t = _T.get(lang, _T["繁體中文"])
    st.markdown(f"### {t['tab_title']}")
    st.markdown(f"<div style='color:#94A3B8; font-size:0.9rem; margin-bottom:16px;'>{t['desc']}</div>", unsafe_allow_html=True)

    if st.button(t["refresh_btn"], key="futures_refresh_btn"):
        st.rerun()

    with st.spinner("載入期貨資料..." if lang == "繁體中文" else "Loading futures data..."):
        vix_r          = fetch_multiple_futures(["VX"])
        vix_result     = vix_r[0] if vix_r else {}
        tw_results     = fetch_multiple_futures(["TWF", "STXF"])
        us_idx_results = fetch_multiple_futures(["ES", "NQ", "YM", "RTY"])
        cmd_results    = fetch_multiple_futures(["GC", "SI", "CL", "BZ"])
        fx_results     = fetch_multiple_futures(["DX", "6E", "6J"])

    # ── 🌐 總體環境多空信號儀表板（v2.9: 6格）─────────────────────
    try:
        from core.macro_provider import fetch_macro_context
        _macro = fetch_macro_context()
        if _macro.get("available"):
            st.markdown("#### 🌐 總體環境多空信號儀表板")

            _mc1, _mc2, _mc3, _mc4, _mc5, _mc6 = st.columns(6)

            _vix_v  = _macro.get("vix",     {}).get("price",      20)
            _vix_c  = _macro.get("vix",     {}).get("change_pct",  0)
            _sox_v  = _macro.get("sox",     {}).get("price",       0)
            _sox_c  = _macro.get("sox",     {}).get("change_pct",  0)
            _twd_v  = _macro.get("usd_twd", {}).get("price",      31)
            _twd_c  = _macro.get("usd_twd", {}).get("change_pct",  0)
            _nq_v   = _macro.get("nasdaq",  {}).get("price",       0)
            _nq_c   = _macro.get("nasdaq",  {}).get("change_pct",  0)
            _sp_v   = _macro.get("sp500",   {}).get("price",       0)
            _sp_c   = _macro.get("sp500",   {}).get("change_pct",  0)
            _dj_v   = _macro.get("dji",     {}).get("price",       0)
            _dj_c   = _macro.get("dji",     {}).get("change_pct",  0)

            _vix_color = "#10B981" if _vix_v < 20 else "#F59E0B" if _vix_v < 30 else "#EF4444"
            _sox_color = "#EF4444" if _sox_c > 1  else "#10B981" if _sox_c < -1  else "#F59E0B"
            _twd_color = "#10B981" if _twd_c < -0.3 else "#EF4444" if _twd_c > 0.3 else "#94A3B8"
            _nq_color  = "#EF4444" if _nq_c  > 0.5 else "#10B981" if _nq_c  < -0.5 else "#94A3B8"
            _sp_color  = "#EF4444" if _sp_c  > 0.5 else "#10B981" if _sp_c  < -0.5 else "#94A3B8"
            _dj_color  = "#EF4444" if _dj_c  > 0.5 else "#10B981" if _dj_c  < -0.5 else "#94A3B8"

            _vix_sig = "🟢" if _vix_v < 20 else "🟡" if _vix_v < 30 else "🔴"
            _sox_sig = "📈" if _sox_c > 1  else "📉" if _sox_c < -1  else "➡️"
            _twd_sig = "🟢" if _twd_c < -0.3 else "🔴" if _twd_c > 0.3 else "⚪"
            _nq_sig  = "📈" if _nq_c  > 0.5 else "📉" if _nq_c  < -0.5 else "➡️"
            _sp_sig  = "📈" if _sp_c  > 0.5 else "📉" if _sp_c  < -0.5 else "➡️"
            _dj_sig  = "📈" if _dj_c  > 0.5 else "📉" if _dj_c  < -0.5 else "➡️"

            for col, title, val_line, sub_line, color in [
                (_mc1, "VIX 恐慌指數",
                 f"{_vix_sig} {_vix_v:.1f}",
                 f"{_vix_c:+.1f}% | {_macro.get('vix_level','')[:6]}",
                 _vix_color),
                (_mc2, "費城半導體 SOX",
                 f"{_sox_sig} {_sox_c:+.1f}%",
                 f"{_sox_v:,.0f}",
                 _sox_color),
                (_mc3, "台幣 USD/TWD",
                 f"{_twd_sig} {_twd_v:.2f}",
                 f"{_twd_c:+.2f}% | {_macro.get('twd_trend','')[:6]}",
                 _twd_color),
                (_mc4, "NASDAQ",
                 f"{_nq_sig} {_nq_c:+.1f}%",
                 f"{_nq_v:,.0f}",
                 _nq_color),
                (_mc5, "S&P 500",
                 f"{_sp_sig} {_sp_c:+.1f}%",
                 f"{_sp_v:,.0f}",
                 _sp_color),
                (_mc6, "道瓊 DJI",
                 f"{_dj_sig} {_dj_c:+.1f}%",
                 f"{_dj_v:,.0f}",
                 _dj_color),
            ]:
                col.markdown(f"""<div class="glass-card" style="padding:10px 8px; text-align:center; border-top:3px solid {color};">
<div style="font-size:0.6rem; color:#94A3B8; white-space:nowrap;">{title}</div>
<div style="font-size:1.1rem; font-weight:800; color:{color};">{val_line}</div>
<div style="font-size:0.6rem; color:#64748B;">{sub_line}</div>
</div>""", unsafe_allow_html=True)

            # 多空綜合研判（6指標）
            _bulls = sum([_sox_c > 0, _nq_c > 0, _sp_c > 0, _dj_c > 0, _vix_v < 20, _twd_c < 0])
            _bears = 6 - _bulls
            _vc    = "#EF4444" if _bulls >= 5 else "#10B981" if _bears >= 5 else "#F59E0B"
            _vt    = (
                f"🔴 強多格局：美股三大指數全面上漲，外資進場意願高，台指期明日開盤偏多" if _bulls >= 5 else
                f"🟢 強空格局：指數全面下跌、VIX高漲，台指期偏空，請注意風險控管"         if _bears >= 5 else
                f"🟡 多空互見（多頭訊號 {_bulls}/6）：需等待指標方向一致後再進場"
            )
            st.markdown(f"""<div style="margin-top:8px; padding:10px 16px; background:rgba(30,41,59,0.6);
border-left:4px solid {_vc}; border-radius:8px; font-size:0.82rem; color:#F8FAFC; font-weight:600;">
🎯 <b>總體環境研判</b>（多頭訊號 {_bulls}/6）：{_vt}
</div>""", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:0.68rem; color:#475569; margin-top:3px;'>更新時間: {_macro.get('updated','--')}</div>",
                        unsafe_allow_html=True)
            st.markdown("---")
    except Exception:
        pass

    # ── VIX 量表 ─────────────────────────────────────────────────
    _render_vix_gauge(vix_result, lang)

    # ── 台灣期貨 ─────────────────────────────────────────────────
    st.markdown(f"**{t['section_tw']}**")
    col1, col2 = st.columns(2)
    for i, r in enumerate(tw_results):
        with (col1 if i % 2 == 0 else col2):
            _render_futures_card(r, lang)
    st.markdown("---")

    # ── 美股指數期貨 ─────────────────────────────────────────────
    st.markdown(f"**{t['section_us_idx']}**")
    col1, col2 = st.columns(2)
    for i, r in enumerate(us_idx_results):
        with (col1 if i % 2 == 0 else col2):
            _render_futures_card(r, lang)
    st.markdown("---")

    # ── 商品期貨 ─────────────────────────────────────────────────
    st.markdown(f"**{t['section_cmd']}**")
    col1, col2 = st.columns(2)
    for i, r in enumerate(cmd_results):
        with (col1 if i % 2 == 0 else col2):
            _render_futures_card(r, lang)

    # ── 外匯 ─────────────────────────────────────────────────────
    st.markdown(f"**{t['section_fx']}**")
    col1, col2 = st.columns(2)
    for i, r in enumerate(fx_results):
        with (col1 if i % 2 == 0 else col2):
            _render_futures_card(r, lang)

    # ── 分析提示 ─────────────────────────────────────────────────
    st.markdown("---")
    st.info(t["analysis_note"])
    st.markdown(f"<div style='font-size:0.75rem; color:#64748B;'>{t['delay_note']}</div>", unsafe_allow_html=True)
