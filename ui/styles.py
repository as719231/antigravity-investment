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

/* ══════════════════════════════════════════════
   📱 手機響應式設計 (Mobile Responsive Design)
   所有 max-width:768px 規則只影響手機，電腦版不受影響。
   ══════════════════════════════════════════════ */

@media (max-width: 768px) {

    /* 1. 全局字體與間距 */
    html, body { font-size: 14px !important; }
    .gradient-text { font-size: 1.6rem !important; letter-spacing: -0.5px !important; }
    .sub-header { font-size: 0.9rem !important; margin-bottom: 12px !important; }

    /* 2. 主內容區留出底部導覽欄空間 */
    [data-testid="stMainBlockContainer"],
    .main .block-container {
        padding-bottom: 72px !important;
        padding-left: 12px !important;
        padding-right: 12px !important;
    }

    /* 3. 側邊欄寬度限制 */
    [data-testid="stSidebar"] {
        min-width: 260px !important;
        max-width: 85vw !important;
    }

    /* 4. Columns 自動堆疊 */
    [data-testid="column"] {
        width: 100% !important;
        flex: 1 1 100% !important;
        min-width: 100% !important;
    }
    [data-testid="stHorizontalBlock"] {
        flex-wrap: wrap !important;
        gap: 8px !important;
    }

    /* 5. 分頁標籤列固定在底部 */
    .stTabs [data-baseweb="tab-list"] {
        position: fixed !important;
        bottom: 0 !important;
        left: 0 !important;
        right: 0 !important;
        z-index: 9999 !important;
        background: #0F172A !important;
        border-top: 1px solid rgba(255,255,255,0.08) !important;
        display: flex !important;
        justify-content: space-around !important;
        align-items: stretch !important;
        padding: 4px 0 env(safe-area-inset-bottom, 4px) !important;
        height: 60px !important;
        gap: 0 !important;
        margin: 0 !important;
        border-radius: 0 !important;
        box-shadow: 0 -4px 20px rgba(0,0,0,0.5) !important;
        overflow-x: auto !important;
        -webkit-overflow-scrolling: touch !important;
    }
    .stTabs [data-baseweb="tab"] {
        flex: 0 0 auto !important;
        min-width: 60px !important;
        max-width: 85px !important;
        height: 52px !important;
        padding: 4px 4px !important;
        border-radius: 0 !important;
        border: none !important;
        background: transparent !important;
        font-size: 0.58rem !important;
        font-weight: 600 !important;
        color: #64748B !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        transition: color 0.2s ease !important;
    }
    .stTabs [aria-selected="true"] {
        background: transparent !important;
        color: #10B981 !important;
        border-bottom: 2px solid #10B981 !important;
        box-shadow: none !important;
        font-weight: 800 !important;
    }
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 8px !important;
    }

    /* 6. 指標卡片壓縮 */
    .glass-card {
        padding: 12px 14px !important;
        margin-bottom: 8px !important;
        border-radius: 12px !important;
    }
    .metric-value { font-size: 1.35rem !important; }
    .metric-title { font-size: 0.7rem !important; }

    /* 7. 按鈕觸控目標放大 */
    div.stButton > button:first-child {
        min-height: 48px !important;
        font-size: 0.95rem !important;
        padding: 12px 16px !important;
    }
    .stDownloadButton > button {
        min-height: 48px !important;
    }

    /* 8. 輸入框放大 */
    .stTextInput input, .stNumberInput input {
        font-size: 1rem !important;
        min-height: 44px !important;
    }

    /* 9. 表格橫向捲動 */
    table {
        display: block !important;
        overflow-x: auto !important;
        -webkit-overflow-scrolling: touch !important;
        font-size: 0.78rem !important;
    }
    th, td {
        padding: 8px 10px !important;
        font-size: 0.78rem !important;
        white-space: nowrap !important;
    }

    /* 10. 隱藏電腦版專用元素 */
    .desktop-only { display: none !important; }
}

/* iPhone SE / 超小螢幕 */
@media (max-width: 390px) {
    .stTabs [data-baseweb="tab"] { font-size: 0.5rem !important; min-width: 50px !important; }
    .gradient-text { font-size: 1.3rem !important; }
    .metric-value { font-size: 1.1rem !important; }
}

</style>
""", unsafe_allow_html=True)
