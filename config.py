import os
from dotenv import load_dotenv

# 載入 .env 檔案（本地開發用）
load_dotenv()

# --- 專案路徑設定 ---
BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
PORTFOLIO_FILE = os.path.join(BASE_DIR, "data", "portfolio.json")
LESSONS_FILE   = os.path.join(BASE_DIR, "data", "lessons.json")

# --- 從 Streamlit Secrets 或環境變數讀取 API Keys ---
def _get_secret(key: str, default: str = "") -> str:
    """
    優先從 st.secrets 讀取（Streamlit Cloud），
    其次從環境變數讀取（本地 .env）。
    """
    try:
        import streamlit as st
        val = st.secrets.get(key, "")
        if val:
            return val
    except Exception:
        pass
    return os.getenv(key, default)


# --- API 金鑰 ---
GEMINI_API_KEY  = _get_secret("GEMINI_API_KEY",  "")
FINMIND_TOKEN   = _get_secret("FINMIND_TOKEN",   "")
GITHUB_TOKEN    = _get_secret("GITHUB_TOKEN",    "")
GIST_ID         = _get_secret("GIST_ID",         "")

# --- 確保資料夾存在（本地模式用）---
os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
