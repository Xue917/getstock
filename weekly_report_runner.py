# -*- coding: utf-8 -*-
"""
weekly_report_runner.py
每週五下午 17:00 定時全自動執行：
1. 比對過去一週全市場推薦標的與真實市場走勢之落差（勝率、報酬、停損停利）
2. 深度分析本週主流強勢族群與主力資金輪動趨勢
3. 輸出結構化「模型迭代回饋報告」文字檔（out/model_feedback_weekly.txt）
4. 重新建置網站並自動 commit & push 至 GitHub
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
    print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] 開始執行每週五 17:00 一週分析報告排程任務...")
    
    # 1. 執行一週分析報告產生器
    run_cmd("python generate_weekly_report.py")
    
    # 2. 重新編譯模板並建置網站
    run_cmd("python build_clean_template.py")
    run_cmd("python build_site.py")
    
    # 3. 推送至 GitHub
    today_str = now.strftime("%Y-%m-%d")
    run_cmd("git add .")
    run_cmd(f'git commit -m "report: 每週五 17:00 一週量化覆盤與趨勢模型回饋報告更新 ({today_str})"')
    run_cmd("git push origin main")
    print(f"[{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 一週分析報告排程執行完成！")

if __name__ == "__main__":
    main()
