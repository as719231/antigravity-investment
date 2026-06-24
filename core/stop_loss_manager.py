# core/stop_loss_manager.py
# =====================================================================
# 停損追蹤管理器（方案 B 完整版）
# 職責：
#   1. 儲存/讀取每筆持倉的停損設定
#   2. 支援三種停損模式：固定比率、固定價格、移動停損
#   3. 每次刷新時比對現價，回傳觸發清單
#   4. 移動停損：帳面獲利 >= trailing_trigger_pct 時，自動將停損上移至
#      成本 × (1 + lock_pct)，確保獲利不會全吐
# =====================================================================

import json
import datetime
from pathlib import Path

_DATA_DIR    = Path(__file__).parent.parent / "data"
_SL_FILE     = _DATA_DIR / "stop_loss_settings.json"


# ── 讀寫 ─────────────────────────────────────────────────────────────

def _load() -> dict:
    """載入停損設定 {stock_id: setting_dict}"""
    if not _SL_FILE.exists():
        return {}
    try:
        with open(_SL_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(data: dict):
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(_SL_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── 公開 API ─────────────────────────────────────────────────────────

def get_all_stops() -> dict:
    """
    取得所有停損設定。
    Returns
    -------
    dict  {stock_id: {name, cost, stop_type, stop_pct, stop_price,
                      trailing_active, trailing_trigger_pct, lock_pct,
                      highest_price, created, last_updated}}
    """
    return _load()


def get_stop(stock_id: str) -> dict:
    """取得單支股票的停損設定，不存在則回傳空 dict"""
    return _load().get(stock_id, {})


def set_stop_loss(
    stock_id: str,
    name: str,
    cost: float,
    stop_type: str = "pct",          # "pct" | "price" | "trailing"
    stop_pct: float = 8.0,           # 固定比率停損（%），stop_type=pct/trailing 時有效
    stop_price: float = None,        # 固定價格停損，stop_type=price 時有效
    trailing_trigger_pct: float = 15.0,  # 獲利達幾%時啟動移動停損
    lock_pct: float = 5.0,           # 移動停損鎖定的最低獲利%
    highest_price: float = None,     # 移動停損追蹤用最高價（首次設定=成本）
) -> dict:
    """
    新增或更新某支股票的停損設定。

    Parameters
    ----------
    stop_type : "pct"      固定比率停損（成本 × (1 - stop_pct/100)）
                "price"    固定價格停損（到達 stop_price 時出場）
                "trailing" 移動停損（獲利達 trailing_trigger_pct 後自動上移）

    Returns
    -------
    dict  更新後的設定
    """
    data = _load()

    if stop_type == "price" and stop_price is not None:
        computed_price = round(stop_price, 2)
    else:
        computed_price = round(cost * (1 - stop_pct / 100), 2)

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    setting = {
        "stock_id":             stock_id,
        "name":                 name,
        "cost":                 cost,
        "stop_type":            stop_type,
        "stop_pct":             stop_pct,
        "stop_price":           computed_price,
        "trailing_active":      False,           # 移動停損是否已啟動
        "trailing_trigger_pct": trailing_trigger_pct,
        "lock_pct":             lock_pct,
        "highest_price":        highest_price or cost,
        "triggered":            False,
        "triggered_at":         None,
        "created":              data.get(stock_id, {}).get("created", now),
        "last_updated":         now,
    }

    data[stock_id] = setting
    _save(data)
    return setting


def remove_stop(stock_id: str):
    """刪除某支股票的停損設定"""
    data = _load()
    if stock_id in data:
        del data[stock_id]
        _save(data)


def check_stops(prices: dict) -> list:
    """
    比對現價與停損線，更新移動停損，回傳觸發清單。

    Parameters
    ----------
    prices : dict  {stock_id: current_price}

    Returns
    -------
    list of dict  每個觸發項目包含：
        stock_id, name, cost, current_price,
        stop_price, loss_pct, stop_type, message
    """
    data    = _load()
    changed = False
    triggered_list = []

    for sid, cfg in data.items():
        price = prices.get(sid)
        if price is None or cfg.get("triggered"):
            continue

        cost         = cfg["cost"]
        stop_type    = cfg.get("stop_type", "pct")
        stop_pct     = cfg.get("stop_pct", 8.0)
        stop_price   = cfg.get("stop_price", cost * 0.92)
        trailing_trig= cfg.get("trailing_trigger_pct", 15.0)
        lock_pct     = cfg.get("lock_pct", 5.0)
        highest      = cfg.get("highest_price", cost)
        paper_pnl_pct = (price - cost) / cost * 100

        # ── 移動停損：更新最高價 & 自動上移停損線 ────────────────
        if stop_type == "trailing":
            if price > highest:
                cfg["highest_price"] = price
                highest = price
                changed = True

            # 啟動條件：帳面獲利 >= trailing_trigger_pct
            if paper_pnl_pct >= trailing_trig and not cfg.get("trailing_active"):
                cfg["trailing_active"] = True
                changed = True

            # 啟動後：停損線 = 最高價 × (1 - stop_pct/100)
            #          但最低保底 = 成本 × (1 + lock_pct/100)
            if cfg.get("trailing_active"):
                new_stop = max(
                    round(highest * (1 - stop_pct / 100), 2),
                    round(cost * (1 + lock_pct / 100), 2),
                )
                if new_stop != cfg["stop_price"]:
                    cfg["stop_price"] = new_stop
                    stop_price = new_stop
                    changed = True

        # ── 觸發判斷 ─────────────────────────────────────────────
        if price <= stop_price:
            loss_pct = (price - cost) / cost * 100
            triggered_list.append({
                "stock_id":    sid,
                "name":        cfg.get("name", sid),
                "cost":        cost,
                "current_price": price,
                "stop_price":  stop_price,
                "loss_pct":    round(loss_pct, 2),
                "stop_type":   stop_type,
                "trailing_active": cfg.get("trailing_active", False),
                "message": _build_message(cfg, price, stop_price, loss_pct),
            })
            cfg["triggered"]    = True
            cfg["triggered_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            changed = True

    if changed:
        _save(data)

    return triggered_list


def reset_triggered(stock_id: str):
    """重置觸發狀態（讓停損重新監控）"""
    data = _load()
    if stock_id in data:
        data[stock_id]["triggered"] = False
        data[stock_id]["triggered_at"] = None
        _save(data)


def clear_all_triggered():
    """清除所有已觸發記錄"""
    data = _load()
    for cfg in data.values():
        cfg["triggered"] = False
        cfg["triggered_at"] = None
    _save(data)


def get_stop_summary(stock_id: str, current_price: float) -> dict:
    """
    取得單支股票停損摘要，供 UI 顯示用。
    Returns
    -------
    dict with keys:
      has_stop, stop_price, stop_type, stop_pct,
      distance_pct (現價距停損%),
      status ("safe" / "warning" / "danger" / "triggered"),
      trailing_active, lock_in_profit_pct
    """
    cfg = get_stop(stock_id)
    if not cfg:
        return {"has_stop": False}

    cost        = cfg.get("cost", current_price)
    stop_price  = cfg.get("stop_price", 0)
    stop_type   = cfg.get("stop_type", "pct")
    triggered   = cfg.get("triggered", False)

    distance_pct = (current_price - stop_price) / current_price * 100 if current_price > 0 else 0
    paper_pnl_pct = (current_price - cost) / cost * 100 if cost > 0 else 0

    if triggered:
        status = "triggered"
    elif distance_pct < 1:
        status = "danger"       # 距停損 < 1%
    elif distance_pct < 3:
        status = "warning"      # 距停損 1~3%
    else:
        status = "safe"

    # 移動停損：目前鎖住的最低獲利
    lock_in = None
    if stop_type == "trailing" and cfg.get("trailing_active"):
        lock_in = round((stop_price - cost) / cost * 100, 1)

    return {
        "has_stop":          True,
        "stop_price":        stop_price,
        "stop_type":         stop_type,
        "stop_pct":          cfg.get("stop_pct", 0),
        "distance_pct":      round(distance_pct, 2),
        "paper_pnl_pct":     round(paper_pnl_pct, 2),
        "status":            status,
        "trailing_active":   cfg.get("trailing_active", False),
        "trailing_trigger_pct": cfg.get("trailing_trigger_pct", 15),
        "lock_in_profit_pct": lock_in,
        "triggered":         triggered,
        "triggered_at":      cfg.get("triggered_at"),
    }


# ── 私有工具 ─────────────────────────────────────────────────────────

def _build_message(cfg: dict, price: float, stop_price: float, loss_pct: float) -> str:
    sid   = cfg.get("stock_id", "")
    name  = cfg.get("name", sid)
    stype = cfg.get("stop_type", "pct")
    trailing_active = cfg.get("trailing_active", False)

    if stype == "trailing" and trailing_active:
        return (
            f"⚠️ 移動停損觸發！{name}({sid}) "
            f"現價 {price} 元 跌破移動停損線 {stop_price} 元，"
            f"損益 {loss_pct:+.1f}%。建議考慮出場保護獲利。"
        )
    elif loss_pct < 0:
        return (
            f"🔴 停損警示！{name}({sid}) "
            f"現價 {price} 元 跌破停損線 {stop_price} 元，"
            f"目前虧損 {loss_pct:.1f}%。建議評估是否執行停損。"
        )
    else:
        return (
            f"⚠️ 停損觸發！{name}({sid}) "
            f"現價 {price} 元 跌破停損線 {stop_price} 元。"
        )
