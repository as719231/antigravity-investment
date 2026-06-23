# core/knowledge_base.py
# =====================================================================
# 第三層：RAG 知識庫模組
# 職責：儲存 AI 高品質回答與使用者筆記，查詢時語意搜尋相關內容注入 Prompt
# 積木說明：獨立模組，讀寫 data/knowledge_base.json，不影響其他邏輯
# =====================================================================

import json
import os
import datetime
import re
from pathlib import Path

_DATA_DIR = Path(__file__).parent.parent / "data"
_KB_FILE  = _DATA_DIR / "knowledge_base.json"

# RAG 設定
MAX_KB_ENTRIES = 200     # 最多儲存幾條
TOP_K_RETRIEVE = 4       # 每次搜尋回傳幾條最相關的


def _load() -> list:
    """讀取知識庫（list of entries）"""
    if not _KB_FILE.exists():
        return []
    try:
        with open(_KB_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save(entries: list):
    try:
        _DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(_KB_FILE, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[kb] 儲存失敗: {e}")


def _tokenize(text: str) -> set:
    """
    簡易中文分詞（字元 bigram + 關鍵詞提取）。
    不需要外部套件，純 Python 實作。
    """
    text = text.lower()
    tokens = set()

    # 英文單詞
    tokens.update(re.findall(r'[a-z0-9]+', text))

    # 中文 bigram（每兩個相鄰字）
    for i in range(len(text) - 1):
        c1, c2 = text[i], text[i+1]
        if '\u4e00' <= c1 <= '\u9fff' or '\u4e00' <= c2 <= '\u9fff':
            tokens.add(c1 + c2)

    # 中文單字（常見關鍵詞直接加）
    for c in text:
        if '\u4e00' <= c <= '\u9fff':
            tokens.add(c)

    return tokens


def _similarity_score(query_tokens: set, entry_tokens: set) -> float:
    """Jaccard 相似度（0~1）"""
    if not query_tokens or not entry_tokens:
        return 0.0
    intersection = len(query_tokens & entry_tokens)
    union = len(query_tokens | entry_tokens)
    return intersection / union if union > 0 else 0.0


def add_entry(question: str, answer: str, stock_id: str = "", tags: list = None, source: str = "auto"):
    """
    新增一條知識到知識庫。

    Parameters
    ----------
    question : 問題（或主題）
    answer   : AI 回答（或筆記內容）
    stock_id : 相關股票代號
    tags     : 手動標籤，例如 ["技術分析", "0050"]
    source   : "auto"（AI 自動存入）/ "manual"（使用者手動）
    """
    entries = _load()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    # 建立可搜尋的 token 集合
    combined_text = question + " " + answer + " " + stock_id
    if tags:
        combined_text += " " + " ".join(tags)
    tokens = list(_tokenize(combined_text))

    entry = {
        "id":       len(entries) + 1,
        "time":     now,
        "stock":    stock_id,
        "question": question[:200],
        "answer":   answer[:800],       # 限制長度控制 token
        "tags":     tags or [],
        "source":   source,
        "tokens":   tokens[:150],       # 儲存 token 加速搜尋
    }
    entries.append(entry)

    # 超過上限，移除最舊的
    if len(entries) > MAX_KB_ENTRIES:
        entries = entries[-MAX_KB_ENTRIES:]

    _save(entries)
    return entry["id"]


def search(query: str, top_k: int = TOP_K_RETRIEVE, stock_filter: str = "") -> list:
    """
    語意搜尋知識庫，回傳最相關的 top_k 條。

    Parameters
    ----------
    query        : 搜尋查詢（使用者問題）
    top_k        : 回傳幾條
    stock_filter : 若指定，優先回傳同股票的內容

    Returns
    -------
    list of dict（含 question, answer, time, stock）
    """
    entries = _load()
    if not entries:
        return []

    query_tokens = _tokenize(query)
    scored = []
    for entry in entries:
        entry_tokens = set(entry.get("tokens", []))
        score = _similarity_score(query_tokens, entry_tokens)

        # 同股票加分
        if stock_filter and entry.get("stock") == stock_filter:
            score += 0.15

        # 最近的內容加一點分（時間衰減倒過來）
        # 不做複雜計算，讓相關性主導

        if score > 0.01:  # 最低門檻
            scored.append((score, entry))

    # 依相關度排序
    scored.sort(key=lambda x: x[0], reverse=True)
    return [e for _, e in scored[:top_k]]


def get_rag_context(query: str, stock_id: str = "", top_k: int = TOP_K_RETRIEVE) -> str:
    """
    取得 RAG 上下文字串，供注入 AI Prompt。

    Parameters
    ----------
    query    : 使用者問題（用來搜尋相關知識）
    stock_id : 當前股票代號
    top_k    : 最多帶幾條知識

    Returns
    -------
    str  格式化的知識庫片段，若無相關知識則回傳空字串
    """
    results = search(query, top_k=top_k, stock_filter=stock_id)
    if not results:
        return ""

    lines = []
    for r in results:
        stock_tag = f"[{r['stock']}] " if r.get("stock") else ""
        lines.append(f"• [{r['time']}] {stock_tag}{r['question']}")
        lines.append(f"  → {r['answer'][:250]}{'...' if len(r['answer']) > 250 else ''}")
        lines.append("")

    return (
        "====== 相關知識庫片段（你過去累積的分析記錄，請參考以提升回答品質）======\n"
        + "\n".join(lines)
        + "======================================================================\n"
    )


def auto_save_from_conversation(user_text: str, ai_text: str, stock_id: str = ""):
    """
    判斷一輪對話是否值得存入知識庫（自動品質過濾）。
    條件：AI 回答夠長（>150字）且包含分析內容。
    """
    if len(ai_text) < 50:
        return   # 回答太短，不值得存

    # 包含分析指標的回答才存
    value_keywords = ["RSI", "KD", "支撐", "壓力", "均線", "📌", "建議", "分析",
                      "PE", "EPS", "法人", "外資", "布林", "成交量"]
    has_value = any(kw in ai_text for kw in value_keywords)
    if not has_value:
        return

    # 推斷標籤
    tags = []
    if stock_id:
        tags.append(stock_id)
    if "RSI" in ai_text or "KD" in ai_text or "均線" in ai_text:
        tags.append("技術分析")
    if "法人" in ai_text or "外資" in ai_text:
        tags.append("籌碼分析")
    if "PE" in ai_text or "EPS" in ai_text or "財報" in ai_text:
        tags.append("基本面")

    add_entry(
        question=user_text,
        answer=ai_text,
        stock_id=stock_id,
        tags=tags,
        source="auto"
    )


def add_manual_note(title: str, content: str, stock_id: str = "", tags: list = None):
    """使用者手動新增筆記到知識庫"""
    add_entry(
        question=title,
        answer=content,
        stock_id=stock_id,
        tags=tags or ["手動筆記"],
        source="manual"
    )


def get_stats() -> dict:
    """回傳知識庫統計"""
    entries = _load()
    auto_count   = sum(1 for e in entries if e.get("source") == "auto")
    manual_count = sum(1 for e in entries if e.get("source") == "manual")
    stocks = {}
    for e in entries:
        s = e.get("stock", "")
        if s:
            stocks[s] = stocks.get(s, 0) + 1
    top_stocks = sorted(stocks.items(), key=lambda x: x[1], reverse=True)[:5]
    return {
        "total":       len(entries),
        "auto_saved":  auto_count,
        "manual_added": manual_count,
        "top_stocks":  top_stocks,
    }
