"""GETSTOCK 全自動 AI 大戶籌碼選股中控台 (Full-Auto AI Stock Picker)

整合 fetch_chips.py、build_site.py、export_twse_day.py、verify_official.py 與 AI 盤後投研報告產生器(含波段買賣點、當沖買賣點與跨日大數據異常對比)。
只用 Python 3 標準函式庫，零外部套件依賴。

用法:
  python auto_pick.py                 # 自動抓取最新交易日盤後資料 → 計算 AI 籌碼選股與買賣點 → 產生報告與網頁
  python auto_pick.py 20261020        # 指定日期全自動執行
  python auto_pick.py --rebuild       # 不重新連線抓取，直接由 out/day_*.json 重新計算 AI 買賣點、跨日異常、報告與網頁
  python auto_pick.py --force         # 強制重新連線證交所/櫃買中心/集保抓取最新盤後資料
  python auto_pick.py --verify        # 執行後自動與證交所/櫃買中心官方資料交叉核對
  python auto_pick.py --open          # 完成後自動以預設瀏覽器開啟 index.html
  python auto_pick.py --daemon        # 常駐背景排程模式 (每個交易日 16:35、22:05、隔日 08:15 自動執行)
"""
import argparse
import datetime as dt
import glob
import json
import os
import subprocess
import sys
import time
import urllib.request
import webbrowser

from fetch_chips import OUT, compute_ai_insight, compute_daytrade_plan

BASE = os.path.dirname(os.path.abspath(__file__))


def call_llm_commentary(prompt_text):
    """若環境變數設有 GEMINI_API_KEY 或 OPENAI_API_KEY，自動呼叫大模型產生深度 AI 盤後解盤。"""
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
            payload = json.dumps({"contents": [{"parts": [{"text": prompt_text}]}]}).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=45) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                return res["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            print(f"[AI] Gemini API 呼叫略過 ({e})，使用內建量化多因子引擎。")

    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        try:
            url = "https://api.openai.com/v1/chat/completions"
            payload = json.dumps({
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt_text}],
                "temperature": 0.3,
            }).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {openai_key}",
            })
            with urllib.request.urlopen(req, timeout=45) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                return res["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"[AI] OpenAI API 呼叫略過 ({e})，使用內建量化多因子引擎。")
    return None


def generate_ai_report(doc):
    """依據單日 out/day_YYYY-MM-DD.json 產生含 AI 買賣點(波段+當沖)與跨日大數據異常對比的 Markdown 報告。"""
    date_str = doc["date"]
    picks = doc.get("picks", [])
    for p in picks:
        if "tradePlan" not in p:
            p.update(compute_ai_insight(p))

    twse_picks = [p for p in picks if p["market"] == "上市"]
    otc_picks = [p for p in picks if p["market"] == "上櫃"]
    s_plus = [p for p in picks if p.get("aiGrade") == "S+"]
    dual_buy = [p for p in picks if p.get("foreignNet", 0) > 0 and p.get("trustNet", 0) > 0]
    big_up = [p for p in picks if (p.get("bigChg") or 0) >= 0.5]
    ca = doc.get("crossDayAnomalies", {})

    lines = [
        f"# GETSTOCK 全自動 AI 盤後大戶籌碼選股報告 ({date_str})",
        "",
        f"- **產出時間**：{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- **集保股權分散表基準週**：{doc.get('tdccDate', '—')} (對比前週 {doc.get('tdccPrevDate', '—')})",
        f"- **合格流動性母體**：共 {doc.get('universe', 0)} 檔 (上市 {doc.get('universeByMarket', {}).get('上市', 0)} 檔 / 上櫃 {doc.get('universeByMarket', {}).get('上櫃', 0)} 檔)",
        f"- **AI 多因子共振統計**：AI `S+ 強勢共識` 共 **{len(s_plus)}** 檔｜`土洋合買` 共 **{len(dual_buy)}** 檔｜`千張大戶週增≥0.5%` 共 **{len(big_up)}** 檔",
        "",
        "## 一、每日收盤指數摘要",
        "",
        "| 指數名稱 | 收盤指數 | 漲跌點數 | 漲跌幅(%) |",
        "|---|---:|---:|---:|",
    ]
    for idx in doc.get("indices", []):
        lines.append(f"| {idx['name']} | {idx['close']:,.2f} | {idx['chg']:+.2f} | {idx['chgPct']:+.2f}% |")

    # 跨日大數據異常偵測專節
    lines.extend([
        "",
        f"## 二、跨日大數據異常偵測（{date_str} 對比前幾日籌碼/量價異動）",
        "",
    ])
    if ca.get("instReversalPicks"):
        lines.append("### 1. 🔄 法人由賣轉買 V 型大反轉（前日賣超 → 今日突反手大買）")
        for x in ca["instReversalPicks"]:
            lines.append(f"- **{x['name']} (`{x['code']}` {x['market']}#{x['rank']})**：收 {x['close']} ({x['chg']:+.2f}%) — {x['note']}｜🎯 **AI 買點 `{x['buyZone']}`、停利 `{x['sellTarget1']}`、停損 `{x['stopLoss']}`**")
        lines.append("")

    if ca.get("divergenceBuyPicks"):
        lines.append("### 2. 🧲 價跌但法人與大戶逆勢狂買（壓低洗盤吃貨背離）")
        for x in ca["divergenceBuyPicks"]:
            lines.append(f"- **{x['name']} (`{x['code']}` {x['market']}#{x['rank']})**：收 {x['close']} ({x['chg']:+.2f}%) — {x['note']}｜🎯 **低接買點 `{x['buyZone']}`、停利 `{x['sellTarget1']}`、停損 `{x['stopLoss']}`**")
        lines.append("")

    if ca.get("consecutivePicks"):
        lines.append("### 3. 👑 連續霸榜主力鎖碼王（連續 ≥3 日穩居推薦榜）")
        for x in ca["consecutivePicks"]:
            lines.append(f"- **{x['name']} (`{x['code']}` {x['market']}#{x['rank']})**：連霸 **{x['streakDays']}** 日（軌跡：{x['rankHistory']}），5日法人累計 `{x['inst5d']:+,}` 張｜🎯 **買點 `{x['buyZone']}`、停利 `{x['sellTarget1']}`、停損 `{x['stopLoss']}`**")
        lines.append("")

    if ca.get("newSurgePicks"):
        lines.append("### 4. 🚀 今日空降前六強 & 排名急竄突襲黑馬")
        for x in ca["newSurgePicks"]:
            lines.append(f"- **{x['name']} (`{x['code']}` {x['market']}#{x['rank']})**：{x['tag']}，今日法人買超 `+{x['inst']:,}` 張｜🎯 **買點 `{x['buyZone']}`、停利 `{x['sellTarget1']}`、停損 `{x['stopLoss']}`**")
        lines.append("")

    if ca.get("droppedAlerts"):
        lines.append("### 5. ⚠️ 前日強勢推薦・今日跌出榜外警報（留意籌碼鬆動與停利防守）")
        for x in ca["droppedAlerts"]:
            lines.append(f"- **{x['name']} (`{x['code']}` {x['market']})**：{x['note']}")
        lines.append("")

    if ca.get("shortTrapAlerts"):
        lines.append("### 6. 💣 當沖爆量拉高・法人偷倒貨警報（慎防隔日早盤獲利賣壓）")
        for x in ca["shortTrapAlerts"]:
            dp = x.get("dtPlan", {})
            lines.append(f"- **{x['name']} (`{x['code']}` {x['market']})**：{x['note']}｜🎯 **當沖先賣點 `{dp.get('entryZone')}`、回補買點 `{dp.get('target1')}`、停損 `{dp.get('stopLoss')}`**")
        lines.append("")

    lines.extend([
        "## 三、AI 強勢共識首選 (S+ 級：含波段建議買點、停利賣點與停損價)",
        "",
    ])
    if s_plus:
        lines.extend([
            "| 市場 | 排名 | 代號 | 名稱 | 收盤價 | 漲跌幅 | 總分 | 策略型態 | 🎯 建議買點區間 | 突破買點 | 💰 停利賣點 1 / 2 | 🛡️ 防守停損 | 跨日異常亮點 |",
            "|---|---:|---|---|---:|---:|---:|---|---|---:|---|---:|---|",
        ])
        for p in sorted(s_plus, key=lambda x: -x["score"]):
            tp = p.get("tradePlan", {})
            anom_str = "、".join(a["type"] for a in p.get("anomalies", [])) or "籌碼集中"
            lines.append(
                f"| {p['market']} | #{p['rank']} | `{p['code']}` | **{p['name']}** | {p['close']} | {p['chgPct']:+.2f}% | **{p['score']:.1f}** | {tp.get('strategy', '')} | **{tp.get('buyZone', '')}** | {tp.get('breakoutBuy', '')} | **{tp.get('sellTarget1', '')} / {tp.get('sellTarget2', '')}** | {tp.get('stopLoss', '')} | {anom_str} |"
            )

    for mk, lst in (("上市", twse_picks), ("上櫃", otc_picks)):
        lines.extend([
            "",
            f"## 四、{mk}推薦 20 檔完整清單（含 AI 買賣點與跨日異常）",
            "",
            "| 名次 | 代號 | 名稱 | AI評級 | 分數 | 收盤 | 漲跌幅 | 🎯 AI 建議買點 | 💰 停利賣點 1 / 2 | 🛡️ 停損價 | 法人合計 | 大戶週增減 | 融資增減 | 跨日異常與標籤 |",
            "|---:|---|---|---|---:|---:|---:|---|---|---:|---:|---:|---:|---|",
        ])
        for p in lst:
            tp = p.get("tradePlan", {})
            big_str = f"{p['bigChg']:+.2f}%" if p.get("bigChg") is not None else "—"
            anom_tags = [f"⚡{a['type']}" for a in p.get("anomalies", [])] + list(p.get("tags", []))
            lines.append(
                f"| {p['rank']} | `{p['code']}` | **{p['name']}** | `{p.get('aiGrade', 'A')}` | **{p['score']:.1f}** | {p['close']} | {p['chgPct']:+.2f}% | **{tp.get('buyZone', '')}** | **{tp.get('sellTarget1', '')} / {tp.get('sellTarget2', '')}** | {tp.get('stopLoss', '')} | {p['instNet']:+,} | {big_str} | {p['marginChg']:+,} | {'、'.join(anom_tags)} |"
            )

    dt_data = doc.get("dayTrade", {})
    for side, title, col_entry, col_exit in (
        ("long", "當沖做多「強勢續攻」20 檔（先買後賣）", "🎯 當沖買點(低接/突破)", "💰 停利賣點 1 / 2"),
        ("short", "當沖做空「隔日沖賣壓 / 弱勢續跌」20 檔（先賣後買）", "🎯 先賣空點(拉高/轉弱)", "💰 回補買點 1 / 2"),
    ):
        rows = dt_data.get(side, [])
        if rows:
            lines.extend([
                "",
                f"## 五、隔日{title}",
                "",
                f"| 名次 | 市場 | 代號 | 名稱 | 型態 | 分數 | 收盤 | 漲跌幅 | {col_entry} | {col_exit} | 🛡️ 停損價 | 週轉率 | 當沖比 | 量增 | 法人(張) |",
                "|---:|---|---|---|---|---:|---:|---:|---|---|---:|---:|---:|---:|---:|",
            ])
            for x in rows:
                dp = x.get("dtPlan") or compute_daytrade_plan(x, side)
                lines.append(
                    f"| {x['rank']} | {x['market']} | `{x['code']}` | **{x['name']}** | {x.get('thesis', '')} | **{x['score']:.1f}** | {x['close']} | {x['chgPct']:+.2f}% | **{dp['entryZone']}** ({dp['breakoutEntry']}) | **{dp['target1']} / {dp['target2']}** | {dp['stopLoss']} | {x['turnover']:.2f}% | {x['dtRatio']:.1f}% | {x['surge']:.1f}x | {x['instNet']:+,} |"
                )

    lines.extend([
        "",
        "---",
        "> **免責聲明**：本報告非證券投資顧問事業，內容（含 AI 買賣點與跨日異常偵測）僅為公開資料整理與規則試算，不構成投資建議或買賣推薦，資料以各機構官方公告為準，投資盈虧自負。",
    ])

    report_path = os.path.join(OUT, f"ai_report_{date_str}.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return report_path


def run_step(cmd, desc):
    print(f"\n>>> [GETSTOCK 全自動流程] {desc}: {' '.join(cmd)}", flush=True)
    res = subprocess.run(cmd, cwd=BASE)
    if res.returncode != 0:
        print(f"!!! [警告] {desc} 回傳代碼 {res.returncode}", flush=True)
    return res.returncode == 0


def is_latest_finalized(date_arg=None):
    """檢查最新交易日(或指定日期)的 out/day_YYYY-MM-DD.json 是否已存在且融資融券已定稿。"""
    if date_arg:
        ymd = f"{date_arg[:4]}-{date_arg[4:6]}-{date_arg[6:]}"
        p = os.path.join(OUT, f"day_{ymd}.json")
        if not os.path.exists(p):
            return False
        doc = json.load(open(p, encoding="utf-8"))
        return not doc.get("marginPending")
    latest_files = sorted(glob.glob(os.path.join(OUT, "day_*.json")), reverse=True)
    if not latest_files:
        return False
    doc = json.load(open(latest_files[0], encoding="utf-8"))
    if doc.get("marginPending"):
        return False
    latest_date = dt.date.fromisoformat(doc["date"])
    now = dt.datetime.now()
    cur = now.date()
    if now.hour < 16 or (now.hour == 16 and now.minute < 30):
        cur -= dt.timedelta(days=1)
    while cur.weekday() >= 5:
        cur -= dt.timedelta(days=1)
    return latest_date >= cur


def run_pipeline(date_arg=None, rebuild_only=False, force_fetch=False, do_verify=False, open_browser=False):
    py = sys.executable
    if not rebuild_only and not force_fetch and is_latest_finalized(date_arg):
        print(">>> [GETSTOCK 智慧快取] 最新交易日盤後資料與融資大戶皆已定稿 (使用 --force 可強制重抓)")
        rebuild_only = True

    if not rebuild_only:
        cmd_fetch = [py, os.path.join(BASE, "fetch_chips.py")]
        if date_arg:
            cmd_fetch.append(date_arg)
        run_step(cmd_fetch, "步驟 1/4：抓取證交所、櫃買中心與集保大戶資料並計算 AI 籌碼分數與買賣點")

        latest_files = sorted(glob.glob(os.path.join(OUT, "day_*.json")), reverse=True)
        if latest_files:
            latest_ymd = os.path.basename(latest_files[0])[4:14].replace("-", "")
            target_ymd = date_arg or latest_ymd
            run_step([py, os.path.join(BASE, "export_twse_day.py"), target_ymd], f"步驟 2/4：匯出 {target_ymd} 盤後 CSV 報表與法人摘要")

    # 先執行 build_site.py 以完成跨日比對(crossDayAnomalies)與買賣點寫入
    run_step([py, os.path.join(BASE, "build_site.py")], "步驟 3/4：計算跨日大數據異常對比並建置 index.html 與 chips_radar.html")

    # 產生所有日期的 AI 盤後選股 Markdown 報告
    latest_files = sorted(glob.glob(os.path.join(OUT, "day_*.json")), reverse=True)
    for idx, fpath in enumerate(latest_files):
        with open(fpath, encoding="utf-8") as f:
            doc = json.load(f)
        rep = generate_ai_report(doc)
        if idx == 0:
            print(f">>> [GETSTOCK 全自動流程] 已產出最新 AI 盤後買賣點與跨日異常報告：{rep}")

    if do_verify and latest_files:
        target_ymd = date_arg or os.path.basename(latest_files[0])[4:14].replace("-", "")
        run_step([py, os.path.join(BASE, "verify_official.py"), target_ymd], f"步驟 4/4：與官方資料核對 ({target_ymd})")

    index_path = os.path.join(BASE, "index.html")
    print(f"\n=== 全自動 AI 選股完成！首頁路徑：{index_path} ===")
    if open_browser and os.path.exists(index_path):
        webbrowser.open(f"file:///{index_path.replace(os.sep, '/')}")


def daemon_loop():
    """常駐背景排程模式：每個交易日 16:35(初版)、22:05(融資定稿)、08:15(隔日當沖定稿)自動執行。"""
    schedules = [("16:35", False), ("22:05", False), ("08:15", True)]
    triggered = set()
    print("=== GETSTOCK 全自動 AI 選股常駐排程已啟動 ===")
    print("排程時間點：每日 16:35 (法人初版)、22:05 (融資+大戶定稿)、08:15 (隔日當沖定稿與官方核對)")
    while True:
        now = dt.datetime.now()
        hm = now.strftime("%H:%M")
        key = f"{now:%Y-%m-%d}_{hm}"
        for target_hm, verify_flag in schedules:
            if hm == target_hm and key not in triggered and now.weekday() < 6:
                triggered.add(key)
                print(f"\n[{now:%Y-%m-%d %H:%M:%S}] 觸發排程任務 ({target_hm})...")
                try:
                    run_pipeline(force_fetch=True, do_verify=verify_flag)
                except Exception as e:
                    print(f"排程執行發生例外：{e}")
        time.sleep(25)


def main():
    parser = argparse.ArgumentParser(description="GETSTOCK 全自動 AI 大戶籌碼選股系統")
    parser.add_argument("date", nargs="?", help="指定交易日 YYYYMMDD (預設為最近一個交易日)")
    parser.add_argument("--rebuild", action="store_true", help="僅使用既有 out/day_*.json 快速重建 AI 報告與網頁")
    parser.add_argument("--force", action="store_true", help="強制重新連線抓取最新盤後資料")
    parser.add_argument("--verify", action="store_true", help="執行 verify_official.py 與官方資料核對")
    parser.add_argument("--open", action="store_true", help="完成後自動開啟 index.html")
    parser.add_argument("--daemon", action="store_true", help="啟動 24 小時常駐背景自動排程")
    args = parser.parse_args()

    if args.daemon:
        daemon_loop()
    else:
        run_pipeline(
            date_arg=args.date,
            rebuild_only=args.rebuild,
            force_fetch=args.force,
            do_verify=args.verify,
            open_browser=args.open,
        )


if __name__ == "__main__":
    main()
