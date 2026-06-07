@echo off
chcp 65001 >nul
title 專屬AI股市理財助手
echo.
echo  ╔══════════════════════════════════════╗
echo  ║   專屬 AI 股市理財助手  正在啟動...   ║
echo  ╚══════════════════════════════════════╝
echo.
echo  正在啟動 Streamlit 伺服器，請稍候...
echo  啟動後請在瀏覽器開啟：http://localhost:8501
echo.

cd /d "%~dp0"
python -m streamlit run app.py --server.address=0.0.0.0 --server.port=8501 --server.headless false

pause
