"""
core/stock_classifier.py
股票類型自動判定引擎

流程：
  Step1 → FinMind 取得公司名稱、產業、市值
  Step2 → Gemini 聯網搜尋取得公司描述 + 近期新聞關鍵字
  Step3 → 關鍵字比對 → 各類型 confidence 分數
  Step4 → ETF / 權值股 特殊規則補分
  Step5 → 取 Primary / Secondary Type
  Step6 → 決定混合模型比例
  Step7 → 快取 180 天

禁止硬編碼股票名單，全部動態判定。
"""

import json
import os
import re
import datetime

import config  # type: ignore

# ─── 快取設定 ─────────────────────────────────────────────────
_THIS_DIR   = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE  = os.path.join(_THIS_DIR, '..', 'data', 'stock_types_cache.json')
CACHE_DAYS  = 180   # 快取有效天數（半年）

# ─── 關鍵字規則 ───────────────────────────────────────────────
# per_hit: 每命中一個關鍵字加幾分（上限100）
KEYWORD_RULES: dict = {
    "AI": {
        "keywords": [
            "AI", "GPU", "ASIC", "Server", "伺服器", "資料中心", "液冷",
            "散熱", "電源供應器", "高速傳輸", "HBM", "CPO", "矽光子",
            "人工智慧", "機器學習", "深度學習", "推論晶片", "訓練晶片",
            "CoWoS", "先進封裝", "AI PC", "Edge AI",
        ],
        "per_hit": 15,
    },
    "低軌衛星": {
        "keywords": [
            "LEO", "低軌衛星", "衛星通訊", "Starlink", "SpaceX", "OneWeb",
            "Kuiper", "衛星天線", "RF", "毫米波", "衛星", "低軌道",
            "衛星網路", "相位陣列", "SATCOM",
        ],
        "per_hit": 20,
    },
    "軍工": {
        "keywords": [
            "軍工", "國防", "飛彈", "無人機", "航太", "軍規", "雷達",
            "軍事", "軍艦", "戰機", "國防部", "軍備", "防衛",
        ],
        "per_hit": 20,
    },
    "機器人": {
        "keywords": [
            "Robot", "Humanoid", "機器人", "自動化", "協作機器人",
            "工業機器人", "人形機器人", "AMR", "AGV",
        ],
        "per_hit": 20,
    },
    "電動車": {
        "keywords": [
            "EV", "電動車", "充電樁", "車用電子", "BMS", "電動巴士",
            "車載", "ADAS", "自駕", "車用", "電動機車", "充電站",
        ],
        "per_hit": 15,
    },
    "半導體": {
        "keywords": [
            "晶圓", "半導體", "IC設計", "封裝測試", "晶片", "製程",
            "光罩", "矽晶圓", "DRAM", "NAND", "Flash", "Fabless",
            "Foundry", "IDM", "記憶體", "邏輯IC",
        ],
        "per_hit": 15,
    },
    "生技醫療": {
        "keywords": [
            "生技", "醫療", "新藥", "製藥", "醫材", "醫院", "臨床",
            "FDA", "健康", "醫學", "藥品", "醫美", "基因", "細胞治療",
        ],
        "per_hit": 15,
    },
    "金融": {
        "keywords": [
            "銀行", "保險", "金控", "證券", "投信", "放款", "存款",
            "壽險", "金融", "票券", "期貨", "資產管理",
        ],
        "per_hit": 15,
    },
    "ETF": {
        "keywords": [
            "ETF", "台灣50", "高股息", "永續", "科技ETF", "指數型",
            "型基金", "指數基金",
        ],
        "per_hit": 100,
        "is_etf": True,
    },
    "權值股": {
        "keywords": [],   # 由市值邏輯決定，不靠關鍵字
        "per_hit": 0,
    },
}

# ─── 類型風險提示（D 面板）────────────────────────────────────
TYPE_RISKS: dict = {
    "AI": [
        "題材退燒風險：AI 伺服器訂單放緩時，本益比壓縮快",
        "高波動性：AI 概念股平均波動為大盤 1.5~2 倍",
        "建議設定較寬止損（-8%），並分批進場",
    ],
    "低軌衛星": [
        "政策風險：衛星頻段授權受各國監管影響大",
        "題材股特性：新聞驅動，短線波動明顯",
        "建議留意 SpaceX / Kuiper 發射進度新聞",
    ],
    "軍工": [
        "地緣政治敏感：緊張升溫時漲快，緩和時回跌也快",
        "訂單能見度差：政府採購資訊透明度低",
        "建議設定嚴格停損，不追高",
    ],
    "機器人": [
        "題材前瞻性高：多數公司仍在研發，獲利能見度低",
        "高本益比：需搭配實際出貨量確認",
        "建議中線布局，優先選擇有實際出貨的公司",
    ],
    "電動車": [
        "政策補貼依賴度高：補貼退出時需重估獲利",
        "競爭激烈：全球電動車廠商持續擴產壓低毛利",
        "建議關注主要車廠季度交車數據",
    ],
    "半導體": [
        "景氣循環影響大：半導體週期通常 12~18 個月",
        "庫存去化是關鍵：庫存高峰期需謹慎",
        "建議追蹤客戶拉貨動態與終端庫存水位",
    ],
    "生技醫療": [
        "新藥審查不確定性高：FDA 核准結果影響股價大",
        "燒錢期長：無獲利的研發階段公司風險高",
        "建議保守配置，單一生技股不超過總部位 5%",
    ],
    "金融": [
        "利率環境敏感：升息利多銀行，降息壓縮利差",
        "法規風險：金融法規調整影響業務空間",
        "建議配合央行利率政策方向操作",
    ],
    "ETF": [
        "折溢價風險：市場恐慌時可能出現折價",
        "成分股集中風險：單一成分股比重過高時利空影響大",
        "建議定期定額，不追高殺低",
    ],
    "權值股": [
        "外資影響力最大：外資動向是主要風向球",
        "指數連動性強：大盤系統性風險難以規避",
        "建議配合三大法人籌碼動向操作",
    ],
    "Unknown": [
        "無法確認股票類型，使用通用分析模型",
        "建議先研究基本面（財報、EPS趨勢）再進場",
    ],
}

# ─── 類型操作策略（I 面板）────────────────────────────────────
TYPE_OPERATION_TIPS: dict = {
    "AI": [
        "操作週期：短中線（1~3 個月），勿長抱等業績",
        "停利設定：較一般股寬（+15~20%）",
        "進場訊號：放量突破前高為強進場訊號",
        "注意：輝達 / 博通法說若下修展望，立即重新評估",
    ],
    "低軌衛星": [
        "操作週期：消息面驅動，適合短線（1~4 週）",
        "停利設定：+10~15%（題材股易急漲急跌）",
        "催化劑：衛星發射成功 / 失敗是重大事件",
        "建議控制部位在總資金 5% 以內",
    ],
    "軍工": [
        "操作週期：地緣政治緊張期看多，緩和期減碼",
        "停利設定：+10~20%（事件驅動型）",
        "注意：和平談判消息可能導致急跌",
        "建議保守看待，嚴守停損",
    ],
    "機器人": [
        "操作週期：中長線布局，定期確認出貨進度",
        "停利設定：+20~30%（題材空間大）",
        "催化劑：Tesla Optimus / 輝達機器人進度為觀察重點",
        "建議選擇有實際出貨的公司，避免純概念股",
    ],
    "電動車": [
        "操作週期：Q2 / Q4 車廠拉貨旺季較有利",
        "停利設定：+10~15%",
        "催化劑：各大車廠季度交車量數據",
        "注意：毛利率持續下滑是重要警訊",
    ],
    "半導體": [
        "操作週期：配合景氣循環，庫存去化後布局",
        "停利設定：+12~20%",
        "催化劑：客戶庫存水位與拉貨數據",
        "建議追蹤台積電法說提到的下游需求方向",
    ],
    "生技醫療": [
        "操作週期：新藥審查結果前保守，核准後可追多",
        "建議控制部位，不超過總部位 5%",
        "催化劑：FDA 審查結果、臨床試驗數據",
        "注意：生技股可能因負面試驗結果腰斬",
    ],
    "金融": [
        "操作週期：利率升降循環配合方向操作",
        "停利設定：+8~15%",
        "注意：央行利率政策是最大變數",
        "高股息金融股適合長線存股",
    ],
    "ETF": [
        "策略：定期定額優於追高殺低",
        "目標報酬：年化 8~10% 為基準",
        "配置比例：建議佔總投資組合 30~50%",
        "注意：高股息 ETF 除息日前後觀察填息速度",
    ],
    "權值股": [
        "操作週期：中長線持有，短線配合法人籌碼",
        "停利設定：牛市可設 +15~25%",
        "最重要訊號：外資連買 3 日以上",
        "注意：需同步觀察台灣加權指數方向",
    ],
    "Unknown": [
        "使用通用操作策略，建議保守",
        "停利設定：+8~12%，停損：-5~7%",
        "建議先研究基本面再進場，不追高",
    ],
}

# ═══════════════════════════════════════════════════════════════
# 私有輔助函數
# ═══════════════════════════════════════════════════════════════

def _load_cache() -> dict:
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _save_cache(cache: dict) -> None:
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"快取儲存失敗: {e}")


def _is_cache_valid(entry: dict) -> bool:
    try:
        cached = datetime.datetime.fromisoformat(entry['cached_at'])
        return (datetime.datetime.now() - cached).days < CACHE_DAYS
    except Exception:
        return False


def _fetch_base_info(stock_id: str) -> dict:
    """從 FinMind 取得公司名稱、產業分類、股票類型"""
    try:
        from FinMind.data import DataLoader  # type: ignore
        dl = DataLoader()
        token = getattr(config, 'FINMIND_TOKEN', '')
        if token:
            dl.login_by_token(api_token=token)

        info_df = dl.taiwan_stock_info()
        row = info_df[info_df['stock_id'] == stock_id]
        if row.empty:
            return {}
        r = row.iloc[0]
        return {
            'name':     str(r.get('stock_name', '')),
            'industry': str(r.get('industry_category', '')),
            'type':     str(r.get('type', '')),
        }
    except Exception as e:
        print(f"FinMind base info 失敗: {e}")
        return {}


def _fetch_market_cap_b(stock_id: str) -> float:
    """取得最新市值，單位：億元。失敗時回傳 0.0"""
    try:
        from FinMind.data import DataLoader  # type: ignore
        import datetime as dt
        dl = DataLoader()
        token = getattr(config, 'FINMIND_TOKEN', '')
        if token:
            dl.login_by_token(api_token=token)

        end   = dt.date.today().strftime('%Y-%m-%d')
        start = (dt.date.today() - dt.timedelta(days=30)).strftime('%Y-%m-%d')
        df = dl.taiwan_stock_market_cap(stock_id=stock_id,
                                        start_date=start, end_date=end)
        if df.empty:
            return 0.0
        val = float(df['market_value'].iloc[-1])
        return val / 1e8   # 轉換為億元
    except Exception as e:
        print(f"市值取得失敗: {e}")
        return 0.0


def _fetch_ai_description(stock_id: str, company_name: str) -> str:
    """
    呼叫 Gemini + Google Search，取得公司產品描述與近期新聞關鍵字。
    回傳純文字，供關鍵字比對使用。
    """
    try:
        from core.ai_agent import get_client  # type: ignore  # lazy import 避免循環
        from google.genai import types         # type: ignore

        client = get_client()
        if not client:
            return ""

        prompt = (
            f"請針對台灣上市公司「{company_name}」（股票代號：{stock_id}），"
            f"用繁體中文列出以下關鍵資訊（只列關鍵字，不需要完整句子）：\n"
            f"1. 主要產品和服務（5~10 個關鍵字）\n"
            f"2. 主要應用領域（3~5 個關鍵字）\n"
            f"3. 主要客戶群或下游產業（3~5 個關鍵字）\n"
            f"4. 2024~2025 年重要新聞主題（3~5 個關鍵字）\n"
            f"請直接列出關鍵字，用逗號或空格分隔即可。"
        )
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[{"google_search": {}}],
                max_output_tokens=500,
            ),
        )
        return response.text or ""
    except Exception as e:
        print(f"AI 描述取得失敗: {e}")
        return ""


def _apply_keywords(full_text: str, base_info: dict) -> dict:
    """對全文套用關鍵字規則，回傳各類型的 confidence 原始分"""
    text_up = full_text.upper()
    scores: dict = {t: 0 for t in KEYWORD_RULES}

    for type_name, rule in KEYWORD_RULES.items():

        # ─ ETF 特殊判定 ─
        if rule.get('is_etf'):
            name_upper = base_info.get('name', '').upper()
            type_upper = base_info.get('type', '').upper()
            if ('ETF' in type_upper or 'ETF' in name_upper
                    or '型基金' in base_info.get('name', '')):
                scores[type_name] = 100
            else:
                # 一般關鍵字比對
                for kw in rule['keywords']:
                    if kw.upper() in text_up:
                        scores[type_name] = 100
                        break
            continue

        # ─ 權值股 → 由市值邏輯決定，此處跳過 ─
        if type_name == '權值股':
            continue

        hit = sum(1 for kw in rule['keywords'] if kw.upper() in text_up)
        scores[type_name] = min(hit * rule['per_hit'], 100)

    return scores


# ═══════════════════════════════════════════════════════════════
# 公開主函數
# ═══════════════════════════════════════════════════════════════

def classify_stock(stock_id: str) -> dict:
    """
    自動判定股票類型。

    回傳格式：
    {
        "stock_id": "2330",
        "company_name": "台積電",
        "primary_type": "AI",
        "primary_confidence": 91,
        "secondary_type": "半導體",
        "secondary_confidence": 80,
        "model_blend": {"primary_weight": 0.8, "secondary_weight": 0.2},
        "reason": [...],
        "market_cap_b": 25000,
        "risks": [...],
        "operation_tips": [...],
        "secondary_risks": [...],
        "secondary_tips": [...],
    }
    若 confidence < 70 → primary_type = "Unknown"
    """
    # ── Step 0: 快取命中 ──
    cache = _load_cache()
    if stock_id in cache and _is_cache_valid(cache[stock_id]):
        print(f"[classifier] 快取命中: {stock_id}")
        return cache[stock_id]['result']

    print(f"[classifier] 開始分析: {stock_id}")

    # ── Step 1: FinMind 基本資料 ──
    base_info = _fetch_base_info(stock_id)
    company_name = base_info.get('name', stock_id)

    # ── Step 2: Gemini 聯網描述 ──
    ai_desc = _fetch_ai_description(stock_id, company_name)

    # ── Step 3: 合併全文 ──
    full_text = " ".join([
        company_name,
        base_info.get('industry', ''),
        base_info.get('type', ''),
        ai_desc,
    ])

    # ── Step 4: 關鍵字比對 ──
    scores = _apply_keywords(full_text, base_info)

    # ── Step 5: 市值補分 → 權值股 ──
    market_cap_b = _fetch_market_cap_b(stock_id)
    if market_cap_b >= 5000:
        scores['權值股'] = min(scores.get('權值股', 0) + 80, 100)
    elif market_cap_b >= 3000:
        scores['權值股'] = min(scores.get('權值股', 0) + 60, 100)
    elif market_cap_b >= 1000:
        scores['權值股'] = min(scores.get('權值股', 0) + 40, 100)

    # ── Step 6: 排序 ──
    sorted_types = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    valid = [(t, s) for t, s in sorted_types if s > 0]

    if not valid or valid[0][1] < 70:
        primary_type       = "Unknown"
        primary_conf       = valid[0][1] if valid else 0
        secondary_type     = valid[1][0] if len(valid) > 1 else None
        secondary_conf     = valid[1][1] if len(valid) > 1 else 0
    else:
        primary_type   = valid[0][0]
        primary_conf   = min(valid[0][1], 100)
        secondary_type = valid[1][0] if len(valid) > 1 else None
        secondary_conf = min(valid[1][1], 100) if len(valid) > 1 else 0

    # ── Step 7: 混合比例 ──
    if secondary_type and secondary_conf >= 70:
        blend = {"primary_weight": 0.8, "secondary_weight": 0.2}
    else:
        blend          = {"primary_weight": 1.0, "secondary_weight": 0.0}
        secondary_type = None
        secondary_conf = 0

    # ── Step 8: 整理 reason ──
    reason = []
    if base_info.get('industry'):
        reason.append(f"產業分類：{base_info['industry']}")
    for kw in KEYWORD_RULES.get(primary_type, {}).get('keywords', []):
        if kw.upper() in full_text.upper():
            reason.append(f"包含關鍵字：{kw}")
        if len(reason) >= 4:
            break
    if market_cap_b > 0:
        reason.append(f"市值約 {market_cap_b:,.0f} 億元")

    result = {
        "stock_id":            stock_id,
        "company_name":        company_name,
        "primary_type":        primary_type,
        "primary_confidence":  int(primary_conf),
        "secondary_type":      secondary_type,
        "secondary_confidence": int(secondary_conf),
        "model_blend":         blend,
        "reason":              reason[:5],
        "market_cap_b":        round(market_cap_b, 0),
        "risks":               TYPE_RISKS.get(primary_type, TYPE_RISKS["Unknown"]),
        "operation_tips":      TYPE_OPERATION_TIPS.get(primary_type, TYPE_OPERATION_TIPS["Unknown"]),
        "secondary_risks":     TYPE_RISKS.get(secondary_type, []) if secondary_type else [],
        "secondary_tips":      TYPE_OPERATION_TIPS.get(secondary_type, []) if secondary_type else [],
    }

    # ── Step 9: 存入快取 ──
    cache[stock_id] = {
        'cached_at': datetime.datetime.now().isoformat(),
        'result':    result,
    }
    _save_cache(cache)

    print(f"[classifier] {stock_id} → {primary_type} ({primary_conf}%) / {secondary_type} ({secondary_conf}%)")
    return result
