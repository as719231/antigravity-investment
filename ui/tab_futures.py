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
    """
    t = _T.get(lang, _T["繁體中文"])
    st.markdown(f"### {t['tab_title']}")
    st.markdown(f"<div style='color:#94A3B8; font-size:0.9rem; margin-bottom:16px;'>{t['desc']}</div>", unsafe_allow_html=True)

    if st.button(t["refresh_btn"], key="futures_refresh_btn"):
        st.rerun()

    with st.spinner("載入期貨資料..." if lang == "繁體中文" else "Loading futures data..."):
        # VIX
        vix_r = fetch_multiple_futures(["VX"])
        vix_result = vix_r[0] if vix_r else {}

        # 台灣期貨
        tw_results = fetch_multiple_futures(["TWF", "STXF"])

        # 美股指數期貨
        us_idx_results = fetch_multiple_futures(["ES", "NQ", "YM", "RTY"])

        # 商品
        cmd_results = fetch_multiple_futures(["GC", "SI", "CL", "BZ"])

        # 外匯
        fx_results = fetch_multiple_futures(["DX", "6E", "6J"])

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
