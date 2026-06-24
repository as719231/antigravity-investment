import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import json
import datetime
from FinMind.data import DataLoader

import config
import importlib
import core.pattern_detector
import core.ai_agent
import core.realtime_provider
importlib.reload(core.pattern_detector)
importlib.reload(core.ai_agent)
importlib.reload(core.realtime_provider)
from core.pattern_detector import evaluate_stock_signals, fetch_stock_data
from core.ai_agent import generate_advisor_response, get_stock_news_briefing, get_ai_stock_recommendations
from core.realtime_provider import fetch_realtime_price

# --- 積木化新分頁模組（各自獨立，不互相影響）---
import ui.tab_us_market as tab_us_market_mod
import ui.tab_futures as tab_futures_mod

# --- 多語言翻譯字典 ---
LANG_DICT = {
    "繁體中文": {
        "page_title": "專屬 AI 股市理財專員",
        "sub_header": "結合 K 線形態自動辨識技術與 Gemini 智慧聯網分析，提供您最專業的投資顧問決策輔助。",
        "settings_title": "⚙️ 設定與核心配置",
        "api_key_label": "請輸入您的 Gemini API Key",
        "api_key_help": "您可以前往 Google AI Studio 免費申請。",
        "choose_brain": "🤖 選擇 AI 專員大腦",
        "model_label": "選擇 AI 大腦模型：",
        "model_help": "gemini-3.5-flash 模型速度與智慧最平衡；gemini-2.5-flash 模型回覆速度極快。",
        "search_title": "🔍 查詢新標的",
        "select_common": "選擇常用股票",
        "manual_input": "或手動輸入其他台股代號",
        "sidebar_warning": "💡 **本系統為純策略建議與形態分析工具。** 任何投資動作請於您的實體證券 App 中手動執行，程式不會且無法進行自動下單。",
        "powered_by": "Powered by AI Stock Advisor Engine",
        "main_title": "📈 專屬 AI 股市理財助手",
        "input_warning": "請在左側欄位輸入正確的股票代碼。",
        "spinner_analyzing": "正在分析標的 {stock_id} 當前走勢...",
        "tab_market": "📊 台股看盤",
        "tab_us_market": "🇺🇸 美股看盤",
        "tab_futures": "📉 期貨市場",
        "tab_portfolio": "💼 持股追蹤",
        "tab_chat": "💬 AI 對話",
        "tab_news": "📰 新聞分析",
        "tab_screener": "💡 智慧選股",
        "tab_lessons": "📚 教學筆記",
        "close_price": "今日收盤價",
        "currency": "元",
        "rsi_label": "強弱 RSI (14)",
        "rsi_overbought": "超買區(偏貴)",
        "rsi_oversold": "超賣區(偏便宜)",
        "rsi_neutral": "盤整觀望區",
        "kd_label": "隨機指標 KD (9, 3, 3)",
        "kd_bullish": "黃金交叉看漲",
        "kd_bearish": "死亡交叉看跌",
        "volatility_label": "波動度 (20天年化)",
        "volatility_high": "高波動度",
        "volatility_low": "低波動度",
        "volatility_stable": "波動平穩",
        "yield_label": "估算股息殖利率",
        "yield_sub": "依歷史配息估算",
        "chart_title": "📈 技術分析 K 線圖 (MA5 / MA20 / MA60)",
        "k_line": "K線",
        "ma5_label": "5MA (週線)",
        "ma20_label": "20MA (月線)",
        "ma60_label": "60MA (季線)",
        "patterns_alarm": "🔍 教學形態自動偵測警報",
        "risk_assess": "當前大腦風險評估",
        "risk_level_title": "當前大腦風險評估",
        "risk_score_desc": "綜合量化評估分：<b>{score}/100</b> (評分愈低代表回調風險愈小，更安全)",
        "tech_patterns": "今日技術形態與交叉訊號：",
        "no_patterns": "🔍 今日股價走勢平穩，目前技術指標與 K 線型態無特殊異動。",
        "portfolio_title": "💼 Akira 主人的專屬股票資產看板",
        "portfolio_value": "股票資產總市值",
        "portfolio_count": "共持有 {count} 檔個股",
        "unrealized_pnl": "未實現損益總額",
        "tax_deducted": "已扣除模擬證券交易稅與手續費",
        "total_return": "股票資產總報酬率",
        "invested_cost": "初始投入成本：{cost:,.0f} 元",
        "holdings_detail": "📋 庫存明細清單",
        "col_code": "代號",
        "col_name": "股票名稱",
        "col_shares": "持有股數",
        "col_avg_cost": "平均買入價",
        "col_latest_close": "最新收盤價",
        "col_total_cost": "投入總成本",
        "col_current_val": "當前總價值",
        "col_pnl": "未實現損益",
        "col_return": "報酬率",
        "chat_title": "🤖 您的專屬 AI 理財專員 - 小雅",
        "chat_desc": "小雅已經閱讀了您的 14 個交易鐵律、5 大分時口訣，並了解您目前的持股。她會全程協助您分析股市、解答疑問。任何下單由您本人手動處理。",
        "chat_placeholder": "向小雅詢問股市看法，例如：『我手上買在 66.2 元的康舒，現在應該賣掉嗎？』",
        "chat_spinner": "小雅正在翻看您的交易鐵律並聯網分析中...",
        "shortcut_panel": "💡 快捷諮詢面板：",
        "shortcut_q1": "📊 依據口訣幫我評估今日 {stock_id}",
        "shortcut_q1_text": "請幫我分析今天 {stock_id} 股價表現，並比對我的14個鐵律與5大分時口訣，給予分析。",
        "shortcut_q2": "⚖️ 檢視我持有的 6282 康舒盈虧與建議",
        "shortcut_q2_text": "我的 6282 康舒持股，成本 66.2 元，請幫我分析並給予出路規劃建議。",
        "shortcut_q3": "📖 幫我複習『分時口訣一與四』的含意",
        "shortcut_q3_text": "請幫我詳細解釋 5 大分時口訣裡面的『口訣一：下午大漲切記離場』與『口訣四：早上大漲注意減倉』有什麼實戰意義？",
        "news_title": "📰 聯網即時新聞與 AI 綜合多維點評",
        "news_desc": "啟用 Google Search Grounding 聯網搜尋工具，一鍵為您彙整關於股票 **{stock_id}** 的最新消息、市場利多與利空隱憂。",
        "news_viewpoint": "🎯 選擇您的分析觀點：",
        "news_perspective": "切換 AI 剖析視角：",
        "news_options": ["長期價值投資視角 (融合 股癌 / 巴菲特 / 彼得林區)", "短期技術當沖視角 (融合 主人14鐵律 / 5分時口訣 / 短線動能)", "🔍 機構分析師深度研究 (CFA 7大清單)"],
        "news_trigger": "🌐 一鍵啟動 AI 聯網多維解析",
        "news_spinner": "正在以【{viewpoint}】解析 {stock_id} 的最新趨勢...",
        "news_report_title": "### 📝 AI 聯網新聞速報分析 ({viewpoint})",
        "screener_title": "💡 智能聯網選股建議",
        "screener_desc": "利用 Google Search Grounding 聯網搜尋與大師選股心法，為您推薦當前市場最適合長期價值投資與短期當沖操作的兩大類前 10 大熱門個股。",
        "select_market": "🎯 選擇股票市場：",
        "market_options": ["台股市場 (Taiwan Stock Market)", "美股市場 (US Stock Market)"],
        "screener_trigger": "🔍 啟動 AI 智能選股推薦",
        "screener_spinner": "正在聯網搜集資料並分析選股中，請稍候...",
        "screener_report_title": "### 📝 AI 智能選股推薦報告 ({market})",
        "lessons_title": "📚 股市教學圖卡 — 隨身複習筆記",
        "lessons_desc": "這是從您放置在 `C:\\Users\\as719\\Desktop\\股市教學` 資料夾中的 21 張圖卡中提取出的精華心法，供您隨時研讀複習：",
        "lessons_h1": "1️⃣ 新手一定要記住的 14 個交易鐵律",
        "lessons_h2": "2️⃣ 五大分時操盤口訣",
        "lessons_h3": "3️⃣ 必背 K 線型態圖形與意義",
        "lessons_h4": "4️⃣ 癌大/主委 (股癌) 的灰階思考心法",
        "lessons_bullish": "🟢 看漲型態 (買入訊號)",
        "lessons_bearish": "🔴 看跌型態 (賣出警告)",
        "lessons_neutral": "🟡 中性與轉折型態",
        "strength_label": "強度",
        "advisor_badge": {"bullish": "買入訊號", "bearish": "賣出訊號", "neutral": "中性訊號"},
        "risk_level_names": {"低風險": "低風險", "中風險": "中風險", "高風險": "高風險"},
        "trade_rec_title": "🎯 AI 交易操盤建議",
        "trade_rec_action_label": "建議動作：",
        "trade_rec_reason_label": "決策依據：",
        "trade_rec_actions": {
            "buy": "現股買進 (做多)",
            "sell_partial": "分倉出貨 (多單減倉)",
            "liquidate": "直接清倉 (現股賣出避險)",
            "watch": "保持觀望 (空手待變)"
        }
    },
    "English": {
        "page_title": "Personal AI Stock Advisor",
        "sub_header": "Combining automated K-line pattern recognition with Gemini internet intelligence to provide professional investment advice.",
        "settings_title": "⚙️ Settings & Core Config",
        "api_key_label": "Please enter your Gemini API Key",
        "api_key_help": "You can get a free API Key at Google AI Studio.",
        "choose_brain": "🤖 Choose AI Advisor Brain",
        "model_label": "Select AI Brain Model:",
        "model_help": "gemini-3.5-flash offers the best balance of speed and smartness; gemini-2.5-flash is extremely fast.",
        "search_title": "🔍 Search New Stock",
        "select_common": "Select Common Stock",
        "manual_input": "Or manually enter Taiwan stock code",
        "sidebar_warning": "💡 **This system is purely a strategy and pattern analysis tool.** Investment actions must be manually executed in your actual brokerage App; the program cannot and will not place automated trades.",
        "powered_by": "Powered by AI Stock Advisor Engine",
        "main_title": "📈 Personal AI Stock Advisor",
        "input_warning": "Please enter a valid stock code in the sidebar.",
        "spinner_analyzing": "Analyzing current trend of stock {stock_id}...",
        "tab_market": "📊 TW Market",
        "tab_us_market": "🇺🇸 US Market",
        "tab_futures": "📉 Futures",
        "tab_portfolio": "💼 Portfolio",
        "tab_chat": "💬 AI Chat",
        "tab_news": "📰 News",
        "tab_screener": "💡 Screener",
        "tab_lessons": "📚 Lessons",
        "close_price": "Today's Close",
        "currency": "TWD",
        "rsi_label": "RSI (14) Strength",
        "rsi_overbought": "Overbought (Expensive)",
        "rsi_oversold": "Oversold (Cheap)",
        "rsi_neutral": "Consolidation (Neutral)",
        "kd_label": "Stochastic KD (9, 3, 3)",
        "kd_bullish": "Golden Cross (Bullish)",
        "kd_bearish": "Death Cross (Bearish)",
        "volatility_label": "Volatility (20d Ann.)",
        "volatility_high": "High Volatility",
        "volatility_low": "Low Volatility",
        "volatility_stable": "Stable Volatility",
        "yield_label": "Estimated Div Yield",
        "yield_sub": "Based on historical payout",
        "chart_title": "📈 Tech Analysis Candlestick Chart (MA5 / MA20 / MA60)",
        "k_line": "K-Line",
        "ma5_label": "5MA (Weekly)",
        "ma20_label": "20MA (Monthly)",
        "ma60_label": "60MA (Quarterly)",
        "patterns_alarm": "🔍 Pattern Detection Alert",
        "risk_assess": "Current Risk Assessment",
        "risk_level_title": "Current Risk Assessment",
        "risk_score_desc": "Comprehensive Score: <b>{score}/100</b> (Lower score indicates lower pullback risk, safer)",
        "tech_patterns": "Today's Technical Patterns & Crossovers:",
        "no_patterns": "🔍 Stock price is stable today; no special patterns or crossovers detected.",
        "portfolio_title": "💼 Akira's Personal Stock Portfolio Tracker",
        "portfolio_value": "Portfolio Market Value",
        "portfolio_count": "Holding {count} stocks",
        "unrealized_pnl": "Total Unrealized P&L",
        "tax_deducted": "Simulated tax and fees deducted",
        "total_return": "Portfolio Return Rate",
        "invested_cost": "Initial Cost: {cost:,.0f} TWD",
        "holdings_detail": "📋 Detailed Holdings List",
        "col_code": "Code",
        "col_name": "Stock Name",
        "col_shares": "Shares Owned",
        "col_avg_cost": "Avg Buy Price",
        "col_latest_close": "Latest Close",
        "col_total_cost": "Total Cost",
        "col_current_val": "Current Value",
        "col_pnl": "Unrealized P&L",
        "col_return": "Return Rate",
        "chat_title": "🤖 Your Personal AI Advisor - Yumi",
        "chat_desc": "Yumi has read your 14 Trading Rules, 5 Intraday Mnemonics, and understands your current portfolio. She will assist you in analyzing the market and answering questions. Any trading orders must be manually executed by you.",
        "chat_placeholder": "Ask Yumi about the market, e.g., 'Should I sell my AcBel shares bought at 66.2 TWD?'",
        "chat_spinner": "Yumi is reviewing your rules and performing online search analysis...",
        "shortcut_panel": "💡 Shortcut Questions:",
        "shortcut_q1": "📊 Evaluate today's {stock_id} using rules",
        "shortcut_q1_text": "Please analyze today's performance of {stock_id} against my 14 trading rules and 5 intraday mnemonics.",
        "shortcut_q2": "⚖️ Review 6282 AcBel P&L and advice",
        "shortcut_q2_text": "My 6282 AcBel stock cost is 66.2 TWD. Please analyze it and advise on my next steps.",
        "shortcut_q3": "📖 Review meanings of 'Intraday Rules 1 & 4'",
        "shortcut_q3_text": "Please explain the practical trading significance of Mnemonics 1 ('Take profit on afternoon rallies') and 4 ('Trim on morning spikes') in detail.",
        "news_title": "📰 Real-time News & AI Multi-dimensional Analysis",
        "news_desc": "Enable Google Search Grounding to aggregate the latest news, market tailwinds, and risks for stock **{stock_id}** in one click.",
        "news_viewpoint": "🎯 Select Your Analysis Perspective:",
        "news_perspective": "Select AI Viewpoint:",
        "news_options": ["Long-term Value Perspective (Buffett, Peter Lynch, Gooaye)", "Short-term Trading Perspective (14 Rules, 5 Mnemonics, Momentum)", "🔍 Institutional Deep Dive (CFA 7-Point Checklist)"],
        "news_trigger": "🌐 Trigger AI Online Analysis",
        "news_spinner": "Analyzing latest trends of {stock_id} from [{viewpoint}] perspective...",
        "news_report_title": "### 📝 AI News Briefing Analysis ({viewpoint})",
        "screener_title": "💡 AI Stock Screener Recommendations",
        "screener_desc": "Utilize Google Search Grounding and stock screening criteria to recommend the top 10 stocks for long-term holding and short-term day trading in Taiwan/US markets.",
        "select_market": "🎯 Select Stock Market:",
        "market_options": ["Taiwan Stock Market", "US Stock Market"],
        "screener_trigger": "🔍 Run AI Stock Screener",
        "screener_spinner": "Searching the web and screening stock candidates, please wait...",
        "screener_report_title": "### 📝 AI Stock Screener Report ({market})",
        "lessons_title": "📚 Stock Lessons — Quick Revision Notes",
        "lessons_desc": "These are core lessons extracted from the 21 tutorial images in your '股市教學' folder on your desktop for quick review:",
        "lessons_h1": "1️⃣ 14 Trading Rules For Beginners",
        "lessons_h2": "2️⃣ Five Intraday Trading Mnemonics",
        "lessons_h3": "3️⃣ Key K-line Patterns & Meanings",
        "lessons_h4": "4️⃣ Gooaye's Gray Thinking Mindset",
        "lessons_bullish": "🟢 Bullish Patterns (Buy Signal)",
        "lessons_bearish": "🔴 Bearish Patterns (Sell Warning)",
        "lessons_neutral": "🟡 Neutral & Reversal Patterns",
        "strength_label": "Strength",
        "advisor_badge": {"bullish": "Buy Signal", "bearish": "Sell Signal", "neutral": "Neutral Signal"},
        "risk_level_names": {"低風險": "Low Risk", "中風險": "Moderate Risk", "高風險": "High Risk"},
        "trade_rec_title": "🎯 AI Trading Recommendation",
        "trade_rec_action_label": "Action:",
        "trade_rec_reason_label": "Rationale:",
        "trade_rec_actions": {
            "buy": "Spot Buy (Long)",
            "sell_partial": "Scale Out (Trim Long)",
            "liquidate": "Liquidate (Sell Spot to Hedge)",
            "watch": "Stand Aside (Hold Cash)"
        }
    },
    "日本語": {
        "page_title": "専属 AI 株式投資アシスタント",
        "sub_header": "ローソク足パターンの自動認識技術と Gemini ネットインテリジェント分析を組み合わせ、専門的な投資アドバイスを提供します。",
        "settings_title": "⚙️ 設定とコア構成",
        "api_key_label": "Gemini API キーを入力してください",
        "api_key_help": "Google AI Studio で無料の API キーを申請できます。",
        "choose_brain": "🤖 AIアドバイザーの脳を選択",
        "model_label": "AI大脳モデルを選択：",
        "model_help": "gemini-3.5-flashは速度と知能のバランスが最適です。gemini-2.5-flashは応答が非常に高速です。",
        "search_title": "🔍 新規銘柄の検索",
        "select_common": "常用銘柄を選択",
        "manual_input": "または台湾株コードを手動入力",
        "sidebar_warning": "💡 **本システムは純粋な戦略提案およびパターン分析ツールです。** 実際の投資行動はご自身の証券アプリで手動で行ってください。自動注文は行えません。",
        "powered_by": "Powered by AI Stock Advisor Engine",
        "main_title": "📈 専属 AI 株式投資アシスタント",
        "input_warning": "左側の欄に正しい株式コードを入力してください。",
        "spinner_analyzing": "銘柄 {stock_id} の現在の動向を分析中...",
        "tab_market": "📊 台湾株",
        "tab_us_market": "🇺🇸 米国株",
        "tab_futures": "📉 先物",
        "tab_portfolio": "💼 保有株",
        "tab_chat": "💬 AIチャット",
        "tab_news": "📰 ニュース",
        "tab_screener": "💡 銘柄選定",
        "tab_lessons": "📚 学習ノート",
        "close_price": "本日終値",
        "currency": "元",
        "rsi_label": "強弱 RSI (14)",
        "rsi_overbought": "買われすぎ (割高)",
        "rsi_oversold": "売られすぎ (割安)",
        "rsi_neutral": "もみ合い (様子見)",
        "kd_label": "ストキャスティクス KD (9, 3, 3)",
        "kd_bullish": "ゴールデンクロス (強気)",
        "kd_bearish": "デッドクロス (弱気)",
        "volatility_label": "ボラティリティ (20日年率)",
        "volatility_high": "高ボラティリティ",
        "volatility_low": "低ボラティリティ",
        "volatility_stable": "ボラティリティ安定",
        "yield_label": "配当利回り予想",
        "yield_sub": "過去の配当データに基づく",
        "chart_title": "📈 技術分析ローソク足チャート (MA5 / MA20 / MA60)",
        "k_line": "ローソク足",
        "ma5_label": "5MA (週足)",
        "ma20_label": "20MA (月足)",
        "ma60_label": "60MA (季足)",
        "patterns_alarm": "🔍 パターン自動検知アラート",
        "risk_assess": "現在のリスク評価",
        "risk_level_title": "現在のリスク評価",
        "risk_score_desc": "総合評価スコア: <b>{score}/100</b> (スコアが低いほど調整リスクが小さく、より安全です)",
        "tech_patterns": "本日の技術パターンとクロスシグナル：",
        "no_patterns": "🔍 本日の株価は安定しています。特殊なパターンやクロスオーバーは検知されませんでした。",
        "portfolio_title": "💼 Akira様専属の保有株式ボード",
        "portfolio_value": "株式資産総時価評価額",
        "portfolio_count": "計 {count} 銘柄保有",
        "unrealized_pnl": "未実現損益総額",
        "tax_deducted": "シミュレーション手数料・税金控除後",
        "total_return": "株式資産総利益率",
        "invested_cost": "初期投資額：{cost:,.0f} 元",
        "holdings_detail": "📋 保有株式明細一覧",
        "col_code": "コード",
        "col_name": "銘柄名",
        "col_shares": "保有株数",
        "col_avg_cost": "平均取得単価",
        "col_latest_close": "現在値",
        "col_total_cost": "投資総額",
        "col_current_val": "時価評価額",
        "col_pnl": "未実現損益",
        "col_return": "利益率",
        "chat_title": "🤖 Akira様専属 AIアドバイザー - ミヤ",
        "chat_desc": "ミヤは14の取引鉄則、5つの分時口訣を熟読し、お客様の現在の保有銘柄を把握しています。市場分析やご質問に全力でお答えします。なお、注文はすべてお客様ご自身で手動で行っていただきます。",
        "chat_placeholder": "ミヤに株の見通しを聞く。例：「66.2元で買った康舒は、今売るべきですか？」",
        "chat_spinner": "ミヤが取引ルールを確認し、ネット検索で分析しています...",
        "shortcut_panel": "💡 クイック相談パネル：",
        "shortcut_q1": "📊 口訣に基づいて本日の {stock_id} を評価する",
        "shortcut_q1_text": "今日の {stock_id} の株価パフォーマンスを、私の14の取引ルールと5つの分時口訣と比較して分析してください。",
        "shortcut_q2": "⚖️ 保有中の 6282 康舒 の損益とアドバイスを確認",
        "shortcut_q2_text": "私の保有する 6282 康舒（取得単価 66.2元）について、現状を分析し今後のアドバイスをください。",
        "shortcut_q3": "📖 『分時口訣 一 と 四』の意味を復習する",
        "shortcut_q3_text": "5つの分時口訣のうち、「口訣一：午後の急騰は手仕舞い」と「口訣四：朝の急騰は部分利確」の実戦的な意義を詳しく説明してください。",
        "news_title": "📰 リアルタイムネットニュース・AI多角分析",
        "news_desc": "Google 検索グラウンディングを有効にし、銘柄 **{stock_id}** に関する最新ニュース、メリット、懸念事項をワンクリックで集計します。",
        "news_viewpoint": "🎯 分析の視点を選択：",
        "news_perspective": "AI分析視点の切り替え：",
        "news_options": ["長期バリュー投資視点 (バフェット、ピーター・リンチ、股癌の融合)", "短期デイトレ視点 (お客様の14鉄則、5つの口訣、短期モメンタム)", "🔍 機関投資家深層分析 (CFA 7大チェックリスト)"],
        "news_trigger": "🌐 ワンクリックでAIネット多角解析を起動",
        "news_spinner": "【{viewpoint}】の視点から {stock_id} の最新動向を分析中...",
        "news_report_title": "### 📝 AIネットニュース速報分析 ({viewpoint})",
        "screener_title": "💡 AIスマート銘柄スクリーナー",
        "screener_desc": "Google 検索グラウンディングと大師の選股基準を活用し、長期バリュー投資および短期デイトレに適した上位10銘柄を推薦します。",
        "select_market": "🎯 株式市場を選択：",
        "market_options": ["台湾株式市場 (Taiwan Market)", "米国株式市場 (US Market)"],
        "screener_trigger": "🔍 AIスマート選股を実行",
        "screener_spinner": "ウェブを検索し、選股候補を分析中。しばらくお待ちください...",
        "screener_report_title": "### 📝 AIスマート選股推薦レポート ({market})",
        "lessons_title": "📚 株式投資學習ノート",
        "lessons_desc": "デスクトップの「股市教學」フォルダにある21枚のカードから抽出されたエッセンスです。いつでも復習できます：",
        "lessons_h1": "1️⃣ 初心者必攜の14の取引鐵則",
        "lessons_h2": "2️⃣ 5つの分時デイトレ口訣",
        "lessons_h3": "3️⃣ 必須ローソク足パターンと意味",
        "lessons_h4": "4️⃣ 股癌のグレーシンキング（灰階思考）",
        "lessons_bullish": "🟢 強気パターン (買いシグナル)",
        "lessons_bearish": "🔴 弱気パターン (売り警告)",
        "lessons_neutral": "🟡 中立・転換パターン",
        "strength_label": "強度",
        "advisor_badge": {"bullish": "買いシグナル", "bearish": "売りシグナル", "neutral": "中立シグナル"},
        "risk_level_names": {"低風險": "低リスク", "中風險": "中リスク", "高風險": "高リスク"},
        "trade_rec_title": "🎯 AI取引操盤アドバイス",
        "trade_rec_action_label": "推奨アクション：",
        "trade_rec_reason_label": "意思決定の根拠：",
        "trade_rec_actions": {
            "buy": "現物買い (買い建て)",
            "sell_partial": "分割売却 (買いポジション縮小)",
            "liquidate": "全売却 (現物売りヘッジ)",
            "watch": "様子見 (キャッシュ維持)"
        }
    },
    "ไทย": {
        "page_title": "ผู้ช่วยส่วนตัว AI วิเคราะห์หุ้น",
        "sub_header": "ผสมผสานเทคโนโลยีตรวจจับรูปแบบแท่งเทียนกับวิเคราะห์ออนไลน์อัจฉริยะ Gemini เพื่อคำแนะนำลงทุนมืออาชีพ",
        "settings_title": "⚙️ การตั้งค่าและกำหนดค่าหลัก",
        "api_key_label": "กรุณากรอก Gemini API Key ของคุณ",
        "api_key_help": "คุณสามารถขอรับ API Key ฟรีได้ที่ Google AI Studio",
        "choose_brain": "🤖 เลือกสมองของที่ปรึกษา AI",
        "model_label": "เลือกโมเดลสมอง AI:",
        "model_help": "gemini-3.5-flash มีความเร็วและความฉลาดที่สมดุลที่สุด gemini-2.5-flash ตอบสนองอย่างรวดเร็วมาก",
        "search_title": "🔍 ค้นหาหุ้นใหม่",
        "select_common": "เลือกหุ้นที่ใช้บ่อย",
        "manual_input": "หรือป้อนรหัสหุ้นไต้หวันด้วยตนเอง",
        "sidebar_warning": "💡 **ระบบนี้เป็นเครื่องมือแนะนำกลยุทธ์และรูปแบบเท่านั้น** การลงทุนต้องทำธุรกรรมด้วยตนเองในแอปพลิเคชันจริงของคุณ ไม่สามารถส่งคำสั่งซื้อขายอัตโนมัติได้",
        "powered_by": "Powered by AI Stock Advisor Engine",
        "main_title": "📈 ผู้ช่วยส่วนตัว AI วิเคราะห์หุ้น",
        "input_warning": "กรุณากรอกรหัสหุ้นที่ถูกต้องในคอลัมน์ด้านซ้าย",
        "spinner_analyzing": "กำลังวิเคราะห์แนวโน้มปัจจุบันของหุ้น {stock_id}...",
        "tab_market": "📊 หุ้นไต้หวัน",
        "tab_us_market": "🇺🇸 หุ้นสหรัฐ",
        "tab_futures": "📉 ฟิวเจอร์ส",
        "tab_portfolio": "💼 พอร์ต",
        "tab_chat": "💬 AI แชท",
        "tab_news": "📰 ข่าว",
        "tab_screener": "💡 เลือกหุ้น",
        "tab_lessons": "📚 บันทึก",
        "close_price": "ราคาปิดวันนี้",
        "currency": "TWD",
        "rsi_label": "ความแข็งแกร่ง RSI (14)",
        "rsi_overbought": "ซื้อมากเกินไป (ค่อนข้างแพง)",
        "rsi_oversold": "ขายมากเกินไป (ค่อนข้างถูก)",
        "rsi_neutral": "ช่วงไซด์เวย์ (เฝ้ารอดู)",
        "kd_label": "ตัวชี้วัดสุ่ม KD (9, 3, 3)",
        "kd_bullish": "Golden Cross (ขาขึ้น)",
        "kd_bearish": "Death Cross (ขาลง)",
        "volatility_label": "ความผันผวน (20 วันรายปี)",
        "volatility_high": "ความผันผวนสูง",
        "volatility_low": "ความผันผวนต่ำ",
        "volatility_stable": "ผันผวนคงที่",
        "yield_label": "อัตราปันผลตอบแทนโดยประมาณ",
        "yield_sub": "ประมาณการจากประวัติปันผล",
        "chart_title": "📈 กราฟแท่งเทียนเทคนิคอล (MA5 / MA20 / MA60)",
        "k_line": "แท่งเทียน",
        "ma5_label": "5MA (รายสัปดาห์)",
        "ma20_label": "20MA (รายเดือน)",
        "ma60_label": "60MA (รายไตรมาส)",
        "patterns_alarm": "🔍 แจ้งเตือนตรวจจับรูปแบบอัตโนมัติ",
        "risk_assess": "การประเมินความเสี่ยงปัจจุบัน",
        "risk_level_title": "การประเมินความเสี่ยงปัจจุบัน",
        "risk_score_desc": "คะแนนรวม: <b>{score}/100</b> (คะแนนต่ำสุดความเสี่ยงย่อตัวต่ำ ปลอดภัยกว่า)",
        "tech_patterns": "รูปแบบเทคนิคอลและสัญญาณครอสโอเวอร์วันนี้:",
        "no_patterns": "🔍 ราคาหุ้นวันนี้ค่อนข้างมีเสถียรภาพ ไม่พบรูปแบบหรือสัญญาณครอสโอเวอร์พิเศษ",
        "portfolio_title": "💼 บอร์ดสินทรัพย์หุ้นส่วนตัวของ Akira",
        "portfolio_value": "มูลค่าตลาดรวมพอร์ตหุ้น",
        "portfolio_count": "ถือครองหุ้นทั้งหมด {count} ตัว",
        "unrealized_pnl": "ยอดรวมกำไรขาดทุนที่ยังไม่เกิดขึ้น",
        "tax_deducted": "หักภาษีหลักทรัพย์และค่าธรรมเนียมจำลองแล้ว",
        "total_return": "อัตราผลตอบแทนรวมพอร์ตหุ้น",
        "invested_cost": "ต้นทุนเริ่มต้น: {cost:,.0f} TWD",
        "holdings_detail": "📋 รายการรายละเอียดพอร์ตหุ้น",
        "col_code": "รหัส",
        "col_name": "ชื่อหุ้น",
        "col_shares": "จำนวนหุ้นที่ถือ",
        "col_avg_cost": "ราคาซื้อเฉลี่ย",
        "col_latest_close": "ราคาปิดล่าสุด",
        "col_total_cost": "ต้นทุนรวม",
        "col_current_val": "มูลค่าปัจจุบัน",
        "col_pnl": "กำไรขาดทุนที่ยังไม่เกิด",
        "col_return": "อัตราผลตอบแทน",
        "chat_title": "🤖 เจ้าหน้าที่ดูแลบัญชี AI ส่วนตัวของคุณ - เสี่ยวหย่า",
        "chat_desc": "เสี่ยวหย่าได้อ่านกฎการซื้อขาย 14 ข้อ และคำคมการซื้อขายรายวัน 5 ข้อ รวมถึงเข้าใจพอร์ตหุ้นปัจจุบันของคุณแล้ว เธอจะช่วยคุณวิเคราะห์ตลาดและตอบคำถาม การทำธุรกรรมใดๆ จะต้องทำด้วยตนเองโดยคุณ",
        "chat_placeholder": "ถามเสี่ยวหย่าเกี่ยวกับมุมมองหุ้น เช่น 'หุ้น AcBel ที่ซื้อในราคา 66.2 บาท ควรขายตอนนี้ไหม?'",
        "chat_spinner": "เสี่ยวหย่ากำลังตรวจสอบกฎการซื้อขายของคุณและวิเคราะห์ทางอินเทอร์เน็ต...",
        "shortcut_panel": "💡 แผงคำถามด่วน:",
        "shortcut_q1": "📊 ประเมิน {stock_id} วันนี้ตามคำคม",
        "shortcut_q1_text": "กรุณาวิเคราะห์ประสิทธิภาพราคาของ {stock_id} วันนี้ โดยเปรียบเทียบกับกฎเหล็ก 14 ข้อและคำคมรายวัน 5 ข้อของฉัน",
        "shortcut_q2": "⚖️ ตรวจสอบกำไรขาดทุนและคำแนะนำสำหรับหุ้น 6282 AcBel",
        "shortcut_q2_text": "หุ้น 6282 AcBel ของฉันมีต้นทุน 66.2 TWD กรุณาวิเคราะห์และให้คำแนะนำในการวางแผนการลงทุน",
        "shortcut_q3": "📖 ทบทวนความหมายของ 'คำคมรายวัน 1 และ 4'",
        "shortcut_q3_text": "กรุณาอธิบายความหมายในทางปฏิบัติของคำคมข้อที่ 1 ('ตอนบ่ายพุ่งอย่าไล่ราคา') และข้อที่ 4 ('ตอนเช้าพุ่งให้ลดพอร์ต') อย่างละเอียด",
        "news_title": "📰 ข่าวเรียลไทม์ออนไลน์และการประเมินหลายมิติของ AI",
        "news_desc": "เปิดใช้เครื่องมือค้นหา Google Search Grounding เพื่อรวบรวมข่าวล่าสุด ข่าวดี และความเสี่ยงของหุ้น **{stock_id}** ในคลิกเดียว",
        "news_viewpoint": "🎯 เลือกมุมมองการวิเคราะห์ของคุณ:",
        "news_perspective": "เปลี่ยนมุมมองการวิเคราะห์ AI:",
        "news_options": ["มุมมองการลงทุนระยะยาว (Buffett, Peter Lynch, Gooaye)", "มุมมองเก็งกำไรระยะสั้น (กฎ 14 ข้อ, คำคม 5 ข้อ, โมเมนตัม)", "🔍 วิเคราะห์เชิงสถาบัน (CFA 7 ประเด็น)"],
        "news_trigger": "🌐 เริ่มการวิเคราะห์หลายมิติของ AI ในคลิกเดียว",
        "news_spinner": "กำลังวิเคราะห์แนวโน้มล่าสุดของ {stock_id} ด้วย [{viewpoint}]...",
        "news_report_title": "### 📝 สรุปรายงานข่าวและการวิเคราะห์ของ AI ({viewpoint})",
        "screener_title": "💡 คำแนะนำการคัดกรองหุ้นอัจฉริยะ AI",
        "screener_desc": "ใช้เครื่องมือค้นหา Google Search Grounding และเกณฑ์การเลือกหุ้นเพื่อแนะนำหุ้น 10 อันดับแรกสำหรับการลงทุนระยะยาวและการเก็งกำไรระยะสั้น",
        "select_market": "🎯 เลือกตลาดหุ้น:",
        "market_options": ["ตลาดหุ้นไต้หวัน (Taiwan Market)", "ตลาดหุ้นสหรัฐฯ (US Market)"],
        "screener_trigger": "🔍 เริ่มคัดกรองหุ้นด้วย AI",
        "screener_spinner": "กำลังค้นหาเว็บและวิเคราะห์หุ้นตัวเลือก กรุณารอสักครู่...",
        "screener_report_title": "### 📝 รายงานการแนะนำหุ้นอัจฉริยะ AI ({market})",
        "lessons_title": "📚 การ์ดการเรียนรู้หุ้น — บันทึกทบทวนด่วน",
        "lessons_desc": "นี่คือเคล็ดลับหลักที่ sghad มาจากการ์ดสอนเล่นหุ้น 21 ใบในโฟลเดอร์ '股市教學' บนเดสก์ท็อปของคุณ เพื่อให้คุณได้ศึกษาทบทวนได้ทุกเมื่อ:",
        "lessons_h1": "1️⃣ 14 กฎเหล็กการซื้อขายที่มือใหม่ต้องจำ",
        "lessons_h2": "2️⃣ คำคมการซื้อขายรายวัน 5 ข้อ",
        "lessons_h3": "3️⃣ รูปแบบแท่งเทียนสำคัญและความหมาย",
        "lessons_h4": "4️⃣ วิธีคิดแบบสีเทา (Gray Thinking) ของ Gooaye",
        "lessons_bullish": "🟢 รูปแบบกระทิง (สัญญาณซื้อ)",
        "lessons_bearish": "🔴 รูปแบบหมี (แจ้งเตือนขาย)",
        "lessons_neutral": "🟡 รูปแบบเป็นกลางและกลับตัว",
        "strength_label": "ความแรง",
        "advisor_badge": {"bullish": "สัญญาณซื้อ", "bearish": "สัญญาณขาย", "neutral": "สัญญาณเป็นกลาง"},
        "risk_level_names": {"低風險": "เสี่ยงต่ำ", "中風險": "เสี่ยงปานกลาง", "高風險": "เสี่ยงสูง"},
        "trade_rec_title": "🎯 คำแนะนำการซื้อขายของ AI",
        "trade_rec_action_label": "การกระทำที่แนะนำ:",
        "trade_rec_reason_label": "เหตุผลประกอบการตัดสินใจ:",
        "trade_rec_actions": {
            "buy": "ซื้อด้วยเงินสด (ทำกำไรขาขึ้น)",
            "sell_partial": "แบ่งขายลดความเสี่ยง (ลดพอร์ต)",
            "liquidate": "ขายล้างพอร์ต (ขายเงินสดป้องกันความเสี่ยง)",
            "watch": "เฝ้ารอดูสถานการณ์ (ถือเงินสดรอ)"
        }
    },
    "Tiếng Việt": {
        "page_title": "Trợ lý AI Tài chính Cá nhân",
        "sub_header": "Kết hợp công nghệ nhận dạng mô hình nến tự động và phân tích mạng thông minh Gemini để hỗ trợ quyết định đầu tư chuyên nghiệp.",
        "settings_title": "⚙️ Thiết lập & Cấu hình cốt lõi",
        "api_key_label": "Vui lòng nhập Gemini API Key của bạn",
        "api_key_help": "Bạn có thể đăng ký khóa API miễn phí tại Google AI Studio.",
        "choose_brain": "🤖 Chọn bộ não trợ lý AI",
        "model_label": "Chọn mô hình bộ não AI:",
        "model_help": "gemini-3.5-flash có sự cân bằng tốt nhất giữa tốc độ và trí tuệ; gemini-2.5-flash phản hồi cực kỳ nhanh chóng.",
        "search_title": "🔍 Tra cứu mã chứng khoán",
        "select_common": "Chọn mã cổ phiếu thông dụng",
        "manual_input": "Hoặc tự nhập mã cổ phiếu Đài Loan",
        "sidebar_warning": "💡 **Hệ thống này chỉ là công cụ phân tích mô hình và đề xuất chiến lược.** Mọi hành động giao dịch phải được thực hiện thủ công trong Ứng dụng chứng khoán của bạn. Chương trình không tự động đặt lệnh.",
        "powered_by": "Powered by AI Stock Advisor Engine",
        "main_title": "📈 Trợ lý AI Tài chính Cá nhân",
        "input_warning": "Vui lòng nhập đúng mã cổ phiếu ở cột bên trái.",
        "spinner_analyzing": "Đang phân tích xu hướng hiện tại của mã {stock_id}...",
        "tab_market": "📊 Cổ phiếu TW",
        "tab_us_market": "🇺🇸 Cổ phiếu Mỹ",
        "tab_futures": "📉 Phái sinh",
        "tab_portfolio": "💼 Danh mục",
        "tab_chat": "💬 AI Chat",
        "tab_news": "📰 Tin tức",
        "tab_screener": "💡 Lọc cổ phiếu",
        "tab_lessons": "📚 Học tập",
        "close_price": "Giá đóng cửa hôm nay",
        "currency": "TWD",
        "rsi_label": "Sức mạnh RSI (14)",
        "rsi_overbought": "Quá mua (Đắt)",
        "rsi_oversold": "Quá bán (Rẻ)",
        "rsi_neutral": "Vùng tích lũy theo dõi",
        "kd_label": "Chỉ báo ngẫu nhiên KD (9, 3, 3)",
        "kd_bullish": "Giao cắt vàng (Tăng)",
        "kd_bearish": "Giao cắt tử thần (Giảm)",
        "volatility_label": "Biến động (20 ngày H.hóa)",
        "volatility_high": "Biến động cao",
        "volatility_low": "Biến động thấp",
        "volatility_stable": "Biến động ổn định",
        "yield_label": "Tỷ lệ cổ tức ước tính",
        "yield_sub": "Ước tính theo cổ tức lịch sử",
        "chart_title": "📈 Biểu đồ nến phân tích kỹ thuật (MA5 / MA20 / MA60)",
        "k_line": "Đường nến",
        "ma5_label": "5MA (Tuần)",
        "ma20_label": "20MA (Tháng)",
        "ma60_label": "60MA (Quý)",
        "patterns_alarm": "🔍 Cảnh báo phát hiện mô hình",
        "risk_assess": "Đánh giá rủi ro hiện tại",
        "risk_level_title": "Đánh giá rủi ro hiện tại",
        "risk_score_desc": "Điểm đánh giá tổng hợp: <b>{score}/100</b> (Điểm càng thấp đại diện rủi ro điều chỉnh càng nhỏ, an toàn hơn)",
        "tech_patterns": "Mô hình kỹ thuật và tín hiệu giao cắt hôm nay:",
        "no_patterns": "🔍 Giá cổ phiếu hôm nay ổn định; không phát hiện mô hình hoặc giao cắt đặc biệt nào.",
        "portfolio_title": "💼 Bảng theo dõi tài sản cổ phiếu của Akira",
        "portfolio_value": "Tổng giá trị thị trường cổ phiếu",
        "portfolio_count": "Đang nắm giữ {count} mã",
        "unrealized_pnl": "Tổng lợi nhuận chưa thực hiện",
        "tax_deducted": "Đã khấu trừ thuế giao dịch và phí mô phỏng",
        "total_return": "Tổng tỷ suất sinh lời cổ phiếu",
        "invested_cost": "Vốn đầu tư ban đầu: {cost:,.0f} TWD",
        "holdings_detail": "📋 Danh sách chi tiết danh mục",
        "col_code": "Mã",
        "col_name": "Tên cổ phiếu",
        "col_shares": "Số cổ phiếu sở hữu",
        "col_avg_cost": "Giá mua trung bình",
        "col_latest_close": "Giá đóng cửa mới nhất",
        "col_total_cost": "Tổng chi phí",
        "col_current_val": "Giá trị hiện tại",
        "col_pnl": "Lợi nhuận chưa thực hiện",
        "col_return": "Tỷ suất sinh lời",
        "chat_title": "🤖 Trợ lý AI Tài chính Cá nhân - Tiểu Nhã",
        "chat_desc": "Tiểu Nhã đã đọc 14 quy tắc giao dịch sắt đá, 5 câu khẩu quyết phân thời của bạn, và hiểu rõ danh mục hiện tại của bạn. Cô ấy sẽ hỗ trợ bạn phân tích thị trường, giải đáp thắc mắc. Mọi giao dịch phải được thực hiện thủ công bởi chính bạn.",
        "chat_placeholder": "Hỏi Tiểu Nhã về góc nhìn chứng khoán, ví dụ: 'Tôi đang giữ cổ phiếu AcBel mua ở giá 66.2 TWD, bây giờ có nên bán không?'",
        "chat_spinner": "Tiểu Nhã đang xem lại quy tắc giao dịch của bạn và tiến hành phân tích tìm kiếm mạng...",
        "shortcut_panel": "💡 Bảng câu hỏi nhanh:",
        "shortcut_q1": "📊 Đánh giá {stock_id} hôm nay dựa theo khẩu quyết",
        "shortcut_q1_text": "Vui lòng phân tích hiệu suất giá của {stock_id} hôm nay, đối chiếu với 14 quy tắc sắt và 5 khẩu quyết phân thời của tôi.",
        "shortcut_q2": "⚖️ Kiểm tra lỗ lãi và kiến nghị cho mã 6282 AcBel",
        "shortcut_q2_text": "Cổ phiếu 6282 AcBel của tôi có giá vốn 66.2 TWD. Vui lòng phân tích và đưa ra khuyến nghị lập kế hoạch lối ra.",
        "shortcut_q3": "📖 Ôn tập ý nghĩa 'Khẩu quyết phân thời 1 và 4'",
        "shortcut_q3_text": "Vui lòng giải thích chi tiết ý nghĩa thực chiến của Khẩu quyết 1 ('Bùng nổ chiều tuyệt đối rời sân') và Khẩu quyết 4 ('Bùng nổ sáng chú ý giảm vị thế') trong 5 khẩu quyết phân thời.",
        "news_title": "📰 Tin tức mạng & Phân tích AI",
        "news_desc": "Kích hoạt công cụ tìm kiếm mạng Google Search Grounding, thu thập tin tức mới nhất, ưu thế thị trường và rủi ro tiềm ẩn của mã cổ phiếu **{stock_id}** trong một cú nhấp chuột.",
        "news_viewpoint": "🎯 Chọn góc nhìn phân tích của bạn:",
        "news_perspective": "Chuyển đổi góc nhìn phân tích AI:",
        "news_options": ["Góc nhìn đầu tư giá trị dài hạn (Kết hợp Buffett, Peter Lynch, Gooaye)", "Góc nhìn giao dịch ngắn hạn (Kết hợp 14 quy tắc, 5 khẩu quyết, Động năng ngắn hạn)", "🔍 Phân tích chuyên sâu CFA (7 điểm kiểm tra)"],
        "news_trigger": "🌐 Kích hoạt phân tích đa chiều AI trực tuyến",
        "news_spinner": "Đang phân tích xu hướng mới nhất của {stock_id} theo góc nhìn [{viewpoint}]...",
        "news_report_title": "### 📝 Bản tin phân tích mạng AI ({viewpoint})",
        "screener_title": "💡 Gợi ý lọc cổ phiếu thông minh AI",
        "screener_desc": "Sử dụng Google Search Grounding và tiêu chí lọc cổ tức/động năng để đề xuất top 10 cổ phiếu thích hợp đầu tư dài hạn và giao dịch ngắn hạn.",
        "select_market": "🎯 Chọn thị trường chứng khoán:",
        "market_options": ["Thị trường Đài Loan (Taiwan Market)", "Thị trường Mỹ (US Market)"],
        "screener_trigger": "🔍 Kích hoạt bộ lọc cổ phiếu AI",
        "screener_spinner": "Đang tìm kiếm mạng và phân tích các ứng viên cổ phiếu, vui lòng đợi...",
        "screener_report_title": "### 📝 Báo cáo đề xuất lọc cổ phiếu AI ({market})",
        "lessons_title": "📚 Thẻ bài học chứng khoán — Sổ tay ôn tập nhanh",
        "lessons_desc": "Đây là tinh hoa được trích xuất từ 21 thẻ bài học trong thư mục '股市教學' trên màn hình máy tính của bạn, giúp bạn xem lại bất cứ lúc nào:",
        "lessons_h1": "1️⃣ 14 quy tắc giao dịch sắt đá cho người mới",
        "lessons_h2": "2️⃣ 5 khẩu quyết giao dịch phân thời",
        "lessons_h3": "3️⃣ Mô hình K-line cơ bản và ý nghĩa",
        "lessons_h4": "4️⃣ Tư duy màu xám (Gray Thinking) của Gooaye",
        "lessons_bullish": "🟢 Mô hình tăng giá (Tín hiệu mua)",
        "lessons_bearish": "🔴 Mô hình giảm giá (Cảnh báo bán)",
        "lessons_neutral": "🟡 Mô hình trung tính & đảo chiều",
        "strength_label": "Độ mạnh",
        "advisor_badge": {"bullish": "Tín hiệu mua", "bearish": "Tín hiệu bán", "neutral": "Tín hiệu trung tính"},
        "risk_level_names": {"低風險": "Rủi ro thấp", "中風險": "Rủi ro trung bình", "高風險": "Rủi ro cao"},
        "trade_rec_title": "🎯 Đề xuất giao dịch AI",
        "trade_rec_action_label": "Hành động đề xuất:",
        "trade_rec_reason_label": "Căn cứ quyết định:",
        "trade_rec_actions": {
            "buy": "Mua bằng tiền mặt (Giao dịch Mua)",
            "sell_partial": "Bán từng phần (Giảm vị thế Mua)",
            "liquidate": "Bán hết toàn bộ (Bán tiền mặt phòng vệ)",
            "watch": "Tiếp tục theo dõi (Giữ tiền mặt theo dõi)"
        }
    }
}

# --- K 線圖交叉與型態名稱翻譯對照 ---
SIGNAL_TRANSLATION = {
    "English": {
        "均線黃金交叉 (5MA / 20MA)": "MA Golden Cross (5MA / 20MA)",
        "均線死亡交叉 (5MA / 20MA)": "MA Death Cross (5MA / 20MA)",
        "中長期黃金交叉 (20MA / 60MA)": "Mid-Long Term Golden Cross (20MA / 60MA)",
        "中長期死亡交叉 (20MA / 60MA)": "Mid-Long Term Death Cross (20MA / 60MA)",
        "十字星": "Doji Star",
        "錘子線 (Hammer)": "Hammer",
        "上吊線 (Hanging Man)": "Hanging Man",
        "倒錘子線 (Inverted Hammer)": "Inverted Hammer",
        "射擊之星 (Shooting Star)": "Shooting Star",
        "墓碑十字星 (Gravestone Doji)": "Gravestone Doji",
        "看漲吞沒 (Bullish Engulfing)": "Bullish Engulfing",
        "看跌吞沒 (Bearish Engulfing)": "Bearish Engulfing",
        "穿刺線 (Piercing Pattern)": "Piercing Pattern",
        "烏雲蓋頂 (Dark Cloud Cover)": "Dark Cloud Cover",
        "鑷子底 (Tweezer Bottom)": "Tweezer Bottom",
        "鑷子頂 (Tweezer Top)": "Tweezer Top",
        "晨星 (Morning Star)": "Morning Star",
        "黃昏星 (Evening Star)": "Evening Star",
        "三白兵 (Three White Soldiers)": "Three White Soldiers",
        "三烏鴉 (Three Black Crows)": "Three Black Crows"
    },
    "日本語": {
        "均線黃金交叉 (5MA / 20MA)": "ゴールデンクロス (5MA / 20MA)",
        "均線死亡交叉 (5MA / 20MA)": "デッドクロス (5MA / 20MA)",
        "中長期黃金交叉 (20MA / 60MA)": "中長期ゴールデンクロス (20MA / 60MA)",
        "中長期死亡交叉 (20MA / 60MA)": "中長期デッドクロス (20MA / 60MA)",
        "十字星": "十字星 (Doji)",
        "錘子線 (Hammer)": "カラカサ (Hammer)",
        "上吊線 (Hanging Man)": "首吊り線 (Hanging Man)",
        "倒錘子線 (Inverted Hammer)": "逆カラカサ (Inverted Hammer)",
        "射擊之星 (Shooting Star)": "流れ星 (Shooting Star)",
        "墓碑十字星 (Gravestone Doji)": "トウバ十字星 (Gravestone Doji)",
        "看漲吞沒 (Bullish Engulfing)": "陽の包み足 (Bullish Engulfing)",
        "看跌吞沒 (Bearish Engulfing)": "陰の包み足 (Bearish Engulfing)",
        "穿刺線 (Piercing Pattern)": "切り込み線 (Piercing Pattern)",
        "烏雲蓋頂 (Dark Cloud Cover)": "かぶせ線 (Dark Cloud Cover)",
        "鑷子底 (Tweezer Bottom)": "毛抜き底 (Tweezer Bottom)",
        "鑷子頂 (Tweezer Top)": "毛抜き天井 (Tweezer Top)",
        "晨星 (Morning Star)": "明けの明星 (Morning Star)",
        "黃昏星 (Evening Star)": "宵の明星 (Evening Star)",
        "三白兵 (Three White Soldiers)": "赤三兵 (Three White Soldiers)",
        "三烏鴉 (Three Black Crows)": "三羽烏 (Three Black Crows)"
    },
    "ไทย": {
        "均線黃金交叉 (5MA / 20MA)": "เส้นค่าเฉลี่ย Golden Cross (5MA / 20MA)",
        "均線死亡交叉 (5MA / 20MA)": "เส้นค่าเฉลี่ย Death Cross (5MA / 20MA)",
        "中長期黃金交叉 (20MA / 60MA)": "Golden Cross ระยะกลาง-ยาว (20MA / 60MA)",
        "中長期死亡交叉 (20MA / 60MA)": "Death Cross ระยะกลาง-ยาว (20MA / 60MA)",
        "十字星": "โดจิ (Doji Star)",
        "錘子線 (Hammer)": "ค้อน (Hammer)",
        "上吊線 (Hanging Man)": "คนแขวนคอ (Hanging Man)",
        "倒錘子線 (Inverted Hammer)": "ค้อนกลับหัว (Inverted Hammer)",
        "射擊之星 (Shooting Star)": "ดาวตก (Shooting Star)",
        "墓碑十字星 (Gravestone Doji)": "โดจิสุสาน (Gravestone Doji)",
        "看漲吞沒 (Bullish Engulfing)": "รูปแบบกลืนกินขาขึ้น (Bullish Engulfing)",
        "看跌吞沒 (Bearish Engulfing)": "รูปแบบกลืนกินขาลง (Bearish Engulfing)",
        "穿刺線 (Piercing Pattern)": "รูปแบบเจาะทะลุ (Piercing Pattern)",
        "烏雲蓋頂 (Dark Cloud Cover)": "เมฆดำปกคลุม (Dark Cloud Cover)",
        "鑷子底 (Tweezer Bottom)": "จุดต่ำสุดแหนบ (Tweezer Bottom)",
        "鑷子頂 (Tweezer Top)": "จุดสูงสุดแหนบ (Tweezer Top)",
        "晨星 (Morning Star)": "ดาวรุ่ง (Morning Star)",
        "黃昏星 (Evening Star)": "ดาวพลบค่ำ (Evening Star)",
        "三白兵 (Three White Soldiers)": "ทหารขาวสามนาย (Three White Soldiers)",
        "三烏鴉 (Three Black Crows)": "อีกาสามตัว (Three Black Crows)"
    },
    "Tiếng Việt": {
        "均線黃金交叉 (5MA / 20MA)": "Giao cắt vàng MA (5MA / 20MA)",
        "均線死亡交叉 (5MA / 20MA)": "Giao cắt tử thần MA (5MA / 20MA)",
        "中長期黃金交叉 (20MA / 60MA)": "Giao cắt vàng trung-dài hạn (20MA / 60MA)",
        "中長期死亡交叉 (20MA / 60MA)": "Giao cắt tử thần trung-dài hạn (20MA / 60MA)",
        "十字星": "Nến Doji (Doji Star)",
        "錘子線 (Hammer)": "Nến Búa (Hammer)",
        "上吊線 (Hanging Man)": "Nến Treo Cổ (Hanging Man)",
        "倒錘子線 (Inverted Hammer)": "Nến Búa Ngược (Inverted Hammer)",
        "射擊之星 (Shooting Star)": "Nến Sao Băng (Shooting Star)",
        "墓碑十字星 (Gravestone Doji)": "Nến Doji Bia Mộ (Gravestone Doji)",
        "看漲吞沒 (Bullish Engulfing)": "Nhấn chìm tăng (Bullish Engulfing)",
        "看跌吞沒 (Bearish Engulfing)": "Nhấn chìm giảm (Bearish Engulfing)",
        "穿刺線 (Piercing Pattern)": "Mô hình xuyên thấu (Piercing Pattern)",
        "烏雲蓋頂 (Dark Cloud Cover)": "Mây đen bao phủ (Dark Cloud Cover)",
        "鑷子底 (Tweezer Bottom)": "Đáy nhíp (Tweezer Bottom)",
        "鑷子頂 (Tweezer Top)": "Đỉnh nhíp (Tweezer Top)",
        "晨星 (Morning Star)": "Sao Mai (Morning Star)",
        "黃昏星 (Evening Star)": "Sao Hôm (Evening Star)",
        "三白兵 (Three White Soldiers)": "Ba chàng lính trắng (Three White Soldiers)",
        "三烏鴉 (Three Black Crows)": "Ba con quạ đen (Three Black Crows)"
    }
}

# --- 側邊欄大腦模型選項翻譯 ---
model_descriptions = {
    "繁體中文": {
        "flash35": "🔥 gemini-3.5-flash (最新世代 - 速度與智慧的最新平衡)",
        "flash25": "🚀 gemini-2.5-flash (極速助手 - 快速對話與簡要新聞)"
    },
    "English": {
        "flash35": "🔥 gemini-3.5-flash (Next Gen - Balance of Speed & Smartness)",
        "flash25": "🚀 gemini-2.5-flash (Fast Assistant - Speedy Chat & Summaries)"
    },
    "日本語": {
        "flash35": "🔥 gemini-3.5-flash (新世代 - 速度と知能の最新バランス)",
        "flash25": "🚀 gemini-2.5-flash (高速助手 - クイック対話・要約用)"
    },
    "ไทย": {
        "flash35": "🔥 gemini-3.5-flash (รุ่นล่าสุด - ความเร็วและความฉลาดที่สมดุล)",
        "flash25": "🚀 gemini-2.5-flash (ผู้ช่วยด่วน - แชทเร็วและสรุปข่าว)"
    },
    "Tiếng Việt": {
        "flash35": "🔥 gemini-3.5-flash (Thế hệ mới - Cân bằng tốc độ & thông minh)",
        "flash25": "🚀 gemini-2.5-flash (Trợ lý siêu tốc - Chat nhanh & tóm tắt tin tức)"
    }
}

# --- 盤中即時行情翻譯字典 ---
REALTIME_DICT = {
    "繁體中文": {
        "clear_cache_btn": "🔄 強制刷新歷史數據",
        "auto_refresh_label": "⏱ 啟動盤中即時行情自動更新",
        "refresh_interval_label": "⏱ 選擇自動更新頻率",
        "interval_10s": "10 秒 (快速)",
        "interval_30s": "30 秒 (標準)",
        "interval_60s": "60 秒 (省流量)",
        "realtime_title": "⚡ 盤中即時行情 (Yahoo)",
        "prev_close": "昨收",
        "near_buy_target": "🔥 已跌破或到達第一批買進價！",
        "near_sell_target": "⚠️ 已突破或到達壓力賣出價！",
        "normal_status": "盤中價格波動中",
        "refresh_success": "歷史數據快取已清除！",
        "edit_title": "🛠️ 編輯個人庫存持股",
        "stock_code_label": "股票代號",
        "stock_name_label": "股票名稱",
        "shares_label": "持有股數",
        "cost_label": "平均買入價 (元)",
        "add_update_btn": "➕ 新增或更新持股",
        "delete_btn": "🗑️ 刪除此代號持股",
        "success_msg": "庫存持股已更新！",
        "delete_success_msg": "已成功刪除該持股！",
        "error_empty_id": "請輸入有效的股票代號！",
        "op_type_label": "🔄 寫入模式",
        "op_accumulate": "加碼累加 (自動計算加權平均成本)",
        "op_overwrite": "直接覆蓋 (取代舊有股數與成本)"
    },
    "English": {
        "clear_cache_btn": "🔄 Force Refresh History",
        "auto_refresh_label": "⏱ Enable Intraday Auto-Refresh",
        "refresh_interval_label": "⏱ Select Auto-Refresh Interval",
        "interval_10s": "10 seconds (Fast)",
        "interval_30s": "30 seconds (Standard)",
        "interval_60s": "60 seconds (Eco)",
        "realtime_title": "⚡ Intraday Real-time Quote (Yahoo)",
        "prev_close": "Prev Close",
        "near_buy_target": "🔥 Price reached buy target!",
        "near_sell_target": "⚠️ Price reached resistance target!",
        "normal_status": "Intraday trading active",
        "refresh_success": "Historical cache cleared!",
        "edit_title": "🛠️ Edit Personal Portfolio Holdings",
        "stock_code_label": "Stock Ticker",
        "stock_name_label": "Stock Name",
        "shares_label": "Shares Owned",
        "cost_label": "Average Cost",
        "add_update_btn": "➕ Add or Update Holding",
        "delete_btn": "🗑️ Delete Ticker",
        "success_msg": "Portfolio updated!",
        "delete_success_msg": "Holding deleted!",
        "error_empty_id": "Please enter a valid stock ticker!",
        "op_type_label": "🔄 Write Mode",
        "op_accumulate": "Accumulate (Auto-calculate weighted avg cost)",
        "op_overwrite": "Overwrite (Directly replace existing data)"
    },
    "日本語": {
        "clear_cache_btn": "🔄 履歴データを強制更新",
        "auto_refresh_label": "⏱ 盤中気配値自動更新を有効化",
        "refresh_interval_label": "⏱ 更新間隔を選択",
        "interval_10s": "10秒 (高速)",
        "interval_30s": "30秒 (標準)",
        "interval_60s": "60秒 (省流量)",
        "realtime_title": "⚡ リアルタイム気配値 (Yahoo)",
        "prev_close": "前日終値",
        "near_buy_target": "🔥 買い参考エリアに到達！",
        "near_sell_target": "⚠️ 売り参考エリアに到達！",
        "normal_status": "日中取引中",
        "refresh_success": "履歴データキャッシュがクリアされました！",
        "edit_title": "🛠️ ポートフォリオの編集",
        "stock_code_label": "銘柄コード",
        "stock_name_label": "銘柄名",
        "shares_label": "保有株数",
        "cost_label": "平均取得単価",
        "add_update_btn": "➕ 追加・更新",
        "delete_btn": "🗑️ 削除",
        "success_msg": "ポートフォリオを更新しました！",
        "delete_success_msg": "保有銘柄を削除しました！",
        "error_empty_id": "有効な銘柄コードを入力してください！",
        "op_type_label": "🔄 書き込みモード",
        "op_accumulate": "買い増し累計 (加重平均コストを自動計算)",
        "op_overwrite": "上書き (既存の株数と単価を直接置換)"
    },
    "ไทย": {
        "clear_cache_btn": "🔄 บังคับรีเฟรชข้อมูลประวัติ",
        "auto_refresh_label": "⏱ เปิดอัปเดતราคาเรียลไทม์",
        "refresh_interval_label": "⏱ เลือกช่วงเวลาการอัปเดต",
        "interval_10s": "10 วินาที (เร็ว)",
        "interval_30s": "30 วินาที (มาตรฐาน)",
        "interval_60s": "60 วินาที (ประหยัด)",
        "realtime_title": "⚡ ราคาเรียลไทม์ (Yahoo)",
        "prev_close": "ปิดวันก่อน",
        "near_buy_target": "🔥 ราคาถึงเป้าหมายการซื้อแล้ว!",
        "near_sell_target": "⚠️ ราคาถึงแนวต้านแล้ว!",
        "normal_status": "กำลังซื้อขายระหว่างวัน",
        "refresh_success": "ล้างแคชข้อมูลประวัติแล้ว!",
        "edit_title": "🛠️ แก้ไขพอร์ตการลงทุนส่วนตัว",
        "stock_code_label": "รหัสหุ้น",
        "stock_name_label": "ชื่อหุ้น",
        "shares_label": "จำนวนหุ้นที่ถือ",
        "cost_label": "ราคาซื้อเฉลี่ย",
        "add_update_btn": "➕ เพิ่มหรืออัปเดตหุ้น",
        "delete_btn": "🗑️ ลบหุ้นนี้",
        "success_msg": "อัปเดตพอร์ตสำเร็จ!",
        "delete_success_msg": "ลบหุ้นสำเร็จ!",
        "error_empty_id": "กรุณากรอกรหัสหุ้นที่ถูกต้อง!",
        "op_type_label": "🔄 โหมดการบันทึก",
        "op_accumulate": "ซื้อเพิ่มสะสม (คำนวณราคาเฉลี่ยถ่วงน้ำหนักอัตโนมัติ)",
        "op_overwrite": "เขียนทับ (แทนที่จำนวนหุ้นและราคาซื้อเดิม)"
    },
    "Tiếng Việt": {
        "clear_cache_btn": "🔄 Buộc làm mới dữ liệu lịch sử",
        "auto_refresh_label": "⏱ Bật tự động cập nhật giá",
        "refresh_interval_label": "⏱ Chọn khoảng thời gian cập nhật",
        "interval_10s": "10 giây (Nhanh)",
        "interval_30s": "30 giây (Chuẩn)",
        "interval_60s": "60 giây (Tiết kiệm)",
        "realtime_title": "⚡ Giá trực tuyến (Yahoo)",
        "prev_close": "Đóng cửa trước",
        "near_buy_target": "🔥 Giá đã đạt mức hỗ trợ mua!",
        "near_sell_target": "⚠️ Giá đã đạt mức kháng cự bán!",
        "normal_status": "Đang giao dịch trực tuyến",
        "refresh_success": "Đã xóa bộ nhớ đệm lịch sử!",
        "edit_title": "🛠️ Chỉnh sửa danh mục đầu tư cá nhân",
        "stock_code_label": "Mã cổ phiếu",
        "stock_name_label": "Tên cổ phiếu",
        "shares_label": "Số lượng sở hữu",
        "cost_label": "Giá mua trung bình",
        "add_update_btn": "➕ Thêm hoặc cập nhật",
        "delete_btn": "🗑️ Xóa mã cổ phiếu này",
        "success_msg": "Danh mục đầu tư đã được cập nhật!",
        "delete_success_msg": "Đã xóa mã cổ phiếu!",
        "error_empty_id": "Vui lòng nhập mã cổ phiếu hợp lệ!",
        "op_type_label": "🔄 Chế độ ghi",
        "op_accumulate": "Tích lũy mua thêm (Tự động tính giá trung bình có trọng số)",
        "op_overwrite": "Ghi đè (Thay thế trực tiếp số lượng và giá vốn cũ)"
    }
}

# --- 側邊欄常用股票選項翻譯 ---
stock_descriptions = {
    "繁體中文": {
        "00878": "00878 (國泰永續高股息)",
        "0050": "0050 (元大台灣50)",
        "3049": "3049 (精金)",
        "6282": "6282 (康舒)",
        "2330": "2330 (台積電)",
        "2454": "2454 (聯發科)"
    },
    "English": {
        "00878": "00878 (Cathay ESG Dividend ETF)",
        "0050": "0050 (Yuanta Taiwan 50 ETF)",
        "3049": "3049 (Hannstar Touch)",
        "6282": "6282 (AcBel Polytech)",
        "2330": "2330 (TSMC)",
        "2454": "2454 (MediaTek)"
    },
    "日本語": {
        "00878": "00878 (国泰サステナ高配当ETF)",
        "0050": "0050 (元大台湾50 ETF)",
        "3049": "3049 (HannStar Touch)",
        "6282": "6282 (AcBel 電源)",
        "2330": "2330 (TSMC / 積体電路)",
        "2454": "2454 (MediaTek / 聯發科)"
    },
    "ไทย": {
        "00878": "00878 (Cathay ESG High Dividend ETF)",
        "0050": "0050 (Yuanta Taiwan 50 ETF)",
        "3049": "3049 (Hannstar Touch)",
        "6282": "6282 (AcBel Polytech)",
        "2330": "2330 (TSMC)",
        "2454": "2454 (MediaTek)"
    },
    "Tiếng Việt": {
        "00878": "00878 (ETF Cathay ESG Cổ tức Cao)",
        "0050": "0050 (ETF Yuanta Taiwan 50)",
        "3049": "3049 (Hannstar Touch)",
        "6282": "6282 (AcBel Polytech)",
        "2330": "2330 (TSMC / Bán dẫn Đài Loan)",
        "2454": "2454 (MediaTek)"
    }
}

# --- 頁面基本配置 ---
st.set_page_config(
    page_title="專屬 AI 股市理財專員",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 📱 裝置偵測：判斷是否為手機（積木化，只影響佈局邏輯）---
import streamlit.components.v1 as _components
_components.html("""
<script>
(function() {
    // 偵測螢幕寬度，決定是否為手機
    var isMobile = window.innerWidth <= 768;
    // 透過 query string 傳給 Streamlit
    var url = new URL(window.location.href);
    var current = url.searchParams.get('_mobile');
    var target  = isMobile ? '1' : '0';
    if (current !== target) {
        url.searchParams.set('_mobile', target);
        window.history.replaceState({}, '', url.toString());
    }
    // 同時在 localStorage 存一份（備援）
    localStorage.setItem('ag_is_mobile', target);
})();
</script>
""", height=0)

# 讀取裝置類型（從 query params）
_qp = st.query_params
IS_MOBILE = _qp.get("_mobile", "0") == "1"



# --- 載入 CSS 樣式系統 (高階深色質感設計) ---
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Noto+Sans+TC:wght@300;400;700&display=swap" rel="stylesheet">
    <style>
        /* 強制設定全網頁與 Streamlit 所有視圖容器為深質感暗色調 */
        html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"], .stApp, .stAppHeader, [class*="css"] {
            font-family: 'Outfit', 'Noto Sans TC', sans-serif !important;
            background-color: #0A0E17 !important;
            color: #E2E8F0 !important;
        }
        
        /* 側邊欄背景與邊框 */
        [data-testid="stSidebar"], [data-testid="stSidebarCollapseButton"] {
            background-color: #0F172A !important;
            border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
        }
        
        /* 標題漸層文字 */
        .gradient-text {
            background: linear-gradient(135deg, #10B981, #FBBF24);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2.8rem;
            font-weight: 800;
            letter-spacing: -1px;
            margin-bottom: 5px;
        }
        
        .sub-header {
            font-size: 1.2rem;
            color: #94A3B8;
            margin-bottom: 30px;
            font-weight: 300;
        }
        
        /* 卡片設計 */
        .glass-card {
            background: rgba(15, 23, 42, 0.65);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            margin-bottom: 20px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .glass-card:hover {
            transform: translateY(-2px);
            border-color: rgba(16, 185, 129, 0.25);
            box-shadow: 0 12px 40px 0 rgba(16, 185, 129, 0.15);
        }
        
        /* 指標卡片 */
        .metric-title {
            font-size: 0.85rem;
            color: #94A3B8;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
        }
        
        .metric-value {
            font-size: 1.8rem;
            font-weight: 800;
            margin: 5px 0px;
            color: #F8FAFC;
        }
        
        .metric-delta-up {
            color: #EF4444; /* 台灣股市：紅色上漲 */
            font-size: 0.9rem;
            font-weight: 600;
        }
        
        .metric-delta-down {
            color: #10B981; /* 台灣股市：綠色下跌 */
            font-size: 0.9rem;
            font-weight: 600;
        }
        
        /* 形態標籤 */
        .tag-bullish {
            background-color: rgba(239, 68, 68, 0.15);
            color: #EF4444;
            border: 1px solid rgba(239, 68, 68, 0.3);
            border-radius: 6px;
            padding: 4px 10px;
            font-size: 0.8rem;
            font-weight: bold;
            display: inline-block;
            margin-right: 5px;
        }
        
        .tag-bearish {
            background-color: rgba(16, 185, 129, 0.15);
            color: #10B981;
            border: 1px solid rgba(16, 185, 129, 0.3);
            border-radius: 6px;
            padding: 4px 10px;
            font-size: 0.8rem;
            font-weight: bold;
            display: inline-block;
            margin-right: 5px;
        }
        
        .tag-neutral {
            background-color: rgba(148, 163, 184, 0.15);
            color: #94A3B8;
            border: 1px solid rgba(148, 163, 184, 0.3);
            border-radius: 6px;
            padding: 4px 10px;
            font-size: 0.8rem;
            font-weight: bold;
            display: inline-block;
            margin-right: 5px;
        }
        
        /* 自訂 Tabs 樣式 */
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
            background-color: transparent;
        }
        
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: rgba(30, 41, 59, 0.4);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            color: #94A3B8;
            padding: 0px 20px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #10B981, #FBBF24) !important;
            color: #0F172A !important;
            border: none !important;
            box-shadow: 0 4px 15px rgba(16, 185, 129, 0.25);
            font-weight: 800 !important;
        }
        
        /* 側邊欄配置 */
        .css-1542mo4 {
            background-color: #0F172A;
        }

        /* 投資理財專業表格設計 */
        table {
            width: 100% !important;
            border-collapse: separate !important;
            border-spacing: 0 !important;
            margin: 15px 0 !important;
            border-radius: 12px !important;
            overflow: hidden !important;
            border: 1px solid rgba(255, 255, 255, 0.05) !important;
        }
        th {
            background-color: #1E293B !important;
            color: #94A3B8 !important;
            font-weight: 700 !important;
            text-transform: uppercase !important;
            font-size: 0.8rem !important;
            letter-spacing: 0.5px !important;
            padding: 12px 16px !important;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
        }
        td {
            padding: 14px 16px !important;
            color: #F8FAFC !important;
            font-size: 0.9rem !important;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
            background-color: rgba(15, 23, 42, 0.35) !important;
        }
        tr:last-child td {
            border-bottom: none !important;
        }
        tr:hover td {
            background-color: rgba(16, 185, 129, 0.05) !important;
        }

        /* 按鈕設計 */
        div.stButton > button:first-child {
            background: linear-gradient(135deg, #10B981, #059669) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 8px 20px !important;
            font-weight: 600 !important;
            transition: all 0.2s ease !important;
            box-shadow: 0 4px 6px rgba(16, 185, 129, 0.15) !important;
        }
        div.stButton > button:first-child:hover {
            transform: translateY(-1px) !important;
            box-shadow: 0 6px 12px rgba(16, 185, 129, 0.25) !important;
        }

        /* ══ 📱 手機響應式 Mobile Responsive ══ */
        @media (max-width: 768px) {
            html, body { font-size: 14px !important; }
            .gradient-text { font-size: 1.6rem !important; letter-spacing: -0.5px !important; }
            .sub-header { font-size: 0.9rem !important; margin-bottom: 12px !important; }
            [data-testid="stMainBlockContainer"],
            .main .block-container {
                padding-bottom: 72px !important;
                padding-left: 12px !important;
                padding-right: 12px !important;
            }
            [data-testid="stSidebar"] { max-width: 85vw !important; }
            [data-testid="column"] {
                width: 100% !important;
                flex: 1 1 100% !important;
                min-width: 100% !important;
            }
            [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; gap: 8px !important; }
            .stTabs [data-baseweb="tab-list"] {
                position: fixed !important;
                bottom: 0 !important;
                left: 0 !important;
                right: 0 !important;
                z-index: 9999 !important;
                background: #0F172A !important;
                border-top: 1px solid rgba(255,255,255,0.08) !important;
                display: flex !important;
                justify-content: space-around !important;
                align-items: stretch !important;
                padding: 4px 0 env(safe-area-inset-bottom, 4px) !important;
                height: 60px !important;
                gap: 0 !important;
                margin: 0 !important;
                border-radius: 0 !important;
                box-shadow: 0 -4px 20px rgba(0,0,0,0.5) !important;
                overflow-x: auto !important;
                -webkit-overflow-scrolling: touch !important;
            }
            .stTabs [data-baseweb="tab"] {
                flex: 0 0 auto !important;
                min-width: 60px !important;
                max-width: 85px !important;
                height: 52px !important;
                padding: 4px !important;
                border-radius: 0 !important;
                border: none !important;
                background: transparent !important;
                font-size: 0.58rem !important;
                font-weight: 600 !important;
                color: #64748B !important;
                display: flex !important;
                flex-direction: column !important;
                align-items: center !important;
                justify-content: center !important;
                white-space: nowrap !important;
                transition: color 0.2s ease !important;
            }
            .stTabs [aria-selected="true"] {
                background: transparent !important;
                color: #10B981 !important;
                border-bottom: 2px solid #10B981 !important;
                box-shadow: none !important;
                font-weight: 800 !important;
            }
            .glass-card { padding: 12px 14px !important; margin-bottom: 8px !important; border-radius: 12px !important; }
            .metric-value { font-size: 1.35rem !important; }
            .metric-title { font-size: 0.7rem !important; }
            div.stButton > button:first-child { min-height: 48px !important; font-size: 0.95rem !important; padding: 12px 16px !important; }
            .stTextInput input, .stNumberInput input { font-size: 1rem !important; min-height: 44px !important; }
            table { display: block !important; overflow-x: auto !important; -webkit-overflow-scrolling: touch !important; font-size: 0.78rem !important; }
            th, td { padding: 8px 10px !important; font-size: 0.78rem !important; white-space: nowrap !important; }
            .desktop-only { display: none !important; }
        }
        @media (max-width: 390px) {
            .stTabs [data-baseweb="tab"] { font-size: 0.5rem !important; min-width: 50px !important; }
            .gradient-text { font-size: 1.3rem !important; }
            .metric-value { font-size: 1.1rem !important; }
        }
    </style>
""", unsafe_allow_html=True)

# --- 資料快取 ---
@st.cache_data(ttl=900)  # 15 分鐘更新一次
def get_cached_stock_signals(stock_id: str):
    return evaluate_stock_signals(stock_id)

@st.cache_data(ttl=900)
def get_stock_last_price(stock_id: str) -> float:
    df = fetch_stock_data(stock_id, days=10)
    if not df.empty:
        return float(df.iloc[-1]['close'])
    return 0.0

# --- 盤中即時行情卡片繪製與 Fragment 宣告（v2.3 升級：TWSE 即時 + 時間戳）---
def draw_realtime_card(stock_id: str, price_targets: dict, selected_lang: str, auto_refresh: bool):
    from core.twse_realtime import get_market_status
    rt = fetch_realtime_price(stock_id)
    if not rt.get("success"):
        st.warning(f"無法取得即時報價: {rt.get('error')}")
        return

    price      = rt["price"]
    change     = rt["change"]
    change_pct = rt["change_percent"]
    symbol     = rt.get("symbol", f"{stock_id}.TW")
    update_time = rt.get("update_time", "--:--:--")
    source      = rt.get("source", "UNKNOWN")
    is_intraday = rt.get("is_intraday", False)

    # 顏色
    if change > 0:
        color, sign = "#EF4444", "+"
    elif change < 0:
        color, sign = "#10B981", ""
    else:
        color, sign = "#94A3B8", ""

    # 資料來源徽章
    if source == "TWSE_REALTIME" and is_intraday:
        source_badge = f'<span style="background:rgba(16,185,129,0.15); color:#10B981; border:1px solid rgba(16,185,129,0.3); border-radius:12px; padding:2px 8px; font-size:0.68rem; font-weight:700;">⚡ 證交所即時</span>'
        time_label   = f'更新 {update_time}'
    elif source == "TWSE_REALTIME":
        source_badge = f'<span style="background:rgba(148,163,184,0.1); color:#94A3B8; border:1px solid rgba(148,163,184,0.2); border-radius:12px; padding:2px 8px; font-size:0.68rem; font-weight:700;">🔒 收盤後</span>'
        time_label   = f'昨收 {rt.get("prev_close",""):.2f}'
    else:
        source_badge = f'<span style="background:rgba(245,158,11,0.1); color:#F59E0B; border:1px solid rgba(245,158,11,0.2); border-radius:12px; padding:2px 8px; font-size:0.68rem; font-weight:700;">⚠ 備用來源</span>'
        time_label   = f'約 {update_time}'

    # 買賣警示
    buy_ideal  = price_targets.get("buy_ideal")
    sell_ideal = price_targets.get("sell_ideal")
    status_alert = ""
    if buy_ideal and price <= buy_ideal:
        status_alert = f'<div style="background:rgba(239,68,68,0.1); color:#EF4444; border:1px solid #EF444433; padding:8px 12px; border-radius:6px; font-size:0.82rem; font-weight:600; text-align:center; margin-top:10px;">{REALTIME_DICT[selected_lang]["near_buy_target"]}</div>'
    elif sell_ideal and price >= sell_ideal:
        status_alert = f'<div style="background:rgba(245,158,11,0.1); color:#F59E0B; border:1px solid #F59E0B33; padding:8px 12px; border-radius:6px; font-size:0.82rem; font-weight:600; text-align:center; margin-top:10px;">{REALTIME_DICT[selected_lang]["near_sell_target"]}</div>'

    buy_desc  = f"{buy_ideal} 元"  if buy_ideal  else "--"
    sell_desc = f"{sell_ideal} 元" if sell_ideal else "--"

    # 五檔掛單（TWSE 才有）— div+flex 避開 Streamlit table 過濾
    asks = rt.get("asks", [])
    bids = rt.get("bids", [])
    order_book_html = ""
    if asks and bids:
        def _ob_row(price_val, qty_val, clr):
            return (
                f'<div style="display:flex;justify-content:space-between;padding:2px 0;">'
                f'<span style="color:{clr};font-size:0.72rem;font-family:monospace;">{price_val:.2f}</span>'
                f'<span style="color:#64748B;font-size:0.72rem;">{qty_val} 張</span></div>'
            )
        ask_html = "".join(_ob_row(p, q, "#10B981") for p, q in reversed(asks[:3]))
        bid_html = "".join(_ob_row(p, q, "#EF4444") for p, q in bids[:3])
        order_book_html = (
            '<div style="margin-top:10px;background:rgba(0,0,0,0.25);border-radius:8px;padding:8px 12px;">'
            '<div style="display:flex;gap:12px;">'
            '<div style="flex:1;">'
            '<div style="font-size:0.65rem;color:#64748B;font-weight:600;margin-bottom:4px;text-align:center;">賣出掛單</div>'
            + ask_html +
            '</div>'
            '<div style="width:1px;background:rgba(255,255,255,0.08);"></div>'
            '<div style="flex:1;">'
            '<div style="font-size:0.65rem;color:#64748B;font-weight:600;margin-bottom:4px;text-align:center;">買進掛單</div>'
            + bid_html +
            '</div>'
            '</div>'
            '</div>'
        )

    st.markdown(f"""<div class="glass-card" style="padding:16px 20px; margin-bottom:16px; background: linear-gradient(135deg, rgba(20,25,50,0.8) 0%, rgba(10,12,30,0.9) 100%); border-left: 4px solid {color};">
<div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:10px;">
<div>
<div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">
  <span style="font-size:0.78rem; color:#94A3B8; font-weight:600;">{REALTIME_DICT[selected_lang]['realtime_title']} - {stock_id}</span>
  {source_badge}
  <span style="font-size:0.65rem; color:#475569;">{time_label}</span>
</div>
<div style="display:flex; align-items:baseline; gap:12px;">
<span style="font-size:2.0rem; font-weight:800; color:#F8FAFC; font-family: monospace; line-height:1;">{price:,.2f}</span>
<span style="font-size:1.1rem; font-weight:700; color:{color}; font-family: monospace;">{sign}{change:+.2f} ({sign}{change_pct:+.2f}%)</span>
</div>
</div>
<div style="display:flex; gap:15px; text-align:right;">
<div>
<div style="font-size:0.72rem; color:#64748B;">{REALTIME_DICT[selected_lang]['prev_close']}</div>
<div style="font-size:0.95rem; font-weight:600; color:#CBD5E1; font-family: monospace;">{rt['prev_close']:,.2f}</div>
</div>
<div>
<div style="font-size:0.72rem; color:#64748B;">支撐位 (買進參考)</div>
<div style="font-size:0.95rem; font-weight:600; color:#10B981; font-family: monospace;">{buy_desc}</div>
</div>
<div>
<div style="font-size:0.72rem; color:#64748B;">壓力位 (賣出參考)</div>
<div style="font-size:0.95rem; font-weight:600; color:#EF4444; font-family: monospace;">{sell_desc}</div>
</div>
</div>
</div>
{order_book_html}
{status_alert}
</div>""", unsafe_allow_html=True)

    if not auto_refresh:
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("🔄 刷新即時報價", key="btn_manual_refresh_quote", use_container_width=True):
                st.rerun()

@st.fragment(run_every=5)
def render_realtime_quote_5s(stock_id: str, price_targets: dict, selected_lang: str):
    """極速模式：每 5 秒刷新（TWSE 盤中最準確）"""
    draw_realtime_card(stock_id, price_targets, selected_lang, auto_refresh=True)

@st.fragment(run_every=10)
def render_realtime_quote_10s(stock_id: str, price_targets: dict, selected_lang: str):
    draw_realtime_card(stock_id, price_targets, selected_lang, auto_refresh=True)

@st.fragment(run_every=30)
def render_realtime_quote_30s(stock_id: str, price_targets: dict, selected_lang: str):
    draw_realtime_card(stock_id, price_targets, selected_lang, auto_refresh=True)

@st.fragment(run_every=60)
def render_realtime_quote_60s(stock_id: str, price_targets: dict, selected_lang: str):
    draw_realtime_card(stock_id, price_targets, selected_lang, auto_refresh=True)

@st.fragment()
def render_realtime_quote_manual(stock_id: str, price_targets: dict, selected_lang: str):
    draw_realtime_card(stock_id, price_targets, selected_lang, auto_refresh=False)


# --- 側邊欄設定區 ---
with st.sidebar:
    # 選擇語言
    selected_lang = st.selectbox(
        "🌐 Language / 語言 / 言語 / ภาษา / Ngôn ngữ",
        ["繁體中文", "English", "日本語", "ไทย", "Tiếng Việt"],
        index=0
    )

    st.markdown(f"### {LANG_DICT[selected_lang]['settings_title']}")
    
    # API 金鑰
    default_api_key = config.GEMINI_API_KEY
    api_key_input = st.text_input(
        LANG_DICT[selected_lang]["api_key_label"],
        value=default_api_key,
        type="password",
        help=LANG_DICT[selected_lang]["api_key_help"]
    )
    if api_key_input:
        config.GEMINI_API_KEY = api_key_input
        
    st.markdown(f"### {LANG_DICT[selected_lang]['choose_brain']}")
    model_options = {
        model_descriptions[selected_lang]["flash35"]: "gemini-3.5-flash",
        model_descriptions[selected_lang]["flash25"]: "gemini-2.5-flash"
    }
    selected_model_label = st.selectbox(
        LANG_DICT[selected_lang]["model_label"],
        list(model_options.keys()),
        help=LANG_DICT[selected_lang]["model_help"]
    )
    selected_model_name = model_options[selected_model_label]
        
    st.markdown("---")
    # 快取與即時更新控制
    if st.button(REALTIME_DICT[selected_lang]["clear_cache_btn"], use_container_width=True):
        st.cache_data.clear()
        st.toast(REALTIME_DICT[selected_lang]["refresh_success"], icon="✅")
        
    auto_refresh = st.toggle(
        REALTIME_DICT[selected_lang]["auto_refresh_label"],
        value=True
    )
    refresh_interval = 30
    if auto_refresh:
        interval_options = {
            "⚡ 極速 5 秒 (盤中推薦)": 5,
            REALTIME_DICT[selected_lang]["interval_10s"]: 10,
            REALTIME_DICT[selected_lang]["interval_30s"]: 30,
            REALTIME_DICT[selected_lang]["interval_60s"]: 60
        }
        selected_interval_label = st.selectbox(
            REALTIME_DICT[selected_lang]["refresh_interval_label"],
            list(interval_options.keys()),
            index=1
        )
        refresh_interval = interval_options[selected_interval_label]
    
    st.markdown("---")
    
    # 股票選擇
    st.markdown(f"### {LANG_DICT[selected_lang]['search_title']}")
    stock_options = {stock_descriptions[selected_lang][k]: k for k in stock_descriptions[selected_lang]}
    
    selected_option = st.selectbox(LANG_DICT[selected_lang]["select_common"], list(stock_options.keys()))
    stock_id_input = st.text_input(LANG_DICT[selected_lang]["manual_input"], value=stock_options[selected_option])
    
    st.markdown("---")
    st.markdown(LANG_DICT[selected_lang]["sidebar_warning"])
    st.markdown(f"<br><br><div style='text-align: center; color: #64748B; font-size: 0.8rem;'>{LANG_DICT[selected_lang]['powered_by']}</div>", unsafe_allow_html=True)

# --- 主標題 ---
st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 15px; margin-top: 10px;">
        <span style="font-size: 2.8rem; line-height: 1;">📈</span>
        <span class="gradient-text" style="margin-bottom: 0px; line-height: 1.2;">{LANG_DICT[selected_lang]['main_title'].replace('📈 ', '').replace('📈', '')}</span>
    </div>
""", unsafe_allow_html=True)
st.markdown(f"<div class='sub-header'>{LANG_DICT[selected_lang]['sub_header']}</div>", unsafe_allow_html=True)

# --- 📱 手機版：頂部股票搜尋欄（電腦版側邊欄已有，手機版在此顯示）---
if IS_MOBILE:
    st.markdown("""<div style='background:rgba(15,23,42,0.9); border:1px solid rgba(255,255,255,0.06);
    border-radius:12px; padding:10px 14px; margin-bottom:14px;
    backdrop-filter:blur(12px);'>
    <div style='font-size:0.72rem; color:#64748B; font-weight:600; margin-bottom:6px;'>
    📱 當前分析標的</div>""", unsafe_allow_html=True)
    _mobile_col1, _mobile_col2 = st.columns([3, 1])
    with _mobile_col1:
        _mobile_ticker = st.text_input(
            "股票代號", value=stock_id,
            key="mobile_quick_ticker",
            label_visibility="collapsed",
            placeholder="輸入股票代號，例：0050 / AAPL"
        )
    with _mobile_col2:
        if st.button("🔍", key="mobile_search_btn", use_container_width=True):
            if _mobile_ticker.strip():
                # 更新側邊欄的 stock_id（透過 session state）
                st.session_state["mobile_override_ticker"] = _mobile_ticker.strip()
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)



# 偵測輸入的股票代號
stock_id = stock_id_input.strip()

# 手機版：若有快速搜尋覆蓋，使用覆蓋值
if "mobile_override_ticker" in st.session_state and st.session_state["mobile_override_ticker"]:
    stock_id = st.session_state["mobile_override_ticker"]


if not stock_id:
    st.warning(LANG_DICT[selected_lang]["input_warning"])
    st.stop()

# 載入該股的所有訊號與指標
with st.spinner(LANG_DICT[selected_lang]["spinner_analyzing"].format(stock_id=stock_id)):
    analysis = get_cached_stock_signals(stock_id)

if "error" in analysis:
    st.error(analysis["error"])
    st.stop()

df = analysis["df"]
metrics = analysis["metrics"]
signals = analysis["signals"]
recommendation = analysis.get("recommendation", None)
price_targets = analysis.get("price_targets", {})
institutional = analysis.get("institutional", {"available": False})
inst_analysis  = analysis.get("inst_analysis",  {"available": False})
stock_type     = analysis.get("stock_type",     {})   # 股票類型自動判定結果
# ── 將 stock_id 注入 price_targets（供記憶系統標記用）───────────────────
price_targets["stock_id"] = stock_id

# ── 注入即時報價到 price_targets（AI 永遠知道最新價格）───────────────
try:
    from core.realtime_provider import fetch_realtime_price as _fetch_rt
    _rt_now = _fetch_rt(stock_id)
    if _rt_now.get("success"):
        price_targets["realtime_price"]    = _rt_now["price"]
        price_targets["realtime_change"]   = _rt_now.get("change", 0)
        price_targets["realtime_pct"]      = _rt_now.get("change_percent", 0)
        price_targets["realtime_time"]     = _rt_now.get("update_time", "--")
        price_targets["realtime_source"]   = _rt_now.get("source", "")
        price_targets["realtime_intraday"] = _rt_now.get("is_intraday", False)
except Exception:
    pass  # 即時報價失敗不影響主要分析流程


currency = LANG_DICT[selected_lang]["currency"]

# --- 頁面 Tabs 配置 ---
tab_market, tab_us_market, tab_futures, tab_portfolio, tab_chat, tab_news, tab_screener, tab_lessons = st.tabs([
    LANG_DICT[selected_lang]["tab_market"],
    LANG_DICT[selected_lang]["tab_us_market"],
    LANG_DICT[selected_lang]["tab_futures"],
    LANG_DICT[selected_lang]["tab_portfolio"],
    LANG_DICT[selected_lang]["tab_chat"],
    LANG_DICT[selected_lang]["tab_news"],
    LANG_DICT[selected_lang]["tab_screener"],
    LANG_DICT[selected_lang]["tab_lessons"]
])

# ==============================================================================
# TAB 1: 📊 即時看盤與型態偵測
# ==============================================================================
with tab_market:
    # ── 盤中即時行情 ──────────────────────────────────────────
    if auto_refresh:
        if refresh_interval == 5:
            render_realtime_quote_5s(stock_id_input, price_targets, selected_lang)
        elif refresh_interval == 10:
            render_realtime_quote_10s(stock_id_input, price_targets, selected_lang)
        elif refresh_interval == 60:
            render_realtime_quote_60s(stock_id_input, price_targets, selected_lang)
        else:
            render_realtime_quote_30s(stock_id_input, price_targets, selected_lang)
    else:
        render_realtime_quote_manual(stock_id_input, price_targets, selected_lang)

    # ── 方案 A：股票類型標籤 ────────────────────────────────────
    if stock_type and stock_type.get("primary_type"):
        pt = stock_type["primary_type"]
        pc = stock_type.get("primary_confidence", 0)
        st_s = stock_type.get("secondary_type")
        sc   = stock_type.get("secondary_confidence", 0)
        reasons_short = "・".join(stock_type.get("reason", [])[:3])

        TYPE_COLORS = {
            "AI": "#6366F1", "低軌衛星": "#0EA5E9", "軍工": "#EF4444",
            "機器人": "#8B5CF6", "電動車": "#10B981", "ETF": "#F59E0B",
            "權值股": "#F97316", "半導體": "#EC4899", "生技醫療": "#14B8A6",
            "金融": "#84CC16", "Unknown": "#64748B",
        }
        p_color = TYPE_COLORS.get(pt, "#64748B")
        s_color = TYPE_COLORS.get(st_s, "#64748B") if st_s else None

        secondary_badge = ""
        if st_s and sc >= 70:
            secondary_badge = f'<span style="background:{s_color}22; color:{s_color}; border:1px solid {s_color}55; padding:4px 12px; border-radius:20px; font-size:0.78rem; font-weight:600;">副&nbsp;{st_s}&nbsp;{sc}%</span>'

        st.markdown(f'<div class="glass-card" style="padding:12px 18px; margin-bottom:12px; display:flex; align-items:center; flex-wrap:wrap; gap:10px; border-left:3px solid {p_color};"><span style="font-size:0.78rem; color:#94A3B8;">🏷 股票類型</span><span style="background:{p_color}; color:#fff; padding:4px 14px; border-radius:20px; font-size:0.85rem; font-weight:700;">主&nbsp;{pt}&nbsp;{pc}%</span>{secondary_badge}<span style="font-size:0.75rem; color:#64748B; flex:1; min-width:160px;">{reasons_short}</span></div>', unsafe_allow_html=True)

    # 頂部即時指標
    col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
    
    # 計算今日漲跌
    price_today = df.iloc[-1]['close']
    price_yesterday = df.iloc[-2]['close']
    change = price_today - price_yesterday
    pct_change = (change / price_yesterday) * 100
    
    delta_str = f"{'+' if change > 0 else ''}{change:.2f} {currency} ({pct_change:+.2f}%)"
    delta_class = "metric-delta-up" if change >= 0 else "metric-delta-down"
    
    with col_m1:
        st.markdown(f"""
            <div class="glass-card" style="padding: 15px;">
                <div class="metric-title">{LANG_DICT[selected_lang]["close_price"]}</div>
                <div class="metric-value">{price_today:.2f} {currency}</div>
                <div class="{delta_class}">{delta_str}</div>
            </div>
        """, unsafe_allow_html=True)
        
    with col_m2:
        rsi_status = LANG_DICT[selected_lang]["rsi_overbought"] if metrics['rsi'] > 70 else LANG_DICT[selected_lang]["rsi_oversold"] if metrics['rsi'] < 30 else LANG_DICT[selected_lang]["rsi_neutral"]
        st.markdown(f"""
            <div class="glass-card" style="padding: 15px;">
                <div class="metric-title">{LANG_DICT[selected_lang]["rsi_label"]}</div>
                <div class="metric-value">{metrics['rsi']:.1f}</div>
                <div style="font-size: 0.85rem; color: #94A3B8;">{rsi_status}</div>
            </div>
        """, unsafe_allow_html=True)
        
    with col_m3:
        kd_status = LANG_DICT[selected_lang]["kd_bullish"] if metrics['k'] > metrics['d'] else LANG_DICT[selected_lang]["kd_bearish"]
        st.markdown(f"""
            <div class="glass-card" style="padding: 15px;">
                <div class="metric-title">{LANG_DICT[selected_lang]["kd_label"]}</div>
                <div class="metric-value">K {metrics['k']:.1f} / D {metrics['d']:.1f}</div>
                <div style="font-size: 0.85rem; color: #94A3B8;">{kd_status}</div>
            </div>
        """, unsafe_allow_html=True)
        
    with col_m4:
        vol_status = LANG_DICT[selected_lang]["volatility_high"] if metrics['volatility'] > 0.25 else LANG_DICT[selected_lang]["volatility_low"] if metrics['volatility'] < 0.12 else LANG_DICT[selected_lang]["volatility_stable"]
        st.markdown(f"""
            <div class="glass-card" style="padding: 15px;">
                <div class="metric-title">{LANG_DICT[selected_lang]["volatility_label"]}</div>
                <div class="metric-value">{metrics['volatility']*100:.1f} %</div>
                <div style="font-size: 0.85rem; color: #94A3B8;">{vol_status}</div>
            </div>
        """, unsafe_allow_html=True)
        
    with col_m5:
        st.markdown(f"""
            <div class="glass-card" style="padding: 15px;">
                <div class="metric-title">{LANG_DICT[selected_lang]["yield_label"]}</div>
                <div class="metric-value">{metrics['est_yield']:.2f} %</div>
                <div style="font-size: 0.85rem; color: #94A3B8;">{LANG_DICT[selected_lang]["yield_sub"]}</div>
            </div>
        """, unsafe_allow_html=True)

    # 中間 K線圖 與 形態偵測器
    col_chart, col_signals = st.columns([2, 1])
    
    with col_chart:
        st.markdown(f"### {LANG_DICT[selected_lang]['chart_title']}")
        
        # 繪製 Plotly 蠟燭圖
        fig = go.Figure()
        
        # K線本體
        # 台灣股市色系：上漲用紅色，下跌用綠色
        fig.add_trace(go.Candlestick(
            x=df['date'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            increasing_line_color='#EF4444', # 上漲為紅
            decreasing_line_color='#10B981', # 下跌為綠
            increasing_fillcolor='rgba(239, 68, 68, 0.4)',
            decreasing_fillcolor='rgba(16, 185, 129, 0.4)',
            name=LANG_DICT[selected_lang]["k_line"]
        ))
        
        # 均線軌跡
        fig.add_trace(go.Scatter(x=df['date'], y=df['ma5'], line=dict(color='#38BDF8', width=1.5), name=LANG_DICT[selected_lang]["ma5_label"]))
        fig.add_trace(go.Scatter(x=df['date'], y=df['ma20'], line=dict(color='#F43F5E', width=1.5), name=LANG_DICT[selected_lang]["ma20_label"]))
        fig.add_trace(go.Scatter(x=df['date'], y=df['ma60'], line=dict(color='#F59E0B', width=1.5), name=LANG_DICT[selected_lang]["ma60_label"]))
        
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0B0F19",
            plot_bgcolor="rgba(30, 41, 59, 0.3)",
            xaxis_rangeslider_visible=False,
            height=450,
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_signals:
        st.markdown(f"### {LANG_DICT[selected_lang]['patterns_alarm']}")
        
        # 風險評估卡片
        risk_color = "#10B981" if metrics['risk_score'] < 35 else "#F59E0B" if metrics['risk_score'] < 65 else "#EF4444"
        risk_level_localized = LANG_DICT[selected_lang]["risk_level_names"].get(metrics['risk_level'], metrics['risk_level'])
        st.markdown(f"""
            <div class="glass-card" style="border-left: 5px solid {risk_color}; padding: 18px; margin-bottom: 20px;">
                <span class="metric-title">{LANG_DICT[selected_lang]["risk_level_title"]}</span>
                <div style="font-size: 1.8rem; font-weight: 800; color: {risk_color}; margin: 5px 0px;">
                    {risk_level_localized}
                </div>
                <div style="font-size: 0.85rem; color: #94A3B8;">
                    {LANG_DICT[selected_lang]["risk_score_desc"].format(score=metrics['risk_score'])}
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # AI 交易操盤建議卡片
        if recommendation:
            rec_action = recommendation["action"]
            rec_reason = recommendation["reason"].get(selected_lang, recommendation["reason"]["繁體中文"])
            rec_color = "#10B981" if rec_action == "buy" else "#94A3B8" if rec_action == "watch" else "#F59E0B" if rec_action == "sell_partial" else "#EF4444"
            rec_action_title = LANG_DICT[selected_lang]["trade_rec_actions"].get(rec_action, rec_action)
            
            st.markdown(f"""
                <div class="glass-card" style="border-left: 5px solid {rec_color}; padding: 18px; margin-bottom: 12px; background: rgba(30, 41, 59, 0.6);">
                    <span class="metric-title">{LANG_DICT[selected_lang]["trade_rec_title"]}</span>
                    <div style="font-size: 1.6rem; font-weight: 800; color: {rec_color}; margin: 5px 0px;">
                        {rec_action_title}
                    </div>
                    <div style="font-size: 0.88rem; color: #E2E8F0; line-height: 1.5; margin-top: 8px;">
                        <b>{LANG_DICT[selected_lang]["trade_rec_reason_label"]}</b> {rec_reason}
                    </div>
                </div>
            """, unsafe_allow_html=True)

        # 📌 買進/賣出參考價位卡片
        if price_targets:
            pt = price_targets
            lang_buy  = {"繁體中文":"買進參考","English":"Buy Reference","日本語":"買い参考","ไทย":"ราคาซื้ออ้างอิง","Tiếng Việt":"Giá mua tham khảo"}
            lang_sell = {"繁體中文":"賣出目標","English":"Sell Target","日本語":"売り目標","ไทย":"เป้าขาย","Tiếng Việt":"Mục tiêu bán"}
            lang_stop = {"繁體中文":"止損參考","English":"Stop Loss","日本語":"損切り","ไทย":"จุดตัดขาดทุน","Tiếng Việt":"Cắt lỗ"}
            lang_sup  = {"繁體中文":"主要支撐","English":"Support","日本語":"支持","ไทย":"แนวรับ","Tiếng Việt":"Hỗ trợ"}
            lang_res  = {"繁體中文":"主要壓力","English":"Resistance","日本語":"抵抗","ไทย":"แนวต้าน","Tiếng Việt":"Kháng cự"}
            lang_pt_title = {"繁體中文":"📌 買賣參考價位","English":"📌 Price Reference Levels","日本語":"📌 売買参考価格","ไทย":"📌 ราคาอ้างอิงสำหรับซื้อขาย","Tiếng Việt":"📌 Mức giá tham chiếu"}
            lang_batch1= {"繁體中文":"第一批買進","English":"Entry 1","日本語":"第1買い","ไทย":"ซื้อล็อตแรก","Tiếng Việt":"Vào lệnh 1"}
            lang_batch2= {"繁體中文":"逢低第二批","English":"Entry 2 (Dip)","日本語":"押し目第2買い","ไทย":"ซื้อล็อตสอง(ย่อ)","Tiếng Việt":"Gom thêm"}
            lang_tp1  = {"繁體中文":"第一目標","English":"Target 1","日本語":"第1目標","ไทย":"เป้าที่ 1","Tiếng Việt":"Mục tiêu 1"}
            lang_tp2  = {"繁體中文":"第二目標","English":"Target 2","日本語":"第2目標","ไทย":"เป้าที่ 2","Tiếng Việt":"Mục tiêu 2"}

            st.markdown(f"""
                <div class="glass-card" style="border-left: 5px solid #38BDF8; padding: 14px 18px; margin-bottom: 12px; background: rgba(15,25,50,0.7);">
                    <div style="font-size:0.85rem; font-weight:700; color:#38BDF8; margin-bottom:8px;">{lang_pt_title.get(selected_lang,'📌 買賣參考價位')}</div>
                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px; font-size:0.82rem;">
                        <div style="color:#94A3B8;">{lang_buy.get(selected_lang,'買進參考')}</div>
                        <div style="color:#94A3B8;">{lang_sell.get(selected_lang,'賣出目標')}</div>
                        <div>
                            <span style="color:#10B981; font-weight:700;">▶ {lang_batch1.get(selected_lang,'第一批')}: </span>
                            <span style="color:#F8FAFC; font-weight:600;">{pt['buy_ideal']} {currency}</span><br>
                            <span style="color:#6EE7B7; font-weight:600;">▶ {lang_batch2.get(selected_lang,'逢低')}: </span>
                            <span style="color:#F8FAFC; font-weight:600;">{pt['buy_dip']} {currency}</span><br>
                            <span style="color:#EF4444; font-weight:600;">✕ {lang_stop.get(selected_lang,'止損')}: </span>
                            <span style="color:#FCA5A5; font-weight:600;">{pt['stop_loss']} {currency}</span>
                        </div>
                        <div>
                            <span style="color:#F59E0B; font-weight:700;">◀ {lang_tp1.get(selected_lang,'第一目標')}: </span>
                            <span style="color:#F8FAFC; font-weight:600;">{pt['take_profit_1']} {currency}</span><br>
                            <span style="color:#FCD34D; font-weight:600;">◀ {lang_tp2.get(selected_lang,'第二目標')}: </span>
                            <span style="color:#F8FAFC; font-weight:600;">{pt['take_profit_2']} {currency}</span><br>
                            <span style="color:#CBD5E1; font-size:0.78rem;">{lang_sup.get(selected_lang,'支撐')}: {pt['primary_support']} | {lang_res.get(selected_lang,'壓力')}: {pt['primary_resistance']}</span>
                        </div>
                    </div>
                    <div style="font-size:0.72rem; color:#64748B; margin-top:6px;">⚠️ {'以上價位為技術面計算之參考，非絕對保證，請自行判斷風險' if selected_lang=='繁體中文' else 'These are technical reference prices only. Always apply your own judgment.'}</div>
                </div>
            """, unsafe_allow_html=True)

        # ── 方案 I：類型專屬操作策略補充 ──────────────────────
        if stock_type and stock_type.get("primary_type") and stock_type["primary_type"] != "Unknown":
            _st_pt   = stock_type["primary_type"]
            _st_tips = stock_type.get("operation_tips", [])
            _st_sec  = stock_type.get("secondary_type")
            _st_s_tips = stock_type.get("secondary_tips", [])

            TYPE_COLORS_I = {
                "AI": "#6366F1", "低軌衛星": "#0EA5E9", "軍工": "#EF4444",
                "機器人": "#8B5CF6", "電動車": "#10B981", "ETF": "#F59E0B",
                "權值股": "#F97316", "半導體": "#EC4899", "生技醫療": "#14B8A6",
                "金融": "#84CC16",
            }
            _ic = TYPE_COLORS_I.get(_st_pt, "#6366F1")
            tips_html = "".join([
                f'<div style="padding:3px 0; font-size:0.82rem; color:#E2E8F0;">📍 {t}</div>'
                for t in _st_tips
            ])
            sec_html = ""
            if _st_sec and _st_s_tips:
                _sc = TYPE_COLORS_I.get(_st_sec, "#94A3B8")
                sec_tips_html = "".join([
                    f'<div style="padding:2px 0; font-size:0.8rem; color:#CBD5E1;">　📎 {t}</div>'
                    for t in _st_s_tips[:2]
                ])
                sec_html = f"""
                    <div style="margin-top:8px; padding-top:8px; border-top:1px solid rgba(255,255,255,0.06);">
                        <span style="font-size:0.75rem; color:{_sc};">副類型 {_st_sec} 補充</span>
                        {sec_tips_html}
                    </div>"""

            st.markdown(f"""
                <div class="glass-card" style="padding:14px 18px; margin-bottom:10px;
                             border-left:3px solid {_ic}; background:rgba(15,20,40,0.6);">
                    <div style="font-size:0.8rem; color:{_ic}; font-weight:700; margin-bottom:6px;">
                        🎯 {_st_pt} 類型操作策略
                    </div>
                    {tips_html}
                    {sec_html}
                </div>
            """, unsafe_allow_html=True)

        # ── 方案 D：類型專屬風險提示 ───────────────────────────
        if stock_type and stock_type.get("primary_type") and stock_type["primary_type"] != "Unknown":
            _st_risks = stock_type.get("risks", [])
            if _st_risks:
                risks_html = "".join([
                    f'<div style="padding:3px 0; font-size:0.8rem; color:#FCA5A5;">⚠ {r}</div>'
                    for r in _st_risks
                ])
                st.markdown(f"""
                    <div class="glass-card" style="padding:12px 18px; margin-bottom:10px;
                                 border-left:3px solid #EF4444; background:rgba(239,68,68,0.06);">
                        <div style="font-size:0.8rem; color:#EF4444; font-weight:700; margin-bottom:5px;">
                            🔔 {stock_type["primary_type"]} 類型特有風險
                        </div>
                        {risks_html}
                    </div>
                """, unsafe_allow_html=True)

        # 偵測形態輸出
        st.markdown(f"<div style='font-size: 0.9rem; font-weight: bold; color: #94A3B8; margin-bottom: 8px;'>{LANG_DICT[selected_lang]['tech_patterns']}</div>", unsafe_allow_html=True)
        
        if signals:
            for s in signals:
                tag_class = "tag-bullish" if s["type"] == "bullish" else "tag-bearish" if s["type"] == "bearish" else "tag-neutral"
                action_badge = LANG_DICT[selected_lang]["advisor_badge"].get(s["type"], s["type"])
                
                # 對訊號名稱進行翻譯
                translated_name = s["name"]
                if selected_lang in SIGNAL_TRANSLATION and s["name"] in SIGNAL_TRANSLATION[selected_lang]:
                    translated_name = SIGNAL_TRANSLATION[selected_lang][s["name"]]
                
                st.markdown(f"""
                    <div style="background-color: rgba(30, 41, 59, 0.4); border: 1px solid rgba(255, 255, 255, 0.05); padding: 12px; border-radius: 8px; margin-bottom: 10px;">
                        <span class="{tag_class}">{action_badge} ({LANG_DICT[selected_lang]["strength_label"]} {s['strength']})</span>
                        <strong style="color: #F8FAFC; font-size: 0.95rem; display: block; margin-top: 5px;">{translated_name}</strong>
                        <span style="color: #94A3B8; font-size: 0.85rem; display: block; margin-top: 3px;">{s['desc']}</span>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info(LANG_DICT[selected_lang]["no_patterns"])

    # 三大法人資料面板 (全寬顯示在K線與訊號下方)
    if institutional.get("available"):
        inst = institutional
        total_net = inst["total_net"]
        foreign_net = inst["foreign_net"]
        trust_net = inst["investment_trust_net"]
        dealer_net = inst["dealer_net"]
        
        inst_title = {"繁體中文":"🏦 三大法人近期買賣超", "English":"🏦 Institutional Investors (30D Net)", "日本語":"🏦 機関投資家 売買動向", "ไทย":"🏦 นักลงทุนสถาบัน", "Tiếng Việt":"🏦 Nhà đầu tư tổ chức"}
        lbl_foreign = {"繁體中文":"外資/外國機構", "English":"Foreign Investors", "日本語":"外国人", "ไทย":"ต่างชาติ", "Tiếng Việt":"Khối ngoại"}
        lbl_trust   = {"繁體中文":"投信", "English":"Investment Trust", "日本語":"投資信託", "ไทย":"กองทุนรวม", "Tiếng Việt":"Quỹ đầu tư"}
        lbl_dealer  = {"繁體中文":"自營商", "English":"Dealers", "日本語":"自己売買", "ไทย":"โบรกเกอร์ตัวเอง", "Tiếng Việt":"Tự doanh"}
        lbl_total   = {"繁體中文":"三大法人合計", "English":"Total Net", "日本語":"合計", "ไทย":"รวม", "Tiếng Việt":"Tổng cộng"}
        lbl_consec  = {"繁體中文":f"外資連續{'買超' if inst['consecutive_buy'] > 0 else '賣超'} {max(inst['consecutive_buy'], inst['consecutive_sell'])} 日", "English":f"Foreign {'Buying' if inst['consecutive_buy'] > 0 else 'Selling'} {max(inst['consecutive_buy'], inst['consecutive_sell'])} days", "日本語":f"外国人{'買い' if inst['consecutive_buy'] > 0 else '売り'}継続 {max(inst['consecutive_buy'], inst['consecutive_sell'])} 日", "ไทย":f"ต่างชาติ{'ซื้อ' if inst['consecutive_buy'] > 0 else 'ขาย'}ต่อเนื่อง {max(inst['consecutive_buy'], inst['consecutive_sell'])} วัน", "Tiếng Việt":f"Ngoại {'mua' if inst['consecutive_buy'] > 0 else 'bán'} liên tục {max(inst['consecutive_buy'], inst['consecutive_sell'])} ngày"}
        
        def fmt_net(v):
            color = "#10B981" if v > 0 else "#EF4444" if v < 0 else "#94A3B8"
            sign = "+" if v > 0 else ""
            return f'<span style="color:{color}; font-weight:700;">{sign}{v:,}</span>'
        
        consec_color = "#10B981" if inst["consecutive_buy"] > 0 else "#EF4444"
        total_color = "#10B981" if total_net > 0 else "#EF4444" if total_net < 0 else "#94A3B8"
        
        st.markdown(f"""
            <div class="glass-card" style="padding: 16px 20px; margin-top: 16px; border-top: 2px solid rgba(56,189,248,0.3);">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                    <span style="font-size:0.95rem; font-weight:700; color:#38BDF8;">{inst_title.get(selected_lang,'🏦 三大法人近期買賣超')}</span>
                    <span style="font-size:0.8rem; padding:3px 8px; border-radius:12px; background:rgba({('16,185,129' if inst['consecutive_buy'] > 0 else '239,68,68')},0.15); color:{consec_color}; font-weight:600;">{lbl_consec.get(selected_lang,'')}</span>
                </div>
                <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:10px; text-align:center;">
                    <div style="background:rgba(30,41,59,0.5); border-radius:8px; padding:10px;">
                        <div style="font-size:0.75rem; color:#94A3B8; margin-bottom:4px;">{lbl_foreign.get(selected_lang,'外資')}</div>
                        <div style="font-size:1rem;">{fmt_net(foreign_net)}</div>
                    </div>
                    <div style="background:rgba(30,41,59,0.5); border-radius:8px; padding:10px;">
                        <div style="font-size:0.75rem; color:#94A3B8; margin-bottom:4px;">{lbl_trust.get(selected_lang,'投信')}</div>
                        <div style="font-size:1rem;">{fmt_net(trust_net)}</div>
                    </div>
                    <div style="background:rgba(30,41,59,0.5); border-radius:8px; padding:10px;">
                        <div style="font-size:0.75rem; color:#94A3B8; margin-bottom:4px;">{lbl_dealer.get(selected_lang,'自營商')}</div>
                        <div style="font-size:1rem;">{fmt_net(dealer_net)}</div>
                    </div>
                    <div style="background:rgba(30,41,59,0.4); border-radius:8px; padding:10px; border:1px solid rgba(56,189,248,0.2);">
                        <div style="font-size:0.75rem; color:#38BDF8; margin-bottom:4px;">{lbl_total.get(selected_lang,'合計')}</div>
                        <div style="font-size:1rem;">{fmt_net(total_net)}</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # 顯示最近幾天的法人明細表
        if inst.get("recent_days"):
            recent_data = inst["recent_days"][:7]
            rows_html = ""
            for r in recent_data:
                d_total = r['foreign'] + r['trust'] + r['dealer']
                rows_html += f"""<tr>
                    <td style="color:#94A3B8; font-size:0.78rem; padding:4px 8px;">{r['date']}</td>
                    <td style="text-align:right; padding:4px 8px; font-size:0.82rem; color:{'#10B981' if r['foreign']>0 else '#EF4444' if r['foreign']<0 else '#64748B'}; font-weight:600;">{'+'if r['foreign']>0 else ''}{r['foreign']:,}</td>
                    <td style="text-align:right; padding:4px 8px; font-size:0.82rem; color:{'#10B981' if r['trust']>0 else '#EF4444' if r['trust']<0 else '#64748B'}; font-weight:600;">{'+'if r['trust']>0 else ''}{r['trust']:,}</td>
                    <td style="text-align:right; padding:4px 8px; font-size:0.82rem; color:{'#10B981' if r['dealer']>0 else '#EF4444' if r['dealer']<0 else '#64748B'}; font-weight:600;">{'+'if r['dealer']>0 else ''}{r['dealer']:,}</td>
                    <td style="text-align:right; padding:4px 8px; font-size:0.82rem; color:{'#10B981' if d_total>0 else '#EF4444' if d_total<0 else '#64748B'}; font-weight:700;">{'+'if d_total>0 else ''}{d_total:,}</td>
                </tr>"""
            st.markdown(f"""
                <div style="margin-top:10px; overflow-x:auto;">
                    <table style="width:100%; border-collapse:collapse; font-size:0.8rem;">
                        <thead>
                            <tr style="border-bottom:1px solid rgba(255,255,255,0.1);">
                                <th style="padding:4px 8px; text-align:left; color:#64748B;">日期</th>
                                <th style="padding:4px 8px; text-align:right; color:#64748B;">{lbl_foreign.get(selected_lang,'外資')}</th>
                                <th style="padding:4px 8px; text-align:right; color:#64748B;">{lbl_trust.get(selected_lang,'投信')}</th>
                                <th style="padding:4px 8px; text-align:right; color:#64748B;">{lbl_dealer.get(selected_lang,'自營商')}</th>
                                <th style="padding:4px 8px; text-align:right; color:#64748B;">{lbl_total.get(selected_lang,'合計')}</th>
                            </tr>
                        </thead>
                        <tbody>{rows_html}</tbody>
                    </table>
                </div>
            """, unsafe_allow_html=True)
    elif not institutional.get("available"):
        st.caption("ℹ️ 三大法人資料暫時無法取得（可能為 ETF 或非台股個股）" if selected_lang == "繁體中文" else "ℹ️ Institutional investor data not available for this ticker.")

    # ── 三大法人五大規則分析面板 ──────────────────────────────────
    if inst_analysis.get("available"):
        ia = inst_analysis
        score     = ia["score"]
        s_type    = ia["score_type"]
        s_label   = ia["score_label"]
        score_color = "#10B981" if s_type == "bullish" else "#EF4444" if s_type == "bearish" else "#94A3B8"

        # 評分顏色對應進度條
        bar_pct = min(score, 100)
        bar_color = score_color

        # 單日分級顏色
        def type_color(t):
            return "#10B981" if t == "bullish" else "#EF4444" if t == "bearish" else "#94A3B8"

        st.markdown(f"""
            <div class="glass-card" style="padding:18px 22px; margin-top:14px; border-top:2px solid {score_color}33;">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:12px; margin-bottom:14px;">
                    <!-- 評分大圖示 -->
                    <div style="text-align:center; min-width:110px;">
                        <div style="font-size:2.4rem; font-weight:900; color:{score_color}; line-height:1;">{score}</div>
                        <div style="font-size:0.72rem; color:#64748B; margin-top:2px;">/ 100 分</div>
                        <div style="font-size:0.85rem; font-weight:700; color:{score_color}; margin-top:4px; padding:3px 10px; border-radius:10px; background:{score_color}22;">{s_label}</div>
                    </div>
                    <!-- 進度條 + 判定摘要 -->
                    <div style="flex:1; min-width:200px;">
                        <div style="background:rgba(255,255,255,0.08); border-radius:6px; height:8px; margin-bottom:10px; overflow:hidden;">
                            <div style="width:{bar_pct}%; height:100%; background:{bar_color}; border-radius:6px; transition:width 0.6s;"></div>
                        </div>
                        <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px; font-size:0.8rem;">
                            <div>
                                <span style="color:#64748B;">📅 單日強度</span><br>
                                <span style="color:{type_color(ia['day_type'])}; font-weight:700;">{ia['day_label']}</span>
                                <span style="color:#64748B; font-size:0.72rem;">（{ia['d0_total_wan']:+,.0f} 萬元）</span>
                            </div>
                            <div>
                                <span style="color:#64748B;">📊 外資連續</span><br>
                                <span style="color:{type_color(ia['consec_type'])}; font-weight:700;">{ia['consec_label']}</span>
                            </div>
                            <div>
                                <span style="color:#64748B;">🏦 法人結構</span><br>
                                <span style="color:{type_color(ia['struct_type'])}; font-weight:700;">{ia['struct_label']}</span>
                            </div>
                            <div>
                                <span style="color:#64748B;">📈 投信連續</span><br>
                                <span style="color:{type_color(ia.get('trust_consec_type','neutral'))}; font-weight:700;">{ia['trust_consec_label']}</span>
                            </div>
                        </div>
                    </div>
                </div>
        """, unsafe_allow_html=True)

        # 評分明細
        if ia["score_details"]:
            details_html = " ".join([
                f'<span style="background:rgba(16,185,129,0.15); color:#6EE7B7; padding:2px 7px; border-radius:8px; font-size:0.75rem; margin:2px; display:inline-block;">{d[0]} <b>+{d[1]}</b></span>'
                for d in ia["score_details"]
            ])
            st.markdown(f"""
                <div style="padding:0 0 8px 0; border-top:1px solid rgba(255,255,255,0.06); padding-top:10px; margin-top:4px;">
                    <span style="font-size:0.75rem; color:#64748B; display:block; margin-bottom:5px;">📌 評分明細</span>
                    {details_html}
                </div>
            """, unsafe_allow_html=True)

        # 警訊
        if ia["warnings"]:
            for w in ia["warnings"]:
                is_danger = "🔴" in w or "⚠️" in w
                w_bg = "rgba(239,68,68,0.12)" if is_danger else "rgba(245,158,11,0.12)"
                w_border = "#EF4444" if is_danger else "#F59E0B"
                st.markdown(f"""
                    <div style="margin-top:6px; padding:8px 12px; border-left:3px solid {w_border}; background:{w_bg}; border-radius:4px; font-size:0.83rem; color:#F8FAFC;">
                        {w}
                    </div>
                """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)


# ==============================================================================
# 📈 深度技術指標面板 + 基本面 + 融資融券（注入台股看盤分頁）
# ==============================================================================
with tab_market:
    # ── A: MACD / 布林 / 成交量深度面板 ─────────────────────────
    try:
        from core.indicator_extractor import extract_technical_indicators
        _ind = extract_technical_indicators(df)
        if _ind.get("available"):
            st.markdown("---")
            st.markdown("#### 📊 深度技術指標")

            _ic1, _ic2, _ic3 = st.columns(3)

            # MACD
            _macd_hist = _ind.get("macd_hist", 0)
            _macd_color = "#EF4444" if _macd_hist >= 0 else "#10B981"
            _macd_sign  = "▲" if _macd_hist >= 0 else "▼"
            with _ic1:
                st.markdown(f"""<div class="glass-card" style="padding:14px; border-left:4px solid {_macd_color};">
<div style="font-size:0.72rem; color:#94A3B8; font-weight:600;">MACD</div>
<div style="font-size:0.95rem; font-weight:700; color:{_macd_color}; margin:4px 0;">DIF {_ind['macd']:+.3f}</div>
<div style="font-size:0.78rem; color:#94A3B8;">DEA {_ind['macd_signal']:+.3f} | 柱 {_macd_sign}{abs(_macd_hist):.3f}</div>
<div style="font-size:0.72rem; color:#64748B; margin-top:4px;">{_ind['macd_label'][:18]}</div>
</div>""", unsafe_allow_html=True)

            # 布林通道
            _boll_pos = _ind.get("boll_label", "")
            _boll_color = "#EF4444" if "上軌" in _boll_pos else "#10B981" if "下軌" in _boll_pos else "#F59E0B"
            with _ic2:
                st.markdown(f"""<div class="glass-card" style="padding:14px; border-left:4px solid {_boll_color};">
<div style="font-size:0.72rem; color:#94A3B8; font-weight:600;">布林通道 (20,2σ)</div>
<div style="font-size:0.95rem; font-weight:700; color:#F8FAFC; margin:4px 0;">上軌 {_ind['boll_upper']}</div>
<div style="font-size:0.78rem; color:#94A3B8;">中軌 {_ind['boll_mid']} | 下軌 {_ind['boll_lower']}</div>
<div style="font-size:0.72rem; color:{_boll_color}; margin-top:4px;">{_ind.get('boll_label','')[:20]}</div>
</div>""", unsafe_allow_html=True)

            # 成交量
            _vol_label = _ind.get("vol_label", "")
            _vol_color = "#F59E0B" if "爆量" in _vol_label else "#6366F1" if "放量" in _vol_label else "#10B981" if "縮量" in _vol_label else "#94A3B8"
            with _ic3:
                _vol_disp = f"{_ind['volume']:,}" if _ind.get('volume') else "--"
                _vma_disp = f"{_ind['vol_ma20']:,}" if _ind.get('vol_ma20') else "--"
                st.markdown(f"""<div class="glass-card" style="padding:14px; border-left:4px solid {_vol_color};">
<div style="font-size:0.72rem; color:#94A3B8; font-weight:600;">成交量 vs 均量</div>
<div style="font-size:0.95rem; font-weight:700; color:#F8FAFC; margin:4px 0;">{_vol_disp} 張</div>
<div style="font-size:0.78rem; color:#94A3B8;">20日均量 {_vma_disp} 張</div>
<div style="font-size:0.72rem; color:{_vol_color}; margin-top:4px;">{_vol_label[:20]}</div>
</div>""", unsafe_allow_html=True)

            # 均線排列
            _ma_color = "#EF4444" if "多頭" in _ind.get("ma_trend","") else "#10B981" if "空頭" in _ind.get("ma_trend","") else "#F59E0B"
            st.markdown(f"""<div style="margin-top:8px; padding:8px 14px; background:rgba(30,41,59,0.5); border-radius:8px; font-size:0.8rem; color:{_ma_color};">
📐 <b>均線排列</b>：{_ind.get('ma_trend','')} &nbsp;｜&nbsp; MA5={_ind.get('ma5','--')} &nbsp; MA20={_ind.get('ma20','--')} &nbsp; MA60={_ind.get('ma60','--')}
</div>""", unsafe_allow_html=True)

    except Exception as _te:
        pass

    # ── B: 基本面快速面板 ─────────────────────────────────────────
    try:
        from core.fundamental_provider import fetch_fundamentals, fetch_monthly_revenue
        _fund = fetch_fundamentals(stock_id)
        if _fund.get("available"):
            st.markdown("---")
            st.markdown("#### 💰 基本面速覽")

            _fc1, _fc2, _fc3, _fc4, _fc5 = st.columns(5)

            def _fund_card(col, title, value, sublabel, color="#F8FAFC"):
                col.markdown(f"""<div class="glass-card" style="padding:12px; text-align:center;">
<div style="font-size:0.68rem; color:#94A3B8;">{title}</div>
<div style="font-size:1.1rem; font-weight:800; color:{color}; margin:4px 0;">{value}</div>
<div style="font-size:0.68rem; color:#64748B;">{sublabel}</div>
</div>""", unsafe_allow_html=True)

            # PE
            pe_val = _fund.get("trailing_pe")
            pe_color = "#EF4444" if pe_val and pe_val > 40 else "#F59E0B" if pe_val and pe_val > 25 else "#10B981"
            _fund_card(_fc1, "本益比 PE", f"{pe_val:.1f}x" if pe_val else "--", _fund.get("pe_status","")[:12], pe_color)

            # ROE
            roe_val = _fund.get("roe_pct")
            roe_color = "#10B981" if roe_val and roe_val >= 15 else "#F59E0B" if roe_val and roe_val >= 8 else "#EF4444"
            _fund_card(_fc2, "ROE 股東報酬率", f"{roe_val:.1f}%" if roe_val else "--", "✅優秀" if roe_val and roe_val >= 15 else "⚠️普通", roe_color)

            # 毛利率
            gm_val = _fund.get("gross_margin_pct")
            gm_color = "#10B981" if gm_val and gm_val >= 40 else "#F59E0B" if gm_val and gm_val >= 20 else "#EF4444"
            _fund_card(_fc3, "毛利率", f"{gm_val:.1f}%" if gm_val else "--", "高護城河" if gm_val and gm_val >= 40 else "正常", gm_color)

            # EPS
            eps_val = _fund.get("trailing_eps")
            feps_val = _fund.get("forward_eps")
            eps_sub  = f"預估EPS {feps_val}" if feps_val else "trailing"
            _fund_card(_fc4, "EPS(元)", f"{eps_val}" if eps_val else "--", eps_sub, "#6366F1")

            # 殖利率
            dy_val = _fund.get("dividend_yield_pct")
            dy_color = "#10B981" if dy_val and dy_val >= 5 else "#94A3B8"
            _fund_card(_fc5, "殖利率", f"{dy_val:.2f}%" if dy_val else "--", "高息股✅" if dy_val and dy_val >= 5 else "一般", dy_color)

            # 52週位置條
            pos_pct = _fund.get("position_52w_pct", 50)
            pos_label = _fund.get("position_52w_label","")
            hi52 = _fund.get("week52_high","--")
            lo52 = _fund.get("week52_low","--")
            pos_color = "#EF4444" if pos_pct > 80 else "#F59E0B" if pos_pct > 50 else "#10B981"
            st.markdown(f"""<div style="margin-top:8px; padding:10px 14px; background:rgba(30,41,59,0.5); border-radius:8px;">
<div style="display:flex; justify-content:space-between; font-size:0.75rem; color:#94A3B8; margin-bottom:5px;">
  <span>52週低點 {lo52}</span><span style="color:{pos_color}; font-weight:700;">📍 目前位置 {pos_pct:.0f}%  {pos_label}</span><span>52週高點 {hi52}</span>
</div>
<div style="background:rgba(255,255,255,0.08); border-radius:6px; height:6px; overflow:hidden;">
  <div style="width:{pos_pct}%; height:100%; background:{pos_color}; border-radius:6px;"></div>
</div>
</div>""", unsafe_allow_html=True)

            # 月營收
            _rev = fetch_monthly_revenue(stock_id)
            if _rev.get("available") and _rev.get("months"):
                rg = _fund.get("revenue_growth_pct")
                rg_color = "#10B981" if rg and rg > 0 else "#EF4444"
                months = _rev.get("months",[])[-3:]
                revs   = [f"{r/1e6:.1f}M" if r >= 1e6 else f"{r/1e3:.0f}K" for r in _rev.get("revenues",[])[-3:]]
                rev_pairs = " → ".join(f"{m[-5:]} {v}" for m, v in zip(months, revs))
                st.markdown(f"""<div style="margin-top:6px; padding:7px 14px; background:rgba(30,41,59,0.4); border-radius:8px; font-size:0.78rem; color:#94A3B8;">
📅 <b>近期月營收</b>：{rev_pairs} &nbsp;｜&nbsp; <span style="color:{rg_color}; font-weight:700;">年增率 {rg:+.1f}%</span>
</div>""", unsafe_allow_html=True)

    except Exception as _fe:
        pass

    # ── C: 融資融券趨勢面板 ─────────────────────────────────────────
    try:
        from core.margin_provider import fetch_margin_data
        _mar = fetch_margin_data(stock_id)
        if _mar.get("available"):
            st.markdown("---")
            st.markdown("#### 🏦 融資融券籌碼")
            _mc1, _mc2, _mc3 = st.columns(3)

            _m5d_chg = _mar.get("margin_change_5d", 0)
            _m5d_color = "#F59E0B" if _m5d_chg > 300 else "#EF4444" if _m5d_chg > 0 else "#10B981"
            _sc = _mar.get("short_change", 0)
            _sc_color = "#EF4444" if _sc > 50 else "#10B981" if _sc < -50 else "#94A3B8"

            _mc1.markdown(f"""<div class="glass-card" style="padding:14px; border-left:4px solid {_m5d_color};">
<div style="font-size:0.72rem; color:#94A3B8;">融資餘額</div>
<div style="font-size:1.1rem; font-weight:800; color:#F8FAFC; margin:4px 0;">{_mar['margin_balance']:,} 張</div>
<div style="font-size:0.75rem; color:{_m5d_color};">5日 {_m5d_chg:+,} 張</div>
</div>""", unsafe_allow_html=True)

            _mc2.markdown(f"""<div class="glass-card" style="padding:14px; border-left:4px solid {_sc_color};">
<div style="font-size:0.72rem; color:#94A3B8;">融券餘額</div>
<div style="font-size:1.1rem; font-weight:800; color:#F8FAFC; margin:4px 0;">{_mar['short_balance']:,} 張</div>
<div style="font-size:0.75rem; color:{_sc_color};">當日 {_sc:+,} 張</div>
</div>""", unsafe_allow_html=True)

            _trend_txt = _mar.get("margin_trend","")
            _trend_color = "#F59E0B" if "增加" in _trend_txt and "大幅" in _trend_txt else "#10B981" if "減少" in _trend_txt else "#94A3B8"
            _mc3.markdown(f"""<div class="glass-card" style="padding:14px; border-left:4px solid {_trend_color};">
<div style="font-size:0.72rem; color:#94A3B8;">融資趨勢解讀</div>
<div style="font-size:0.78rem; color:{_trend_color}; margin-top:8px; line-height:1.4;">{_trend_txt}</div>
</div>""", unsafe_allow_html=True)

    except Exception as _me:
        pass

# ==============================================================================
# 🚨 價格警示檢查（每次頁面重載時自動比對）
# ==============================================================================
try:
    from core.alert_manager import check_alerts, get_all_alerts, add_alert, remove_alert, clear_triggered, get_stats as alert_stats
    # 用持股库存的現價來比對警示
    _current_prices = {}
    try:
        from core.realtime_provider import fetch_realtime_price as _frp
        import json as _json
        _pf_path = config.PORTFOLIO_FILE
        if os.path.exists(_pf_path):
            with open(_pf_path, encoding="utf-8") as _f:
                _pf = _json.load(_f)
            for _sid in list(_pf.keys())[:5]:  # 最多檢查 5 支，避免太慢
                _rt = _frp(_sid)
                if _rt.get("success"):
                    _current_prices[_sid] = _rt["price"]
    except Exception:
        pass

    _triggered = check_alerts(_current_prices) if _current_prices else []
    if _triggered:
        for _t in _triggered:
            _sign = "↑" if _t["condition"] == ">" else "↓"
            st.toast(
                f"🔔 警示觸發！ {_t['stock_id']} {_t['stock_name']} "
                f"{'>漲到' if _t['condition'] == '>' else '<跌到'} "
                f"{_t['price']} 元，現價: {_t.get('trigger_price', '--')} 元",
                icon="🔔"
            )
except Exception:
    pass

# ==============================================================================
# 🗺️ 台股板塊熱圖 (Sector Heatmap)
# ==============================================================================
with tab_market:
    st.markdown("---")
    st.markdown("### 🗺️ 台股板塊熱圖 · Sector Heatmap")

    try:
        from core.sector_heatmap import fetch_sector_indices
        import plotly.graph_objects as go

        _sectors = fetch_sector_indices()
        if _sectors:
            # 生成熱圖色块（用 Plotly Treemap/Bar）
            _names    = [s["name"] for s in _sectors if s["name"] != "大盤"]
            _changes  = [s["change_pct"] for s in _sectors if s["name"] != "大盤"]
            _closes   = [s["close"] for s in _sectors if s["name"] != "大盤"]
            _labels   = [f"{n}<br>{c:+.2f}%" for n, c in zip(_names, _changes)]

            _colors = []
            for c in _changes:
                if c >= 2:    _colors.append("#b91c1c")
                elif c >= 1:  _colors.append("#dc2626")
                elif c >= 0:  _colors.append("#ef4444")
                elif c >= -1: _colors.append("#16a34a")
                elif c >= -2: _colors.append("#15803d")
                else:         _colors.append("#166534")

            _fig_heat = go.Figure(go.Bar(
                x=_names,
                y=[abs(c) + 0.1 for c in _changes],
                text=_labels,
                textposition="inside",
                marker_color=_colors,
                hovertemplate="<b>%{x}</b><br>分類指數: %{customdata:.2f}<br>漲跌: %{text}<extra></extra>",
                customdata=_closes,
            ))
            _fig_heat.update_layout(
                height=320,
                margin=dict(l=10, r=10, t=10, b=40),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(15,23,42,0.6)",
                font_color="white",
                xaxis=dict(showgrid=False, tickangle=-30, tickfont_size=10),
                yaxis=dict(showgrid=False, showticklabels=False),
                showlegend=False,
            )
            st.plotly_chart(_fig_heat, use_container_width=True, config={"displayModeBar": False})

            # 大盤指數漲跌
            _market = next((s for s in _sectors if s["name"] == "大盤"), None)
            if _market:
                _mc = _market["change_pct"]
                _color_m = "🔴" if _mc > 0 else "🟢"
                st.caption(f"{_color_m} 大盤加權指數: {_market['close']:,.2f}  {_mc:+.2f}%")
        else:
            st.info("目前為非交易時間，類股資料將於盤後更新")

    except Exception as _he:
        st.caption(f"熱圖載入中... ({str(_he)[:50]})")

# ==============================================================================
# 📅 除權息/財報行事曆
# ==============================================================================
with tab_market:
    st.markdown("---")
    st.markdown("### 📅 除權息行事曆（未來 60 天）")
    try:
        from core.calendar_provider import fetch_upcoming_dividends
        from core.profile_manager import get_profile_summary

        _prof      = get_profile_summary()
        _watched   = list(_prof.get("watched_stocks", {}).keys())
        _divs      = fetch_upcoming_dividends(days_ahead=60)

        if _divs:
            # 若有監看股票，先顯示監看股票的除權息，再顯示其他
            _divs_watched = [d for d in _divs if d["stock_id"] in _watched] if _watched else []
            _divs_other   = [d for d in _divs if d["stock_id"] not in _watched][:20]
            _divs_display = _divs_watched + _divs_other

            if _divs_watched:
                st.caption(f"🔖 你的監看股票共有 {len(_divs_watched)} 支即將除權息")

            _cal_cols = st.columns([2, 3, 2, 2, 2, 2])
            _headers  = ["代號", "名稱", "除權息日", "剩天", "現金股利", "類型"]
            for col, h in zip(_cal_cols, _headers):
                col.markdown(f"**{h}**")
            st.markdown('<hr style="margin:4px 0; opacity:.2">', unsafe_allow_html=True)

            for d in _divs_display[:25]:
                c1, c2, c3, c4, c5, c6 = st.columns([2, 3, 2, 2, 2, 2])
                days_left = d["days_left"]
                urgency   = "🔴" if days_left <= 7 else ("🟡" if days_left <= 30 else "🟢")
                is_mine   = d["stock_id"] in _watched
                name_str  = f"⭐ {d['stock_name']}" if is_mine else d["stock_name"]

                c1.write(d["stock_id"])
                c2.write(name_str)
                c3.write(d["ex_date"])
                c4.write(f"{urgency} {days_left}天")
                c5.write(f"{d['cash_div']} 元" if d.get("cash_div") and d["cash_div"] != "0" else "-")
                c6.write(d.get("div_type", "-"))
        else:
            st.info("目前近 60 天內無除權息公告，或資料載入失敗")
    except Exception as _ce:
        st.caption(f"行事曆載入中... ({str(_ce)[:80]})")

# ==============================================================================
# 🔔 價格警示管理面板
# ==============================================================================
with tab_market:
    st.markdown("---")
    with st.expander("🔔 價格警示管理", expanded=False):
        try:
            from core.alert_manager import (
                add_alert, remove_alert, get_all_alerts,
                clear_triggered, get_stats as alert_stats
            )
            _ast = alert_stats()
            st.caption(f"現有警示: {_ast['active']} 個活跳 | {_ast['triggered']} 個已觸發")

            # 新增警示表單
            with st.form("alert_form_main"):
                _af1, _af2, _af3, _af4 = st.columns([2, 2, 1.5, 3])
                with _af1:
                    _alert_sid  = st.text_input("股票代號", value=stock_id, placeholder="e.g. 0050")
                with _af2:
                    _alert_name = st.text_input("名稱(可略)", placeholder="e.g. 元大台灣50")
                with _af3:
                    _alert_cond = st.selectbox("條件", ["↑ 漲到（高於）", "↓ 跌到（低於）"])
                with _af4:
                    _alert_price = st.number_input("目標價格(元)", min_value=0.0, step=0.5, format="%.2f")
                _alert_note  = st.text_input("備註(可略)", placeholder="e.g. 第一批買進價位")
                if st.form_submit_button("➕ 新增警示", use_container_width=True):
                    if _alert_sid and _alert_price > 0:
                        _cond_map = {"↑ 漲到（高於）": ">", "↓ 跌到（低於）": "<"}
                        add_alert(
                            stock_id=_alert_sid.strip(),
                            stock_name=_alert_name.strip() or _alert_sid.strip(),
                            condition=_cond_map[_alert_cond],
                            price=_alert_price,
                            note=_alert_note.strip()
                        )
                        st.toast(f"警示已設定！{_alert_sid} {'>漲到' if '>' in _cond_map[_alert_cond] else '<跌到'} {_alert_price}元", icon="🔔")
                        st.rerun()
                    else:
                        st.warning("請填寫股票代號和目標價格")

            # 現有警示清單
            _alerts = get_all_alerts()
            if _alerts:
                for _al in _alerts:
                    _acol1, _acol2, _acol3, _acol4 = st.columns([2, 3, 3, 1])
                    _acol1.write(_al["stock_id"])
                    _cond_label = f"{'>漲到' if _al['condition'] == '>' else '<跌到'} {_al['price']}元"
                    _acol2.write(_cond_label)
                    _status = "✅ 已觸發" if _al["triggered"] else "⏳ 監控中"
                    _acol3.write(f"{_status} {_al.get('note', '')}")
                    if _acol4.button("🗑️", key=f"del_alert_{_al['id']}"):
                        remove_alert(_al["id"])
                        st.rerun()

                _ccol1, _ccol2 = st.columns(2)
                with _ccol1:
                    if st.button("🧹 清除已觸發", use_container_width=True):
                        clear_triggered()
                        st.rerun()
            else:
                st.info("尚無警示，請上方新增")

        except Exception as _ae:
            st.error(f"警示模組靈: {_ae}")

# ==============================================================================
# TAB 2: 💼 專屬持股追蹤看板
# ==============================================================================
with tab_portfolio:
    st.markdown(f"### {LANG_DICT[selected_lang]['portfolio_title']}")
    
    # 載入庫存 JSON 檔案
    portfolio_file = config.PORTFOLIO_FILE
    if os.path.exists(portfolio_file):
        with open(portfolio_file, "r", encoding="utf-8") as f:
            portfolio = json.load(f)
            
        # 抓取並計算實時價值
        p_rows = []
        total_market_val = 0.0
        total_cost_val = 0.0
        
        for p_id, p_info in portfolio.items():
            current_p = get_stock_last_price(p_id)
            cost = p_info["cost"]
            shares = p_info["shares"]
            
            p_cost = cost * shares
            p_val = current_p * shares
            
            # 計算估計的賣出手續費與證券交易稅 (台股標準，小數點以下捨去)
            sell_fee = int(p_val * 0.001425)
            # 證券交易稅：ETFs 為 0.1%，一般個股為 0.3%
            tax_rate = 0.001 if p_id in ["0050", "0056", "00878", "00919", "00929", "00940"] else 0.003
            sell_tax = int(p_val * tax_rate)
            
            p_val_net = p_val - sell_fee - sell_tax
            p_pnl = p_val_net - p_cost
            p_return = (p_pnl / p_cost) * 100 if p_cost > 0 else 0.0
            
            total_market_val += p_val_net
            total_cost_val += p_cost
            
            col_code = LANG_DICT[selected_lang]["col_code"]
            col_name = LANG_DICT[selected_lang]["col_name"]
            col_shares = LANG_DICT[selected_lang]["col_shares"]
            col_avg_cost = LANG_DICT[selected_lang]["col_avg_cost"]
            col_latest_close = LANG_DICT[selected_lang]["col_latest_close"]
            col_total_cost = LANG_DICT[selected_lang]["col_total_cost"]
            col_current_val = LANG_DICT[selected_lang]["col_current_val"]
            col_pnl = LANG_DICT[selected_lang]["col_pnl"]
            col_return = LANG_DICT[selected_lang]["col_return"]
            
            shares_unit = "股" if selected_lang == "繁體中文" else "株" if selected_lang == "日本語" else "shares" if selected_lang == "English" else "หุ้น" if selected_lang == "ไทย" else "cổ phiếu"
            p_rows.append({
                col_code: p_id,
                col_name: p_info["name"],
                col_shares: f"{shares:,} {shares_unit}",
                col_avg_cost: f"{cost:.3f} {currency}",
                col_latest_close: f"{current_p:.2f} {currency}",
                col_total_cost: f"{p_cost:,.0f} {currency}",
                col_current_val: f"{p_val_net:,.0f} {currency}",
                col_pnl: p_pnl,
                col_return: p_return
            })
            
        total_pnl = total_market_val - total_cost_val
        total_return = (total_pnl / total_cost_val) * 100 if total_cost_val > 0 else 0.0
        
        # 頂部綜合資產彙總
        col_p1, col_p2, col_p3 = st.columns(3)
        
        with col_p1:
            st.markdown(f"""
                <div class="glass-card" style="text-align: center;">
                    <div class="metric-title">{LANG_DICT[selected_lang]["portfolio_value"]}</div>
                    <div class="metric-value" style="font-size: 2.2rem; color: #38BDF8;">{total_market_val:,.0f} {currency}</div>
                    <div style="font-size: 0.85rem; color: #94A3B8;">{LANG_DICT[selected_lang]["portfolio_count"].format(count=len(portfolio))}</div>
                </div>
            """, unsafe_allow_html=True)
            
        pnl_class = "metric-delta-up" if total_pnl >= 0 else "metric-delta-down"
        pnl_sign = "+" if total_pnl >= 0 else ""
        
        with col_p2:
            st.markdown(f"""
                <div class="glass-card" style="text-align: center;">
                    <div class="metric-title">{LANG_DICT[selected_lang]["unrealized_pnl"]}</div>
                    <div class="metric-value {pnl_class}" style="font-size: 2.2rem;">{pnl_sign}{total_pnl:,.0f} {currency}</div>
                    <div style="font-size: 0.85rem; color: #94A3B8;">{LANG_DICT[selected_lang]["tax_deducted"]}</div>
                </div>
            """, unsafe_allow_html=True)
            
        with col_p3:
            st.markdown(f"""
                <div class="glass-card" style="text-align: center;">
                    <div class="metric-title">{LANG_DICT[selected_lang]["total_return"]}</div>
                    <div class="metric-value {pnl_class}" style="font-size: 2.2rem;">{total_return:+.2f} %</div>
                    <div style="font-size: 0.85rem; color: #94A3B8;">{LANG_DICT[selected_lang]["invested_cost"].format(cost=total_cost_val)}</div>
                </div>
            """, unsafe_allow_html=True)
            
        # 顯示庫存清單表格 (自訂精美樣式)
        st.markdown(f"<h4 style='color:#F8FAFC;'>{LANG_DICT[selected_lang]['holdings_detail']}</h4>", unsafe_allow_html=True)
        
        # 轉成 DataFrame 繪製 HTML 表格
        df_portfolio = pd.DataFrame(p_rows)
        
        # 格式化損益與報酬率並上色
        def color_pnl_html(val):
            color = "#EF4444" if val >= 0 else "#10B981"
            sign = "+" if val >= 0 else ""
            return f"<span style='color:{color}; font-weight:bold;'>{sign}{val:,.0f} {currency}</span>"
            
        def color_return_html(val):
            color = "#EF4444" if val >= 0 else "#10B981"
            return f"<span style='color:{color}; font-weight:bold;'>{val:+.2f} %</span>"
            
        df_portfolio[col_pnl] = df_portfolio[col_pnl].apply(color_pnl_html)
        df_portfolio[col_return] = df_portfolio[col_return].apply(color_return_html)
        
        # 輸出 HTML
        st.write(df_portfolio.to_html(escape=False, index=False, justify='center'), unsafe_allow_html=True)
        
    else:
        st.info("尚未建立持股 portfolio.json 檔案。")

    # ── 🛠️ 編輯個人庫存持股 UI ──────────────────────────────────────
    st.markdown("---")
    st.markdown(f"<h4 style='color:#F8FAFC;'>{REALTIME_DICT[selected_lang]['edit_title']}</h4>", unsafe_allow_html=True)
    
    edit_col1, edit_col2, edit_col3, edit_col4 = st.columns(4)
    with edit_col1:
        edit_id = st.text_input(f"{REALTIME_DICT[selected_lang]['stock_code_label']} (e.g. 0050)", key="p_edit_id")
    with edit_col2:
        edit_name = st.text_input(f"{REALTIME_DICT[selected_lang]['stock_name_label']} (e.g. 台積電)", key="p_edit_name")
    with edit_col3:
        edit_shares = st.number_input(REALTIME_DICT[selected_lang]['shares_label'], min_value=1, step=1, value=1000, key="p_edit_shares")
    with edit_col4:
        edit_cost = st.number_input(REALTIME_DICT[selected_lang]['cost_label'], min_value=0.01, step=0.01, value=100.0, key="p_edit_cost")
        
    write_mode = st.radio(
        REALTIME_DICT[selected_lang]["op_type_label"],
        [REALTIME_DICT[selected_lang]["op_accumulate"], REALTIME_DICT[selected_lang]["op_overwrite"]],
        index=0,
        horizontal=True
    )
    
    btn_col1, btn_col2, _ = st.columns([1, 1, 2])
    with btn_col1:
        if st.button(REALTIME_DICT[selected_lang]['add_update_btn'], use_container_width=True, type="primary"):
            if edit_id.strip():
                p_file = config.PORTFOLIO_FILE
                curr_p = {}
                if os.path.exists(p_file):
                    try:
                        with open(p_file, "r", encoding="utf-8") as f:
                            curr_p = json.load(f)
                    except Exception:
                        pass
                
                stock_key = edit_id.strip()
                if stock_key in curr_p and write_mode == REALTIME_DICT[selected_lang]["op_accumulate"]:
                    old_shares = curr_p[stock_key]["shares"]
                    old_cost = curr_p[stock_key]["cost"]
                    new_shares = int(edit_shares)
                    new_cost = float(edit_cost)
                    
                    total_shares = old_shares + new_shares
                    total_cost = (old_shares * old_cost) + (new_shares * new_cost)
                    weighted_avg_cost = total_cost / total_shares if total_shares > 0 else 0.0
                    
                    name_to_use = edit_name.strip() if edit_name.strip() else curr_p[stock_key]["name"]
                    curr_p[stock_key] = {
                        "name": name_to_use,
                        "shares": total_shares,
                        "cost": round(weighted_avg_cost, 4)
                    }
                else:
                    name_to_use = edit_name.strip() if edit_name.strip() else edit_id.strip()
                    curr_p[stock_key] = {
                        "name": name_to_use,
                        "shares": int(edit_shares),
                        "cost": float(edit_cost)
                    }
                
                with open(p_file, "w", encoding="utf-8") as f:
                    json.dump(curr_p, f, indent=4, ensure_ascii=False)
                    
                st.toast(REALTIME_DICT[selected_lang]['success_msg'], icon="✅")
                st.rerun()
            else:
                st.error(REALTIME_DICT[selected_lang]['error_empty_id'])
                
    with btn_col2:
        if st.button(REALTIME_DICT[selected_lang]['delete_btn'], use_container_width=True):
            if edit_id.strip():
                p_file = config.PORTFOLIO_FILE
                curr_p = {}
                if os.path.exists(p_file):
                    try:
                        with open(p_file, "r", encoding="utf-8") as f:
                            curr_p = json.load(f)
                    except Exception:
                        pass
                
                if edit_id.strip() in curr_p:
                    curr_p.pop(edit_id.strip())
                    with open(p_file, "w", encoding="utf-8") as f:
                        json.dump(curr_p, f, indent=4, ensure_ascii=False)
                    st.toast(REALTIME_DICT[selected_lang]['delete_success_msg'], icon="🗑️")
                    st.rerun()
            else:
                st.error(REALTIME_DICT[selected_lang]['error_empty_id'])

# ==============================================================================
# TAB 3: 💬 理財專員對話室
# ==============================================================================
with tab_chat:
    st.markdown(f"### {LANG_DICT[selected_lang]['chat_title']}")
    st.markdown(LANG_DICT[selected_lang]["chat_desc"])
    
    # ── 三層記憶狀態列 ──────────────────────────────────────────────
    try:
        from core.memory_manager  import get_stats as mem_stats, clear_memory
        from core.profile_manager import get_profile_summary
        from core.knowledge_base  import get_stats as kb_stats, add_manual_note
        _mem  = mem_stats()
        _kb   = kb_stats()
        _prof = get_profile_summary()

        with st.expander("🧠 AI 記憶狀態", expanded=False):
            mc1, mc2, mc3 = st.columns(3)
            with mc1:
                st.metric("📝 對話記憶", f"{_mem['total']} 輪",
                          help=f"最新：{_mem.get('newest','--')}")
            with mc2:
                top_watched = list(_prof.get('watched_stocks', {}).keys())[:3]
                st.metric("👤 個人檔案", f"{len(_prof.get('watched_stocks',{}))} 支股票",
                          help=f"最常看：{top_watched}")
            with mc3:
                st.metric("📚 知識庫", f"{_kb['total']} 條",
                          help=f"自動儲存 {_kb['auto_saved']} 條 | 手動 {_kb['manual_added']} 條")

            top_stocks_list = sorted(_prof.get("watched_stocks", {}).items(), key=lambda x: x[1], reverse=True)[:5]
            if top_stocks_list:
                st.caption("常看股票：" + "、".join(f"{s}({n}次)" for s,n in top_stocks_list))
            indicators_list = _prof.get("preferred_indicators", [])
            if indicators_list:
                st.caption("慣用指標：" + "、".join(indicators_list[:6]))

            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("🗑️ 清除對話記憶", key="btn_clear_memory", use_container_width=True):
                    clear_memory()
                    st.toast("對話記憶已清除", icon="🗑️")
            with col_b:
                if st.button("📋 清除本 Session 歷史", key="btn_clear_session", use_container_width=True):
                    st.session_state.chat_history = []
                    st.rerun()

            with st.form("kb_note_form"):
                note_title   = st.text_input("筆記標題", placeholder="例：0050 的波動週期觀察")
                note_content = st.text_area("筆記內容", placeholder="在此寫下你的投資心得或分析...", height=80)
                note_stock   = st.text_input("相關股票代號（可留空）", value=stock_id)
                if st.form_submit_button("📥 存入知識庫", use_container_width=True):
                    if note_title and note_content:
                        add_manual_note(note_title, note_content, stock_id=note_stock)
                        st.toast(f"「{note_title}」已存入知識庫！", icon="📚")
                    else:
                        st.warning("請填寫標題和內容")
    except Exception:
        pass  # 記憶模組不影響主要對話功能

    # 初始化聊天對話歷史
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        
    # 顯示對話歷史
    for msg in st.session_state.chat_history:
        avatar = "🤖" if msg["role"] == "model" else "👨‍💼"
        with st.chat_message(msg["role"], avatar=avatar):
            st.write(msg["text"])
            
    # 對話輸入框
    if user_query := st.chat_input(LANG_DICT[selected_lang]["chat_placeholder"]):
        # 顯示使用者發言
        with st.chat_message("user", avatar="👨‍💼"):
            st.write(user_query)
            
        # 將發言寫入歷史紀錄
        st.session_state.chat_history.append({"role": "user", "text": user_query})
        
        # ── 準備分析數據（技術指標/總經/融資融券/基本面）──
        _ai_indicators  = None
        _ai_macro       = None
        _ai_margin      = None
        _ai_fundamental = None

        _current_stock_id = price_targets.get("stock_id", stock_id) if price_targets else stock_id
        try:
            # 任務1：技術指標精確數值（從已下載的 K 線算）
            from core.pattern_detector import fetch_stock_data
            from core.indicator_extractor import extract_technical_indicators
            _df_for_ai = fetch_stock_data(_current_stock_id, days=120)
            if not _df_for_ai.empty:
                _ai_indicators = extract_technical_indicators(_df_for_ai)
        except Exception:
            pass

        try:
            # 任務2：總體經濟（VIX/SOX/台幣/美股）
            from core.macro_provider import fetch_macro_context
            _ai_macro = fetch_macro_context()
        except Exception:
            pass

        try:
            # 任務3：融資融券
            from core.margin_provider import fetch_margin_data
            _ai_margin = fetch_margin_data(_current_stock_id)
        except Exception:
            pass

        try:
            # 任務4：基本面（EPS/ROE/毛利率/PE）
            from core.fundamental_provider import fetch_fundamentals, fetch_monthly_revenue
            _fund = fetch_fundamentals(_current_stock_id)
            _rev  = fetch_monthly_revenue(_current_stock_id)
            if _fund.get("available"):
                _fund["monthly_revenue"] = _rev
                _ai_fundamental = _fund
        except Exception:
            pass

        # 呼叫理財專員 API
        with st.spinner(LANG_DICT[selected_lang]["chat_spinner"]):
            from core.ai_agent import generate_advisor_response
            response_text = generate_advisor_response(
                st.session_state.chat_history[:-1], 
                user_query, 
                model_name=selected_model_name,
                selected_lang=selected_lang,
                price_targets=price_targets,
                institutional=institutional,
                stock_type=stock_type,
                indicators=_ai_indicators,
                macro=_ai_macro,
                margin=_ai_margin,
                fundamental=_ai_fundamental
            )
            
        # 顯示 AI 回覆
        with st.chat_message("model", avatar="🤖"):
            st.write(response_text)
            
        # 將回覆寫入歷史紀錄
        st.session_state.chat_history.append({"role": "model", "text": response_text})

    # 提供快速快捷問題按鈕
    st.markdown(f"<br><p style='color:#94A3B8; font-size:0.9rem;'>{LANG_DICT[selected_lang]['shortcut_panel']}</p>", unsafe_allow_html=True)
    c_q1, c_q2, c_q3 = st.columns(3)
    
    with c_q1:
        q1_label = LANG_DICT[selected_lang]["shortcut_q1"].format(stock_id=stock_id)
        if st.button(q1_label):
            # 將快捷問題直接寫入對話
            q1_text = LANG_DICT[selected_lang]["shortcut_q1_text"].format(stock_id=stock_id)
            st.session_state.chat_history.append({"role": "user", "text": q1_text})
            with st.spinner(LANG_DICT[selected_lang]["chat_spinner"]):
                resp = generate_advisor_response(
                    st.session_state.chat_history[:-1], 
                    q1_text, 
                    model_name=selected_model_name,
                    selected_lang=selected_lang,
                    price_targets=price_targets,
                    institutional=institutional,
                    stock_type=stock_type,
                    indicators=_ai_indicators if "_ai_indicators" in dir() else None,
                    macro=_ai_macro if "_ai_macro" in dir() else None,
                    margin=_ai_margin if "_ai_margin" in dir() else None,
                    fundamental=_ai_fundamental if "_ai_fundamental" in dir() else None
                )
                st.session_state.chat_history.append({"role": "model", "text": resp})
            st.rerun()
            
    with c_q2:
        q2_label = LANG_DICT[selected_lang]["shortcut_q2"]
        if st.button(q2_label):
            q2_text = LANG_DICT[selected_lang]["shortcut_q2_text"]
            st.session_state.chat_history.append({"role": "user", "text": q2_text})
            with st.spinner(LANG_DICT[selected_lang]["chat_spinner"]):
                resp = generate_advisor_response(
                    st.session_state.chat_history[:-1], 
                    q2_text, 
                    model_name=selected_model_name,
                    selected_lang=selected_lang,
                    price_targets=price_targets,
                    institutional=institutional,
                    stock_type=stock_type,
                    indicators=_ai_indicators if "_ai_indicators" in dir() else None,
                    macro=_ai_macro if "_ai_macro" in dir() else None,
                    margin=_ai_margin if "_ai_margin" in dir() else None,
                    fundamental=_ai_fundamental if "_ai_fundamental" in dir() else None
                )
                st.session_state.chat_history.append({"role": "model", "text": resp})
            st.rerun()
            
    with c_q3:
        q3_label = LANG_DICT[selected_lang]["shortcut_q3"]
        if st.button(q3_label):
            q3_text = LANG_DICT[selected_lang]["shortcut_q3_text"]
            st.session_state.chat_history.append({"role": "user", "text": q3_text})
            with st.spinner(LANG_DICT[selected_lang]["chat_spinner"]):
                resp = generate_advisor_response(
                    st.session_state.chat_history[:-1], 
                    q3_text, 
                    model_name=selected_model_name,
                    selected_lang=selected_lang,
                    price_targets=price_targets,
                    institutional=institutional,
                    stock_type=stock_type,
                    indicators=_ai_indicators if "_ai_indicators" in dir() else None,
                    macro=_ai_macro if "_ai_macro" in dir() else None,
                    margin=_ai_margin if "_ai_margin" in dir() else None,
                    fundamental=_ai_fundamental if "_ai_fundamental" in dir() else None
                )
                st.session_state.chat_history.append({"role": "model", "text": resp})
            st.rerun()

# ==============================================================================
# TAB 4: 📰 聯網新聞與 AI 分析
# ==============================================================================
with tab_news:
    st.markdown(f"### {LANG_DICT[selected_lang]['news_title']}")
    st.markdown(LANG_DICT[selected_lang]["news_desc"].format(stock_id=stock_id))
    
    # 取得名稱 (如果常用)
    stock_name_map = {
        "00878": "Cathay ESG Dividend ETF" if selected_lang == "English" else "國泰永續高股息",
        "0050": "Yuanta Taiwan 50 ETF" if selected_lang == "English" else "元大台灣50",
        "3049": "Hannstar Touch" if selected_lang == "English" else "精金",
        "6282": "AcBel Polytech" if selected_lang == "English" else "康舒",
        "2330": "TSMC" if selected_lang == "English" else "台積電",
        "2454": "MediaTek" if selected_lang == "English" else "聯發科"
    }
    stock_name = stock_name_map.get(stock_id, "")
    
    # 選擇分析觀點
    st.markdown(LANG_DICT[selected_lang]["news_viewpoint"])
    viewpoint = st.radio(
        LANG_DICT[selected_lang]["news_perspective"],
        LANG_DICT[selected_lang]["news_options"],
        horizontal=True
    )
    
    trigger_btn = st.button(LANG_DICT[selected_lang]["news_trigger"], type="primary")
    
    if trigger_btn:
        viewpoint_short = viewpoint.split(' ')[0]
        with st.spinner(LANG_DICT[selected_lang]["news_spinner"].format(stock_id=stock_id, viewpoint=viewpoint_short)):
            ai_news_report = get_stock_news_briefing(
                stock_id, 
                stock_name, 
                viewpoint, 
                model_name=selected_model_name, 
                selected_lang=selected_lang
            )
            
        st.markdown("---")
        st.markdown(LANG_DICT[selected_lang]["news_report_title"].format(viewpoint=viewpoint_short))
        st.info(ai_news_report)

        # ── 分享工具列：匯出精美 HTML（保留完整排版）────────────
        import datetime as _dt, re as _re
        _ts    = _dt.datetime.now().strftime("%Y%m%d_%H%M")
        _now   = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")
        _fname = f"AI分析報告_{stock_id}_{_ts}.html"

        def _md_to_html(text):
            import re
            # 表格
            def _tbl(m):
                rows = [r for r in m.group(0).strip().splitlines() if r.strip()]
                html, hdr = [], True
                for row in rows:
                    if re.match(r'^\s*\|?[-: |]+\|?\s*$', row):
                        hdr = False; continue
                    cells = [c.strip() for c in row.strip().strip('|').split('|')]
                    tag = 'th' if hdr else 'td'
                    html.append('<tr>' + ''.join(f'<{tag}>{c}</{tag}>' for c in cells) + '</tr>')
                    hdr = False
                return '<table>' + ''.join(html) + '</table>'
            text = re.sub(r'(\|[^\n]+\n)+', _tbl, text)
            # 標題
            text = re.sub(r'^####\s+(.+)$', r'<h4>\1</h4>', text, flags=re.MULTILINE)
            text = re.sub(r'^###\s+(.+)$',  r'<h3>\1</h3>', text, flags=re.MULTILINE)
            text = re.sub(r'^##\s+(.+)$',   r'<h2>\1</h2>', text, flags=re.MULTILINE)
            text = re.sub(r'^#\s+(.+)$',    r'<h1>\1</h1>', text, flags=re.MULTILINE)
            # 粗體/斜體
            text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', text)
            text = re.sub(r'\*\*(.+?)\*\*',       r'<strong>\1</strong>', text)
            text = re.sub(r'\*(.+?)\*',             r'<em>\1</em>', text)
            # 條列
            lines_in = text.split('\n'); out = []; in_ul = False
            for ln in lines_in:
                if re.match(r'^\s*[-*]\s+', ln):
                    if not in_ul: out.append('<ul>'); in_ul = True
                    out.append('<li>' + re.sub(r'^\s*[-*]\s+','',ln) + '</li>')
                else:
                    if in_ul: out.append('</ul>'); in_ul = False
                    out.append(ln)
            if in_ul: out.append('</ul>')
            text = '\n'.join(out)
            text = re.sub(r'^\s*---+\s*$', '<hr>', text, flags=re.MULTILINE)
            text = re.sub(r'^>\s+(.+)$', r'<blockquote>\1</blockquote>', text, flags=re.MULTILINE)
            paras = re.split(r'\n{2,}', text); result = []
            for p in paras:
                p = p.strip()
                if p and not any(p.startswith(t) for t in ['<h','<ul','<ol','<table','<hr','<block']):
                    p = '<p>' + p.replace('\n','<br>') + '</p>'
                result.append(p)
            return '\n'.join(result)

        _body = _md_to_html(ai_news_report)
        _vp   = viewpoint_short

        _html = f"""<!DOCTYPE html>
<html lang="zh-TW"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>AI 分析報告 — {stock_id}</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;600;700&family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
<style>
:root{{--bg:#0b0f19;--card:#131929;--bdr:#1e293b;--txt:#e2e8f0;--muted:#94a3b8;--acc:#38bdf8;}}
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{background:var(--bg);color:var(--txt);font-family:'Noto Sans TC','Inter',sans-serif;font-size:15px;line-height:1.8;}}
.wrap{{max-width:900px;margin:0 auto;padding:32px 24px 64px;}}
.hdr{{background:linear-gradient(135deg,#0f172a,#1e293b);border:1px solid var(--bdr);border-radius:16px;padding:28px 32px;margin-bottom:28px;}}
.hdr h1{{font-size:1.55rem;font-weight:700;color:var(--acc);margin-bottom:8px;}}
.badge{{display:inline-block;background:rgba(56,189,248,.12);color:var(--acc);border:1px solid rgba(56,189,248,.3);border-radius:20px;padding:3px 12px;font-size:.8rem;font-weight:600;margin-right:8px;}}
.body{{background:var(--card);border:1px solid var(--bdr);border-radius:16px;padding:32px;}}
h1,h2{{color:var(--acc);font-size:1.2rem;font-weight:700;margin:28px 0 10px;padding-bottom:6px;border-bottom:1px solid var(--bdr);}}
h3{{color:#f8fafc;font-size:1.05rem;font-weight:700;margin:18px 0 8px;}}
h4{{color:var(--muted);font-size:.95rem;margin:14px 0 6px;}}
p{{margin:8px 0 10px;}}
ul{{margin:8px 0 10px 20px;}}
li{{margin-bottom:5px;}}li::marker{{color:var(--acc);}}
table{{width:100%;border-collapse:collapse;margin:14px 0;font-size:.87rem;border-radius:8px;overflow:hidden;}}
th{{background:rgba(56,189,248,.12);color:var(--acc);font-weight:700;padding:10px 14px;text-align:left;border:1px solid var(--bdr);}}
td{{padding:9px 14px;border:1px solid var(--bdr);}}
tr:nth-child(even) td{{background:rgba(30,41,59,.4);}}
hr{{border:none;border-top:1px solid var(--bdr);margin:22px 0;}}
blockquote{{border-left:4px solid var(--acc);padding:8px 16px;margin:10px 0;background:rgba(56,189,248,.06);border-radius:0 8px 8px 0;color:var(--muted);font-style:italic;}}
strong{{color:#f8fafc;font-weight:700;}}
.foot{{text-align:center;margin-top:36px;color:var(--muted);font-size:.78rem;}}
</style></head><body>
<div class="wrap">
<div class="hdr">
<h1>📊 AI 分析報告 — {stock_id}</h1>
<div><span class="badge">{_vp}</span><span class="badge">產出時間：{_now}</span></div>
</div>
<div class="body">{_body}</div>
<div class="foot">由 AI 股市理財助手自動產出 · 僅供參考，非投資建議 · {_now}</div>
</div></body></html>"""

        _btn_col, _ = st.columns([2, 4])
        with _btn_col:
            st.download_button(
                label="📤 匯出 HTML 報告（傳給朋友直接用瀏覽器打開）",
                data=_html.encode("utf-8"),
                file_name=_fname,
                mime="text/html",
                use_container_width=True,
                key="news_html_btn",
                type="primary"
            )
        st.caption("💡 朋友收到 HTML 檔後，用瀏覽器打開即可看到完整排版，不需要任何軟體。")


# ==============================================================================
# TAB 5: 💡 智慧選股推薦
# ==============================================================================
with tab_screener:
    st.markdown(f"### {LANG_DICT[selected_lang]['screener_title']}")
    st.markdown(LANG_DICT[selected_lang]["screener_desc"])
    
    # 選擇市場
    st.markdown(LANG_DICT[selected_lang]["select_market"])
    screener_market = st.radio(
        LANG_DICT[selected_lang]["select_market"],
        LANG_DICT[selected_lang]["market_options"],
        horizontal=True,
        key="screener_market_radio",
        label_visibility="collapsed"
    )
    
    # 利用 session_state 快取選股結果，避免重複整理
    if "screener_results" not in st.session_state:
        st.session_state.screener_results = {}
        
    trigger_screener_btn = st.button(LANG_DICT[selected_lang]["screener_trigger"], type="primary")
    
    cache_key = f"{screener_market}_{selected_lang}"
    
    if trigger_screener_btn:
        with st.spinner(LANG_DICT[selected_lang]["screener_spinner"]):
            from core.ai_agent import get_ai_stock_recommendations
            result = get_ai_stock_recommendations(
                screener_market, 
                selected_lang=selected_lang,
                model_name=selected_model_name
            )
            st.session_state.screener_results[cache_key] = result
            
    if cache_key in st.session_state.screener_results:
        st.markdown("---")
        st.markdown(LANG_DICT[selected_lang]["screener_report_title"].format(market=screener_market.split(' ')[0]))
        st.info(st.session_state.screener_results[cache_key])

# ==============================================================================
# TAB 2: 🇺🇸 美股即時看盤（積木模組：ui/tab_us_market.py）
# ==============================================================================
with tab_us_market:
    tab_us_market_mod.render(selected_lang)

# ==============================================================================
# TAB 3: 📉 期貨市場看盤（積木模組：ui/tab_futures.py）
# ==============================================================================
with tab_futures:
    tab_futures_mod.render(selected_lang)

# ==============================================================================
# TAB 6: 📚 股市教學隨身筆記
# ==============================================================================
with tab_lessons:
    st.markdown(f"### {LANG_DICT[selected_lang]['lessons_title']}")
    st.markdown(LANG_DICT[selected_lang]["lessons_desc"])
    
    # 載入教學 JSON 數據
    lessons_path = config.LESSONS_FILE
    if os.path.exists(lessons_path):
        with open(lessons_path, "r", encoding="utf-8") as f:
            lessons = json.load(f)
            
        # 1. 14 條鐵律
        st.markdown(f"#### {LANG_DICT[selected_lang]['lessons_h1']}")
        for rule in lessons["trading_rules"]:
            st.markdown(f"- {rule}")
            
        st.markdown("---")
        
        # 2. 5 大分時口訣
        st.markdown(f"#### {LANG_DICT[selected_lang]['lessons_h2']}")
        for m in lessons["intraday_mnemonics"]:
            st.markdown(f"""
                <div class="glass-card" style="padding: 12px; margin-bottom: 12px;">
                    <strong style="color: #06B6D4; font-size: 1.05rem;">口訣 {m['id']}：{m['title']}</strong><br>
                    <span style="color: #F8FAFC; font-size: 0.9rem; display: block; margin-top: 5px;">適用條件：{m['condition']}</span>
                    <span style="color: #94A3B8; font-size: 0.85rem; display: block; margin-top: 3px;">底層邏輯：{m['logic']}</span>
                </div>
            """, unsafe_allow_html=True)
            
        st.markdown("---")
        
        # 3. K 線形態
        st.markdown(f"#### {LANG_DICT[selected_lang]['lessons_h3']}")
        
        c_k1, c_k2, c_k3 = st.columns(3)
        
        with c_k1:
            st.markdown(f"##### {LANG_DICT[selected_lang]['lessons_bullish']}")
            # 遍歷尋找看漲
            for p_type in ["single", "double", "triple"]:
                for p in lessons["kline_patterns"][p_type]:
                    if p["trend"] == "bullish":
                        strength_text = f" (強度: {p['strength']})" if "strength" in p else ""
                        st.markdown(f"**{p['name']}**{strength_text}：{p['meaning']}")
                        
        with c_k2:
            st.markdown(f"##### {LANG_DICT[selected_lang]['lessons_bearish']}")
            for p_type in ["single", "double", "triple"]:
                for p in lessons["kline_patterns"][p_type]:
                    if p["trend"] == "bearish":
                        strength_text = f" (強度: {p['strength']})" if "strength" in p else ""
                        st.markdown(f"**{p['name']}**{strength_text}：{p['meaning']}")
                        
        with c_k3:
            st.markdown(f"##### {LANG_DICT[selected_lang]['lessons_neutral']}")
            for p_type in ["single", "double", "triple"]:
                for p in lessons["kline_patterns"][p_type]:
                    if p["trend"] == "neutral":
                        st.markdown(f"**{p['name']}**：{p['meaning']}")
                        
        # 4. 股癌心法
        if "gooaye_philosophy" in lessons:
            st.markdown("---")
            st.markdown(f"#### {LANG_DICT[selected_lang]['lessons_h4']}")
            for item in lessons["gooaye_philosophy"]:
                st.markdown(f"- {item}")
                        
    else:
        st.info("尚未建立 lessons.json 教學檔案。")
