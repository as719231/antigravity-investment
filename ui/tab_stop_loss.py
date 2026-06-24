# ui/tab_stop_loss.py
# =====================================================================
# 停損追蹤看板（方案 B 完整版）
# 職責：
#   渲染「停損管理」子面板，嵌入至 tab_portfolio
#   - 每筆持倉顯示損益% + 停損設定 + 距停損距離（彩色警示）
#   - 新增/修改/刪除停損設定
#   - 三種模式：固定比率 / 固定價格 / 移動停損
#   - 整體持倉最大虧損警示
# =====================================================================

import streamlit as st
from core.stop_loss_manager import (
    get_all_stops, get_stop_summary, set_stop_loss,
    remove_stop, clear_all_triggered, reset_triggered,
)


# ── 顏色 & 狀態設定 ──────────────────────────────────────────────────
_STATUS_CONFIG = {
    "safe":      {"color": "#10B981", "bg": "rgba(16,185,129,0.08)", "border": "#10B981", "icon": "✅", "label": "安全"},
    "warning":   {"color": "#F59E0B", "bg": "rgba(245,158,11,0.12)", "border": "#F59E0B", "icon": "⚠️", "label": "接近停損"},
    "danger":    {"color": "#EF4444", "bg": "rgba(239,68,68,0.18)",  "border": "#EF4444", "icon": "🔴", "label": "極度危險"},
    "triggered": {"color": "#7C3AED", "bg": "rgba(124,58,237,0.15)", "border": "#7C3AED", "icon": "💥", "label": "已觸發"},
}

_STOP_TYPE_LABELS = {
    "pct":      "📉 固定比率停損",
    "price":    "💲 固定價格停損",
    "trailing": "🏃 移動停損（Trailing Stop）",
}


def _render_stop_card(sid: str, name: str, cost: float, price: float,
                      shares: int, summary: dict):
    """渲染單筆停損卡片"""
    if not summary.get("has_stop"):
        return

    cfg    = _STATUS_CONFIG.get(summary["status"], _STATUS_CONFIG["safe"])
    dist   = summary["distance_pct"]
    stop_p = summary["stop_price"]
    pnl    = summary["paper_pnl_pct"]
    stype  = summary["stop_type"]
    ta     = summary.get("trailing_active", False)
    lock   = summary.get("lock_in_profit_pct")

    # 距停損進度條（100%=在停損線，0%=遠離停損線）
    bar_danger_pct = max(0, min(100, int(100 - dist * 5)))

    # 移動停損徽章
    trailing_badge = ""
    if stype == "trailing":
        if ta:
            lock_txt  = f"鎖定獲利 {lock:+.1f}%" if lock is not None else "已啟動"
            trailing_badge = f'<span style="background:rgba(99,102,241,0.2); color:#818CF8; border:1px solid #6366F1; padding:2px 8px; border-radius:12px; font-size:0.65rem; font-weight:700;">🏃 移動中 · {lock_txt}</span>'
        else:
            trig_pct = summary.get("trailing_trigger_pct", 15)
            trailing_badge = f'<span style="background:rgba(245,158,11,0.1); color:#F59E0B; border:1px solid #F59E0B55; padding:2px 8px; border-radius:12px; font-size:0.65rem;">⏳ 等待觸發 (+{trig_pct}%)</span>'

    pnl_color   = "#EF4444" if pnl < 0 else "#10B981"
    dist_color  = cfg["color"]
    dist_text   = f"距停損 {dist:.1f}%" if not summary.get("triggered") else "已觸發"

    st.markdown(f"""
<div style="border:1px solid {cfg['border']}44; border-left:4px solid {cfg['border']};
background:{cfg['bg']}; border-radius:10px; padding:14px 18px; margin-bottom:10px;">

  <!-- 上排：名稱、損益、狀態 -->
  <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
    <div>
      <span style="font-size:0.8rem; color:#94A3B8; font-weight:600;">{sid}</span>
      <span style="font-size:1rem; font-weight:800; color:#F8FAFC; margin-left:6px;">{name}</span>
      &nbsp;{trailing_badge}
    </div>
    <div style="text-align:right;">
      <span style="font-size:1.2rem; font-weight:900; color:{pnl_color};">{pnl:+.2f}%</span>
      <span style="font-size:0.72rem; color:#64748B; margin-left:6px;">{cfg['icon']} {cfg['label']}</span>
    </div>
  </div>

  <!-- 中排：停損線資訊 -->
  <div style="display:flex; gap:16px; margin-top:10px; font-size:0.78rem; flex-wrap:wrap;">
    <span style="color:#94A3B8;">成本 <b style="color:#F8FAFC;">{cost:.2f}</b></span>
    <span style="color:#94A3B8;">現價 <b style="color:#F8FAFC;">{price:.2f}</b></span>
    <span style="color:#94A3B8;">停損線 <b style="color:{cfg['color']};">{stop_p:.2f}</b></span>
    <span style="color:{dist_color}; font-weight:700;">{dist_text}</span>
    <span style="color:#64748B;">{_STOP_TYPE_LABELS.get(stype, stype)}</span>
  </div>

  <!-- 下排：危險程度進度條 -->
  <div style="margin-top:8px; background:rgba(255,255,255,0.06); border-radius:4px; height:5px; overflow:hidden;">
    <div style="width:{bar_danger_pct}%; height:100%; background:{cfg['color']}; border-radius:4px; transition:width 0.5s;"></div>
  </div>
  <div style="display:flex; justify-content:space-between; font-size:0.62rem; color:#475569; margin-top:2px;">
    <span>停損線 {stop_p:.2f}</span>
    <span style="color:{cfg['color']};">{'← 現價接近此處' if dist < 5 else ''}</span>
    <span>現價 {price:.2f}</span>
  </div>

</div>
""", unsafe_allow_html=True)


def render(portfolio: dict, prices: dict, lang: str = "繁體中文"):
    """
    渲染停損追蹤看板。

    Parameters
    ----------
    portfolio : dict  {stock_id: {name, shares, cost, ...}}
    prices    : dict  {stock_id: current_price}
    lang      : str
    """
    st.markdown("---")
    st.markdown("### 🛡️ 停損追蹤看板")
    st.markdown(
        "<div style='color:#94A3B8; font-size:0.85rem; margin-bottom:16px;'>"
        "為每筆持倉設定個別停損機制，跌破時立即提醒。支援固定比率、固定價格、移動停損三種模式。"
        "</div>",
        unsafe_allow_html=True
    )

    stops_data = get_all_stops()

    # ── 整體持倉虧損警示 ────────────────────────────────────────────
    total_cost_val  = 0
    total_mkt_val   = 0
    any_warning     = False
    max_loss_items  = []

    for sid, pos in portfolio.items():
        price = prices.get(sid)
        if price and pos.get("cost") and pos.get("shares"):
            cost_v = pos["cost"] * pos["shares"]
            mkt_v  = price * pos["shares"]
            total_cost_val += cost_v
            total_mkt_val  += mkt_v
            pnl_pct = (price - pos["cost"]) / pos["cost"] * 100
            if pnl_pct <= -5:
                max_loss_items.append((sid, pos.get("name",""), pnl_pct))
            summary = get_stop_summary(sid, price)
            if summary.get("status") in ("warning", "danger", "triggered"):
                any_warning = True

    if total_cost_val > 0:
        portfolio_pnl_pct = (total_mkt_val - total_cost_val) / total_cost_val * 100
        pf_color = "#EF4444" if portfolio_pnl_pct < 0 else "#10B981"
        warning_txt = ""
        if portfolio_pnl_pct <= -10:
            warning_txt = " 🔴 整體持倉虧損超過 10%！建議全面審視部位。"
        elif portfolio_pnl_pct <= -5:
            warning_txt = " ⚠️ 整體持倉虧損超過 5%，請提高警戒。"

        st.markdown(f"""
<div style="padding:12px 18px; background:rgba(30,41,59,0.6); border-radius:10px;
border-left:4px solid {pf_color}; margin-bottom:16px; display:flex; justify-content:space-between; align-items:center;">
  <div>
    <span style="font-size:0.75rem; color:#94A3B8;">整體持倉損益</span>
    <span style="font-size:1.4rem; font-weight:900; color:{pf_color}; margin-left:10px;">{portfolio_pnl_pct:+.2f}%</span>
    <span style="font-size:0.75rem; color:#EF4444;">{warning_txt}</span>
  </div>
  <div style="font-size:0.78rem; color:#64748B; text-align:right;">
    市值 {total_mkt_val:,.0f}<br>成本 {total_cost_val:,.0f}
  </div>
</div>""", unsafe_allow_html=True)

    # ── 有停損設定的持倉：顯示停損卡片 ─────────────────────────────
    active_stops = [sid for sid in portfolio if sid in stops_data]

    if active_stops:
        for sid in active_stops:
            pos   = portfolio[sid]
            price = prices.get(sid, pos.get("cost", 0))
            summary = get_stop_summary(sid, price)
            _render_stop_card(
                sid    = sid,
                name   = pos.get("name", sid),
                cost   = pos.get("cost", 0),
                price  = price,
                shares = pos.get("shares", 0),
                summary= summary,
            )

        # 清除已觸發按鈕
        col_cl, _ = st.columns([1, 3])
        with col_cl:
            if st.button("🧹 清除已觸發停損記錄", key="sl_clear_triggered"):
                clear_all_triggered()
                st.toast("已清除所有觸發記錄", icon="✅")
                st.rerun()
    else:
        st.info("ℹ️ 目前沒有持倉設定停損，請在下方「設定停損」區塊新增。")

    # ── 停損設定表單 ─────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### ⚙️ 設定/修改停損")

    if not portfolio:
        st.warning("持倉追蹤看板尚無持倉，請先在上方新增持倉。")
        return

    # 選擇股票
    pf_options = {f"{sid} {pos.get('name','')}": sid for sid, pos in portfolio.items()}
    selected_label = st.selectbox(
        "選擇持倉股票",
        options=list(pf_options.keys()),
        key="sl_stock_select"
    )
    selected_sid = pf_options[selected_label]
    pos = portfolio[selected_sid]
    cost = pos.get("cost", 0)
    shares = pos.get("shares", 0)
    current_price = prices.get(selected_sid, cost)
    existing = stops_data.get(selected_sid, {})

    # 顯示目前設定摘要
    if existing:
        ex_type  = existing.get("stop_type", "pct")
        ex_sprice= existing.get("stop_price", 0)
        ex_spct  = existing.get("stop_pct", 8)
        ex_ta    = existing.get("trailing_active", False)
        ex_color = "#10B981" if not existing.get("triggered") else "#7C3AED"
        st.markdown(f"""<div style="padding:8px 14px; background:rgba(30,41,59,0.5); border-radius:8px;
font-size:0.8rem; color:#94A3B8; margin-bottom:10px; border-left:3px solid {ex_color};">
<b>目前停損設定：</b> {_STOP_TYPE_LABELS.get(ex_type, ex_type)} &nbsp;｜&nbsp;
停損線 <b style="color:{ex_color};">{ex_sprice:.2f} 元</b>
{' &nbsp;｜&nbsp; 移動停損<b style="color:#818CF8;">已啟動</b>' if ex_ta else ''}
</div>""", unsafe_allow_html=True)

    form_col1, form_col2 = st.columns(2)

    with form_col1:
        stop_type_label = st.selectbox(
            "停損模式",
            options=list(_STOP_TYPE_LABELS.values()),
            index=list(_STOP_TYPE_LABELS.keys()).index(existing.get("stop_type","pct")) if existing else 0,
            key="sl_type_select"
        )
        stop_type = {v: k for k, v in _STOP_TYPE_LABELS.items()}[stop_type_label]

    with form_col2:
        if stop_type == "price":
            stop_price_input = st.number_input(
                "停損目標價（元）",
                min_value=0.01,
                value=float(existing.get("stop_price", round(cost * 0.92, 2))),
                step=0.5,
                format="%.2f",
                key="sl_price_input"
            )
            stop_pct_input = round((cost - stop_price_input) / cost * 100, 1)
            st.caption(f"相當於從成本跌 {stop_pct_input:.1f}%")
        else:
            # 預設值
            default_pct = existing.get("stop_pct", 8.0)
            stop_pct_input = st.number_input(
                "停損幅度（%）",
                min_value=1.0, max_value=30.0,
                value=float(default_pct),
                step=0.5,
                format="%.1f",
                key="sl_pct_input"
            )
            stop_price_input = round(cost * (1 - stop_pct_input / 100), 2)
            st.caption(f"停損線 = {stop_price_input:.2f} 元")

    # 移動停損進階設定
    if stop_type == "trailing":
        with st.expander("🏃 移動停損進階設定", expanded=True):
            tr_col1, tr_col2 = st.columns(2)
            with tr_col1:
                trailing_trigger = st.number_input(
                    "啟動門檻（帳面獲利達幾%時啟動）",
                    min_value=5.0, max_value=50.0,
                    value=float(existing.get("trailing_trigger_pct", 15.0)),
                    step=1.0, format="%.0f",
                    key="sl_trigger_pct"
                )
            with tr_col2:
                lock_profit = st.number_input(
                    "最低鎖定獲利%（停損線不低於此）",
                    min_value=0.0, max_value=20.0,
                    value=float(existing.get("lock_pct", 5.0)),
                    step=1.0, format="%.0f",
                    key="sl_lock_pct"
                )
            st.markdown(f"""<div style="padding:8px 12px; background:rgba(99,102,241,0.1);
border-radius:6px; font-size:0.78rem; color:#A5B4FC;">
🏃 <b>移動停損說明</b>：當帳面獲利達 <b>+{trailing_trigger:.0f}%</b> 時啟動；
之後每次股價創新高，停損線自動上移（回撤 {stop_pct_input:.0f}%），
但最低保底鎖住獲利 <b>+{lock_profit:.0f}%</b>。
</div>""", unsafe_allow_html=True)
    else:
        trailing_trigger = existing.get("trailing_trigger_pct", 15.0)
        lock_profit      = existing.get("lock_pct", 5.0)

    # 操作按鈕
    btn_col1, btn_col2, btn_col3 = st.columns([2, 2, 1])
    with btn_col1:
        if st.button("💾 儲存停損設定", type="primary", use_container_width=True, key="sl_save_btn"):
            set_stop_loss(
                stock_id    = selected_sid,
                name        = pos.get("name", selected_sid),
                cost        = cost,
                stop_type   = stop_type,
                stop_pct    = stop_pct_input,
                stop_price  = stop_price_input if stop_type == "price" else None,
                trailing_trigger_pct = trailing_trigger,
                lock_pct    = lock_profit,
                highest_price = current_price,
            )
            type_zh = {"pct": "固定比率", "price": "固定價格", "trailing": "移動停損"}
            st.toast(
                f"✅ {pos.get('name',selected_sid)} 停損設定完成！"
                f"模式：{type_zh.get(stop_type,'--')}，停損線 {stop_price_input:.2f} 元",
                icon="🛡️"
            )
            st.rerun()

    with btn_col2:
        if existing:
            if st.button("🔄 重置觸發狀態", use_container_width=True, key="sl_reset_btn"):
                reset_triggered(selected_sid)
                st.toast(f"✅ {selected_sid} 停損已重置，重新監控中", icon="✅")
                st.rerun()

    with btn_col3:
        if existing:
            if st.button("🗑️ 刪除", use_container_width=True, key="sl_delete_btn"):
                remove_stop(selected_sid)
                st.toast(f"已刪除 {selected_sid} 的停損設定", icon="🗑️")
                st.rerun()

    # ── 停損模式說明 ─────────────────────────────────────────────────
    with st.expander("📖 三種停損模式說明"):
        st.markdown("""
| 模式 | 說明 | 適合對象 |
|------|------|---------|
| 📉 **固定比率停損** | 設定從買入成本跌幾%就出場（如 -8%） | 大多數長線/波段投資人 |
| 💲 **固定價格停損** | 設定一個絕對價格，跌到就提醒 | 有明確支撐位分析者 |
| 🏃 **移動停損** | 股價每次創新高，停損線自動上移；獲利達門檻後啟動，確保不會「從賺到賠」 | 趨勢追蹤、波段操作者 |

> ⚠️ **重要聲明**：本系統只提供**警示提醒**，不會自動執行任何買賣。所有投資決策請由 Akira 自行判斷。
        """)
