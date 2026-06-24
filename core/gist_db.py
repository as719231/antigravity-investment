# core/gist_db.py
# =====================================================================
# GitHub Gist 雲端資料庫（Cloud 版持久化方案）
# 職責：
#   用 GitHub Gist 作為免費雲端 JSON 資料庫。
#   本地開發時直接讀寫 data/ 目錄（不需要 Gist）。
#   Cloud 部署時從 Gist 讀寫（需要 GITHUB_TOKEN + GIST_ID）。
# =====================================================================

import json
import os
from pathlib import Path

_DATA_DIR = Path(__file__).parent.parent / "data"
_IS_CLOUD  = False  # 啟動時偵測

# 要同步的檔案清單（Gist filename -> local filename）
_GIST_FILES = {
    "portfolio.json":         "portfolio.json",
    "us_portfolio.json":      "us_portfolio.json",
    "price_alerts.json":      "price_alerts.json",
    "stop_loss_settings.json":"stop_loss_settings.json",
    "chat_memory.json":       "chat_memory.json",
    "knowledge_base.json":    "knowledge_base.json",
    "akira_profile.json":     "akira_profile.json",
    "lessons.json":           "lessons.json",
}


def _get_secrets() -> tuple:
    """
    取得 GitHub Token 和 Gist ID。
    優先從 streamlit.secrets 讀取（Cloud），
    其次從環境變數讀取（本地）。
    """
    try:
        import streamlit as st
        token   = st.secrets.get("GITHUB_TOKEN", "")
        gist_id = st.secrets.get("GIST_ID", "")
        if token and gist_id:
            return token, gist_id
    except Exception:
        pass

    token   = os.getenv("GITHUB_TOKEN", "")
    gist_id = os.getenv("GIST_ID", "")
    return token, gist_id


def is_cloud_mode() -> bool:
    """檢查是否在 Streamlit Cloud 上執行"""
    token, gist_id = _get_secrets()
    return bool(token and gist_id)


def read_gist_file(filename: str) -> dict | list:
    """
    從 GitHub Gist 讀取 JSON 檔案。
    如果不是 Cloud 模式，從本地讀取。
    """
    token, gist_id = _get_secrets()

    # 本地模式：直接讀 data/ 目錄
    if not (token and gist_id):
        local_path = _DATA_DIR / filename
        if local_path.exists():
            try:
                return json.loads(local_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {} if not filename.endswith("_list.json") else []

    # Cloud 模式：從 Gist 讀取
    try:
        import urllib.request
        url = f"https://api.github.com/gists/{gist_id}"
        req = urllib.request.Request(
            url,
            headers={"Authorization": f"token {token}",
                     "Accept": "application/vnd.github.v3+json"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            files = data.get("files", {})
            if filename in files:
                content = files[filename].get("content", "{}")
                return json.loads(content)
    except Exception as e:
        print(f"[gist_db] 讀取 {filename} 失敗: {e}")

    # Fallback：讀本地
    local_path = _DATA_DIR / filename
    if local_path.exists():
        try:
            return json.loads(local_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    return {}


def write_gist_file(filename: str, data: dict | list) -> bool:
    """
    寫入 JSON 到 GitHub Gist（Cloud 模式）或本地（本地模式）。
    Returns True if successful.
    """
    token, gist_id = _get_secrets()

    # 本地模式：直接寫 data/ 目錄
    if not (token and gist_id):
        local_path = _DATA_DIR / filename
        try:
            _DATA_DIR.mkdir(parents=True, exist_ok=True)
            local_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            return True
        except Exception as e:
            print(f"[gist_db] 本地寫入 {filename} 失敗: {e}")
            return False

    # Cloud 模式：寫入 Gist
    try:
        import urllib.request
        payload = json.dumps({
            "files": {
                filename: {
                    "content": json.dumps(data, ensure_ascii=False, indent=2)
                }
            }
        }).encode("utf-8")

        url = f"https://api.github.com/gists/{gist_id}"
        req = urllib.request.Request(
            url,
            data=payload,
            method="PATCH",
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json",
            }
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"[gist_db] Gist 寫入 {filename} 失敗: {e}")
        # 降級：寫本地
        try:
            local_path = _DATA_DIR / filename
            local_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
        except Exception:
            pass
        return False


def init_gist_if_needed(initial_files: dict = None):
    """
    首次部署時，把本地 data/ 檔案上傳到 Gist。
    只在 Gist 尚未有這些檔案時才執行。
    """
    token, gist_id = _get_secrets()
    if not (token and gist_id):
        return  # 本地模式不需要

    if initial_files:
        for fname, content in initial_files.items():
            write_gist_file(fname, content)
