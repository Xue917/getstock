# -*- coding: utf-8 -*-
"""
daily_recommend.py
每日開盤前一晚 22:00 (週日～週四) 定時全自動執行：
1. 抓取最新盤後資料，針對全市場 1,474 檔上市櫃股票進行多因子量化評估與當沖標的計算
2. 重新編譯生成最新網站與資料庫
3. 自動 commit 並 push 至 GitHub main 分支
"""
import os
import subprocess
import datetime as dt

BASE = os.path.dirname(os.path.abspath(__file__))

def run_cmd(cmd):
    print(f">> 執行: {cmd}")
    res = subprocess.run(cmd, shell=True, cwd=BASE, capture_output=True, text=True, encoding="utf-8")
    if res.returncode != 0:
        print(f"錯誤: {res.stderr}")
    else:
        print(res.stdout.strip())
    return res.returncode == 0

def main():
    now = dt.datetime.now()
    print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] 開始執行每日盤前 22:00 全市場推薦排程任務...")
    
    # 1. 抓取與計算全市場推薦 (1,474 檔母體)
    run_cmd("python fetch_chips.py")
    
    # 2. 生成一週分析報告數據
    run_cmd("python generate_weekly_report.py")
    
    # 3. 編譯模板並建置網站
    run_cmd("python build_clean_template.py")
    run_cmd("python build_site.py")
    
    # 4. 推送至 GitHub
    today_str = now.strftime("%Y-%m-%d")
    run_cmd("git add .")
    run_cmd(f'git commit -m "auto: 每日盤前 22:00 全市場股票與當沖量化推薦更新 ({today_str})"')
    run_cmd("git push origin main")
    print(f"[{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 每日推薦排程執行完成！")

if __name__ == "__main__":
    main()
