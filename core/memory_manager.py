# core/memory_manager.py
# =====================================================================
# 第一層：對話記憶管理模組
# 職責：儲存 / 讀取跨 Session 的對話歷史，最多保留 N 輪
# 積木說明：獨立模組，不影響 AI 邏輯或 UI，只做 JSON 讀寫
# =====================================================================

import json
import os
import datetime
from pathlib import Path

# 儲存路徑（在 data/ 資料夾下）
_DATA_DIR     = Path(__file__).parent.parent / "data"
_MEMORY_FILE  = _DATA_DIR / "chat_memory.json"

# 保留最近幾輪對話（1 輪 = 1 問 + 1 答）
MAX_ROUNDS = 20


def _load_raw() -> dict:
    """讀取 JSON 原始資料，不存在則回傳預設結構"""
    if not _MEMORY_FILE.exists():
        return {"sessions": [], "total_rounds": 0}
    try:
        with open(_MEMORY_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"sessions": [], "total_rounds": 0}


def _save_raw(data: dict):
    """寫入 JSON，失敗不 crash"""
    try:
        _DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(_MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[memory] 儲存失敗: {e}")


def save_conversation(user_text: str, ai_text: str, stock_id: str = ""):
    """
    儲存一輪對話（問 + 答）到持久化記憶。

    Parameters
    ----------
    user_text : 使用者問題
    ai_text   : AI 回答
    stock_id  : 當時查詢的股票代號（可選）
    """
    data = _load_raw()
    now  = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    entry = {
        "time":     now,
        "stock":    stock_id,
        "user":     user_text[:500],       # 限制長度，控制 token
        "ai":       ai_text[:1000],        # AI 回答最多 1000 字
    }
    data["sessions"].append(entry)
    data["total_rounds"] = len(data["sessions"])

    # 只保留最近 MAX_ROUNDS 輪
    if len(data["sessions"]) > MAX_ROUNDS:
        data["sessions"] = data["sessions"][-MAX_ROUNDS:]

    _save_raw(data)


def get_memory_context(max_rounds: int = 10) -> str:
    """
    取得記憶上下文字串，供注入 AI Prompt。

    Parameters
    ----------
    max_rounds : 帶入最近幾輪（預設 10 輪）

    Returns
    -------
    str  格式化的對話記憶段落，若無記憶則回傳空字串
    """
    data = _load_raw()
    sessions = data.get("sessions", [])
    if not sessions:
        return ""

    recent = sessions[-max_rounds:]
    lines  = []
    for s in recent:
        stock_tag = f"[{s['stock']}] " if s.get("stock") else ""
        lines.append(f"[{s['time']}] {stock_tag}主人問：{s['user']}")
        lines.append(f"  AI 回答摘要：{s['ai'][:300]}{'...' if len(s['ai']) > 300 else ''}")
        lines.append("")

    return (
        "====== 主人過去的對話記憶（請參考以了解主人的投資習慣與偏好）======\n"
        + "\n".join(lines)
        + "=================================================================\n"
    )


def get_stats() -> dict:
    """回傳記憶統計資訊"""
    data = _load_raw()
    sessions = data.get("sessions", [])
    if not sessions:
        return {"total": 0, "oldest": None, "newest": None}
    return {
        "total":  len(sessions),
        "oldest": sessions[0].get("time"),
        "newest": sessions[-1].get("time"),
    }


def clear_memory():
    """清除所有對話記憶"""
    _save_raw({"sessions": [], "total_rounds": 0})
