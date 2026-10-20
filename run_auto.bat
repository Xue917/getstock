@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================================
echo   GETSTOCK 全自動 AI 大戶籌碼選股系統
echo ========================================================
python auto_pick.py --open %*
if errorlevel 1 (
    echo.
    echo [提示] 執行發生錯誤，請確認已安裝 Python 3。
    pause
)
