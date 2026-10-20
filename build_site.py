"""把 out/day_*.json 的推薦結果、AI 買賣點(波段+當沖)、跨日大數據異常、全市場個股健檢資料庫與歷史回測匯入網頁。

用法: python build_site.py
輸出: index.html(可直接雙擊開啟的全方位 AI 選股機器首頁)
      chips_radar.html(籌碼雷達五維度明細網頁,內嵌完整盤後資料)
      site_publish.html(發布到 Artifact 用的版本,不含 <html>/<head> 外框)
      ../vibe-site/index.html(若 ../vibe-site 資料夾存在則同步輸出)
"""
import datetime as dt
import glob
import json
import os
import re
import time
import urllib.request

from fetch_chips import (
    CACHE, LOOKBACK, MARKETS, MIN_AVG_LOTS, MIN_PRICE, WEIGHTS,
    compute_ai_insight, compute_daytrade_plan, compute_trade_plan,
    is_common_stock, margins, pct_rank, ssl_context, streak,
    tdcc_for, tpex_inst, tpex_price, twse_inst, twse_price,
)

BASE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(BASE, "..", "vibe-site", "index.html")
SHOW_DAYS = 11

INDUSTRY = {
    "01": "水泥", "02": "食品", "03": "塑膠", "04": "紡織纖維", "05": "電機機械", "06": "電器電纜",
    "08": "玻璃陶瓷", "09": "造紙", "10": "鋼鐵", "11": "橡膠", "12": "汽車", "14": "建材營造",
    "15": "航運", "16": "觀光餐旅", "17": "金融保險", "18": "貿易百貨", "19": "綜合", "20": "其他",
    "21": "化學", "22": "生技醫療", "23": "油電燃氣", "24": "半導體", "25": "電腦週邊",
    "26": "光電", "27": "通信網路", "28": "電子零組件", "29": "電子通路", "30": "資訊服務",
    "31": "其他電子", "32": "文化創意", "33": "農業科技", "34": "電子商務", "35": "綠能環保",
    "36": "數位雲端", "37": "運動休閒", "38": "居家生活", "91": "存託憑證",
}


def industries():
    """上市/上櫃公司基本資料的產業別,快取 7 天。若離線則使用既有快取。"""
    path = os.path.join(CACHE, "industry.json")
    existing = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            existing = json.load(f)
        if time.time() - os.path.getmtime(path) < 7 * 86400 and len(existing) >= 100:
            return existing
    out = dict(existing)
    for url in ("https://openapi.twse.com.tw/v1/opendata/t187ap03_L",
                "https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O"):
        for attempt in range(2):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                rows = json.loads(urllib.request.urlopen(req, timeout=30, context=ssl_context(url)).read().decode("utf-8-sig"))
                for r in rows:
                    code = r.get("公司代號") or r.get("SecuritiesCompanyCode")
                    ind = r.get("產業別") or r.get("SecuritiesIndustryCode")
                    if code and ind:
                        out[code.strip()] = INDUSTRY.get(ind.strip(), "其他")
                break
            except Exception as e:
                print("產業別下載失敗(改用快取):", url, e)
                time.sleep(2)
    if out:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False)
    return out


def reason(p):
    s = [f"三大法人{'買超' if p['instNet'] >= 0 else '賣超'} {abs(p['instNet']):,} 張(外資 {p['foreignNet']:+,}、投信 {p['trustNet']:+,})"]
    if p["trustStreak"] >= 2:
        s.append(f"投信連買 {p['trustStreak']} 日")
    if p["foreignStreak"] >= 2:
        s.append(f"外資連買 {p['foreignStreak']} 日")
    s.append(f"近 5 日法人累計 {p['inst5d']:+,} 張")
    if p.get("bigPct") is not None:
        t = f"千張大戶持股 {p['bigPct']:.2f}%"
        if p.get("bigChg") is not None:
            t += f",較前一週{'增加' if p['bigChg'] >= 0 else '減少'} {abs(p['bigChg']):.2f} 個百分點"
        s.append(t)
    if p["marginChg"]:
        s.append(f"融資{'減少' if p['marginChg'] < 0 else '增加'} {abs(p['marginChg']):,} 張")
    return ";".join(s) + "。"


def build_full_universe_db(latest_doc, ind):
    """從快取建立最新交易日全市場 550+ 檔高流動性個股資料庫(供全市場選股機器、個股 AI 健檢與避雷針使用)。"""
    try:
        tdays = [dt.date.fromisoformat(x) for x in latest_doc["tradingDays"]]  # 新 → 舊
        d0 = tdays[0]
        inst, price = [], []
        for d in tdays:
            p_i = os.path.join(CACHE, f"tpex_3i_{d:%Y%m%d}.json")
            p_t = os.path.join(CACHE, f"twse_t86_{d:%Y%m%d}.json")
            if not (os.path.exists(p_i) and os.path.exists(p_t)):
                return []
            i = dict(tpex_inst(d) or {})
            mk = {c: "上櫃" for c in i}
            tw = twse_inst(d) or {}
            i.update(tw)
            mk.update({c: "上市" for c in tw})
            inst.append((i, mk))
            p = dict(tpex_price(d) or {})
            p.update(twse_price(d) or {})
            price.append(p)
        mg, _ = margins(d0)
        tdcc_date = latest_doc["tdccDate"].replace("-", "")
        prev_tdcc = (latest_doc.get("tdccPrevDate") or "").replace("-", "")
        big_path = os.path.join(CACHE, f"tdcc_{tdcc_date}.json")
        big = json.load(open(big_path, encoding="utf-8")) if os.path.exists(big_path) else {}

        today_inst, market = inst[0]
        rows = []
        for code, r in today_inst.items():
            if not is_common_stock(code) or code not in price[0]:
                continue
            vols = [p[code]["vol"] / 1000 for p in price if code in p]
            avg_vol = sum(vols) / len(vols)
            close = price[0][code]["close"]
            if avg_vol < MIN_AVG_LOTS or close < MIN_PRICE:
                continue
            hist = [inst[k][0].get(code, {}).get("total", 0) / 1000 for k in range(len(tdays))]
            f_hist = [inst[k][0].get(code, {}).get("foreign", 0) for k in range(len(tdays))]
            t_hist = [inst[k][0].get(code, {}).get("trust", 0) for k in range(len(tdays))]
            m = mg.get(code, {})
            diff = price[0][code]["diff"]
            series_closes = [px[code]["close"] if code in px else None for px in reversed(price)]
            b_pct = big.get(code)
            b_chg = None
            if prev_tdcc and b_pct is not None:
                prev_f = os.path.join(CACHE, f"tdcc_{prev_tdcc}_{code}.txt")
                if os.path.exists(prev_f):
                    try:
                        b_chg = round(b_pct - float(open(prev_f).read().strip()), 2)
                    except Exception:
                        pass
            rows.append({
                "code": code, "name": r["name"], "market": market[code],
                "sector": ind.get(code, "其他"),
                "close": close, "chg": round(diff / (close - diff) * 100, 2) if close - diff else 0,
                "chgPct": round(diff / (close - diff) * 100, 2) if close - diff else 0,
                "avgVol": round(avg_vol), "vol": round(price[0][code]["vol"] / 1000),
                "volume": round(price[0][code]["vol"] / 1000),
                "foreign": round(r["foreign"] / 1000), "trust": round(r["trust"] / 1000),
                "dealer": round(r["dealer"] / 1000), "inst": round(r["total"] / 1000),
                "foreignNet": round(r["foreign"] / 1000), "trustNet": round(r["trust"] / 1000),
                "dealerNet": round(r["dealer"] / 1000), "instNet": round(r["total"] / 1000),
                "instHist": [round(x) for x in hist], "inst5d": round(sum(hist)),
                "foreignStreak": streak(f_hist), "trustStreak": streak(t_hist),
                "marginChg": round(m.get("marginChg", 0)), "marginBal": round(m.get("marginBal", 0)),
                "shortChg": round(m.get("shortChg", 0)),
                "bigPct": b_pct, "bigChg": b_chg,
                "series": series_closes,
            })

        # 計算全市場 551 檔的籌碼百分位分數與買賣點
        for mk in MARKETS:
            grp = [x for x in rows if x["market"] == mk]
            r1 = pct_rank([x["instNet"] / x["avgVol"] for x in grp])
            r5 = pct_rank([x["inst5d"] / (x["avgVol"] * LOOKBACK) for x in grp])
            rs = pct_rank([x["foreignStreak"] + x["trustStreak"] * 1.5 for x in grp])
            rm = pct_rank([-x["marginChg"] / x["avgVol"] for x in grp])
            for x, a, b, c, e in zip(grp, r1, r5, rs, rm):
                chg_b = x["bigChg"] if x["bigChg"] is not None else 0
                big_pt = round(max(0, min(1, (chg_b + 1) / 2)) * WEIGHTS["big"], 1)
                x["parts"] = {
                    "inst1": round(a * WEIGHTS["inst1"], 1),
                    "inst5": round(b * WEIGHTS["inst5"], 1),
                    "streak": round(c * WEIGHTS["streak"], 1),
                    "margin": round(e * WEIGHTS["margin"], 1),
                    "big": big_pt,
                }
                x["rawScore"] = round(sum(x["parts"].values()), 1)
                x["score"] = round(x["rawScore"])
                ai_info = compute_ai_insight(x)
                if x["instNet"] < 0 and x["inst5d"] < 0:
                    x["aiGrade"] = "D (避開)"
                    x["aiSignal"] = "法人提款・反彈減碼"
                elif x["instNet"] < 0:
                    x["aiGrade"] = "C (觀望)"
                    x["aiSignal"] = "短線調節・守撐觀察"
                else:
                    x["aiGrade"] = ai_info["aiGrade"]
                    x["aiSignal"] = ai_info["aiSignal"]
                x["tradePlan"] = ai_info["tradePlan"]
                x["reason"] = reason(x)
        return sorted(rows, key=lambda x: -x["rawScore"])
    except Exception as e:
        print("建立全市場資料庫略過:", e)
        return []


def build_historical_backtest(docs, ind):
    """計算歷史推薦股(10/05 ~ 10/19)在推薦後的實際價格追蹤表現與勝率回測。"""
    # 建立每日收盤價查詢表: close_map[date][code] = close
    close_map = {}
    for d in docs:
        dt_str = d["date"]
        close_map.setdefault(dt_str, {})
        for p in d.get("picks", []):
            close_map[dt_str][p["code"]] = p["close"]
        for mk in ("上市", "上櫃"):
            for k in ("turnover", "volumeRank"):
                for x in d.get(k, {}).get(mk, []):
                    close_map[dt_str][x["code"]] = x["close"]
        for side in ("long", "short"):
            for x in d.get("dayTrade", {}).get(side, []):
                close_map[dt_str][x["code"]] = x["close"]

    # 從 cache 補充近 5 日完整收盤價
    for p in glob.glob(os.path.join(CACHE, "twse_price_*.json")):
        m = re.search(r"_(\d{8})\.json$", p)
        if m:
            ymd = m.group(1)
            dt_str = f"{ymd[:4]}-{ymd[4:6]}-{ymd[6:]}"
            d_obj = dt.date(int(ymd[:4]), int(ymd[4:6]), int(ymd[6:]))
            for code, v in (twse_price(d_obj) or {}).items():
                if v.get("close"):
                    close_map.setdefault(dt_str, {})[code] = v["close"]
    for p in glob.glob(os.path.join(CACHE, "tpex_price_*.json")):
        m = re.search(r"_(\d{8})\.json$", p)
        if m:
            ymd = m.group(1)
            dt_str = f"{ymd[:4]}-{ymd[4:6]}-{ymd[6:]}"
            d_obj = dt.date(int(ymd[:4]), int(ymd[4:6]), int(ymd[6:]))
            for code, v in (tpex_price(d_obj) or {}).items():
                if v.get("close"):
                    close_map.setdefault(dt_str, {})[code] = v["close"]

    all_dates_asc = sorted(close_map.keys())
    records = []
    # 只回測至少有 1 個後續交易日可驗證的推薦日
    for d in reversed(docs[1:]):
        rec_date = d["date"]
        future_dates = [dt_s for dt_s in all_dates_asc if dt_s > rec_date]
        if not future_dates:
            continue
        for p in d.get("picks", []):
            c = p["code"]
            entry_p = p["close"]
            if not entry_p:
                continue
            f_closes = [(fd, close_map[fd][c]) for fd in future_dates if c in close_map.get(fd, {}) and close_map[fd][c] > 0]
            if not f_closes:
                continue
            max_date, max_close = max(f_closes, key=lambda item: item[1])
            latest_date, latest_close = f_closes[-1]
            max_ret = round((max_close - entry_p) / entry_p * 100, 2)
            latest_ret = round((latest_close - entry_p) / entry_p * 100, 2)
            records.append({
                "recDate": rec_date,
                "code": c,
                "name": p["name"],
                "market": p["market"],
                "sector": ind.get(c, "其他"),
                "rank": p["rank"],
                "score": round(p["score"], 1),
                "aiGrade": p.get("aiGrade", "A"),
                "entryClose": entry_p,
                "maxDate": max_date,
                "maxClose": max_close,
                "maxReturnPct": max_ret,
                "latestClose": latest_close,
                "latestReturnPct": latest_ret,
                "holdDays": len(f_closes),
            })

    if not records:
        return {"totalTracked": 0, "winRate": 0, "avgMaxReturn": 0, "sPlusWinRate": 0, "topWinners": []}

    wins = [r for r in records if r["maxReturnPct"] > 0]
    s_plus_recs = [r for r in records if r["score"] >= 85 or r["aiGrade"] == "S+"]
    s_plus_wins = [r for r in s_plus_recs if r["maxReturnPct"] > 0]

    # 去重取每檔最佳波段代表作前 20 名
    best_by_code = {}
    for r in sorted(records, key=lambda x: -x["maxReturnPct"]):
        if r["code"] not in best_by_code:
            best_by_code[r["code"]] = r
    top_winners = sorted(best_by_code.values(), key=lambda x: -x["maxReturnPct"])[:20]

    return {
        "totalTracked": len(records),
        "winRate": round(len(wins) / len(records) * 100, 1),
        "avgMaxReturn": round(sum(r["maxReturnPct"] for r in records) / len(records), 2),
        "sPlusWinRate": round(len(s_plus_wins) / len(s_plus_recs) * 100, 1) if s_plus_recs else 0,
        "topWinners": top_winners,
    }


def build_cross_day_anomalies(doc_idx, docs, picks, day_trade, ind):
    """與前幾個交易日對比，產生跨日大數據異常偵測報告。"""
    doc = docs[doc_idx]
    prev_doc = docs[doc_idx + 1] if doc_idx + 1 < len(docs) else None
    prev_date = prev_doc["date"] if prev_doc else None
    prev_picks_map = {x["code"]: x for x in (prev_doc.get("picks", []) if prev_doc else [])}

    consecutive = []
    for p in picks:
        c = p["code"]
        s_days = 1
        rank_hist = [f"{doc['date'][5:]}:#{p['rank']}"]
        for k in range(doc_idx + 1, len(docs)):
            found = next((x for x in docs[k].get("picks", []) if x["code"] == c), None)
            if found:
                s_days += 1
                rank_hist.append(f"{docs[k]['date'][5:]}:#{found['rank']}")
            else:
                break
        if s_days >= 3:
            consecutive.append({
                "code": c, "name": p["name"], "market": p["market"], "sector": p["sector"],
                "rank": p["rank"], "score": p["rawScore"], "close": p["close"], "chg": p["chg"],
                "streakDays": s_days, "rankHistory": " ← ".join(rank_hist[:5]),
                "inst5d": p["inst5d"], "bigChg": p["bigChg"],
                "buyZone": p["tradePlan"]["buyZone"], "sellTarget1": p["tradePlan"]["sellTarget1"], "stopLoss": p["tradePlan"]["stopLoss"],
            })
    consecutive.sort(key=lambda x: (-x["streakDays"], -x["score"]))

    new_surge = []
    for p in picks:
        prev_p = prev_picks_map.get(p["code"])
        if prev_p is None and p["rank"] <= 6:
            new_surge.append({
                "code": p["code"], "name": p["name"], "market": p["market"], "sector": p["sector"],
                "rank": p["rank"], "score": p["rawScore"], "close": p["close"], "chg": p["chg"],
                "inst": p["inst"], "bigChg": p["bigChg"],
                "tag": f"昨日未上榜 → 今日空降 {p['market']} #{p['rank']}",
                "buyZone": p["tradePlan"]["buyZone"], "sellTarget1": p["tradePlan"]["sellTarget1"], "stopLoss": p["tradePlan"]["stopLoss"],
            })
        elif prev_p is not None and prev_p["rank"] - p["rank"] >= 5:
            jump = prev_p["rank"] - p["rank"]
            new_surge.append({
                "code": p["code"], "name": p["name"], "market": p["market"], "sector": p["sector"],
                "rank": p["rank"], "score": p["rawScore"], "close": p["close"], "chg": p["chg"],
                "inst": p["inst"], "bigChg": p["bigChg"],
                "tag": f"排名急竄 ↑{jump} 名 (#{prev_p['rank']} → #{p['rank']})",
                "buyZone": p["tradePlan"]["buyZone"], "sellTarget1": p["tradePlan"]["sellTarget1"], "stopLoss": p["tradePlan"]["stopLoss"],
            })

    inst_reversal = []
    for p in picks:
        hist = p.get("instHist") or []
        if len(hist) >= 2 and hist[1] < 0 and p["inst"] >= max(200, p["avgVol"] * 0.15):
            inst_reversal.append({
                "code": p["code"], "name": p["name"], "market": p["market"], "sector": p["sector"],
                "rank": p["rank"], "close": p["close"], "chg": p["chg"],
                "prevInst": hist[1], "todayInst": p["inst"],
                "note": f"前日法人賣超 {hist[1]:+,} 張 → 今日突然反手狂買 {p['inst']:+,} 張",
                "buyZone": p["tradePlan"]["buyZone"], "sellTarget1": p["tradePlan"]["sellTarget1"], "stopLoss": p["tradePlan"]["stopLoss"],
            })

    divergence_buy = []
    for p in picks:
        if p["chg"] < 0 and p["inst"] > 0 and (p.get("marginChg", 0) < 0 or (p.get("bigChg") or 0) > 0):
            divergence_buy.append({
                "code": p["code"], "name": p["name"], "market": p["market"], "sector": p["sector"],
                "rank": p["rank"], "close": p["close"], "chg": p["chg"],
                "inst": p["inst"], "bigChg": p["bigChg"], "marginChg": p["marginChg"],
                "note": f"股價逆勢跌 {p['chg']:+.2f}%，但法人買超 +{p['inst']:,} 張、融資 {p['marginChg']:+,} 張（壓低洗盤吃貨）",
                "buyZone": p["tradePlan"]["buyZone"], "sellTarget1": p["tradePlan"]["sellTarget1"], "stopLoss": p["tradePlan"]["stopLoss"],
            })

    dropped_alerts = []
    if prev_doc:
        curr_codes = {x["code"] for x in picks}
        for old_p in sorted(prev_doc.get("picks", []), key=lambda x: x["rank"]):
            if old_p["code"] not in curr_codes and old_p["rank"] <= 8:
                dropped_alerts.append({
                    "code": old_p["code"], "name": old_p["name"], "market": old_p["market"],
                    "sector": ind.get(old_p["code"], "其他"),
                    "prevRank": old_p["rank"], "prevScore": old_p["score"], "prevClose": old_p["close"],
                    "note": f"前日({prev_date[5:]})位居 {old_p['market']} #{old_p['rank']}({old_p['score']}分)，今日跌出推薦榜（法人買盤降溫或轉賣，宜留意 5MA 停利防守）",
                })

    short_traps = []
    for x in day_trade.get("short", [])[:8]:
        if x.get("surge", 0) >= 2.2 and x.get("chgPct", 0) >= 3.0 and x.get("instNet", 0) <= 0:
            short_traps.append({
                "code": x["code"], "name": x["name"], "market": x["market"], "sector": x["sector"],
                "close": x["close"], "chgPct": x["chgPct"], "surge": x["surge"],
                "dtRatio": x["dtRatio"], "instNet": x["instNet"],
                "dtPlan": x["dtPlan"],
                "note": f"急漲 {x['chgPct']:+.2f}% 且爆量 {x['surge']:.1f} 倍(當沖比 {x['dtRatio']:.1f}%)，但三大法人賣超 {abs(x['instNet']):,} 張（短線隔日沖主力拉高，明早易有獲利倒貨賣壓）",
            })

    sec_now, sec_prev = {}, {}
    for p in picks:
        sec_now[p["sector"]] = sec_now.get(p["sector"], 0) + 1
    if prev_doc:
        for p in prev_doc.get("picks", []):
            s = ind.get(p["code"], "其他")
            sec_prev[s] = sec_prev.get(s, 0) + 1
    all_secs = set(sec_now) | set(sec_prev)
    sec_shift = []
    for s in all_secs:
        n_now, n_prev = sec_now.get(s, 0), sec_prev.get(s, 0)
        diff = n_now - n_prev
        if n_now >= 2 or abs(diff) >= 2:
            sec_shift.append({"sector": s, "today": n_now, "prev": n_prev, "diff": diff})
    sec_shift.sort(key=lambda x: (-x["diff"], -x["today"]))

    return {
        "prevDate": prev_date,
        "consecutivePicks": consecutive[:8],
        "newSurgePicks": new_surge[:8],
        "instReversalPicks": inst_reversal[:8],
        "divergenceBuyPicks": divergence_buy[:8],
        "droppedAlerts": dropped_alerts[:8],
        "shortTrapAlerts": short_traps[:6],
        "sectorShift": sec_shift[:8],
    }


def build_ai_overview(doc, picks, cross_anom):
    """產生單日 AI 盤後選股總覽摘要與關鍵指標。"""
    dual_buy = [p for p in picks if p["foreign"] > 0 and p["trust"] > 0]
    big_up = [p for p in picks if p.get("bigChg") is not None and p["bigChg"] >= 0.4]
    margin_down = [p for p in picks if p.get("marginChg", 0) < 0]
    s_plus = [p for p in picks if p.get("aiGrade") == "S+"]

    sec_count = {}
    for p in picks:
        sec_count[p["sector"]] = sec_count.get(p["sector"], 0) + 1
    top_secs = sorted(sec_count.items(), key=lambda x: -x[1])[:4]
    sec_str = "、".join(f"{k}({v}檔)" for k, v in top_secs)

    idx_map = {x["name"]: x for x in doc.get("indices", [])}
    taiex = idx_map.get("加權指數")
    tpex = idx_map.get("櫃買指數")
    idx_txt = []
    if taiex:
        idx_txt.append(f"加權指數收 {taiex['close']:,.2f} ({taiex['chgPct']:+.2f}%)")
    if tpex:
        idx_txt.append(f"櫃買指數收 {tpex['close']:,.2f} ({tpex['chgPct']:+.2f}%)")

    twse_top = [p for p in picks if p["market"] == "上市"][:3]
    otc_top = [p for p in picks if p["market"] == "上櫃"][:3]
    twse_names = "、".join(f"{p['name']}({p['code']} 買點:{p['tradePlan']['buyZone']})" for p in twse_top)
    otc_names = "、".join(f"{p['name']}({p['code']} 買點:{p['tradePlan']['buyZone']})" for p in otc_top)

    consec_names = "、".join(f"{x['name']}({x['code']}連霸{x['streakDays']}日)" for x in cross_anom["consecutivePicks"][:4])
    rev_count = len(cross_anom["instReversalPicks"])
    div_count = len(cross_anom["divergenceBuyPicks"])

    headline = (
        f"AI 盤後多因子模型從 {doc.get('universe', 0):,} 檔合格個股中篩選出上市 20 檔、上櫃 20 檔。"
        f"{'；'.join(idx_txt)}。本日資金最集中族群為：{sec_str}。"
        f"全場共 {len(s_plus)} 檔獲評 AI「S+ 強勢共識」、{len(dual_buy)} 檔「土洋合買」、"
        f"{rev_count} 檔出現「法人由賣轉買大反轉」、{div_count} 檔呈現「價跌法人逆勢吃貨背離」。"
        f"跨日連續霸榜鎖碼股：{consec_names or '無'}。"
        f"上市首選：{twse_names}；上櫃首選：{otc_names}。"
    )
    return {
        "headline": headline,
        "sPlusCount": len(s_plus),
        "dualBuyCount": len(dual_buy),
        "bigUpCount": len(big_up),
        "marginDownCount": len(margin_down),
        "reversalCount": rev_count,
        "divergenceCount": div_count,
        "consecutiveCount": len(cross_anom["consecutivePicks"]),
        "topSectors": [{"name": k, "count": v} for k, v in top_secs],
    }


def main():
    ind = industries()
    docs = []
    paths = sorted(glob.glob(os.path.join(BASE, "out", "day_*.json")), reverse=True)[:SHOW_DAYS]
    for path in paths:
        with open(path, encoding="utf-8") as f:
            docs.append(json.load(f))

    days = []
    for doc_idx, doc in enumerate(docs):
        tdays = [dt.date.fromisoformat(x) for x in reversed(doc["tradingDays"])]  # 舊 → 新
        need_fetch_series = any(
            not p.get("series") or sum(1 for v in p.get("series", []) if v is not None) < 2
            for p in doc["picks"]
        )
        prices = []
        if need_fetch_series:
            for d in tdays:
                try:
                    p = dict(tpex_price(d) or {})
                    p.update(twse_price(d) or {})
                except Exception:
                    p = {}
                prices.append(p)

        prev_doc = docs[doc_idx + 1] if doc_idx + 1 < len(docs) else None
        prev_rank_map = {x["code"]: x["rank"] for x in (prev_doc.get("picks", []) if prev_doc else [])}
        idx_map = {x["name"]: x.get("chgPct", 0) for x in doc.get("indices", [])}

        picks = []
        for p in doc["picks"]:
            c = p["code"]
            s_days = 1
            for k in range(doc_idx + 1, len(docs)):
                if any(x["code"] == c for x in docs[k].get("picks", [])):
                    s_days += 1
                else:
                    break

            series = p.get("series")
            if not series or sum(1 for v in series if v is not None) < 2:
                series = [px[c]["close"] if c in px else None for px in prices]
                if not any(series):
                    series = [p["close"]] * len(tdays)
            p["series"] = series

            mkt_chg = idx_map.get("加權指數", 0) if p["market"] == "上市" else idx_map.get("櫃買指數", 0)
            ai_info = compute_ai_insight(p, prev_rank=prev_rank_map.get(c), streak_days=s_days, mkt_chg_pct=mkt_chg)
            p.update(ai_info)

            tags = list(p.get("tags") or [])
            if p.get("foreignNet", 0) > 0 and p.get("trustNet", 0) > 0 and "土洋合買" not in tags:
                tags.insert(0, "土洋合買")
            if not tags:
                tags = ["法人買超"]

            picks.append({
                "rank": p["rank"], "code": c, "name": p["name"], "market": p["market"],
                "sector": ind.get(c, p.get("sector", "其他")),
                "close": p["close"], "chg": p["chgPct"],
                "vol": p["volume"], "avgVol": p.get("avgVol", p["volume"]),
                "foreign": p.get("foreignNet", 0), "trust": p.get("trustNet", 0),
                "dealer": p.get("dealerNet", 0), "inst": p.get("instNet", 0),
                "inst5d": p.get("inst5d", 0), "instHist": p.get("instHist", []),
                "foreignStreak": p.get("foreignStreak", 0), "trustStreak": p.get("trustStreak", 0),
                "bigPct": p.get("bigPct"), "bigChg": p.get("bigChg"),
                "marginChg": p.get("marginChg", 0), "marginBal": p.get("marginBal", 0),
                "shortChg": p.get("shortChg", 0),
                "score": round(p["score"]), "rawScore": round(p["score"], 1),
                "parts": p.get("parts", {}),
                "series": series,
                "tags": tags, "reason": reason(p),
                "prevRank": prev_rank_map.get(c),
                "streakDays": s_days,
                "aiGrade": ai_info["aiGrade"],
                "aiSignal": ai_info["aiSignal"],
                "aiSummary": ai_info["aiSummary"],
                "aiResonance": ai_info["aiResonance"],
                "tradePlan": ai_info["tradePlan"],
                "anomalies": ai_info["anomalies"],
            })

        dt_out = {}
        for side in ("long", "short"):
            dt_out[side] = []
            for x in doc.get("dayTrade", {}).get(side, []):
                dt_plan = compute_daytrade_plan(x, side)
                x["dtPlan"] = dt_plan
                dt_out[side].append(dict(x, sector=ind.get(x["code"], "其他"), dtPlan=dt_plan))

        cross_anom = build_cross_day_anomalies(doc_idx, docs, picks, dt_out, ind)
        ai_overview = build_ai_overview(doc, picks, cross_anom)

        doc["crossDayAnomalies"] = cross_anom
        with open(paths[doc_idx], "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=1)

        pick_codes = {p["code"] for p in doc["picks"]}
        days.append({
            "date": doc["date"],
            "seriesDates": [f"{d.month}/{d.day}" for d in tdays],
            "tradingDays": doc.get("tradingDays", []),
            "tdccDate": doc["tdccDate"],
            "tdccPrevDate": doc.get("tdccPrevDate"),
            "generatedAt": doc.get("generatedAt", ""),
            "universe": doc["universe"],
            "universeByMarket": doc.get("universeByMarket", {}),
            "marginPending": doc.get("marginPending", []),
            "aiOverview": ai_overview,
            "crossDayAnomalies": cross_anom,
            "picks": picks,
            "indices": doc.get("indices", []),
            "dayTrade": dt_out,
            **{
                key: [dict(x, sector=ind.get(x["code"], "其他"), inPicks=x["code"] in pick_codes)
                      for mk in ("上市", "上櫃") for x in doc.get(key, {}).get(mk, [])]
                for key in ("turnover", "volumeRank")
            }
        })

    universe_db = build_full_universe_db(docs[0], ind) if docs else []
    backtest_stats = build_historical_backtest(docs, ind) if len(docs) > 1 else {}

    data = {
        "generatedAt": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "days": days,
        "universeDB": universe_db,
        "backtest": backtest_stats,
    }
    data_json = json.dumps(data, ensure_ascii=False)

    with open(os.path.join(BASE, "site_template.html"), encoding="utf-8") as f:
        body = f.read().replace("/*DATA*/null", data_json)
    with open(os.path.join(BASE, "site_publish.html"), "w", encoding="utf-8") as f:
        f.write(body)
    page = ('<!doctype html>\n<html lang="zh-Hant">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            '<link rel="icon" href="images/logo.svg" type="image/svg+xml">\n'
            "<style>body{margin:0}[hidden]{display:none!important}img{max-width:100%}</style>\n"
            f"</head>\n<body>\n{body}\n</body>\n</html>\n")

    targets = [os.path.join(BASE, "index.html")]
    if os.path.isdir(os.path.dirname(SITE)):
        targets.append(SITE)
    for target in targets:
        with open(target, "w", encoding="utf-8") as f:
            f.write(page)
        print("已匯入", [d["date"] for d in days], f"(含全市場 {len(universe_db)} 檔健檢庫與歷史回測) →", os.path.abspath(target))

    radar_path = os.path.join(BASE, "chips_radar.html")
    if os.path.exists(radar_path):
        with open(radar_path, encoding="utf-8") as f:
            r_html = f.read()
        r_html = re.sub(
            r"/\*RADAR_DATA_START\*/.*?/\*RADAR_DATA_END\*/",
            f"/*RADAR_DATA_START*/{json.dumps(docs, ensure_ascii=False)}/*RADAR_DATA_END*/",
            r_html,
            flags=re.S,
        )
        with open(radar_path, "w", encoding="utf-8") as f:
            f.write(r_html)
        print("已同步更新籌碼雷達 →", os.path.abspath(radar_path))


if __name__ == "__main__":
    main()
