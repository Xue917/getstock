@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================================
echo   設定 Windows 工作排程器：每日 22:05 自動執行 GETSTOCK AI 選股
echo ========================================================
schtasks /Create /F /SC DAILY /TN "GETSTOCK_Daily_AI_Stock_Picker" /TR "python \"%~dp0auto_pick.py\" --force" /ST 22:05
if errorlevel 1 (
    echo [失敗] 請以「系統管理員身分」執行此批次檔。
) else (
    echo [成功] 已建立每日 22:05 自動選股排程 (GETSTOCK_Daily_AI_Stock_Picker)！
)
pause
