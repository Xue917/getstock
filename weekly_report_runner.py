# -*- coding: utf-8 -*-
"""
weekly_report_runner.py
每週五下午 17:00 定時自動執行：
1. 嚴格限定「同週 (週一至週五)」評估母體
2. 產出推薦股票「漲最多的 10 檔」與「虧最多的 10 檔」
3. 自動以大數據庫執行「動態權重自適應回測調校 (auto_tune_model.py)」，找到更賺的股票
4. 匯出格式化「模型迭代回饋報告」文字檔 (out/model_feedback_weekly.txt)
5. 重新建置網站並自動 commit & push 到 GitHub
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
    print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] 開始執行每週五 17:00 一週分析報告與大數據模型調校...")

    # 1. 大數據自動自適應調校模型權重 (持續進化，找到更賺的股票)
    run_cmd("python auto_tune_model.py")

    # 2. 產出同週分析報告 (含漲最多 10 檔與虧最多 10 檔)
    run_cmd("python generate_weekly_report.py")

    # 3. 重新編譯模板並建置網站
    run_cmd("python build_clean_template.py")
    run_cmd("python build_site.py")

    # 4. 推送至 GitHub
    today_str = now.strftime("%Y-%m-%d")
    run_cmd("git add .")
    run_cmd(f'git commit -m "report: 每週五 17:00 一週同週覆盤、漲跌前10檔與大數據自適應權重調校更新 ({today_str})"')
    run_cmd("git push origin main")
    print(f"[{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 一週分析報告與大數據模型調校完成！")

if __name__ == "__main__":
    main()
