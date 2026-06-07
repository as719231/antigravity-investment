# 🚀 抗重力計畫 — AI 被動收入儀表板

每月投入 5,000 元，讓 AI 幫您分析股市、追蹤被動收入成長。

## 📁 專案結構

```
antigravity-investment/
├── app.py                     # 主程式：Streamlit UI 儀表板 (主要入口)
├── ai_financial_advisor.py    # AI 分析模組 (指令列測試用)
├── stock_monitor.py           # 股價監控模組 (指令列測試用)
├── passive_income_simulator.py# 被動收入複利模擬器
├── requirements.txt           # 套件清單
├── .env.example               # API Key 設定範本 (請自行複製為 .env)
└── README.md                  # 本說明文件
```

## ⚙️ 安裝與執行

### 第一步：安裝 Python (只需做一次)
如果新電腦沒有 Python，請去 https://www.python.org/downloads/ 下載安裝。

### 第二步：安裝套件
在終端機 (PowerShell) 中，切換到本專案資料夾，執行：
```powershell
py -m pip install -r requirements.txt
```

### 第三步：設定 API Key
複製 `.env.example` 並改名為 `.env`，然後填入您的 Gemini API Key：
```
GEMINI_API_KEY=您的金鑰填在這裡
```

> 您可以去 https://aistudio.google.com/app/apikey 免費申請。

### 第四步：啟動儀表板
```powershell
streamlit run app.py
```
瀏覽器會自動開啟 http://localhost:8501。

---

## 📊 各程式說明

| 程式 | 功能 |
|------|------|
| `app.py` | **主要入口**，有完整的 UI 圖表與 AI 分析 |
| `passive_income_simulator.py` | 計算複利增長，預測未來被動收入 |
| `stock_monitor.py` | 快速查詢指定標的的最新股價 |
| `ai_financial_advisor.py` | 指令列版本的 AI 分析 |

---

## 🎯 投資策略摘要

- **標的**：00878 (國泰永續高股息 ETF)
- **方式**：每月定期定額 5,000 元，透過永豐金「豐存股」自動扣款
- **目標**：15 年後達成每月被動收入 7,000 元以上
- **本程式角色**：AI 監控大腦，協助判斷市場時機，提供建議（實際買賣由券商系統執行）

---

## ⚠️ 注意事項

- `.env` 檔案請勿傳給他人或上傳到 GitHub（裡面含有您的 API Key）
- 本程式不會自動下單，僅提供分析建議
- 所有投資均有風險，請自行評估

---

## 🔗 下一步目標

- [ ] 部署到 Streamlit Community Cloud（讓朋友不用安裝就能用）
- [ ] 串接 LINE Notify（每日推送財富進度報告）
- [ ] 串接永豐金 Shioaji API（實現真正的自動下單）
