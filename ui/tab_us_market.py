# ui/tab_us_market.py
# =====================================================================
# 美股看盤分頁積木
# 職責：只負責美股 UI 渲染，不碰台股、期貨任何邏輯
# =====================================================================

import streamlit as st
import json
import os
import datetime

import config
from core.realtime_provider import fetch_us_stock_price, get_us_watchlist_default, US_STOCK_NAMES


# --- 多語言文字 (僅此模組使用) ---
_T = {
    "繁體中文": {
        "tab_title":       "🇺🇸 美股市場即時看盤",
        "desc":            "追蹤美股龍頭與 ETF 即時動態（Yahoo Finance，約 15 分鐘延遲）",
        "watchlist_title": "📋 自訂監控清單",
        "watchlist_hint":  "輸入美股代號，多個用逗號分隔（例：AAPL, NVDA, TSLA）",
        "watchlist_apply": "🔄 套用清單",
        "price_usd":       "美元 USD",
        "prev_close":      "昨收",
        "change":          "漲跌",
        "pct":             "漲跌幅",
        "market_state":    "盤況",
        "up_color":        "#EF4444",   # 美股：紅色上漲（照台灣習慣）
        "down_color":      "#10B981",   # 美股：綠色下跌
        "portfolio_title": "💼 美股持倉追蹤",
        "portfolio_hint":  "尚未新增美股持倉，請在下方新增",
        "add_title":       "➕ 新增 / 更新美股持倉",
        "ticker_label":    "股票代號 (Ticker)",
        "shares_label":    "持有股數（股）",
        "cost_label":      "平均買入成本（美元/股）",
        "mode_label":      "🔄 寫入模式",
        "mode_acc":        "加碼累加（自動計算加權均價）",
        "mode_ow":         "直接覆蓋",
        "add_btn":         "➕ 新增或更新",
        "del_btn":         "🗑️ 刪除",
        "success_add":     "✅ 美股持倉已更新！",
        "success_del":     "✅ 已刪除該持倉！",
        "err_ticker":      "❌ 請輸入有效的股票代號",
        "col_ticker":      "代號",
        "col_name":        "名稱",
        "col_shares":      "持股數",
        "col_cost":        "均價(USD)",
        "col_price":       "即時報價",
        "col_pnl_usd":     "損益(USD)",
        "col_pnl_pct":     "報酬率",
        "refresh_btn":     "🔄 刷新報價",
        "market_closed":   "盤後/休市",
        "market_pre":      "盤前交易",
        "market_regular":  "盤中交易",
        "market_post":     "盤後交易",
        "delay_note":      "⚠️ 報價為 Yahoo Finance 免費資料，約有 15 分鐘延遲",
        "analysis_tip":    "💡 分析提示：美股的走勢對台股隔天的開盤情緒有直接影響，特別是費半指數（SOX）與 NASDAQ。",
    },
    "English": {
        "tab_title":       "🇺🇸 US Market Live Monitor",
        "desc":            "Track US stocks & ETFs in real-time (Yahoo Finance, ~15 min delay)",
        "watchlist_title": "📋 Custom Watchlist",
        "watchlist_hint":  "Enter US tickers separated by commas (e.g.: AAPL, NVDA, TSLA)",
        "watchlist_apply": "🔄 Apply Watchlist",
        "price_usd":       "USD",
        "prev_close":      "Prev Close",
        "change":          "Change",
        "pct":             "Change %",
        "market_state":    "Market",
        "up_color":        "#EF4444",
        "down_color":      "#10B981",
        "portfolio_title": "💼 US Stock Portfolio",
        "portfolio_hint":  "No US stock positions yet. Add below.",
        "add_title":       "➕ Add / Update US Stock Position",
        "ticker_label":    "Stock Ticker",
        "shares_label":    "Shares Owned",
        "cost_label":      "Average Cost (USD/share)",
        "mode_label":      "🔄 Write Mode",
        "mode_acc":        "Accumulate (Auto weighted avg cost)",
        "mode_ow":         "Overwrite",
        "add_btn":         "➕ Add or Update",
        "del_btn":         "🗑️ Delete",
        "success_add":     "✅ US portfolio updated!",
        "success_del":     "✅ Position deleted!",
        "err_ticker":      "❌ Please enter a valid ticker",
        "col_ticker":      "Ticker",
        "col_name":        "Name",
        "col_shares":      "Shares",
        "col_cost":        "Avg Cost(USD)",
        "col_price":       "Live Price",
        "col_pnl_usd":     "P&L (USD)",
        "col_pnl_pct":     "Return %",
        "refresh_btn":     "🔄 Refresh Prices",
        "market_closed":   "Closed",
        "market_pre":      "Pre-Market",
        "market_regular":  "Regular",
        "market_post":     "After Hours",
        "delay_note":      "⚠️ Prices from Yahoo Finance free tier (~15 min delay)",
        "analysis_tip":    "💡 Tip: US market direction directly impacts Taiwan market opening sentiment next day, especially SOX (Philly Semiconductor) and NASDAQ.",
    },
    "日本語": {
        "tab_title":       "🇺🇸 米国株リアルタイムモニター",
        "desc":            "米国株・ETFのリアルタイム動向を追跡（Yahoo Finance、約15分ディレイ）",
        "watchlist_title": "📋 ウォッチリスト",
        "watchlist_hint":  "銘柄コードをカンマ区切りで入力（例：AAPL, NVDA, TSLA）",
        "watchlist_apply": "🔄 適用",
        "price_usd":       "USD",
        "prev_close":      "前日終値",
        "change":          "前日比",
        "pct":             "変化率",
        "market_state":    "相場状態",
        "up_color":        "#EF4444",
        "down_color":      "#10B981",
        "portfolio_title": "💼 米国株ポートフォリオ",
        "portfolio_hint":  "まだ米国株ポジションがありません",
        "add_title":       "➕ 米国株を追加/更新",
        "ticker_label":    "ティッカーコード",
        "shares_label":    "保有株数",
        "cost_label":      "平均取得単価（USD）",
        "mode_label":      "🔄 書き込みモード",
        "mode_acc":        "買い増し累計（加重平均を自動計算）",
        "mode_ow":         "上書き",
        "add_btn":         "➕ 追加・更新",
        "del_btn":         "🗑️ 削除",
        "success_add":     "✅ ポートフォリオ更新完了！",
        "success_del":     "✅ 削除完了！",
        "err_ticker":      "❌ 有効な銘柄コードを入力してください",
        "col_ticker":      "コード",
        "col_name":        "銘柄名",
        "col_shares":      "保有株数",
        "col_cost":        "平均単価(USD)",
        "col_price":       "現在値",
        "col_pnl_usd":     "損益(USD)",
        "col_pnl_pct":     "収益率",
        "refresh_btn":     "🔄 更新",
        "market_closed":   "休場",
        "market_pre":      "寄前取引",
        "market_regular":  "通常取引",
        "market_post":     "時間外取引",
        "delay_note":      "⚠️ Yahoo Finance 無料プランのため約15分遅延",
        "analysis_tip":    "💡 ヒント：米国市場の動きは翌日の台湾市場の寄付きに直接影響します。特にSOXとNASDAQが重要です。",
    },
    "ไทย": {
        "tab_title":       "🇺🇸 ตลาดหุ้นสหรัฐ",
        "desc":            "ติดตามหุ้นสหรัฐและ ETF แบบเรียลไทม์ (ข้อมูลล่าช้าประมาณ 15 นาที)",
        "watchlist_title": "📋 รายการหุ้นที่ติดตาม",
        "watchlist_hint":  "ป้อนรหัสหุ้นคั่นด้วยจุลภาค (เช่น AAPL, NVDA, TSLA)",
        "watchlist_apply": "🔄 ยืนยัน",
        "price_usd":       "USD",
        "prev_close":      "ราคาปิดก่อนหน้า",
        "change":          "เปลี่ยนแปลง",
        "pct":             "% เปลี่ยนแปลง",
        "market_state":    "สถานะตลาด",
        "up_color":        "#EF4444",
        "down_color":      "#10B981",
        "portfolio_title": "💼 พอร์ตหุ้นสหรัฐ",
        "portfolio_hint":  "ยังไม่มีการถือครองหุ้นสหรัฐ",
        "add_title":       "➕ เพิ่ม/อัปเดตหุ้นสหรัฐ",
        "ticker_label":    "รหัสหุ้น",
        "shares_label":    "จำนวนหุ้น",
        "cost_label":      "ราคาเฉลี่ย (USD/หุ้น)",
        "mode_label":      "🔄 โหมดบันทึก",
        "mode_acc":        "ซื้อเพิ่มสะสม",
        "mode_ow":         "เขียนทับ",
        "add_btn":         "➕ เพิ่มหรืออัปเดต",
        "del_btn":         "🗑️ ลบ",
        "success_add":     "✅ อัปเดตพอร์ตสำเร็จ!",
        "success_del":     "✅ ลบสำเร็จ!",
        "err_ticker":      "❌ กรุณากรอกรหัสหุ้นที่ถูกต้อง",
        "col_ticker":      "รหัส",
        "col_name":        "ชื่อ",
        "col_shares":      "จำนวนหุ้น",
        "col_cost":        "ราคาเฉลี่ย(USD)",
        "col_price":       "ราคาปัจจุบัน",
        "col_pnl_usd":     "กำไร/ขาดทุน(USD)",
        "col_pnl_pct":     "อัตราผลตอบแทน",
        "refresh_btn":     "🔄 รีเฟรช",
        "market_closed":   "ปิดตลาด",
        "market_pre":      "ก่อนเปิดตลาด",
        "market_regular":  "ระหว่างวัน",
        "market_post":     "หลังปิดตลาด",
        "delay_note":      "⚠️ ข้อมูลล่าช้าประมาณ 15 นาทีจาก Yahoo Finance",
        "analysis_tip":    "💡 เคล็ดลับ: ทิศทางตลาดสหรัฐส่งผลโดยตรงต่ออารมณ์เปิดตลาดไต้หวันวันถัดไป",
    },
    "Tiếng Việt": {
        "tab_title":       "🇺🇸 Thị Trường Mỹ",
        "desc":            "Theo dõi cổ phiếu Mỹ & ETF theo thời gian thực (Yahoo Finance, trễ ~15 phút)",
        "watchlist_title": "📋 Danh sách theo dõi",
        "watchlist_hint":  "Nhập mã cổ phiếu cách nhau bằng dấu phẩy (VD: AAPL, NVDA, TSLA)",
        "watchlist_apply": "🔄 Áp dụng",
        "price_usd":       "USD",
        "prev_close":      "Đóng cửa trước",
        "change":          "Thay đổi",
        "pct":             "% Thay đổi",
        "market_state":    "Trạng thái",
        "up_color":        "#EF4444",
        "down_color":      "#10B981",
        "portfolio_title": "💼 Danh mục cổ phiếu Mỹ",
        "portfolio_hint":  "Chưa có vị thế nào. Thêm bên dưới.",
        "add_title":       "➕ Thêm / Cập nhật vị thế",
        "ticker_label":    "Mã cổ phiếu",
        "shares_label":    "Số lượng cổ phiếu",
        "cost_label":      "Giá mua trung bình (USD)",
        "mode_label":      "🔄 Chế độ ghi",
        "mode_acc":        "Tích lũy mua thêm",
        "mode_ow":         "Ghi đè",
        "add_btn":         "➕ Thêm hoặc cập nhật",
        "del_btn":         "🗑️ Xóa",
        "success_add":     "✅ Cập nhật thành công!",
        "success_del":     "✅ Đã xóa!",
        "err_ticker":      "❌ Vui lòng nhập mã hợp lệ",
        "col_ticker":      "Mã",
        "col_name":        "Tên",
        "col_shares":      "Số lượng",
        "col_cost":        "Giá TB(USD)",
        "col_price":       "Giá hiện tại",
        "col_pnl_usd":     "Lãi/Lỗ(USD)",
        "col_pnl_pct":     "Tỷ suất",
        "refresh_btn":     "🔄 Làm mới",
        "market_closed":   "Đóng cửa",
        "market_pre":      "Trước giờ mở",
        "market_regular":  "Trong giờ",
        "market_post":     "Sau giờ đóng",
        "delay_note":      "⚠️ Dữ liệu Yahoo Finance miễn phí, trễ khoảng 15 phút",
        "analysis_tip":    "💡 Mẹo: Xu hướng thị trường Mỹ ảnh hưởng trực tiếp đến tâm lý mở cửa thị trường Đài Loan ngày hôm sau.",
    },
}


def _market_state_label(state: str, lang: str) -> str:
    t = _T[lang]
    mapping = {
        "PRE": t["market_pre"],
        "REGULAR": t["market_regular"],
        "POST": t["market_post"],
        "POSTPOST": t["market_post"],
        "PREPRE": t["market_pre"],
        "CLOSED": t["market_closed"],
    }
    return mapping.get(state.upper(), t["market_closed"])


def _render_price_card(result: dict, lang: str):
    """渲染單一美股即時報價卡片"""
    t = _T[lang]
    if not result.get("success"):
        st.markdown(f"""<div class="glass-card" style="padding:12px; border-left:4px solid #64748B;">
<span style="color:#94A3B8; font-size:0.85rem;">{result.get('ticker','?')} — 無法取得報價: {result.get('error','')}</span>
</div>""", unsafe_allow_html=True)
        return

    price = result["price"]
    change = result["change"]
    change_pct = result["change_percent"]
    ticker = result.get("ticker", result.get("symbol", ""))
    name_zh = result.get("name_zh", ticker)
    name_en = result.get("name_en", ticker)
    market_state = result.get("market_state", "UNKNOWN")

    if change > 0:
        color = t["up_color"]
        sign = "▲ +"
    elif change < 0:
        color = t["down_color"]
        sign = "▼ "
    else:
        color = "#94A3B8"
        sign = ""

    state_label = _market_state_label(market_state, lang)

    st.markdown(f"""<div class="glass-card" style="padding:14px 18px; margin-bottom:10px; border-left:4px solid {color}; background:linear-gradient(135deg,rgba(20,25,50,0.8),rgba(10,12,30,0.9));">
<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
<div>
<div style="font-size:0.75rem; color:#94A3B8; font-weight:600;">{ticker} &nbsp;|&nbsp; {name_zh} / {name_en}</div>
<div style="display:flex; align-items:baseline; gap:10px; margin-top:3px;">
<span style="font-size:1.85rem; font-weight:800; color:#F8FAFC; font-family:monospace;">${price:,.2f}</span>
<span style="font-size:1rem; font-weight:700; color:{color}; font-family:monospace;">{sign}{change:.2f} ({change_pct:+.2f}%)</span>
</div>
</div>
<div style="text-align:right;">
<div style="font-size:0.72rem; color:#64748B;">{t['prev_close']}</div>
<div style="font-size:0.9rem; color:#CBD5E1; font-family:monospace;">${result['prev_close']:,.2f}</div>
<div style="font-size:0.7rem; margin-top:3px; padding:2px 6px; border-radius:4px; background:rgba(100,116,139,0.2); color:#94A3B8; display:inline-block;">{state_label}</div>
</div>
</div>
</div>""", unsafe_allow_html=True)


def _load_us_portfolio() -> dict:
    """載入美股持倉 JSON"""
    path = os.path.join(config.BASE_DIR, "data", "us_portfolio.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_us_portfolio(data: dict):
    """儲存美股持倉 JSON"""
    path = os.path.join(config.BASE_DIR, "data", "us_portfolio.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def render(lang: str):
    """
    渲染美股看盤分頁。
    唯一對外接口：只需傳入語言設定。
    """
    t = _T.get(lang, _T["繁體中文"])
    st.markdown(f"### {t['tab_title']}")
    st.markdown(f"<div style='color:#94A3B8; font-size:0.9rem; margin-bottom:12px;'>{t['desc']}</div>", unsafe_allow_html=True)

    # ── 1. 自訂監控清單 ──────────────────────────────────────────
    st.markdown(f"#### {t['watchlist_title']}")

    if "us_watchlist" not in st.session_state:
        st.session_state.us_watchlist = get_us_watchlist_default()

    watchlist_input = st.text_input(
        t["watchlist_hint"],
        value=", ".join(st.session_state.us_watchlist),
        key="us_watchlist_input",
        label_visibility="collapsed"
    )

    col_apply, col_refresh, _ = st.columns([1, 1, 4])
    with col_apply:
        if st.button(t["watchlist_apply"], key="us_apply_watchlist", use_container_width=True):
            new_list = [s.strip().upper() for s in watchlist_input.split(",") if s.strip()]
            if new_list:
                st.session_state.us_watchlist = new_list
                st.rerun()
    with col_refresh:
        if st.button(t["refresh_btn"], key="us_refresh_btn", use_container_width=True):
            st.rerun()

    # ── 2. 即時報價卡片（2欄佈局）───────────────────────────────
    watchlist = st.session_state.us_watchlist
    results = []
    with st.spinner("抓取美股報價中..." if lang == "繁體中文" else "Fetching US stock prices..."):
        for ticker in watchlist:
            r = fetch_us_stock_price(ticker)
            r["ticker"] = ticker
            results.append(r)

    ncols = 2
    cols = st.columns(ncols)
    for idx, r in enumerate(results):
        with cols[idx % ncols]:
            _render_price_card(r, lang)

    st.markdown(f"<div style='font-size:0.75rem; color:#64748B; margin-bottom:16px;'>⚠️ {t['delay_note'].replace('⚠️ ','')}</div>", unsafe_allow_html=True)

    # ── 3. 分析提示 ──────────────────────────────────────────────
    st.info(t["analysis_tip"])

    st.markdown("---")

    # ── 4. 美股持倉追蹤 ──────────────────────────────────────────
    st.markdown(f"#### {t['portfolio_title']}")

    us_portfolio = _load_us_portfolio()

    if us_portfolio:
        import pandas as pd
        rows = []
        for ticker, info in us_portfolio.items():
            price_r = fetch_us_stock_price(ticker)
            live_price = price_r["price"] if price_r.get("success") else None
            shares = info["shares"]
            avg_cost = info["cost"]
            total_cost = shares * avg_cost
            if live_price:
                total_val = shares * live_price
                pnl_usd = total_val - total_cost
                pnl_pct = (pnl_usd / total_cost) * 100 if total_cost > 0 else 0
                price_str = f"${live_price:,.2f}"
            else:
                pnl_usd = 0
                pnl_pct = 0
                price_str = "N/A"

            pnl_color = "#EF4444" if pnl_usd >= 0 else "#10B981"
            pnl_str = f"<span style='color:{pnl_color}; font-weight:700;'>{'+' if pnl_usd >= 0 else ''}{pnl_usd:,.2f}</span>"
            pct_str = f"<span style='color:{pnl_color}; font-weight:700;'>{pnl_pct:+.2f}%</span>"

            name_info = US_STOCK_NAMES.get(ticker, {"zh": ticker, "en": ticker})

            rows.append({
                t["col_ticker"]: ticker,
                t["col_name"]:   f"{name_info['zh']} / {name_info['en']}",
                t["col_shares"]: f"{shares} 股",
                t["col_cost"]:   f"${avg_cost:,.2f}",
                t["col_price"]:  price_str,
                t["col_pnl_usd"]: pnl_str,
                t["col_pnl_pct"]: pct_str,
            })

        df = pd.DataFrame(rows)
        st.write(df.to_html(escape=False, index=False, justify="center"), unsafe_allow_html=True)
    else:
        st.info(t["portfolio_hint"])

    # ── 5. 持倉編輯器 ────────────────────────────────────────────
    with st.expander(t["add_title"], expanded=False):
        ec1, ec2, ec3, ec4 = st.columns([1, 2, 1, 1])
        with ec1:
            edit_ticker = st.text_input(t["ticker_label"], key="us_edit_ticker").strip().upper()
        with ec2:
            # 自動填入名稱提示
            name_hint = US_STOCK_NAMES.get(edit_ticker, {}).get("zh", "") if edit_ticker else ""
            edit_name_hint = st.text_input("名稱備註", value=name_hint, key="us_edit_name")
        with ec3:
            edit_shares = st.number_input(t["shares_label"], min_value=0.001, step=1.0, value=1.0, key="us_edit_shares")
        with ec4:
            edit_cost = st.number_input(t["cost_label"], min_value=0.01, step=0.01, value=100.0, key="us_edit_cost")

        write_mode = st.radio(
            t["mode_label"],
            [t["mode_acc"], t["mode_ow"]],
            index=0,
            horizontal=True,
            key="us_write_mode"
        )

        btn_add, btn_del, _ = st.columns([1, 1, 3])
        with btn_add:
            if st.button(t["add_btn"], type="primary", use_container_width=True, key="us_btn_add"):
                if not edit_ticker:
                    st.error(t["err_ticker"])
                else:
                    curr = _load_us_portfolio()
                    if edit_ticker in curr and write_mode == t["mode_acc"]:
                        old_shares = curr[edit_ticker]["shares"]
                        old_cost   = curr[edit_ticker]["cost"]
                        new_total  = old_shares + edit_shares
                        new_cost   = ((old_shares * old_cost) + (edit_shares * edit_cost)) / new_total
                        curr[edit_ticker] = {
                            "shares": round(new_total, 6),
                            "cost":   round(new_cost, 4),
                            "note":   edit_name_hint or curr[edit_ticker].get("note", "")
                        }
                    else:
                        curr[edit_ticker] = {
                            "shares": round(float(edit_shares), 6),
                            "cost":   round(float(edit_cost), 4),
                            "note":   edit_name_hint
                        }
                    _save_us_portfolio(curr)
                    st.success(t["success_add"])
                    st.rerun()

        with btn_del:
            if st.button(t["del_btn"], use_container_width=True, key="us_btn_del"):
                if not edit_ticker:
                    st.error(t["err_ticker"])
                else:
                    curr = _load_us_portfolio()
                    curr.pop(edit_ticker, None)
                    _save_us_portfolio(curr)
                    st.success(t["success_del"])
                    st.rerun()
