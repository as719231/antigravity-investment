# ui/styles.py
# =====================================================================
# 全局 CSS 樣式系統 - 統一管理設計主題，積木化獨立
# 修改此檔案只影響外觀，不影響任何業務邏輯
# =====================================================================
import streamlit as st


def inject_global_css():
    """注入全域 CSS 樣式系統（深色玻璃質感設計）"""
    st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Noto+Sans+TC:wght@300;400;700&display=swap" rel="stylesheet">
<style>
html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"], .stApp, .stAppHeader, [class*="css"] {
    font-family: 'Outfit', 'Noto Sans TC', sans-serif !important;
    background-color: #0A0E17 !important;
    color: #E2E8F0 !important;
}
[data-testid="stSidebar"], [data-testid="stSidebarCollapseButton"] {
    background-color: #0F172A !important;
    border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
}
.gradient-text {
    background: linear-gradient(135deg, #10B981, #FBBF24);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.8rem;
    font-weight: 800;
    letter-spacing: -1px;
    margin-bottom: 5px;
}
.sub-header {
    font-size: 1.2rem;
    color: #94A3B8;
    margin-bottom: 30px;
    font-weight: 300;
}
.glass-card {
    background: rgba(15, 23, 42, 0.65);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    margin-bottom: 20px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.glass-card:hover {
    transform: translateY(-2px);
    border-color: rgba(16, 185, 129, 0.25);
    box-shadow: 0 12px 40px 0 rgba(16, 185, 129, 0.15);
}
.metric-title {
    font-size: 0.85rem;
    color: #94A3B8;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-weight: 600;
}
.metric-value {
    font-size: 1.8rem;
    font-weight: 800;
    margin: 5px 0px;
    color: #F8FAFC;
}
.metric-delta-up {
    color: #EF4444;
    font-size: 0.9rem;
    font-weight: 600;
}
.metric-delta-down {
    color: #10B981;
    font-size: 0.9rem;
    font-weight: 600;
}
.tag-bullish {
    background-color: rgba(239, 68, 68, 0.15);
    color: #EF4444;
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 0.8rem;
    font-weight: bold;
    display: inline-block;
    margin-right: 5px;
}
.tag-bearish {
    background-color: rgba(16, 185, 129, 0.15);
    color: #10B981;
    border: 1px solid rgba(16, 185, 129, 0.3);
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 0.8rem;
    font-weight: bold;
    display: inline-block;
    margin-right: 5px;
}
.tag-neutral {
    background-color: rgba(148, 163, 184, 0.15);
    color: #94A3B8;
    border: 1px solid rgba(148, 163, 184, 0.3);
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 0.8rem;
    font-weight: bold;
    display: inline-block;
    margin-right: 5px;
}
.stTabs [data-baseweb="tab-list"] {
    gap: 10px;
    background-color: transparent;
}
.stTabs [data-baseweb="tab"] {
    height: 50px;
    white-space: pre-wrap;
    background-color: rgba(30, 41, 59, 0.4);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 10px;
    color: #94A3B8;
    padding: 0px 20px;
    font-weight: 600;
    transition: all 0.3s ease;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #10B981, #FBBF24) !important;
    color: #0F172A !important;
    border: none !important;
    box-shadow: 0 4px 15px rgba(16, 185, 129, 0.25);
    font-weight: 800 !important;
}
table {
    width: 100% !important;
    border-collapse: separate !important;
    border-spacing: 0 !important;
    margin: 15px 0 !important;
    border-radius: 12px !important;
    overflow: hidden !important;
    border: 1px solid rgba(255, 255, 255, 0.05) !important;
}
th {
    background-color: #1E293B !important;
    color: #94A3B8 !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    font-size: 0.8rem !important;
    letter-spacing: 0.5px !important;
    padding: 12px 16px !important;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
}
td {
    padding: 14px 16px !important;
    color: #F8FAFC !important;
    font-size: 0.9rem !important;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
    background-color: rgba(15, 23, 42, 0.35) !important;
}
tr:last-child td { border-bottom: none !important; }
tr:hover td { background-color: rgba(16, 185, 129, 0.05) !important; }
div.stButton > button:first-child {
    background: linear-gradient(135deg, #10B981, #059669) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 8px 20px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 6px rgba(16, 185, 129, 0.15) !important;
}
div.stButton > button:first-child:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 12px rgba(16, 185, 129, 0.25) !important;
}
</style>
""", unsafe_allow_html=True)
