# -*- coding: utf-8 -*-
# Windows Task Scheduler 註冊腳本
# 以系統管理員身分執行此 PowerShell 腳本即可將排程自動註冊進 Windows 工作排程器

$pythonPath = (Get-Command python).Source
$stockDir = "C:\Users\user\Desktop\GETSTOCK"

Write-Host "=== GETSTOCK 自動定時排程註冊工具 ===" -ForegroundColor Cyan
Write-Host "偵測 Python 路徑: $pythonPath" -ForegroundColor Gray
Write-Host "專案工作目錄: $stockDir" -ForegroundColor Gray

# 1. 每日盤前 22:00 推薦排程（週日至週四）
$dailyTaskName = "GETSTOCK_Daily_Recommendation_2200"
$dailyScript = Join-Path $stockDir "daily_recommend.py"
$dailyAction = New-ScheduledTaskAction -Execute $pythonPath -Argument "`"$dailyScript`"" -WorkingDirectory $stockDir
$dailyTrigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday,Monday,Tuesday,Wednesday,Thursday -At 22:00
$dailySettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName $dailyTaskName -Action $dailyAction -Trigger $dailyTrigger -Settings $dailySettings -Description "GETSTOCK 每日開盤前一晚 22:00 全市場推薦與當沖自動更新" -Force
Write-Host " [V] 已註冊每日推薦工作: $dailyTaskName (每週日~週四 22:00)" -ForegroundColor Green

# 2. 每週五 17:00 一週分析報告排程
$weeklyTaskName = "GETSTOCK_Weekly_Report_Friday_1700"
$weeklyScript = Join-Path $stockDir "weekly_report_runner.py"
$weeklyAction = New-ScheduledTaskAction -Execute $pythonPath -Argument "`"$weeklyScript`"" -WorkingDirectory $stockDir
$weeklyTrigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Friday -At 17:00
$weeklySettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName $weeklyTaskName -Action $weeklyAction -Trigger $weeklyTrigger -Settings $weeklySettings -Description "GETSTOCK 每週五 17:00 一週覆盤分析與模型迭代回饋報告產出" -Force
Write-Host " [V] 已註冊每週報告工作: $weeklyTaskName (每週五 17:00)" -ForegroundColor Green

Write-Host "`n全部排程註冊完成！" -ForegroundColor Yellow
