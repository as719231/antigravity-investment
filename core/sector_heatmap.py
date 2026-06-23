# core/sector_heatmap.py
# =====================================================================
# 功能：台股板塊熱圖資料提供模組
# 資料來源：TWSE MI_INDEX (盤後類股指數) + 自定義產業對照表
# =====================================================================

import requests
import re
from functools import lru_cache

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.twse.com.tw/"
}

# ── 自定義產業分類（TWSE 類股指數名稱 → 簡短標籤）─────────────────
_SECTOR_KEYWORDS = {
    "半導體": ["半導體", "DRAM", "IC設計", "晶圓"],
    "電子零組件": ["電子零組件", "電子零件", "光電"],
    "電腦及周邊": ["電腦及周邊", "資訊服務", "電腦"],
    "通信網路": ["通信網路", "電信"],
    "光電": ["光電"],
    "其他電子": ["其他電子"],
    "金融保險": ["金融保險", "金融", "銀行", "保險"],
    "建材營造": ["建材", "營造"],
    "食品工業": ["食品"],
    "紡織纖維": ["紡織"],
    "鋼鐵工業": ["鋼鐵"],
    "化學工業": ["化學"],
    "生技醫療": ["生技", "醫療", "生物"],
    "航運業": ["航運", "航空", "海運", "陸運"],
    "塑膠工業": ["塑膠"],
    "觀光餐旅": ["觀光", "餐旅"],
    "油電燃氣": ["油電", "燃氣"],
    "機電工業": ["機電"],
    "電機機械": ["電機", "機械"],
    "橡膠工業": ["橡膠"],
    "造紙工業": ["造紙"],
    "礦業及泥製品": ["礦業", "泥製品"],
    "貿易百貨": ["貿易", "百貨"],
    "其他": [],
}


def _parse_change(html_str: str) -> str:
    """從 HTML 色碼判斷漲跌符號"""
    if "red" in str(html_str):
        return "+"
    elif "green" in str(html_str):
        return "-"
    return ""


def fetch_sector_indices() -> list:
    """
    從 TWSE 取得類股指數當日漲跌。
    返回: list of dict，每筆含 name, close, change_pct, direction
    使用 MI_INDEX type=IND 取得主要類股指數
    """
    url = "https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?type=IND&response=json"
    try:
        r = requests.get(url, headers=_HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        return []

    results = []
    tables = data.get("tables", [])

    # 定義我們要抓的主要產業類股指數名稱
    target_sectors = {
        "半導體": "半導體",
        "電子零組件": "電子零組件",
        "電腦及周邊": "電腦及周邊",
        "通信網路": "通信網路",
        "光電": "光電",
        "其他電子": "其他電子",
        "金融保險": "金融保險",
        "建材營造": "建材營造",
        "食品工業": "食品工業",
        "紡織纖維": "紡織纖維",
        "鋼鐵工業": "鋼鐵工業",
        "化學工業": "化學工業",
        "生技醫療": "生技醫療",
        "航運業": "航運業",
        "塑膠工業": "塑膠工業",
        "觀光餐旅": "觀光餐旅",
        "油電燃氣": "油電燃氣",
        "電機機械": "電機機械",
        "發行量加權股價指數": "大盤",
    }

    for table in tables:
        fields = table.get("fields", [])
        rows   = table.get("data", [])
        if not fields or not rows:
            continue

        for row in rows:
            if len(row) < 5:
                continue
            name = str(row[0]).strip()
            # 對照目標
            matched_label = None
            for key, label in target_sectors.items():
                if key in name:
                    matched_label = label
                    break
            if not matched_label:
                continue

            try:
                close     = float(str(row[1]).replace(",", ""))
                direction = _parse_change(row[2])
                chg_pct   = float(str(row[4]).replace(",", "").replace("%", ""))
                if direction == "-":
                    chg_pct = -abs(chg_pct)
                else:
                    chg_pct = abs(chg_pct)

                results.append({
                    "name":       matched_label,
                    "full_name":  name,
                    "close":      close,
                    "change_pct": chg_pct,
                })
            except (ValueError, IndexError):
                continue

    # 去重（同類股名稱只保留第一筆）
    seen = set()
    deduped = []
    for r in results:
        if r["name"] not in seen:
            seen.add(r["name"])
            deduped.append(r)

    # 依漲跌幅排序
    deduped.sort(key=lambda x: x["change_pct"], reverse=True)
    return deduped


def get_market_breadth() -> dict:
    """
    取得大盤漲跌家數（上漲/下跌/持平）。
    從 ALLBUT0999 的 Table 7 解析。
    """
    url = "https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?type=ALLBUT0999&response=json"
    try:
        r = requests.get(url, headers=_HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception:
        return {}

    tables = data.get("tables", [])
    for table in tables:
        fields = table.get("fields", [])
        rows   = table.get("data", [])
        if "上漲" in str(fields) or "上漲" in str(rows):
            for row in rows:
                if "上漲" in str(row[0]):
                    # parse "3,191(208)"
                    match_up = re.search(r"([\d,]+)\((\d+)\)", str(row[1]) if len(row) > 1 else str(row))
                    up_total = int(match_up.group(1).replace(",", "")) if match_up else 0
                    up_limit = int(match_up.group(2)) if match_up else 0
                elif "下跌" in str(row[0]):
                    match_dn = re.search(r"([\d,]+)\((\d+)\)", str(row[1]) if len(row) > 1 else str(row))
                    dn_total = int(match_dn.group(1).replace(",", "")) if match_dn else 0
                    dn_limit = int(match_dn.group(2)) if match_dn else 0
                elif "持平" in str(row[0]):
                    flat = int(str(row[1]).replace(",", "")) if len(row) > 1 else 0

    return {
        "up": locals().get("up_total", 0),
        "up_limit": locals().get("up_limit", 0),
        "down": locals().get("dn_total", 0),
        "down_limit": locals().get("dn_limit", 0),
        "flat": locals().get("flat", 0),
    }
