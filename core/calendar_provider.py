# core/calendar_provider.py  (v3 - use no-date endpoint for today's data + pagination)
# =====================================================================
# 功能：除權息/重要日期日曆資料提供模組
# 資料來源：TWSE TWT49U API - 不帶日期參數取得最新除權息日程
# =====================================================================

import requests
import json
import re
import datetime
from pathlib import Path

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.twse.com.tw/"
}
_CACHE_FILE = Path(__file__).parent.parent / "data" / "calendar_cache.json"


def _get_today() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d")


def _parse_roc_date(date_str: str):
    """解析民國年日期字串，如 '115年06月24日'"""
    m = re.match(r"(\d+)年(\d+)月(\d+)日", str(date_str))
    if m:
        year  = int(m.group(1)) + 1911
        month = int(m.group(2))
        day   = int(m.group(3))
        try:
            return datetime.date(year, month, day)
        except ValueError:
            return None
    return None


def _load_cache() -> dict:
    if not _CACHE_FILE.exists():
        return {}
    try:
        with open(_CACHE_FILE, encoding="utf-8") as f:
            cache = json.load(f)
        if cache.get("date") == _get_today():
            return cache
    except Exception:
        pass
    return {}


def _save_cache(data: dict):
    try:
        _CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        data["date"] = _get_today()
        with open(_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def fetch_upcoming_dividends(days_ahead: int = 60) -> list:
    """
    取得近期的除權息行事曆。
    TWSE API 不帶日期時返回「最近一批」除權息資料（通常是近 1-2 週）。
    為取得更多資料，我們連續拉幾頁。
    """
    cache = _load_cache()
    if cache.get("dividends"):
        return cache["dividends"]

    results = []
    seen_ids = set()
    now = datetime.date.today()

    # TWSE API：不帶日期，取今日及近日除權息
    base_url = "https://www.twse.com.tw/rwd/zh/exRight/TWT49U?response=json"

    # 嘗試拉取（可能有多頁，用 &pageno=N）
    for page in range(1, 8):
        url = f"{base_url}&pageno={page}" if page > 1 else base_url
        try:
            r = requests.get(url, headers=_HEADERS, timeout=10)
            if not r.ok:
                break
            data = r.json()
            if data.get("stat") != "OK":
                break

            rows = data.get("data", [])
            if not rows:
                break

            for row in rows:
                try:
                    ex_date_str = str(row[0]).strip()
                    ex_date     = _parse_roc_date(ex_date_str)
                    if not ex_date:
                        continue

                    delta = (ex_date - now).days
                    if delta < -30 or delta > days_ahead:
                        continue

                    stock_id   = str(row[1]).strip()
                    stock_name = str(row[2]).strip()
                    cash_div   = str(row[5]).strip() if len(row) > 5 else "0"
                    div_type   = str(row[6]).strip() if len(row) > 6 else ""

                    key = f"{stock_id}_{ex_date}"
                    if key in seen_ids:
                        continue
                    seen_ids.add(key)

                    results.append({
                        "stock_id":   stock_id,
                        "stock_name": stock_name,
                        "ex_date":    ex_date.strftime("%Y-%m-%d"),
                        "days_left":  delta,
                        "div_type":   div_type,
                        "cash_div":   cash_div if cash_div not in ["0", "0.000000", ""] else "0",
                    })
                except (ValueError, IndexError):
                    continue

        except Exception as e:
            print(f"[calendar] page {page} 失敗: {e}")
            break

    results.sort(key=lambda x: x["ex_date"])
    _save_cache({"dividends": results})
    return results


def get_full_calendar(watched_stocks: list = None, days_ahead: int = 60) -> dict:
    """整合除權息行事曆"""
    dividends = fetch_upcoming_dividends(days_ahead=days_ahead)
    return {
        "dividends":    dividends,
        "last_updated": _get_today(),
    }
