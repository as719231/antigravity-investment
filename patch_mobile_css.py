#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Patch styles.py to add mobile responsive CSS"""

with open('ui/styles.py', encoding='utf-8') as f:
    content = f.read()

MOBILE_CSS = '''
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
'''

# Insert before </style>
OLD = '</style>\n""", unsafe_allow_html=True)'
NEW = MOBILE_CSS + '\n</style>\n""", unsafe_allow_html=True)'

if OLD in content:
    content = content.replace(OLD, NEW)
    with open('ui/styles.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: mobile CSS added to styles.py")
else:
    print("ERROR: closing tag not found!")
    print("Last 100 chars:", repr(content[-100:]))
