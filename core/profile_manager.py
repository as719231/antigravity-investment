# core/profile_manager.py
# =====================================================================
# 第二層：Akira 個人投資檔案管理模組
# 職責：學習並累積使用者的投資偏好、常看股票、風險態度、過去疑慮
# 積木說明：獨立模組，讀寫 data/akira_profile.json，不影響其他邏輯
# =====================================================================

import json
import os
import datetime
import re
from pathlib import Path

_DATA_DIR    = Path(__file__).parent.parent / "data"
_PROFILE_FILE = _DATA_DIR / "akira_profile.json"


# ── 預設個人檔案結構 ─────────────────────────────────────────────────
_DEFAULT_PROFILE = {
    "owner":          "Akira",
    "created":        None,
    "last_updated":   None,

    # 投資風格（從對話中自動推斷）
    "risk_style":     "穩健型",      # 穩健型 / 積極型 / 保守型
    "invest_horizon": "長期",         # 短線 / 中線 / 長期

    # 常關注的股票（自動統計查詢次數）
    "watched_stocks": {},             # {"0050": 12, "2330": 8, ...}

    # 明確表達過的投資原則（從對話提取）
    "stated_principles": [],          # ["不開槓桿", "喜歡 ETF", ...]

    # 曾問過的擔憂 / 疑慮（最多保留 20 條）
    "past_concerns": [],              # [{"time": "...", "concern": "..."}]

    # 曾讚賞 / 採納的建議
    "liked_advice": [],               # ["建議買 0050", ...]

    # 買賣記錄摘要（從持倉檔案同步）
    "trade_summary": [],

    # 偏好指標（自動從問題中推斷）
    "preferred_indicators": [],       # ["RSI", "KD", "均線"]

    # 問過最多次的問題類型
    "top_question_types": {},         # {"技術分析": 15, "基本面": 3, ...}
}


def _load() -> dict:
    if not _PROFILE_FILE.exists():
        profile = dict(_DEFAULT_PROFILE)
        profile["created"] = datetime.datetime.now().strftime("%Y-%m-%d")
        return profile
    try:
        with open(_PROFILE_FILE, encoding="utf-8") as f:
            data = json.load(f)
        # 補上可能缺少的新欄位
        for k, v in _DEFAULT_PROFILE.items():
            if k not in data:
                data[k] = v
        return data
    except Exception:
        return dict(_DEFAULT_PROFILE)


def _save(data: dict):
    try:
        _DATA_DIR.mkdir(parents=True, exist_ok=True)
        data["last_updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        with open(_PROFILE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[profile] 儲存失敗: {e}")


# ── 自動學習規則 ─────────────────────────────────────────────────────

def _detect_question_type(text: str) -> str:
    """從問題文字推斷問題類型"""
    text_lower = text.lower()
    if any(k in text_lower for k in ["rsi", "kd", "ma", "均線", "k線", "技術", "型態", "支撐", "壓力"]):
        return "技術分析"
    if any(k in text_lower for k in ["本益比", "pe", "財報", "eps", "營收", "獲利", "基本面"]):
        return "基本面分析"
    if any(k in text_lower for k in ["新聞", "消息", "事件", "利多", "利空", "法說"]):
        return "新聞事件"
    if any(k in text_lower for k in ["買", "賣", "進場", "出場", "停損", "停利"]):
        return "買賣決策"
    if any(k in text_lower for k in ["etf", "0050", "006208", "00878", "指數"]):
        return "ETF/指數"
    if any(k in text_lower for k in ["風險", "擔心", "怕", "疑慮", "不確定"]):
        return "風險評估"
    return "其他"


def _detect_concern(user_text: str) -> str:
    """從問題中提取擔憂關鍵字"""
    concern_keywords = [
        "擔心", "怕", "不安", "疑慮", "不確定", "風險", "會不會",
        "會跌嗎", "會漲嗎", "安全嗎", "危險", "有問題嗎"
    ]
    for kw in concern_keywords:
        if kw in user_text:
            return user_text[:150]  # 保留完整擔憂內容（前150字）
    return ""


def _extract_indicators(text: str) -> list:
    """從問題中提取提到的技術指標"""
    found = []
    indicator_map = {
        "RSI": ["rsi", "相對強弱"],
        "KD":  ["kd", "隨機指標", "kd值"],
        "MACD": ["macd", "指數平滑異同移動平均"],
        "均線": ["均線", "ma5", "ma20", "ma60", "移動平均"],
        "布林": ["布林", "bollinger"],
        "成交量": ["成交量", "volume", "量能"],
        "K線形態": ["k線", "k棒", "型態", "吞沒", "晨星", "錘子"],
    }
    text_lower = text.lower()
    for name, keywords in indicator_map.items():
        if any(k in text_lower for k in keywords):
            found.append(name)
    return found


def update_profile_from_conversation(user_text: str, ai_text: str, stock_id: str = ""):
    """
    從一輪對話自動學習，更新個人檔案。
    每次對話完成後呼叫此函式。

    Parameters
    ----------
    user_text : 使用者問題
    ai_text   : AI 回答
    stock_id  : 當前查詢的股票代號
    """
    profile = _load()
    now     = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    # 1. 更新常看股票計數
    if stock_id:
        profile["watched_stocks"][stock_id] = profile["watched_stocks"].get(stock_id, 0) + 1

    # 2. 更新問題類型統計
    q_type = _detect_question_type(user_text)
    profile["top_question_types"][q_type] = profile["top_question_types"].get(q_type, 0) + 1

    # 3. 偵測並記錄擔憂
    concern = _detect_concern(user_text)
    if concern:
        profile["past_concerns"].append({"time": now, "concern": concern})
        # 只保留最近 20 條
        if len(profile["past_concerns"]) > 20:
            profile["past_concerns"] = profile["past_concerns"][-20:]

    # 4. 更新偏好指標
    indicators = _extract_indicators(user_text)
    for ind in indicators:
        if ind not in profile["preferred_indicators"]:
            profile["preferred_indicators"].append(ind)

    # 5. 從 AI 回答中提取操作建議（若 AI 給了具體買賣建議）
    if "📌" in ai_text and len(profile["liked_advice"]) < 30:
        # 提取 AI 建議的第一行
        for line in ai_text.split("\n"):
            if "📌" in line and len(line) > 5:
                advice_entry = f"[{now}] {stock_id}: {line[:100]}"
                if advice_entry not in profile["liked_advice"]:
                    profile["liked_advice"].append(advice_entry)
                break

    _save(profile)


def get_profile_context() -> str:
    """
    取得個人檔案上下文字串，供注入 AI Prompt。
    """
    profile = _load()

    # 最常看的股票（前5名）
    top_stocks = sorted(profile["watched_stocks"].items(), key=lambda x: x[1], reverse=True)[:5]
    stocks_str = "、".join(f"{s}({n}次)" for s, n in top_stocks) if top_stocks else "尚無記錄"

    # 最常問的問題類型（前3名）
    top_types = sorted(profile["top_question_types"].items(), key=lambda x: x[1], reverse=True)[:3]
    types_str = "、".join(f"{t}({n}次)" for t, n in top_types) if top_types else "尚無記錄"

    # 偏好指標
    indicators_str = "、".join(profile["preferred_indicators"][:6]) if profile["preferred_indicators"] else "尚無記錄"

    # 最近的擔憂（最多3條）
    recent_concerns = profile["past_concerns"][-3:] if profile["past_concerns"] else []
    concerns_str = "\n".join(f"  [{c['time']}] {c['concern'][:80]}" for c in recent_concerns) if recent_concerns else "  無"

    # 明確原則
    principles_str = "\n".join(f"  - {p}" for p in profile["stated_principles"]) if profile["stated_principles"] else "  - 不開槓桿、不融資融券（系統預設）"

    return f"""
====== Akira 個人投資檔案（請以此了解主人的偏好，給出更個人化的建議）======
- 投資風格：{profile['risk_style']} / {profile['invest_horizon']}持有
- 最常關注的股票：{stocks_str}
- 最常詢問的分析類型：{types_str}
- 慣用技術指標：{indicators_str}
- 投資原則：
{principles_str}
- 主人曾提出的擔憂（最近 3 條）：
{concerns_str}
- 資料統計期間：{profile.get('created','--')} 至 {profile.get('last_updated','--')}
=====================================================================
"""


def update_stated_principle(principle: str):
    """手動新增投資原則（從設定頁面或 AI 辨識後呼叫）"""
    profile = _load()
    if principle not in profile["stated_principles"]:
        profile["stated_principles"].append(principle)
    _save(profile)


def get_profile_summary() -> dict:
    """回傳個人檔案摘要（供 UI 顯示）"""
    return _load()
