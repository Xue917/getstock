# -*- coding: utf-8 -*-
"""
daily_recommend.py
每日開盤前一晚 22:00 (週日至週四) 定時自動執行：
1. 自動載入大數據最佳化權重 (out/model_weights.json)
2. 評估全市場 1,474 檔上市櫃股票，進行多因子量化評級與當沖多空評選
3. 重新編譯生成最新網頁與資料庫
4. 自動 commit 與 push 到 GitHub main 分支
"""
import os
import subprocess
import datetime as dt

BASE = os.path.dirname(os.path.abspath(__file__))

def run_cmd(cmd):
    print(f">> 執行: {cmd}")
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    res = subprocess.run(
        cmd,
        shell=True,
        cwd=BASE,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env
    )
    if res.returncode != 0:
        print(f"錯誤: {res.stderr or ''}")
    else:
        if res.stdout:
            print(res.stdout.strip())
    return res.returncode == 0

def main():
    now = dt.datetime.now()
    print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] 開始執行每日開盤前 22:00 推薦排程...")

    # 1. 確保大數據動態最佳化權重存在
    if not os.path.exists(os.path.join(BASE, "out", "model_weights.json")):
        run_cmd("python auto_tune_model.py")

    # 2. 評估全市場推薦 (1,474 檔全市場)
    run_cmd("python fetch_chips.py")

    # 3. 產出一週同週分析報告數據
    run_cmd("python generate_weekly_report.py")

    # 4. 編譯模板並建置網站
    run_cmd("python build_clean_template.py")
    run_cmd("python build_site.py")

    # 5. 推送至 GitHub
    today_str = now.strftime("%Y-%m-%d")
    run_cmd("git add .")
    run_cmd(f'git commit -m "auto: 每日開盤前 22:00 全市場推薦與大數據自適應權重更新 ({today_str})"')
    run_cmd("git push origin main")
    print(f"[{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 每日推薦排程執行完成！")

if __name__ == "__main__":
    main()
