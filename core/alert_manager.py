# core/alert_manager.py
# =====================================================================
# 功能：App 內價格警示管理
# 職責：儲存/讀取用戶設定的價格警示，每次刷新時比對現價是否觸發
# =====================================================================

import json
import datetime
from pathlib import Path

_DATA_DIR   = Path(__file__).parent.parent / "data"
_ALERT_FILE = _DATA_DIR / "price_alerts.json"


def _load() -> list:
    if not _ALERT_FILE.exists():
        return []
    try:
        with open(_ALERT_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save(alerts: list):
    try:
        _DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(_ALERT_FILE, "w", encoding="utf-8") as f:
            json.dump(alerts, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[alert] 儲存失敗: {e}")


def add_alert(stock_id: str, stock_name: str, condition: str,
              price: float, note: str = "") -> int:
    """
    新增一個價格警示。

    Parameters
    ----------
    stock_id   : 股票代號 e.g. '0050'
    stock_name : 股票名稱 e.g. '元大台灣50'
    condition  : '>' (漲到) 或 '<' (跌到)
    price      : 目標觸發價
    note       : 備註（可選）

    Returns
    -------
    int  警示 ID
    """
    alerts = _load()
    alert_id = max((a["id"] for a in alerts), default=0) + 1
    alerts.append({
        "id":         alert_id,
        "stock_id":   stock_id,
        "stock_name": stock_name,
        "condition":  condition,
        "price":      price,
        "note":       note,
        "created":    datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "triggered":  False,
        "trigger_time": None,
    })
    _save(alerts)
    return alert_id


def remove_alert(alert_id: int):
    """刪除指定 ID 的警示"""
    alerts = [a for a in _load() if a["id"] != alert_id]
    _save(alerts)


def get_all_alerts() -> list:
    """取得所有警示（含已觸發和未觸發）"""
    return _load()


def get_active_alerts() -> list:
    """只回傳尚未觸發的警示"""
    return [a for a in _load() if not a["triggered"]]


def check_alerts(current_prices: dict) -> list:
    """
    比對現價，回傳本次新觸發的警示列表。

    Parameters
    ----------
    current_prices : dict  {stock_id: current_price}
                    例如 {'0050': 180.5, '2330': 950.0}

    Returns
    -------
    list of dict  新觸發的警示（可用於 UI 提示）
    """
    alerts  = _load()
    triggered_now = []
    changed  = False

    for a in alerts:
        if a["triggered"]:
            continue
        sid   = a["stock_id"]
        price = current_prices.get(sid)
        if price is None:
            continue

        hit = False
        if a["condition"] == ">" and price >= a["price"]:
            hit = True
        elif a["condition"] == "<" and price <= a["price"]:
            hit = True

        if hit:
            a["triggered"]    = True
            a["trigger_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            a["trigger_price"] = price
            triggered_now.append(a)
            changed = True

    if changed:
        _save(alerts)

    return triggered_now


def clear_triggered():
    """清除所有已觸發的警示"""
    alerts = [a for a in _load() if not a["triggered"]]
    _save(alerts)


def get_stats() -> dict:
    alerts = _load()
    return {
        "total":     len(alerts),
        "active":    sum(1 for a in alerts if not a["triggered"]),
        "triggered": sum(1 for a in alerts if a["triggered"]),
    }
