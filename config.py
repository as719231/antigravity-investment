import os
from dotenv import load_dotenv

# 載入 .env 檔案
load_dotenv()

# --- 專案路徑設定 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PORTFOLIO_FILE = os.path.join(BASE_DIR, "data", "portfolio.json")
LESSONS_FILE = os.path.join(BASE_DIR, "data", "lessons.json")

# --- 金鑰金鑰 ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# 確保資料夾存在
os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
