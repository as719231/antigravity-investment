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
importlib.reload(core.pattern_detector)
importlib.reload(core.ai_agent)
from core.pattern_detector import evaluate_stock_signals, fetch_stock_data
from core.ai_agent import generate_advisor_response, get_stock_news_briefing, get_ai_stock_recommendations
from core.realtime_provider import fetch_realtime_price

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
        "tab_market": "📊 即時看盤與型態偵測",
        "tab_portfolio": "💼 專屬持股追蹤看板",
        "tab_chat": "💬 理財專員對話室",
        "tab_news": "📰 聯網新聞與 AI 分析",
        "tab_screener": "💡 智慧選股推薦",
        "tab_lessons": "📚 股市教學隨身筆記",
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
        "news_options": ["長期價值投資視角 (融合 股癌 / 巴菲特 / 彼得林區)", "短期技術當沖視角 (融合 主人14鐵律 / 5分時口訣 / 短線動能)"],
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
        "tab_market": "📊 Real-time Board & Pattern Detection",
        "tab_portfolio": "💼 Portfolio Tracker",
        "tab_chat": "💬 Advisor Chatroom",
        "tab_news": "📰 Web News & AI Analysis",
        "tab_screener": "💡 AI Screener",
        "tab_lessons": "📚 Stock Lessons & Notes",
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
        "news_options": ["Long-term Value Perspective (Buffett, Peter Lynch, Gooaye)", "Short-term Trading Perspective (14 Rules, 5 Mnemonics, Momentum)"],
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
        "tab_market": "📊 リアルタイム板・パターン検知",
        "tab_portfolio": "💼 専属ポートフォリオ追跡",
        "tab_chat": "💬 アドバイザー対話室",
        "tab_news": "📰 ネットニュース・AI分析",
        "tab_screener": "💡 AIスクリーナー",
        "tab_lessons": "📚 株式投資学習ノート",
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
        "news_options": ["長期バリュー投資視点 (バフェット、ピーター・リンチ、股癌の融合)", "短期デイトレ視点 (お客様の14鉄則、5つの口訣、短期モメンタム)"],
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
        "tab_market": "📊 การดูบอร์ดเรียลไทม์และการตรวจจับรูปแบบ",
        "tab_portfolio": "💼 บอร์ดติดตามพอร์ตหุ้นส่วนตัว",
        "tab_chat": "💬 ห้องสนทนากับเจ้าหน้าที่ดูแลบัญชี",
        "tab_news": "📰 ข่าวออนไลน์และการวิเคราะห์ AI",
        "tab_screener": "💡 แนะนำการสกรีนหุ้น",
        "tab_lessons": "📚 บันทึกการเรียนรู้ตลาดหุ้น",
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
        "news_options": ["มุมมองการลงทุนระยะยาว (Buffett, Peter Lynch, Gooaye)", "มุมมองเก็งกำไรระยะสั้น (กฎ 14 ข้อ, คำคม 5 ข้อ, โมเมนตัม)"],
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
        "tab_market": "📊 Xem bảng giá & Phát hiện mô hình",
        "tab_portfolio": "💼 Bảng theo dõi danh mục cá nhân",
        "tab_chat": "💬 Phòng trò chuyện với trợ lý",
        "tab_news": "📰 Tin tức mạng & Phân tích AI",
        "tab_screener": "💡 Trình lọc cổ phiếu AI",
        "tab_lessons": "📚 Sổ tay học tập chứng khoán",
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
        "news_options": ["Góc nhìn đầu tư giá trị dài hạn (Kết hợp Buffett, Peter Lynch, Gooaye)", "Góc nhìn giao dịch ngắn hạn (Kết hợp 14 quy tắc, 5 khẩu quyết, Động năng ngắn hạn)"],
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
        "auto_refresh_label": "⏱ 啟動盤中即時行情自動更新 (30秒)",
        "realtime_title": "⚡ 盤中即時行情 (Yahoo)",
        "prev_close": "昨收",
        "near_buy_target": "🔥 已跌破或到達第一批買進價！",
        "near_sell_target": "⚠️ 已突破或到達壓力賣出價！",
        "normal_status": "盤中價格波動中",
        "refresh_success": "歷史數據快取已清除！"
    },
    "English": {
        "clear_cache_btn": "🔄 Force Refresh History",
        "auto_refresh_label": "⏱ Enable Intraday Auto-Refresh (30s)",
        "realtime_title": "⚡ Intraday Real-time Quote (Yahoo)",
        "prev_close": "Prev Close",
        "near_buy_target": "🔥 Price reached buy target!",
        "near_sell_target": "⚠️ Price reached resistance target!",
        "normal_status": "Intraday trading active",
        "refresh_success": "Historical cache cleared!"
    },
    "日本語": {
        "clear_cache_btn": "🔄 履歴データを強制更新",
        "auto_refresh_label": "⏱ 盤中気配値自動更新を有効化 (30秒)",
        "realtime_title": "⚡ リアルタイム気配値 (Yahoo)",
        "prev_close": "前日終値",
        "near_buy_target": "🔥 買い参考エリアに到達！",
        "near_sell_target": "⚠️ 売り参考エリアに到達！",
        "normal_status": "日中取引中",
        "refresh_success": "履歴データキャッシュがクリアされました！"
    },
    "ไทย": {
        "clear_cache_btn": "🔄 บังคับรีเฟรชข้อมูลประวัติ",
        "auto_refresh_label": "⏱ เปิดอัปเดตราคาเรียลไทม์ (30 วินาที)",
        "realtime_title": "⚡ ราคาเรียลไทม์ (Yahoo)",
        "prev_close": "ปิดวันก่อน",
        "near_buy_target": "🔥 ราคาถึงเป้าหมายการซื้อแล้ว!",
        "near_sell_target": "⚠️ ราคาถึงแนวต้านแล้ว!",
        "normal_status": "กำลังซื้อขายระหว่างวัน",
        "refresh_success": "ล้างแคชข้อมูลประวัติแล้ว!"
    },
    "Tiếng Việt": {
        "clear_cache_btn": "🔄 Buộc làm mới dữ liệu lịch sử",
        "auto_refresh_label": "⏱ Bật tự động cập nhật giá (30 giây)",
        "realtime_title": "⚡ Giá trực tuyến (Yahoo)",
        "prev_close": "Đóng cửa trước",
        "near_buy_target": "🔥 Giá đã đạt mức hỗ trợ mua!",
        "near_sell_target": "⚠️ Giá đã đạt mức kháng cự bán!",
        "normal_status": "Đang giao dịch trực tuyến",
        "refresh_success": "Đã xóa bộ nhớ đệm lịch sử!"
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

# --- 盤中即時行情卡片繪製與 Fragment 宣告 ---
def draw_realtime_card(stock_id: str, price_targets: dict, selected_lang: str, auto_refresh: bool):
    rt = fetch_realtime_price(stock_id)
    if not rt.get("success"):
        st.warning(f"無法取得即時報價: {rt.get('error')}")
        return
        
    price = rt["price"]
    change = rt["change"]
    change_pct = rt["change_percent"]
    symbol = rt["symbol"]
    
    if change > 0:
        color = "#EF4444"
        sign = "+"
    elif change < 0:
        color = "#10B981"
        sign = ""
    else:
        color = "#94A3B8"
        sign = ""
        
    buy_ideal = price_targets.get("buy_ideal")
    sell_ideal = price_targets.get("sell_ideal")
    
    status_alert = ""
    if buy_ideal and price <= buy_ideal:
        status_alert = f"""
            <div style="background:rgba(239,68,68,0.1); color:#EF4444; border:1px solid #EF444433; 
                        padding:8px 12px; border-radius:6px; font-size:0.82rem; font-weight:600; text-align:center; margin-top:10px;">
                {REALTIME_DICT[selected_lang]["near_buy_target"]}
            </div>
        """
    elif sell_ideal and price >= sell_ideal:
        status_alert = f"""
            <div style="background:rgba(245,158,11,0.1); color:#F59E0B; border:1px solid #F59E0B33; 
                        padding:8px 12px; border-radius:6px; font-size:0.82rem; font-weight:600; text-align:center; margin-top:10px;">
                {REALTIME_DICT[selected_lang]["near_sell_target"]}
            </div>
        """
        
    buy_desc = f"{buy_ideal} 元" if buy_ideal else "--"
    sell_desc = f"{sell_ideal} 元" if sell_ideal else "--"
    
    st.markdown(f"""
        <div class="glass-card" style="padding:16px 20px; margin-bottom:16px; 
                     background: linear-gradient(135deg, rgba(20,25,50,0.8) 0%, rgba(10,12,30,0.9) 100%); 
                     border-left: 4px solid {color};">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
                <div>
                    <div style="font-size:0.8rem; color:#94A3B8; font-weight:600;">
                        {REALTIME_DICT[selected_lang]["realtime_title"]} - {symbol}
                    </div>
                    <div style="display:flex; align-items:baseline; gap:12px; margin-top:4px;">
                        <span style="font-size:2.0rem; font-weight:800; color:#F8FAFC; font-family: monospace; line-height:1;">
                            {price:,.2f}
                        </span>
                        <span style="font-size:1.1rem; font-weight:700; color:{color}; font-family: monospace;">
                            {sign}{change:+.2f} ({sign}{change_pct:+.2f}%)
                        </span>
                    </div>
                </div>
                <div style="display:flex; gap:15px; text-align:right;">
                    <div>
                        <div style="font-size:0.72rem; color:#64748B;">{REALTIME_DICT[selected_lang]["prev_close"]}</div>
                        <div style="font-size:0.95rem; font-weight:600; color:#CBD5E1; font-family: monospace;">
                            {rt["prev_close"]:,.2f}
                        </div>
                    </div>
                    <div>
                        <div style="font-size:0.72rem; color:#64748B;">支撐位 (買進參考)</div>
                        <div style="font-size:0.95rem; font-weight:600; color:#10B981; font-family: monospace;">
                            {buy_desc}
                        </div>
                    </div>
                    <div>
                        <div style="font-size:0.72rem; color:#64748B;">壓力位 (賣出參考)</div>
                        <div style="font-size:0.95rem; font-weight:600; color:#EF4444; font-family: monospace;">
                            {sell_desc}
                        </div>
                    </div>
                </div>
            </div>
            {status_alert}
        </div>
    """, unsafe_allow_html=True)
    
    if not auto_refresh:
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("🔄 刷新即時報價", key="btn_manual_refresh_quote", use_container_width=True):
                st.rerun()

@st.fragment(run_every=30)
def render_realtime_quote_auto(stock_id: str, price_targets: dict, selected_lang: str):
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

# 偵測輸入的股票代號
stock_id = stock_id_input.strip()

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

currency = LANG_DICT[selected_lang]["currency"]

# --- 頁面 Tabs 配置 ---
tab_market, tab_portfolio, tab_chat, tab_news, tab_screener, tab_lessons = st.tabs([
    LANG_DICT[selected_lang]["tab_market"],
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
        render_realtime_quote_auto(stock_id_input, price_targets, selected_lang)
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
            secondary_badge = f"""
                <span style="background:{s_color}22; color:{s_color}; border:1px solid {s_color}55;
                             padding:4px 12px; border-radius:20px; font-size:0.78rem; font-weight:600;">
                    副&nbsp;{st_s}&nbsp;{sc}%
                </span>"""

        st.markdown(f"""
            <div class="glass-card" style="padding:12px 18px; margin-bottom:12px; display:flex;
                         align-items:center; flex-wrap:wrap; gap:10px; border-left:3px solid {p_color};">
                <span style="font-size:0.78rem; color:#94A3B8;">🏷 股票類型</span>
                <span style="background:{p_color}; color:#fff; padding:4px 14px; border-radius:20px;
                             font-size:0.85rem; font-weight:700;">
                    主&nbsp;{pt}&nbsp;{pc}%
                </span>
                {secondary_badge}
                <span style="font-size:0.75rem; color:#64748B; flex:1; min-width:160px;">
                    {reasons_short}
                </span>
            </div>
        """, unsafe_allow_html=True)

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

# ==============================================================================
# TAB 3: 💬 理財專員對話室
# ==============================================================================
with tab_chat:
    st.markdown(f"### {LANG_DICT[selected_lang]['chat_title']}")
    st.markdown(LANG_DICT[selected_lang]["chat_desc"])
    
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
                stock_type=stock_type
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
                    stock_type=stock_type
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
                    stock_type=stock_type
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
                    stock_type=stock_type
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
        with st.spinner(LANG_DICT[selected_lang]["news_spinner"].format(viewpoint=viewpoint_short)):
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
