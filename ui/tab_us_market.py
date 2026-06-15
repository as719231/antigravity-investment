# ui/tab_us_market.py
# =====================================================================
# 美股看盤分頁積木（比照台股，完整技術分析版）
# 職責：US 股票 UI 渲染，不碰台股、期貨任何邏輯
# =====================================================================

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import json
import os

import config
from core.us_data_provider import (
    fetch_us_stock_analysis,
    fetch_institutional_data,
    fetch_market_indices,
)
from core.realtime_provider import fetch_us_stock_price, US_STOCK_NAMES


# ── 多語言文字 ───────────────────────────────────────────────────────
_T = {
    "繁體中文": {
        "tab_title":     "🇺🇸 美股即時看盤（技術分析）",
        "input_label":   "輸入美股代號分析（例：AAPL / NVDA / TSM）",
        "input_btn":     "🔍 開始分析",
        "spinner":       "正在分析 {ticker}...",
        "price_card":    "即時報價",
        "prev_close":    "昨收",
        "close_price":   "最新收盤價",
        "rsi_label":     "RSI (14)",
        "rsi_ob":        "超買（偏貴）",
        "rsi_os":        "超賣（偏便宜）",
        "rsi_neutral":   "中性整理",
        "kd_label":      "KD (9,3,3)",
        "kd_bull":       "黃金交叉（偏多）",
        "kd_bear":       "死亡交叉（偏空）",
        "vol_label":     "波動率 (年化)",
        "vol_high":      "高波動 注意風險",
        "vol_low":       "低波動 穩健型",
        "vol_stable":    "正常波動",
        "yield_label":   "預估殖利率",
        "yield_sub":     "（依 Yahoo 最新配息）",
        "chart_title":   "📊 K 線圖 + 均線",
        "patterns_title":"🔔 形態警報",
        "no_signals":    "本期無明顯形態信號",
        "risk_title":    "風險評估",
        "ma5":           "5MA",
        "ma20":          "20MA",
        "ma60":          "60MA",
        "k_line":        "K 線",
        "rec_title":     "🤖 AI 操盤建議",
        "rec_reason":    "依據：",
        "rec_actions": {
            "buy":          "分批買進",
            "sell_partial": "考慮減倉",
            "liquidate":    "清倉防禦",
            "watch":        "觀望持倉",
        },
        "pt_title":      "📌 買賣參考價位",
        "pt_buy1":       "第一批買進",
        "pt_buy2":       "逢低第二批",
        "pt_stop":       "止損參考",
        "pt_tp1":        "第一目標",
        "pt_tp2":        "第二目標",
        "pt_sup":        "主要支撐",
        "pt_res":        "主要壓力",
        "pt_note":       "以上價位為技術面計算之參考，非絕對保證，請自行判斷風險",
        "inst_title":    "🏛️ 機構持股與做空比例",
        "inst_pct":      "機構持股比",
        "insider_pct":   "內部人持股比",
        "retail_pct":    "散戶持股比（推算）",
        "short_pct":     "做空比例（Float）",
        "short_ratio":   "空頭回補天數",
        "inst_na":       "機構持股資料暫不可用",
        "market_title":  "📈 大盤指數即時動態",
        "prev":          "昨收",
        "watchlist_title":"📋 快速看盤清單（報價監控）",
        "watchlist_hint": "輸入代號，逗號分隔（例：AAPL, NVDA, TSLA）",
        "watchlist_apply":"🔄 套用",
        "refresh_btn":   "🔄 刷新報價",
        "portfolio_title":"💼 美股持倉追蹤（USD 計帳）",
        "portfolio_hint": "尚未新增美股持倉，請在下方新增。",
        "add_title":     "➕ 新增 / 更新美股持倉",
        "ticker_label":  "股票代號",
        "shares_label":  "持有股數",
        "cost_label":    "平均買入成本 (USD/股)",
        "mode_label":    "🔄 寫入模式",
        "mode_acc":      "加碼累加（自動計算加權均價）",
        "mode_ow":       "直接覆蓋",
        "add_btn":       "➕ 新增或更新",
        "del_btn":       "🗑️ 刪除",
        "success_add":   "✅ 持倉已更新！",
        "success_del":   "✅ 已刪除！",
        "err_ticker":    "❌ 請輸入有效代號",
        "col_ticker":    "代號",
        "col_name":      "公司名稱",
        "col_shares":    "股數",
        "col_cost":      "均價(USD)",
        "col_price":     "即時報價",
        "col_pnl":       "損益(USD)",
        "col_pct":       "報酬率",
        "delay_note":    "⚠️ K 線為前一交易日收盤資料；即時報價約有 15 分鐘延遲。",
        "up_color":      "#EF4444",
        "dn_color":      "#10B981",
    },
    "English": {
        "tab_title":     "🇺🇸 US Market — Technical Analysis",
        "input_label":   "Enter US stock ticker to analyze (e.g. AAPL / NVDA / TSM)",
        "input_btn":     "🔍 Analyze",
        "spinner":       "Analyzing {ticker}...",
        "price_card":    "Live Price",
        "prev_close":    "Prev Close",
        "close_price":   "Latest Close",
        "rsi_label":     "RSI (14)",
        "rsi_ob":        "Overbought (Expensive)",
        "rsi_os":        "Oversold (Cheap)",
        "rsi_neutral":   "Neutral / Consolidation",
        "kd_label":      "Stochastic KD (9,3,3)",
        "kd_bull":       "Golden Cross (Bullish)",
        "kd_bear":       "Death Cross (Bearish)",
        "vol_label":     "Volatility (Annualized)",
        "vol_high":      "High vol – Watch risk",
        "vol_low":       "Low vol – Steady stock",
        "vol_stable":    "Normal volatility",
        "yield_label":   "Est. Dividend Yield",
        "yield_sub":     "(From latest Yahoo data)",
        "chart_title":   "📊 Candlestick Chart + MAs",
        "patterns_title":"🔔 Pattern Alerts",
        "no_signals":    "No notable patterns detected",
        "risk_title":    "Risk Assessment",
        "ma5":           "5MA",
        "ma20":          "20MA",
        "ma60":          "60MA",
        "k_line":        "Candle",
        "rec_title":     "🤖 AI Trading Recommendation",
        "rec_reason":    "Basis:",
        "rec_actions": {
            "buy":          "Staged Buy Entry",
            "sell_partial": "Consider Partial Sell",
            "liquidate":    "Defensive Liquidation",
            "watch":        "Watch & Hold",
        },
        "pt_title":      "📌 Price Reference Levels",
        "pt_buy1":       "Entry 1",
        "pt_buy2":       "Entry 2 (Dip)",
        "pt_stop":       "Stop Loss",
        "pt_tp1":        "Target 1",
        "pt_tp2":        "Target 2",
        "pt_sup":        "Support",
        "pt_res":        "Resistance",
        "pt_note":       "Technical reference only. Always apply your own judgment.",
        "inst_title":    "🏛️ Institutional Holdings & Short Interest",
        "inst_pct":      "Institutional Ownership",
        "insider_pct":   "Insider Ownership",
        "retail_pct":    "Retail (Estimated)",
        "short_pct":     "Short % of Float",
        "short_ratio":   "Short Ratio (Days to Cover)",
        "inst_na":       "Institutional data unavailable",
        "market_title":  "📈 Live Market Indices",
        "prev":          "Prev",
        "watchlist_title":"📋 Watchlist",
        "watchlist_hint": "Enter tickers separated by commas (e.g. AAPL, NVDA, TSLA)",
        "watchlist_apply":"🔄 Apply",
        "refresh_btn":   "🔄 Refresh",
        "portfolio_title":"💼 US Stock Portfolio (USD)",
        "portfolio_hint": "No positions yet. Add below.",
        "add_title":     "➕ Add / Update Position",
        "ticker_label":  "Ticker",
        "shares_label":  "Shares Owned",
        "cost_label":    "Avg Cost (USD/share)",
        "mode_label":    "🔄 Write Mode",
        "mode_acc":      "Accumulate (Auto weighted avg cost)",
        "mode_ow":       "Overwrite",
        "add_btn":       "➕ Add or Update",
        "del_btn":       "🗑️ Delete",
        "success_add":   "✅ Portfolio updated!",
        "success_del":   "✅ Deleted!",
        "err_ticker":    "❌ Enter a valid ticker",
        "col_ticker":    "Ticker",
        "col_name":      "Company",
        "col_shares":    "Shares",
        "col_cost":      "Avg Cost",
        "col_price":     "Live Price",
        "col_pnl":       "P&L (USD)",
        "col_pct":       "Return %",
        "delay_note":    "⚠️ Chart data is prior-day close; live prices have ~15 min delay.",
        "up_color":      "#EF4444",
        "dn_color":      "#10B981",
    },
    "日本語": {
        "tab_title":     "🇺🇸 米国株テクニカル分析",
        "input_label":   "銘柄コードを入力（例：AAPL / NVDA / TSM）",
        "input_btn":     "🔍 分析開始",
        "spinner":       "{ticker} を分析中...",
        "price_card":    "現在値",
        "prev_close":    "前日終値",
        "close_price":   "最新終値",
        "rsi_label":     "RSI (14)",
        "rsi_ob":        "買われ過ぎ",
        "rsi_os":        "売られ過ぎ",
        "rsi_neutral":   "中立",
        "kd_label":      "ストキャスティクス KD",
        "kd_bull":       "ゴールデンクロス",
        "kd_bear":       "デッドクロス",
        "vol_label":     "ボラティリティ（年率）",
        "vol_high":      "高ボラ",
        "vol_low":       "低ボラ",
        "vol_stable":    "通常",
        "yield_label":   "配当利回り（推計）",
        "yield_sub":     "（Yahoo最新データ）",
        "chart_title":   "📊 ローソク足チャート",
        "patterns_title":"🔔 パターンアラート",
        "no_signals":    "顕著なパターンなし",
        "risk_title":    "リスク評価",
        "ma5":           "5MA",
        "ma20":          "20MA",
        "ma60":          "60MA",
        "k_line":        "ローソク",
        "rec_title":     "🤖 AI 売買シグナル",
        "rec_reason":    "根拠：",
        "rec_actions": {
            "buy":          "分割買い",
            "sell_partial": "部分利確",
            "liquidate":    "全決済",
            "watch":        "様子見",
        },
        "pt_title":      "📌 売買参考価格",
        "pt_buy1":       "第1買い",
        "pt_buy2":       "押し目第2買い",
        "pt_stop":       "損切り",
        "pt_tp1":        "第1目標",
        "pt_tp2":        "第2目標",
        "pt_sup":        "支持",
        "pt_res":        "抵抗",
        "pt_note":       "テクニカル参考価格。投資判断は自己責任でお願いします。",
        "inst_title":    "🏛️ 機関投資家保有比率・空売り比率",
        "inst_pct":      "機関投資家比率",
        "insider_pct":   "インサイダー比率",
        "retail_pct":    "個人投資家（推計）",
        "short_pct":     "空売り比率",
        "short_ratio":   "空売り残日数",
        "inst_na":       "機関投資家データなし",
        "market_title":  "📈 主要指数リアルタイム",
        "prev":          "前日",
        "watchlist_title":"📋 ウォッチリスト",
        "watchlist_hint": "コード入力（例：AAPL, NVDA, TSLA）",
        "watchlist_apply":"🔄 適用",
        "refresh_btn":   "🔄 更新",
        "portfolio_title":"💼 米国株ポートフォリオ（USD）",
        "portfolio_hint": "ポジションなし。下記から追加。",
        "add_title":     "➕ ポジション追加・更新",
        "ticker_label":  "ティッカー",
        "shares_label":  "保有株数",
        "cost_label":    "平均取得価格（USD）",
        "mode_label":    "書き込みモード",
        "mode_acc":      "買い増し（加重平均自動計算）",
        "mode_ow":       "上書き",
        "add_btn":       "➕ 追加・更新",
        "del_btn":       "🗑️ 削除",
        "success_add":   "✅ 更新完了！",
        "success_del":   "✅ 削除完了！",
        "err_ticker":    "❌ 有効なコードを入力",
        "col_ticker":    "コード",
        "col_name":      "銘柄名",
        "col_shares":    "株数",
        "col_cost":      "平均価格",
        "col_price":     "現在値",
        "col_pnl":       "損益（USD）",
        "col_pct":       "収益率",
        "delay_note":    "⚠️ チャートは前日終値。現在値は約15分遅延。",
        "up_color":      "#EF4444",
        "dn_color":      "#10B981",
    },
    "ไทย": {
        "tab_title":     "🇺🇸 หุ้นสหรัฐ - วิเคราะห์ทางเทคนิค",
        "input_label":   "ป้อนรหัสหุ้น (เช่น AAPL / NVDA / TSM)",
        "input_btn":     "🔍 วิเคราะห์",
        "spinner":       "กำลังวิเคราะห์ {ticker}...",
        "price_card":    "ราคาปัจจุบัน",
        "prev_close":    "ราคาปิดก่อนหน้า",
        "close_price":   "ราคาปิดล่าสุด",
        "rsi_label":     "RSI (14)",
        "rsi_ob":        "ซื้อมากเกินไป",
        "rsi_os":        "ขายมากเกินไป",
        "rsi_neutral":   "เป็นกลาง",
        "kd_label":      "KD Stochastic",
        "kd_bull":       "Golden Cross",
        "kd_bear":       "Death Cross",
        "vol_label":     "ความผันผวน (รายปี)",
        "vol_high":      "ผันผวนสูง",
        "vol_low":       "ผันผวนต่ำ",
        "vol_stable":    "ปกติ",
        "yield_label":   "อัตราผลตอบแทนเงินปันผล",
        "yield_sub":     "(ข้อมูล Yahoo)",
        "chart_title":   "📊 กราฟแท่งเทียน",
        "patterns_title":"🔔 สัญญาณรูปแบบ",
        "no_signals":    "ไม่มีรูปแบบที่ชัดเจน",
        "risk_title":    "การประเมินความเสี่ยง",
        "ma5":           "5MA",
        "ma20":          "20MA",
        "ma60":          "60MA",
        "k_line":        "แท่งเทียน",
        "rec_title":     "🤖 คำแนะนำ AI",
        "rec_reason":    "เหตุผล:",
        "rec_actions": {
            "buy":          "ซื้อแบบทยอย",
            "sell_partial": "ขายบางส่วน",
            "liquidate":    "ขายทั้งหมด",
            "watch":        "รอดู",
        },
        "pt_title":      "📌 ราคาอ้างอิง",
        "pt_buy1":       "ซื้อล็อตแรก",
        "pt_buy2":       "ซื้อล็อตสอง",
        "pt_stop":       "จุดตัดขาดทุน",
        "pt_tp1":        "เป้าที่ 1",
        "pt_tp2":        "เป้าที่ 2",
        "pt_sup":        "แนวรับ",
        "pt_res":        "แนวต้าน",
        "pt_note":       "ราคาอ้างอิงทางเทคนิคเท่านั้น",
        "inst_title":    "🏛️ การถือครองสถาบัน & Short Interest",
        "inst_pct":      "สถาบันถือ",
        "insider_pct":   "Insider ถือ",
        "retail_pct":    "รายย่อย (ประมาณ)",
        "short_pct":     "Short %",
        "short_ratio":   "วันปิด Short",
        "inst_na":       "ไม่มีข้อมูลสถาบัน",
        "market_title":  "📈 ดัชนีตลาดหลัก",
        "prev":          "ก่อนหน้า",
        "watchlist_title":"📋 รายการติดตาม",
        "watchlist_hint": "ป้อนรหัสคั่นด้วยจุลภาค",
        "watchlist_apply":"🔄 ยืนยัน",
        "refresh_btn":   "🔄 รีเฟรช",
        "portfolio_title":"💼 พอร์ตหุ้นสหรัฐ (USD)",
        "portfolio_hint": "ยังไม่มีตำแหน่ง",
        "add_title":     "➕ เพิ่ม/อัปเดต",
        "ticker_label":  "รหัสหุ้น",
        "shares_label":  "จำนวนหุ้น",
        "cost_label":    "ราคาเฉลี่ย (USD)",
        "mode_label":    "โหมดบันทึก",
        "mode_acc":      "ซื้อเพิ่ม",
        "mode_ow":       "เขียนทับ",
        "add_btn":       "➕ เพิ่ม/อัปเดต",
        "del_btn":       "🗑️ ลบ",
        "success_add":   "✅ อัปเดตสำเร็จ!",
        "success_del":   "✅ ลบสำเร็จ!",
        "err_ticker":    "❌ กรุณากรอกรหัสที่ถูกต้อง",
        "col_ticker":    "รหัส",
        "col_name":      "ชื่อ",
        "col_shares":    "จำนวน",
        "col_cost":      "ราคาเฉลี่ย",
        "col_price":     "ราคาปัจจุบัน",
        "col_pnl":       "กำไร/ขาดทุน",
        "col_pct":       "ผลตอบแทน%",
        "delay_note":    "⚠️ กราฟเป็นข้อมูลปิดวันก่อน ราคาปัจจุบันล่าช้า ~15 นาที",
        "up_color":      "#EF4444",
        "dn_color":      "#10B981",
    },
    "Tiếng Việt": {
        "tab_title":     "🇺🇸 Cổ phiếu Mỹ - Phân tích kỹ thuật",
        "input_label":   "Nhập mã cổ phiếu Mỹ (VD: AAPL / NVDA / TSM)",
        "input_btn":     "🔍 Phân tích",
        "spinner":       "Đang phân tích {ticker}...",
        "price_card":    "Giá hiện tại",
        "prev_close":    "Đóng cửa trước",
        "close_price":   "Giá đóng cửa gần nhất",
        "rsi_label":     "RSI (14)",
        "rsi_ob":        "Mua quá mức",
        "rsi_os":        "Bán quá mức",
        "rsi_neutral":   "Trung tính",
        "kd_label":      "Stochastic KD",
        "kd_bull":       "Golden Cross (Tăng)",
        "kd_bear":       "Death Cross (Giảm)",
        "vol_label":     "Biến động (Năm)",
        "vol_high":      "Biến động cao",
        "vol_low":       "Biến động thấp",
        "vol_stable":    "Bình thường",
        "yield_label":   "Tỷ suất cổ tức",
        "yield_sub":     "(Yahoo Finance)",
        "chart_title":   "📊 Biểu đồ nến",
        "patterns_title":"🔔 Cảnh báo mô hình",
        "no_signals":    "Không có mô hình đáng chú ý",
        "risk_title":    "Đánh giá rủi ro",
        "ma5":           "5MA",
        "ma20":          "20MA",
        "ma60":          "60MA",
        "k_line":        "Nến",
        "rec_title":     "🤖 Khuyến nghị AI",
        "rec_reason":    "Lý do:",
        "rec_actions": {
            "buy":          "Mua từng phần",
            "sell_partial": "Chốt lời một phần",
            "liquidate":    "Bán toàn bộ",
            "watch":        "Chờ quan sát",
        },
        "pt_title":      "📌 Mức giá tham chiếu",
        "pt_buy1":       "Vào lệnh 1",
        "pt_buy2":       "Gom thêm",
        "pt_stop":       "Cắt lỗ",
        "pt_tp1":        "Mục tiêu 1",
        "pt_tp2":        "Mục tiêu 2",
        "pt_sup":        "Hỗ trợ",
        "pt_res":        "Kháng cự",
        "pt_note":       "Giá tham chiếu kỹ thuật. Tự chịu trách nhiệm đầu tư.",
        "inst_title":    "🏛️ Tỷ lệ nắm giữ tổ chức & Short",
        "inst_pct":      "Tổ chức nắm giữ",
        "insider_pct":   "Nội bộ nắm giữ",
        "retail_pct":    "Nhà đầu tư lẻ (ước tính)",
        "short_pct":     "Tỷ lệ Short",
        "short_ratio":   "Ngày bù Short",
        "inst_na":       "Không có dữ liệu tổ chức",
        "market_title":  "📈 Chỉ số thị trường",
        "prev":          "Trước",
        "watchlist_title":"📋 Danh sách theo dõi",
        "watchlist_hint": "Nhập mã cách nhau bằng dấu phẩy",
        "watchlist_apply":"🔄 Áp dụng",
        "refresh_btn":   "🔄 Làm mới",
        "portfolio_title":"💼 Danh mục cổ phiếu Mỹ (USD)",
        "portfolio_hint": "Chưa có vị thế nào.",
        "add_title":     "➕ Thêm / Cập nhật vị thế",
        "ticker_label":  "Mã cổ phiếu",
        "shares_label":  "Số lượng",
        "cost_label":    "Giá mua TB (USD/cp)",
        "mode_label":    "Chế độ ghi",
        "mode_acc":      "Tích lũy mua thêm",
        "mode_ow":       "Ghi đè",
        "add_btn":       "➕ Thêm hoặc cập nhật",
        "del_btn":       "🗑️ Xóa",
        "success_add":   "✅ Cập nhật thành công!",
        "success_del":   "✅ Đã xóa!",
        "err_ticker":    "❌ Nhập mã hợp lệ",
        "col_ticker":    "Mã",
        "col_name":      "Tên công ty",
        "col_shares":    "Số CP",
        "col_cost":      "Giá TB(USD)",
        "col_price":     "Giá hiện tại",
        "col_pnl":       "Lãi/Lỗ(USD)",
        "col_pct":       "Tỷ suất",
        "delay_note":    "⚠️ Biểu đồ dùng dữ liệu đóng cửa hôm trước; giá trực tiếp trễ ~15 phút.",
        "up_color":      "#EF4444",
        "dn_color":      "#10B981",
    },
}

DEFAULT_WATCHLIST = ["AAPL", "NVDA", "TSLA", "MSFT", "AMZN", "TSM", "QQQ", "VOO"]


# ── 工具函式 ─────────────────────────────────────────────────────────

def _load_us_portfolio() -> dict:
    path = os.path.join(config.BASE_DIR, "data", "us_portfolio.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_us_portfolio(data: dict):
    path = os.path.join(config.BASE_DIR, "data", "us_portfolio.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def _sign_color(val: float, t: dict) -> tuple:
    """回傳 (sign_str, color_str)"""
    if val > 0:   return ("▲ +", t["up_color"])
    elif val < 0: return ("▼ ", t["dn_color"])
    else:          return ("",   "#94A3B8")


# ── 區塊渲染函式 ─────────────────────────────────────────────────────

def _render_market_indices(indices: dict, t: dict):
    """大盤指數橫排卡片"""
    st.markdown(f"#### {t['market_title']}")
    items = list(indices.items())
    cols  = st.columns(len(items))
    for i, (key, r) in enumerate(items):
        with cols[i]:
            if r.get("success"):
                sign, color = _sign_color(r["change"], t)
                st.markdown(f"""<div class="glass-card" style="padding:10px 12px; text-align:center; border-left:3px solid {color}; margin-bottom:8px;">
<div style="font-size:0.65rem; color:#94A3B8; font-weight:600;">{r['flag']} {r['name_zh']}</div>
<div style="font-size:1.15rem; font-weight:800; color:#F8FAFC; font-family:monospace;">{r['price']:,.2f}</div>
<div style="font-size:0.78rem; color:{color}; font-weight:700;">{sign}{r['change']:.2f} ({r['change_pct']:+.2f}%)</div>
</div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""<div class="glass-card" style="padding:10px 12px; text-align:center; margin-bottom:8px;">
<div style="font-size:0.65rem; color:#94A3B8;">{r.get('flag','📊')} {r.get('name_zh', key)}</div>
<div style="font-size:0.85rem; color:#64748B;">N/A</div>
</div>""", unsafe_allow_html=True)


def _render_realtime_card(ticker: str, t: dict):
    """即時報價卡片（比照台股）"""
    rt = fetch_us_stock_price(ticker)
    if not rt.get("success"):
        st.warning(f"無法取得 {ticker} 即時報價")
        return

    price      = rt["price"]
    change     = rt["change"]
    change_pct = rt["change_percent"]
    sign, color = _sign_color(change, t)

    st.markdown(f"""<div class="glass-card" style="padding:16px 20px; margin-bottom:16px; background:linear-gradient(135deg,rgba(20,25,50,0.8),rgba(10,12,30,0.9)); border-left:4px solid {color};">
<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
<div>
<div style="font-size:0.8rem; color:#94A3B8; font-weight:600;">⚡ {t['price_card']} — {ticker}</div>
<div style="display:flex; align-items:baseline; gap:12px; margin-top:4px;">
<span style="font-size:2.0rem; font-weight:800; color:#F8FAFC; font-family:monospace;">${price:,.2f}</span>
<span style="font-size:1.1rem; font-weight:700; color:{color}; font-family:monospace;">{sign}{change:.2f} ({change_pct:+.2f}%)</span>
</div>
</div>
<div style="text-align:right;">
<div style="font-size:0.72rem; color:#64748B;">{t['prev_close']}</div>
<div style="font-size:0.95rem; font-weight:600; color:#CBD5E1; font-family:monospace;">${rt['prev_close']:,.2f}</div>
</div>
</div>
</div>""", unsafe_allow_html=True)


def _render_metric_cards(metrics: dict, t: dict):
    """5 個指標卡片（比照台股佈局）"""
    c1, c2, c3, c4, c5 = st.columns(5)

    close = metrics["close"]
    rsi   = metrics["rsi"]
    k     = metrics["k"]
    d     = metrics["d"]
    vol   = metrics["volatility"]
    yield_pct = metrics["est_yield"]

    # 收盤
    with c1:
        st.markdown(f"""<div class="glass-card" style="padding:15px;">
<div class="metric-title">{t['close_price']}</div>
<div class="metric-value">${close:,.2f}</div>
<div style="font-size:0.85rem; color:#94A3B8;">USD</div>
</div>""", unsafe_allow_html=True)

    # RSI
    rsi_status = t["rsi_ob"] if rsi > 70 else t["rsi_os"] if rsi < 30 else t["rsi_neutral"]
    with c2:
        st.markdown(f"""<div class="glass-card" style="padding:15px;">
<div class="metric-title">{t['rsi_label']}</div>
<div class="metric-value">{rsi:.1f}</div>
<div style="font-size:0.85rem; color:#94A3B8;">{rsi_status}</div>
</div>""", unsafe_allow_html=True)

    # KD
    kd_status = t["kd_bull"] if k > d else t["kd_bear"]
    with c3:
        st.markdown(f"""<div class="glass-card" style="padding:15px;">
<div class="metric-title">{t['kd_label']}</div>
<div class="metric-value">K {k:.1f} / D {d:.1f}</div>
<div style="font-size:0.85rem; color:#94A3B8;">{kd_status}</div>
</div>""", unsafe_allow_html=True)

    # 波動率
    vol_status = t["vol_high"] if vol > 0.35 else t["vol_low"] if vol < 0.15 else t["vol_stable"]
    with c4:
        st.markdown(f"""<div class="glass-card" style="padding:15px;">
<div class="metric-title">{t['vol_label']}</div>
<div class="metric-value">{vol*100:.1f}%</div>
<div style="font-size:0.85rem; color:#94A3B8;">{vol_status}</div>
</div>""", unsafe_allow_html=True)

    # 殖利率
    with c5:
        yield_str = f"{yield_pct:.2f}%" if yield_pct > 0 else "N/A"
        st.markdown(f"""<div class="glass-card" style="padding:15px;">
<div class="metric-title">{t['yield_label']}</div>
<div class="metric-value">{yield_str}</div>
<div style="font-size:0.85rem; color:#94A3B8;">{t['yield_sub']}</div>
</div>""", unsafe_allow_html=True)


def _render_chart_and_signals(df, signals: list, metrics: dict, t: dict):
    """K 線圖 + 形態警報（比照台股雙欄佈局）"""
    col_chart, col_signals = st.columns([2, 1])

    with col_chart:
        st.markdown(f"### {t['chart_title']}")
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=df["date"],
            open=df["open"], high=df["high"],
            low=df["low"],   close=df["close"],
            increasing_line_color="#EF4444",
            decreasing_line_color="#10B981",
            increasing_fillcolor="rgba(239,68,68,0.4)",
            decreasing_fillcolor="rgba(16,185,129,0.4)",
            name=t["k_line"]
        ))
        fig.add_trace(go.Scatter(x=df["date"], y=df["ma5"],  line=dict(color="#38BDF8", width=1.5), name=t["ma5"]))
        fig.add_trace(go.Scatter(x=df["date"], y=df["ma20"], line=dict(color="#F43F5E", width=1.5), name=t["ma20"]))
        fig.add_trace(go.Scatter(x=df["date"], y=df["ma60"], line=dict(color="#F59E0B", width=1.5), name=t["ma60"]))
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0B0F19",
            plot_bgcolor="rgba(30,41,59,0.3)",
            xaxis_rangeslider_visible=False,
            height=450,
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_signals:
        st.markdown(f"### {t['patterns_title']}")

        # 風險卡片
        risk_score = metrics["risk_score"]
        risk_level = metrics["risk_level"]
        risk_color = "#10B981" if risk_score < 35 else "#F59E0B" if risk_score < 65 else "#EF4444"
        st.markdown(f"""<div class="glass-card" style="border-left:5px solid {risk_color}; padding:18px; margin-bottom:20px;">
<span class="metric-title">{t['risk_title']}</span>
<div style="font-size:1.8rem; font-weight:800; color:{risk_color}; margin:5px 0;">
{risk_level}
</div>
<div style="font-size:0.85rem; color:#94A3B8;">Score: {risk_score}/100</div>
</div>""", unsafe_allow_html=True)

        # 形態信號
        if not signals:
            st.markdown(f"<div style='color:#64748B; font-size:0.9rem; padding:12px;'>✅ {t['no_signals']}</div>", unsafe_allow_html=True)
        else:
            for s in signals:
                tag_class = "tag-bullish" if s["type"] == "bullish" else "tag-bearish" if s["type"] == "bearish" else "tag-neutral"
                st.markdown(f'<span class="{tag_class}">{s["name"]}</span><br>', unsafe_allow_html=True)


def _render_recommendation(rec: dict, t: dict):
    """AI 操盤建議卡片"""
    if not rec:
        return
    action    = rec.get("action", "watch")
    reason_zh = rec["reason"].get("繁體中文", "")
    rec_color = "#10B981" if action == "buy" else "#94A3B8" if action == "watch" else "#F59E0B" if action == "sell_partial" else "#EF4444"
    action_label = t["rec_actions"].get(action, action)
    st.markdown(f"""<div class="glass-card" style="border-left:5px solid {rec_color}; padding:18px; margin-bottom:12px; background:rgba(30,41,59,0.6);">
<span class="metric-title">{t['rec_title']}</span>
<div style="font-size:1.6rem; font-weight:800; color:{rec_color}; margin:5px 0;">{action_label}</div>
<div style="font-size:0.88rem; color:#E2E8F0; line-height:1.5; margin-top:8px;">
<b>{t['rec_reason']}</b> {reason_zh}
</div>
</div>""", unsafe_allow_html=True)


def _render_price_targets(pt: dict, t: dict):
    """買賣參考價位卡片"""
    if not pt:
        return
    st.markdown(f"""<div class="glass-card" style="border-left:5px solid #38BDF8; padding:14px 18px; margin-bottom:12px; background:rgba(15,25,50,0.7);">
<div style="font-size:0.85rem; font-weight:700; color:#38BDF8; margin-bottom:8px;">{t['pt_title']}</div>
<div style="display:grid; grid-template-columns:1fr 1fr; gap:6px; font-size:0.82rem;">
<div style="color:#94A3B8;">{t['pt_buy1']}</div><div style="color:#94A3B8;">{t['pt_tp1']}</div>
<div>
<span style="color:#10B981; font-weight:700;">▶ {t['pt_buy1']}: </span><span style="color:#F8FAFC; font-weight:600;">${pt['buy_ideal']:,.2f}</span><br>
<span style="color:#6EE7B7; font-weight:600;">▶ {t['pt_buy2']}: </span><span style="color:#F8FAFC; font-weight:600;">${pt['buy_dip']:,.2f}</span><br>
<span style="color:#EF4444; font-weight:600;">✕ {t['pt_stop']}: </span><span style="color:#FCA5A5; font-weight:600;">${pt['stop_loss']:,.2f}</span>
</div>
<div>
<span style="color:#F59E0B; font-weight:700;">◀ {t['pt_tp1']}: </span><span style="color:#F8FAFC; font-weight:600;">${pt['take_profit_1']:,.2f}</span><br>
<span style="color:#FCD34D; font-weight:600;">◀ {t['pt_tp2']}: </span><span style="color:#F8FAFC; font-weight:600;">${pt['take_profit_2']:,.2f}</span><br>
<span style="color:#CBD5E1; font-size:0.78rem;">{t['pt_sup']}: {pt['primary_support']} | {t['pt_res']}: {pt['primary_resistance']}</span>
</div>
</div>
<div style="font-size:0.72rem; color:#64748B; margin-top:6px;">⚠️ {t['pt_note']}</div>
</div>""", unsafe_allow_html=True)


def _render_institutional(inst: dict, t: dict):
    """機構持股 + 做空比例卡片"""
    st.markdown(f"#### {t['inst_title']}")
    if not inst.get("available"):
        st.markdown(f"<div style='color:#64748B; font-size:0.85rem;'>{t['inst_na']}</div>", unsafe_allow_html=True)
        return

    # 持股比例橫條
    inst_pct    = inst["inst_pct"]
    insider_pct = inst["insider_pct"]
    retail_pct  = inst["retail_pct"]
    short_pct   = inst["short_pct"]
    short_ratio = inst["short_ratio"]

    # 做空比例警示色
    short_color = "#EF4444" if short_pct > 15 else "#F59E0B" if short_pct > 8 else "#10B981"

    st.markdown(f"""<div class="glass-card" style="padding:16px 18px; margin-bottom:12px;">
<div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; font-size:0.85rem;">
<div>
<div style="color:#94A3B8; font-size:0.75rem; font-weight:600; margin-bottom:6px;">持股結構</div>
<div style="margin-bottom:4px;">
<span style="color:#38BDF8;">🏛 {t['inst_pct']}</span>
<span style="float:right; font-weight:700; color:#F8FAFC;">{inst_pct:.1f}%</span>
</div>
<div style="background:rgba(30,41,59,0.6); border-radius:4px; height:6px; margin-bottom:8px;">
<div style="background:#38BDF8; height:100%; width:{min(inst_pct,100)}%; border-radius:4px;"></div>
</div>
<div style="margin-bottom:4px;">
<span style="color:#F59E0B;">👔 {t['insider_pct']}</span>
<span style="float:right; font-weight:700; color:#F8FAFC;">{insider_pct:.1f}%</span>
</div>
<div style="margin-bottom:4px;">
<span style="color:#94A3B8;">👥 {t['retail_pct']}</span>
<span style="float:right; font-weight:700; color:#F8FAFC;">{retail_pct:.1f}%</span>
</div>
</div>
<div>
<div style="color:#94A3B8; font-size:0.75rem; font-weight:600; margin-bottom:6px;">做空壓力</div>
<div style="margin-bottom:4px;">
<span style="color:{short_color};">🩳 {t['short_pct']}</span>
<span style="float:right; font-weight:800; color:{short_color};">{short_pct:.1f}%</span>
</div>
<div style="background:rgba(30,41,59,0.6); border-radius:4px; height:6px; margin-bottom:8px;">
<div style="background:{short_color}; height:100%; width:{min(short_pct*4,100)}%; border-radius:4px;"></div>
</div>
<div style="margin-bottom:4px;">
<span style="color:#94A3B8;">📅 {t['short_ratio']}</span>
<span style="float:right; font-weight:700; color:#F8FAFC;">{short_ratio:.1f} 天</span>
</div>
</div>
</div>
</div>""", unsafe_allow_html=True)


def _render_watchlist_section(t: dict):
    """底部快速監控清單"""
    st.markdown("---")
    st.markdown(f"#### {t['watchlist_title']}")

    if "us_watchlist" not in st.session_state:
        st.session_state.us_watchlist = DEFAULT_WATCHLIST[:]

    wl_input = st.text_input(
        t["watchlist_hint"], value=", ".join(st.session_state.us_watchlist),
        key="us_wl_input", label_visibility="collapsed"
    )
    ca, cb, _ = st.columns([1, 1, 4])
    with ca:
        if st.button(t["watchlist_apply"], key="us_wl_apply", use_container_width=True):
            new = [s.strip().upper() for s in wl_input.split(",") if s.strip()]
            if new:
                st.session_state.us_watchlist = new
                st.rerun()
    with cb:
        if st.button(t["refresh_btn"], key="us_wl_refresh", use_container_width=True):
            st.rerun()

    watchlist = st.session_state.us_watchlist
    with st.spinner("取得報價中..."):
        rows_data = []
        for ticker in watchlist:
            r = fetch_us_stock_price(ticker)
            if r.get("success"):
                sign, color = _sign_color(r["change"], t)
                name_info = US_STOCK_NAMES.get(ticker, {"zh": ticker, "en": ticker})
                rows_data.append({
                    t["col_ticker"]: ticker,
                    t["col_name"]:   f"{name_info['zh']} / {name_info['en']}",
                    t["col_price"]:  f"<span style='font-family:monospace; font-weight:700;'>${r['price']:,.2f}</span>",
                    t["col_pct"]:    f"<span style='color:{color}; font-weight:700;'>{sign}{r['change_percent']:.2f}%</span>",
                })
    if rows_data:
        df_display = pd.DataFrame(rows_data)
        st.write(df_display.to_html(escape=False, index=False, justify="center"), unsafe_allow_html=True)


def _render_portfolio_section(t: dict):
    """美股持倉追蹤 + 編輯器"""
    st.markdown("---")
    st.markdown(f"#### {t['portfolio_title']}")

    portfolio = _load_us_portfolio()
    if portfolio:
        rows = []
        for ticker, info in portfolio.items():
            rq = fetch_us_stock_price(ticker)
            live_price = rq["price"] if rq.get("success") else None
            shares   = info["shares"]
            avg_cost = info["cost"]
            total_cost = shares * avg_cost
            if live_price:
                pnl = shares * live_price - total_cost
                pct = (pnl / total_cost) * 100 if total_cost > 0 else 0
                price_str = f"<span style='font-family:monospace;'>${live_price:,.2f}</span>"
                p_color   = t["up_color"] if pnl >= 0 else t["dn_color"]
                pnl_str   = f"<span style='color:{p_color}; font-weight:700;'>{'+' if pnl>=0 else ''}{pnl:,.2f}</span>"
                pct_str   = f"<span style='color:{p_color}; font-weight:700;'>{pct:+.2f}%</span>"
            else:
                price_str = "N/A"
                pnl_str   = "N/A"
                pct_str   = "N/A"
            name_info = US_STOCK_NAMES.get(ticker, {"zh": ticker, "en": ticker})
            rows.append({
                t["col_ticker"]: ticker,
                t["col_name"]:   f"{name_info['zh']} / {name_info['en']}",
                t["col_shares"]: f"{shares} 股",
                t["col_cost"]:   f"${avg_cost:,.2f}",
                t["col_price"]:  price_str,
                t["col_pnl"]:    pnl_str,
                t["col_pct"]:    pct_str,
            })
        st.write(pd.DataFrame(rows).to_html(escape=False, index=False, justify="center"), unsafe_allow_html=True)
    else:
        st.info(t["portfolio_hint"])

    with st.expander(t["add_title"], expanded=False):
        ec1, ec2, ec3, ec4 = st.columns([1, 2, 1, 1])
        with ec1:
            edit_ticker = st.text_input(t["ticker_label"], key="us_edit_ticker").strip().upper()
        with ec2:
            name_hint = US_STOCK_NAMES.get(edit_ticker, {}).get("zh", "") if edit_ticker else ""
            st.text_input("備註", value=name_hint, key="us_edit_name")
        with ec3:
            edit_shares = st.number_input(t["shares_label"], min_value=0.001, step=1.0, value=1.0, key="us_edit_shares")
        with ec4:
            edit_cost = st.number_input(t["cost_label"], min_value=0.01, step=0.01, value=100.0, key="us_edit_cost")
        write_mode = st.radio(t["mode_label"], [t["mode_acc"], t["mode_ow"]], horizontal=True, key="us_wm")
        ba, bd, _ = st.columns([1, 1, 3])
        with ba:
            if st.button(t["add_btn"], type="primary", use_container_width=True, key="us_btn_add"):
                if not edit_ticker:
                    st.error(t["err_ticker"])
                else:
                    curr = _load_us_portfolio()
                    if edit_ticker in curr and write_mode == t["mode_acc"]:
                        os_ = curr[edit_ticker]["shares"]
                        oc_ = curr[edit_ticker]["cost"]
                        ns  = os_ + edit_shares
                        nc  = ((os_ * oc_) + (edit_shares * edit_cost)) / ns
                        curr[edit_ticker] = {"shares": round(ns, 6), "cost": round(nc, 4)}
                    else:
                        curr[edit_ticker] = {"shares": round(float(edit_shares), 6), "cost": round(float(edit_cost), 4)}
                    _save_us_portfolio(curr)
                    st.success(t["success_add"])
                    st.rerun()
        with bd:
            if st.button(t["del_btn"], use_container_width=True, key="us_btn_del"):
                if not edit_ticker:
                    st.error(t["err_ticker"])
                else:
                    curr = _load_us_portfolio()
                    curr.pop(edit_ticker, None)
                    _save_us_portfolio(curr)
                    st.success(t["success_del"])
                    st.rerun()


# ── 主入口 ───────────────────────────────────────────────────────────

def render(lang: str):
    """
    渲染美股看盤分頁（完整技術分析版）。
    唯一對外接口：只需傳入語言設定。
    """
    t = _T.get(lang, _T["繁體中文"])

    # ── 大盤指數（最頂端，提供背景判斷）──────────────────────────
    with st.spinner("載入大盤指數..."):
        indices = fetch_market_indices()
    if indices:
        _render_market_indices(indices, t)

    st.markdown("---")

    # ── 個股分析入口 ─────────────────────────────────────────────
    st.markdown(f"### {t['tab_title']}")
    col_input, col_btn = st.columns([4, 1])
    with col_input:
        ticker_input = st.text_input(
            t["input_label"],
            value=st.session_state.get("us_last_ticker", "AAPL"),
            key="us_ticker_input",
            label_visibility="collapsed",
            placeholder=t["input_label"]
        ).strip().upper()
    with col_btn:
        do_analyze = st.button(t["input_btn"], type="primary", use_container_width=True, key="us_analyze_btn")

    # 若有輸入就分析（首次或按鈕）
    if ticker_input:
        st.session_state["us_last_ticker"] = ticker_input

    if do_analyze or (ticker_input and "us_analysis_cache" not in st.session_state):
        with st.spinner(t["spinner"].format(ticker=ticker_input)):
            analysis = fetch_us_stock_analysis(ticker_input)
            inst     = fetch_institutional_data(ticker_input)
        st.session_state["us_analysis_cache"] = analysis
        st.session_state["us_inst_cache"]     = inst
        st.session_state["us_last_ticker"]    = ticker_input

    analysis = st.session_state.get("us_analysis_cache", {})
    inst     = st.session_state.get("us_inst_cache", {})

    if "error" in analysis:
        st.error(analysis["error"])
    elif analysis:
        ticker   = analysis.get("ticker", ticker_input)
        df       = analysis["df"]
        metrics  = analysis["metrics"]
        signals  = analysis["signals"]
        pt       = analysis["price_targets"]
        rec      = analysis.get("recommendation")

        # 即時報價
        _render_realtime_card(ticker, t)

        # 指標卡片
        _render_metric_cards(metrics, t)

        # K線圖 + 形態偵測
        _render_chart_and_signals(df, signals, metrics, t)

        # AI 建議 + 價位
        col_a, col_b = st.columns(2)
        with col_a:
            _render_recommendation(rec, t)
        with col_b:
            _render_price_targets(pt, t)

        # 機構持股
        _render_institutional(inst, t)

    # 延遲說明
    st.markdown(f"<div style='font-size:0.75rem; color:#64748B; margin-top:4px;'>{t['delay_note']}</div>", unsafe_allow_html=True)

    # ── 底部：快速看盤清單 + 持倉追蹤 ───────────────────────────
    _render_watchlist_section(t)
    _render_portfolio_section(t)
