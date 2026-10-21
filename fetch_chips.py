"""每日大戶籌碼與全自動 AI 選股:抓取證交所/櫃買中心/集保公開資料,計算籌碼分數、AI 買賣點與跨日異常偵測,輸出上市、上櫃各前 20 名。

用法: python fetch_chips.py [YYYYMMDD]   (不給日期 = 最近一個已有盤後資料的交易日)
輸出: out/day_YYYY-MM-DD.json  (寫入網頁資料庫 days/<date> 的內容)
"""
import datetime as dt
import http.client
import http.cookiejar
import json
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(BASE, "cache")
OUT = os.path.join(BASE, "out")
os.makedirs(CACHE, exist_ok=True)
os.makedirs(OUT, exist_ok=True)

UA = {"User-Agent": "Mozilla/5.0"}
HTTP_RETRIES = 5        # 網路不穩時每個網址最多嘗試的次數
LOOKBACK = 5            # 法人累計與均量的交易日數
MIN_AVG_LOTS = 1000     # 排除小型股:5 日均量至少 1000 張
MIN_PRICE = 10          # 排除低價股
MARKETS = ("上市", "上櫃")
TOP_N = 20              # 上市、上櫃各推薦 20 檔
TDCC_CANDIDATES = 50    # 每個市場只對前 50 名候選股查集保上週資料

# 各指標權重(合計 100)。主力分點沒有免驗證碼的公開來源,權重先設 0。
WEIGHTS = {"inst1": 25, "inst5": 25, "streak": 10, "big": 25, "margin": 15, "broker": 0}


# Windows Python 3.13 環境常缺少台灣政府/TWCA 憑證鏈或受本機防毒 HTTPS 掃描影響導致 CERTIFICATE_VERIFY_FAILED。
# 統一使用不強制驗證本機憑證鏈的 SSL Context，確保證交所、櫃買中心與集保結算所連線穩定。
SSL_CTX = ssl._create_unverified_context()


def ssl_context(url):
    return SSL_CTX


def tick_round(price):
    """依台股升降單位(tick)取整。"""
    if price is None or price <= 0:
        return 0.0
    step = 0.01 if price < 10 else 0.05 if price < 50 else 0.1 if price < 100 else 0.5 if price < 500 else 1.0 if price < 1000 else 5.0
    return round(round(price / step) * step, 2)


def http_get(url, cache_name=None, sleep=0.5):
    if cache_name:
        p = os.path.join(CACHE, cache_name)
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                return f.read()
    req = urllib.request.Request(url, headers=UA)
    for attempt in range(1, HTTP_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=90, context=ssl_context(url)) as r:
                raw = r.read()
            break
        except (urllib.error.URLError, TimeoutError, ConnectionError, http.client.IncompleteRead) as e:
            if attempt == HTTP_RETRIES:
                raise
            wait = 15 * attempt
            print(f"連線失敗({e}),{wait} 秒後重試第 {attempt + 1} 次:{url.split('?')[0]}", flush=True)
            time.sleep(wait)
    text = None
    for enc in ("utf-8-sig", "cp950"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            pass
    time.sleep(sleep)
    return text


def get_json(url, cache_name):
    text = http_get(url)
    j = json.loads(text)
    has_rows = bool(j.get("data")) or any(t.get("data") for t in j.get("tables") or [])
    ok = str(j.get("stat", "")).lower() == "ok" and has_rows
    if ok:
        with open(os.path.join(CACHE, cache_name), "w", encoding="utf-8") as f:
            f.write(text)
    return j if ok else None


CACHE_FINAL_HOUR = 22  # 證交所、櫃買中心盤後資料當天稍晚仍可能更正,資料日 22:00 以後下載的才視為定稿
DAYTRADE_FINAL_HOUR = 8  # 當沖統計更正得更晚(曾在 22:40 後仍有更正),隔天 08:00 以後下載的才視為定稿


def cache_is_final(path, cache_name):
    m = re.search(r"_(\d{8})\.json$", cache_name)
    if not m:
        return True
    day = dt.datetime.strptime(m.group(1), "%Y%m%d")
    if "daytrade" in cache_name:
        final_at = day + dt.timedelta(days=1, hours=DAYTRADE_FINAL_HOUR)
    else:
        final_at = day.replace(hour=CACHE_FINAL_HOUR)
    return dt.datetime.fromtimestamp(os.path.getmtime(path)) >= final_at


def cached_json(url, cache_name):
    p = os.path.join(CACHE, cache_name)
    if os.path.exists(p) and cache_is_final(p, cache_name):
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return get_json(url, cache_name)


def num(s):
    s = str(s).replace(",", "").strip()
    try:
        return float(s)
    except ValueError:
        return 0.0


def is_common_stock(code):
    return bool(re.fullmatch(r"[1-9]\d{3}", code))


# ---------- 各資料來源 ----------

def twse_inst(d):
    j = cached_json(f"https://www.twse.com.tw/rwd/zh/fund/T86?date={d:%Y%m%d}&selectType=ALLBUT0999&response=json",
                    f"twse_t86_{d:%Y%m%d}.json")
    if not j:
        return None
    out = {}
    for r in j["data"]:
        code = r[0].strip()
        out[code] = {"name": r[1].strip(), "foreign": num(r[4]) + num(r[7]), "trust": num(r[10]),
                     "dealer": num(r[11]), "total": num(r[18])}
    return out


def tpex_inst(d):
    j = cached_json(f"https://www.tpex.org.tw/www/zh-tw/insti/dailyTrade?type=Daily&sect=EW&date={d:%Y/%m/%d}&response=json",
                    f"tpex_3i_{d:%Y%m%d}.json")
    if not j:
        return None
    out = {}
    for r in j["tables"][0]["data"]:
        code = r[0].strip()
        out[code] = {"name": r[1].strip(), "foreign": num(r[10]), "trust": num(r[13]),
                     "dealer": num(r[22]), "total": num(r[23])}
    return out


def twse_price(d):
    j = cached_json(f"https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date={d:%Y%m%d}&type=ALLBUT0999&response=json",
                    f"twse_price_{d:%Y%m%d}.json")
    if not j:
        return None
    table = next((t for t in j["tables"] if t.get("fields") and t["fields"][0] == "證券代號" and "收盤價" in t["fields"]), None)
    if not table:
        return None
    out = {}
    for r in table["data"]:
        close = num(r[8])
        diff = num(r[10]) * (-1 if "-" in r[9] else 1)
        out[r[0].strip()] = {"name": r[1].strip(), "vol": num(r[2]), "value": num(r[4]), "close": close, "diff": diff,
                             "open": num(r[5]), "high": num(r[6]), "low": num(r[7])}
    return out


def tpex_price(d):
    j = cached_json(f"https://www.tpex.org.tw/www/zh-tw/afterTrading/otc?date={d:%Y/%m/%d}&type=EW&response=json",
                    f"tpex_price_{d:%Y%m%d}.json")
    if not j:
        return None
    out = {}
    for r in j["tables"][0]["data"]:
        out[r[0].strip()] = {"name": r[1].strip(), "vol": num(r[7]), "value": num(r[8]), "close": num(r[2]),
                             "diff": num(r[3]), "shares": num(r[14]),
                             "open": num(r[4]), "high": num(r[5]), "low": num(r[6])}
    return out


def twse_shares():
    """上市公司已發行普通股數(證交所公司基本資料),快取 7 天。"""
    path = os.path.join(CACHE, "twse_shares.json")
    if os.path.exists(path) and time.time() - os.path.getmtime(path) < 7 * 86400:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    rows = json.loads(http_get("https://openapi.twse.com.tw/v1/opendata/t187ap03_L", sleep=1))
    out = {r["公司代號"].strip(): num(r.get("已發行普通股數或TDR原股發行股數", 0)) for r in rows if r.get("公司代號")}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f)
    return out


# 首頁要顯示的指數:(顯示名稱, 證交所指數名稱);證交所沒有「運輸類」,以航運類指數代表
TWSE_INDICES = [("加權指數", "發行量加權股價指數"), ("航運", "航運類指數"), ("電子", "電子工業類指數"),
                ("塑化", "塑膠化工類指數"), ("紡織", "紡織纖維類指數"), ("生技", "生技醫療類指數"), ("鋼鐵", "鋼鐵類指數"), ("造紙", "造紙類指數")]


def market_indices(d):
    """當日收盤指數:加權指數、櫃買指數與幾個類股指數。回傳 [{name, close, chg, chgPct}, ...]。"""
    out = {}
    j = cached_json(f"https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date={d:%Y%m%d}&type=ALLBUT0999&response=json",
                    f"twse_price_{d:%Y%m%d}.json")
    if j:
        idx = next((t for t in j["tables"] if t.get("fields") and t["fields"][0] == "指數"), {"data": []})
        rows = {r[0].strip(): r for r in idx["data"]}
        for short, full in TWSE_INDICES:
            r = rows.get(full)
            if r:
                sign = -1 if "green" in r[2] or "-" in r[2] else 1
                out[short] = {"name": short, "close": num(r[1]), "chg": round(sign * num(r[3]), 2), "chgPct": num(r[4])}
    j = cached_json(f"https://www.tpex.org.tw/www/zh-tw/indexInfo/inx?date={d:%Y/%m/%d}&response=json",
                    f"tpex_inx_{d:%Y%m%d}.json")
    row = next((r for r in (j or {}).get("tables", [{}])[0].get("data", []) if r[0] == f"{d:%Y/%m/%d}"), None)
    if row:
        close, chg = num(row[4]), num(row[5])
        out["櫃買指數"] = {"name": "櫃買指數", "close": close, "chg": chg,
                       "chgPct": round(chg / (close - chg) * 100, 2) if close - chg else 0}
    order = ["加權指數", "櫃買指數", "航運", "電子", "塑化", "紡織", "生技", "鋼鐵", "造紙"]
    return [out[k] for k in order if k in out]


def daily_stock_rows(d):
    """當日上市、上櫃每檔普通股的行情與週轉率(成交股數 ÷ 已發行股數):{市場: [列, ...]}。"""
    result = {}
    for mk, prices, shares in (("上市", twse_price(d) or {}, twse_shares()),
                               ("上櫃", tpex_price(d) or {}, None)):
        rows = []
        for code, p in prices.items():
            sh = p.get("shares") if shares is None else shares.get(code)
            if not is_common_stock(code) or not p["vol"] or not p["close"]:
                continue
            prev = p["close"] - p["diff"]
            rows.append({"code": code, "name": p["name"], "market": mk, "close": p["close"],
                         "chgPct": round(p["diff"] / prev * 100, 2) if prev else 0,
                         "volume": round(p["vol"] / 1000), "value": round(p["value"] / 1e8, 2),
                         "turnover": round(p["vol"] / sh * 100, 2) if sh else None})
        result[mk] = rows
    return result


def daytrade_list(d):
    """證交所、櫃買中心「當日沖銷交易標的」:{代號: {"dtVol": 當沖成交股數, "noShortFirst": 暫停先賣後買}}。"""
    out = {}
    j = cached_json(f"https://www.twse.com.tw/rwd/zh/dayTrading/TWTB4U?date={d:%Y%m%d}&selectType=All&response=json",
                    f"twse_daytrade_{d:%Y%m%d}.json")
    for t in (j or {}).get("tables", []):
        if t.get("fields") and t["fields"][0] == "證券代號":
            for r in t["data"]:
                out[r[0].strip()] = {"dtVol": num(r[3]), "noShortFirst": r[2].strip() == "Y"}
    j = cached_json(f"https://www.tpex.org.tw/www/zh-tw/intraday/stat?type=Daily&date={d:%Y/%m/%d}&response=json",
                    f"tpex_daytrade_{d:%Y%m%d}.json")
    for t in (j or {}).get("tables", []):
        if t.get("fields") and t["fields"][0] == "證券代號":
            for r in t["data"]:
                out[r[0].strip()] = {"dtVol": num(r[3]), "noShortFirst": r[2].strip() == "Y"}
    return out


DT_MIN_LOTS = 2000   # 當沖標的至少要有的當日成交量(張),太冷門的進出不易
DT_WEIGHTS = {
    "long": {"chg": 20, "pos": 15, "inst": 20, "surge": 15, "turnover": 20, "dt": 10},
    "short": {"chg": 20, "pos": 10, "inst": 20, "surge": 20, "turnover": 20, "dt": 10},
}


def compute_daytrade_plan(x, side):
    """為當沖做多/做空個股計算 AI 隔日當沖買點、賣點(停利)與停損出場價。"""
    c = x["close"]
    thesis = x.get("thesis", "強勢續攻" if side == "long" else "隔日沖賣壓")
    if side == "long":
        entry_low = tick_round(c * 0.992)
        entry_high = tick_round(c * 1.005)
        breakout = tick_round(c * 1.015)
        tp1 = tick_round(c * 1.025)
        tp2 = tick_round(c * 1.045)
        sl = tick_round(c * 0.985)
        plan = {
            "direction": "做多(先買後賣)",
            "entryZone": f"{entry_low} ～ {entry_high}",
            "breakoutEntry": breakout,
            "target1": tp1,
            "target2": tp2,
            "stopLoss": sl,
            "aiGuide": (
                f"【當沖做多買賣點】① 買點：早盤回測守穩 {entry_low}～{entry_high} 低接，或 09:15 後帶量站上均價線(VWAP)突破 {breakout} 順勢買進；"
                f"② 停利賣點：急拉達 {tp1}(+2.5%) 先平倉一半，衝高 {tp2}(+4.5%) 全數獲利了結；"
                f"③ 停損賣點：跌破均價線且失守 {sl}(-1.5%) 立即停損出場，13:15 前強制平倉不留倉。"
            ),
        }
    elif thesis == "隔日沖賣壓":
        entry_low = tick_round(c * 1.01)
        entry_high = tick_round(c * 1.03)
        weak_entry = tick_round(c * 0.995)
        tp1 = tick_round(c * 0.98)
        tp2 = tick_round(c * 0.96)
        sl = tick_round(c * 1.045)
        plan = {
            "direction": "做空(先賣後買・隔日沖獲利賣壓)",
            "entryZone": f"{entry_low} ～ {entry_high}",
            "breakoutEntry": weak_entry,
            "target1": tp1,
            "target2": tp2,
            "stopLoss": sl,
            "aiGuide": (
                f"【當沖做空買賣點】① 先賣空點：今日大漲但法人沒買，隔日早盤開高衝至 {entry_low}～{entry_high} 爆量不漲且跌破均價線(VWAP)時先賣，或開平直接跌破昨收 {weak_entry} 順勢放空；"
                f"② 停利回補買點：隔日沖賣壓湧現跌至 {tp1}(-2%) 先回補一半，急殺至 {tp2}(-4%) 全數買回；"
                f"③ 停損回補買點：若強勢軋空突破 {sl}(+4.5%) 立即買回停損，嚴禁被鎖漲停。"
            ),
        }
    else:
        entry_low = tick_round(c * 0.995)
        entry_high = tick_round(c * 1.01)
        weak_entry = tick_round(c * 0.99)
        tp1 = tick_round(c * 0.975)
        tp2 = tick_round(c * 0.955)
        sl = tick_round(c * 1.02)
        plan = {
            "direction": "做空(先賣後買・弱勢續跌)",
            "entryZone": f"{entry_low} ～ {entry_high}",
            "breakoutEntry": weak_entry,
            "target1": tp1,
            "target2": tp2,
            "stopLoss": sl,
            "aiGuide": (
                f"【當沖做空買賣點】① 先賣空點：今日收低且法人賣超，隔日早盤反彈至 {entry_low}～{entry_high} 遇均價線反壓不過時先賣，或開低跌破 {weak_entry} 順勢追空；"
                f"② 停利回補買點：續跌達 {tp1}(-2.5%) 先回補一半，急殺 {tp2}(-4.5%) 全數買回；"
                f"③ 停損回補買點：帶量站回 {sl}(+2%) 之上立即停損回補。"
            ),
        }
    return plan


def daytrade_candidates(days, n=20):
    """依交易日 days(新到舊)的最後一天資料,挑出當沖做多、做空各 n 檔(上市櫃合併排名)。"""
    d0 = days[0]
    today = daily_stock_rows(d0)
    prices = [dict(tpex_price(d) or {}, **(twse_price(d) or {})) for d in days]
    inst = dict(tpex_inst(d0) or {}, **(twse_inst(d0) or {}))
    dt_list = daytrade_list(d0)
    rows = []
    for mk, lst in today.items():
        for x in lst:
            c, p = x["code"], prices[0].get(x["code"], {})
            prev_vols = [px[c]["vol"] / 1000 for px in prices[1:] if c in px and px[c]["vol"]]
            if c not in dt_list or x["volume"] < DT_MIN_LOTS or x["close"] < MIN_PRICE or x["turnover"] is None or not prev_vols:
                continue
            hi, lo = p.get("high", 0), p.get("low", 0)
            inst_net = round(inst.get(c, {}).get("total", 0) / 1000)
            rows.append(dict(x,
                             dtRatio=round(dt_list[c]["dtVol"] / 1000 / x["volume"] * 100, 1),
                             surge=round(x["volume"] / (sum(prev_vols) / len(prev_vols)), 2),
                             pos=round((x["close"] - lo) / (hi - lo), 2) if hi > lo else 1.0,
                             instNet=inst_net, instRatio=inst_net / x["volume"],
                             shortable=not dt_list[c]["noShortFirst"]))
    ranks = {k: pct_rank([x[f] for x in rows]) for k, f in
             (("chg", "chgPct"), ("pos", "pos"), ("inst", "instRatio"), ("surge", "surge"), ("turnover", "turnover"), ("dt", "dtRatio"))}
    for i, x in enumerate(rows):
        r = {k: v[i] for k, v in ranks.items()}
        wl, ws = DT_WEIGHTS["long"], DT_WEIGHTS["short"]
        x["longScore"] = round(sum(r[k] * w for k, w in wl.items()), 1)
        x["shortScore"] = round(sum((1 - r[k] if k == "inst" else r[k]) * w for k, w in ws.items()), 1)
        x["nextDaySell"] = x["chgPct"] >= 5 and x["surge"] >= 2 and x["pos"] >= 0.8 and x["instNet"] <= 0

    def tags(x, side):
        t = []
        if x.get("thesis") == "弱勢續跌": t.append("弱勢續跌")
        if x["chgPct"] >= 9.5: t.append("漲停")
        if x["chgPct"] <= -9.5: t.append("跌停")
        if x["nextDaySell"]: t.append("隔日沖賣壓")
        if x["surge"] >= 2: t.append(f"爆量 {x['surge']:.1f} 倍")
        if x["turnover"] >= 10: t.append("高週轉")
        if x["dtRatio"] >= 40: t.append("當沖熱")
        if side == "long" and x["pos"] >= 0.95: t.append("收最高")
        if side == "short" and x.get("thesis") == "弱勢續跌" and x["pos"] <= 0.05: t.append("收最低")
        if side == "long" and x["instNet"] > 0: t.append("法人買超")
        if side == "short" and x["instNet"] < 0: t.append("法人賣超")
        return t

    def reason(x, side):
        s = [f"漲跌 {x['chgPct']:+.2f}%,收盤位於當日區間 {x['pos'] * 100:.0f}%",
             f"成交量為前 4 日均量的 {x['surge']:.1f} 倍,週轉率 {x['turnover']:.2f}%,當沖比率 {x['dtRatio']:.1f}%",
             f"三大法人{'買超' if x['instNet'] >= 0 else '賣超'} {abs(x['instNet']):,} 張"]
        return ";".join(s) + "。"

    keep = ["code", "name", "market", "close", "chgPct", "volume", "value", "turnover", "dtRatio", "surge", "pos", "instNet", "shortable"]
    long_pool = [x for x in rows if x["chgPct"] > 0 and x["instNet"] > 0]
    short_pool = [x for x in rows if x["chgPct"] > 0 and x["instNet"] <= 0 and x["shortable"]]
    for i, x in enumerate(rows):
        r = {k: v[i] for k, v in ranks.items()}
        x["weakScore"] = round(sum((1 - r[k] if k in ("chg", "pos", "inst") else r[k]) * w
                                   for k, w in DT_WEIGHTS["long"].items()), 1)
    weak_pool = [x for x in rows if x["chgPct"] < 0 and x["instNet"] < 0 and x["shortable"]]
    out = {}
    picks = {"long": [(x, x["longScore"], "強勢續攻") for x in sorted(long_pool, key=lambda x: -x["longScore"])[:n]]}
    shorts = [(x, x["shortScore"], "隔日沖賣壓") for x in sorted(short_pool, key=lambda x: -x["shortScore"])[:n]]
    if len(shorts) < n:
        shorts += [(x, x["weakScore"], "弱勢續跌") for x in sorted(weak_pool, key=lambda x: -x["weakScore"])[:n - len(shorts)]]
    picks["short"] = shorts
    for side, lst in picks.items():
        out[side] = []
        for i, (x, score, thesis) in enumerate(lst, 1):
            x["thesis"] = thesis
            dt_plan = compute_daytrade_plan(x, side)
            out[side].append(dict({k: x[k] for k in keep}, rank=i, score=score, thesis=thesis,
                                  tags=tags(x, side), reason=reason(x, side), dtPlan=dt_plan))
    out["universe"] = len(rows)
    return out


def rank_by(rows_by_market, key, n=20):
    """依 key 由大到小排名,上市、上櫃各取前 n 名(key 為 None 的不列入)。"""
    result = {}
    for mk, rows in rows_by_market.items():
        top = sorted((x for x in rows if x[key] is not None), key=lambda x: -x[key])[:n]
        result[mk] = [dict(x, rank=i) for i, x in enumerate(top, 1)]
    return result


def margins(d):
    """回傳 (融資融券資料, 尚未公布的市場集合)。融資融券約晚上 9 點半才公布。"""
    out, missing = {}, set()
    j = cached_json(f"https://www.twse.com.tw/rwd/zh/marginTrading/MI_MARGN?date={d:%Y%m%d}&selectType=ALL&response=json",
                    f"twse_margin_{d:%Y%m%d}.json")
    if j:
        for r in j["tables"][1]["data"]:
            out[r[0].strip()] = {"marginChg": num(r[6]) - num(r[5]), "marginBal": num(r[6]),
                                 "shortChg": num(r[12]) - num(r[11])}
    else:
        missing.add("上市")
    j = cached_json(f"https://www.tpex.org.tw/www/zh-tw/margin/balance?date={d:%Y/%m/%d}&response=json",
                    f"tpex_margin_{d:%Y%m%d}.json")
    if j:
        for r in j["tables"][0]["data"]:
            out[r[0].strip()] = {"marginChg": num(r[6]) - num(r[2]), "marginBal": num(r[6]),
                                 "shortChg": num(r[14]) - num(r[10])}
    else:
        missing.add("上櫃")
    return out, missing


def tdcc_latest():
    """集保戶股權分散表(最新一週):回傳 (資料日, {代號: 千張大戶持股%})。"""
    text = http_get("https://opendata.tdcc.com.tw/getOD.ashx?id=1-5", sleep=1)
    out, date = {}, None
    for line in text.splitlines()[1:]:
        p = line.split(",")
        if len(p) < 6:
            continue
        date = p[0]
        if p[2] == "15":   # 第 15 級 = 1,000,001 股以上 = 千張大戶
            out[p[1].strip()] = float(p[5])
    with open(os.path.join(CACHE, f"tdcc_{date}.json"), "w", encoding="utf-8") as f:
        json.dump(out, f)
    return date, out


def tdcc_for(d0):
    """取資料日期不晚於交易日 d0 的集保週資料,避免重算舊日期時用到之後才有的資料。"""
    date, out = tdcc_latest()
    target = f"{d0:%Y%m%d}"
    if date <= target:
        return date, out
    older = sorted(n[5:13] for n in os.listdir(CACHE)
                   if re.fullmatch(r"tdcc_\d{8}\.json", n) and n[5:13] <= target)
    if not older:
        print(f"警告:找不到 {target} 以前的集保週資料,改用最新一週 {date}")
        return date, out
    with open(os.path.join(CACHE, f"tdcc_{older[-1]}.json"), encoding="utf-8") as f:
        return older[-1], json.load(f)


class TdccHistory:
    """集保網站「股權分散表查詢」,查單一股票指定週的千張大戶比例。"""
    URL = "https://www.tdcc.com.tw/portal/zh/smWeb/qryStock"

    def __init__(self):
        cj = http.cookiejar.CookieJar()
        self.op = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(cj),
            urllib.request.HTTPSHandler(context=SSL_CTX),
        )
        self.op.addheaders = list(UA.items())
        self.dates = None

    def _form(self):
        html = self.op.open(self.URL, timeout=60).read().decode("utf-8")
        self.dates = re.findall(r'<option value="(\d{8})"', html)
        return re.search(r'name="SYNCHRONIZER_TOKEN" value="([^"]+)"', html).group(1)

    def big_pct(self, code, date):
        cache = os.path.join(CACHE, f"tdcc_{date}_{code}.txt")
        if os.path.exists(cache):
            with open(cache) as f:
                return float(f.read())
        tok = self._form()
        data = {"SYNCHRONIZER_TOKEN": tok, "SYNCHRONIZER_URI": "/portal/zh/smWeb/qryStock", "method": "submit",
                "firDate": self.dates[0], "scaDate": date, "sqlMethod": "StockNo", "stockNo": code, "stockName": ""}
        html = self.op.open(self.URL, data=urllib.parse.urlencode(data).encode(), timeout=60).read().decode("utf-8")
        time.sleep(0.3)
        m = re.search(r"<td[^>]*>15</td>\s*<td[^>]*>[^<]+</td>\s*<td[^>]*>[\d,]+</td>\s*<td[^>]*>[\d,]+</td>\s*<td[^>]*>([\d.]+)</td>", html)
        if not m:
            return None
        with open(cache, "w") as f:
            f.write(m.group(1))
        return float(m.group(1))


# ---------- AI 選股多因子診斷、買賣點計算與跨日異常引擎 ----------

def compute_trade_plan(p, ai_grade="A"):
    """根據近 5 日收盤序列、均價、乖離率與籌碼強度，計算具體波段買點、停利賣點與停損價。"""
    close = p.get("close", 0)
    chg_pct = p.get("chgPct", 0)
    valid_s = [v for v in (p.get("series") or []) if v is not None]
    if not valid_s:
        valid_s = [close]
    ma5 = sum(valid_s) / len(valid_s)
    high5 = max(valid_s)
    low5 = min(valid_s)
    bias5 = (close - ma5) / ma5 * 100 if ma5 else 0

    if chg_pct >= 3.5 or bias5 >= 3.5:
        strategy = "強勢突破・拉回低接"
        b1 = tick_round(min(ma5, close * 0.965))
        b2 = tick_round(close * 0.988)
        buy_low, buy_high = min(b1, b2), max(b1, b2)
        breakout_buy = tick_round(close * 1.015)
        buy_desc = f"當日漲幅或正乖離較大，建議等拉回 {buy_low}～{buy_high}（支撐區）低接，或帶量突破 {breakout_buy} 右側追強"
    elif chg_pct < 0:
        strategy = "逆勢吃貨・逢低承接"
        b1 = tick_round(min(low5, close * 0.98))
        b2 = tick_round(close)
        buy_low, buy_high = min(b1, b2), max(b1, b2)
        breakout_buy = tick_round(max(ma5, close * 1.01))
        buy_desc = f"股價回檔但法人逆勢吸籌，可於 {buy_low}～{buy_high} 左側分批低接，站回 {breakout_buy} 確認轉強"
    else:
        strategy = "籌碼鎖碼・順勢布局"
        b1 = tick_round(min(ma5, close * 0.985))
        b2 = tick_round(close * 1.005)
        buy_low, buy_high = min(b1, b2), max(b1, b2)
        breakout_buy = tick_round(max(high5, close * 1.015))
        buy_desc = f"貼近 5 日線({ma5:.2f})量價穩健，建議於 {buy_low}～{buy_high} 分批買進，突破 {breakout_buy} 加碼"

    tp1 = tick_round(max(high5 * 1.02, close * 1.05))
    tp2_mult = 1.11 if ai_grade == "S+" else 1.09 if ai_grade == "A+" else 1.075
    tp2 = tick_round(max(tp1 * 1.03, close * tp2_mult))
    sl = tick_round(min(ma5 * 0.975, low5 * 0.985, close * 0.96))
    if sl >= buy_low:
        sl = tick_round(buy_low * 0.965)

    tp1_pct = round((tp1 - close) / close * 100, 1) if close else 0
    tp2_pct = round((tp2 - close) / close * 100, 1) if close else 0
    sl_pct = round((sl - close) / close * 100, 1) if close else 0

    return {
        "strategy": strategy,
        "ma5": round(ma5, 2),
        "high5": high5,
        "low5": low5,
        "bias5": round(bias5, 2),
        "buyLow": buy_low,
        "buyHigh": buy_high,
        "breakoutBuy": breakout_buy,
        "buyZone": f"{buy_low} ～ {buy_high}",
        "sellTarget1": tp1,
        "target1Pct": tp1_pct,
        "sellTarget2": tp2,
        "target2Pct": tp2_pct,
        "stopLoss": sl,
        "stopPct": sl_pct,
        "buyDesc": buy_desc,
        "sellDesc": f"第一賣點 {tp1} (+{tp1_pct}%) 先停利一半；波段目標賣點 {tp2} (+{tp2_pct}%)；跌破 {sl} ({sl_pct}%) 或法人連2日轉賣則停損出場。",
    }


def detect_stock_anomalies(p, prev_rank=None, streak_days=1, mkt_chg_pct=0.0):
    """偵測單一個股與前幾日對比之大數據異常訊號。"""
    anomalies = []
    hist = p.get("instHist") or []
    avg_vol = max(1, p.get("avgVol", 1))
    vol = p.get("volume", 0)
    vol_ratio = vol / avg_vol
    chg_pct = p.get("chgPct", 0)
    inst_net = p.get("instNet", 0)
    big_chg = p.get("bigChg")
    margin_chg = p.get("marginChg", 0)

    # 1. 法人由賣轉買大反轉 (前幾日賣超、今日突然大買)
    if len(hist) >= 2 and hist[1] < 0 and inst_net >= avg_vol * 0.2:
        anomalies.append({
            "type": "法人由賣轉買",
            "level": "high",
            "text": f"前日法人賣超 {abs(hist[1]):,} 張，今日突反手大買 +{inst_net:,} 張（V型認錯回補）",
        })
    elif len(hist) >= 3 and sum(hist[1:]) < 0 and inst_net > abs(sum(hist[1:])):
        anomalies.append({
            "type": "一舉扭轉賣超",
            "level": "high",
            "text": f"前 4 日法人累計賣超 {abs(sum(hist[1:])):,} 張，今日單日狂買 +{inst_net:,} 張一舉翻正",
        })

    # 2. 價跌但法人逆勢大買(壓低吃貨背離)
    if chg_pct < 0 and inst_net >= avg_vol * 0.15:
        anomalies.append({
            "type": "價跌逆勢吃貨",
            "level": "high",
            "text": f"今日股價收跌 {chg_pct:+.2f}%，但三大法人卻逆勢買超 +{inst_net:,} 張（標準壓低吃貨背離）",
        })

    # 3. 爆量異動 (相較前幾日均量)
    if vol_ratio >= 1.8:
        anomalies.append({
            "type": f"爆量 {vol_ratio:.1f} 倍",
            "level": "med",
            "text": f"今日成交 {vol:,} 張，暴增為 5 日均量({avg_vol:,}張)的 {vol_ratio:.1f} 倍，主力資金異常點火",
        })
    elif vol_ratio <= 0.55 and inst_net > 0 and (big_chg or 0) > 0:
        anomalies.append({
            "type": "量縮惜售鎖碼",
            "level": "med",
            "text": f"今日成交量萎縮至均量的 {vol_ratio:.1f} 倍，但法人與千張大戶同步買進，籌碼高度鎖定",
        })

    # 4. 跨日榜單排名異動
    if prev_rank is None and p.get("rank", 99) <= 6:
        anomalies.append({
            "type": f"空降 #{p['rank']} 黑馬",
            "level": "high",
            "text": f"前日未在推薦榜內，今日籌碼分數飆上 {p.get('score', 0):.1f} 分直接空降 {p.get('market', '')}第 {p['rank']} 名",
        })
    elif prev_rank is not None and prev_rank - p.get("rank", 99) >= 5:
        jump = prev_rank - p["rank"]
        anomalies.append({
            "type": f"排名急升 ↑{jump}名",
            "level": "med",
            "text": f"較前一日排名(#{prev_rank})大幅竄升 {jump} 個名次至 #{p['rank']}",
        })

    if streak_days >= 3:
        anomalies.append({
            "type": f"連霸榜 {streak_days} 日",
            "level": "high",
            "text": f"連續 {streak_days} 個交易日蟬聯 AI 大戶推薦榜，主力波段鎖碼極度穩定",
        })

    # 5. 大盤重挫時逆勢抗跌
    if mkt_chg_pct <= -0.8 and chg_pct > 0:
        anomalies.append({
            "type": "逆勢抗跌收紅",
            "level": "med",
            "text": f"大盤指數下跌 {mkt_chg_pct:+.2f}%，個股卻逆勢上漲 {chg_pct:+.2f}% 且法人買超護盤",
        })

    # 6. 大戶暴增與融資大減異常背離
    if big_chg is not None and big_chg >= 1.5 and margin_chg < 0:
        anomalies.append({
            "type": "大戶狂掃・散戶退場",
            "level": "high",
            "text": f"千張大戶單週暴增 +{big_chg:.2f}%，同時融資減少 {abs(margin_chg):,} 張，籌碼極速向大戶集中",
        })

    return anomalies


def compute_ai_insight(p, prev_rank=None, streak_days=1, mkt_chg_pct=0.0):
    """根據三大法人、千張大戶、融資退場與量價動能,計算 AI 選股評級、具體買賣點與跨日異常診斷。"""
    score = p.get("score", 0)
    f_net = p.get("foreignNet", p.get("foreign", 0))
    t_net = p.get("trustNet", p.get("trust", 0))
    f_str = p.get("foreignStreak", 0)
    t_str = p.get("trustStreak", 0)
    big_chg = p.get("bigChg")
    margin_chg = p.get("marginChg", 0)
    vol = p.get("volume", p.get("vol", 0))
    avg_vol = max(1, p.get("avgVol", vol or 1))

    # 計算共振因子數
    resonance = 0
    highlights = []
    if f_net > 0 and t_net > 0:
        resonance += 2
        highlights.append("土洋法人同步買超")
    elif t_str >= 3:
        resonance += 1
        highlights.append(f"投信連買 {t_str} 日鎖碼")
    elif f_str >= 3:
        resonance += 1
        highlights.append(f"外資連買 {f_str} 日布局")

    if big_chg is not None and big_chg >= 0.4:
        resonance += 2
        highlights.append(f"千張大戶週增 +{big_chg:.2f}%")
    elif big_chg is not None and big_chg > 0:
        resonance += 1
        highlights.append("大戶持股穩步增加")

    if margin_chg < 0:
        resonance += 1
        highlights.append(f"散戶融資退場 {abs(margin_chg):,} 張")

    if p.get("inst5d", 0) > avg_vol * 0.8:
        resonance += 1
        highlights.append("5日法人買盤強勁")

    if score >= 85 and resonance >= 3:
        grade = "S+"
        signal = "多因子共振・主力鎖碼"
    elif score >= 80 or (score >= 76 and resonance >= 3):
        grade = "A+"
        signal = "籌碼集中・波段偏多"
    elif score >= 72:
        grade = "A"
        signal = "法人進駐・穩健偏多"
    else:
        grade = "B+"
        signal = "籌碼轉強・追蹤觀察"

    trade_plan = compute_trade_plan(p, grade)
    anomalies = detect_stock_anomalies(p, prev_rank=prev_rank, streak_days=streak_days, mkt_chg_pct=mkt_chg_pct)

    prefix = "、".join(highlights[:3]) if highlights else "三大法人買超佔均量比高"
    anom_txt = f"；{anomalies[0]['text']}" if anomalies else ""
    summary = f"{prefix}{anom_txt}。"
    return {
        "aiGrade": grade,
        "aiSignal": signal,
        "aiSummary": summary,
        "aiResonance": resonance,
        "tradePlan": trade_plan,
        "anomalies": anomalies,
    }


# ---------- 計算 ----------

def trading_days(end, n):
    """從 end 往回找 n 個有三大法人資料的交易日(新到舊)。"""
    days, d = [], end
    while len(days) < n and (end - d).days < 30:
        if d.weekday() < 5 and twse_inst(d):
            days.append(d)
        d -= dt.timedelta(days=1)
    return days


def pct_rank(values):
    """回傳每個值在清單中的百分位(0~1)。同分的股票取平均名次,拿到一樣的百分位。"""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    denom = max(1, len(values) - 1)
    pos = 0
    while pos < len(order):
        end = pos
        while end + 1 < len(order) and values[order[end + 1]] == values[order[pos]]:
            end += 1
        for k in range(pos, end + 1):
            ranks[order[k]] = (pos + end) / 2 / denom
        pos = end + 1
    return ranks


def streak(series):
    n = 0
    for v in series:  # 新到舊
        if v > 0:
            n += 1
        else:
            break
    return n


def main():
    if len(sys.argv) > 1:
        end = dt.datetime.strptime(sys.argv[1], "%Y%m%d").date()
    else:
        end = dt.date.today()
    days = trading_days(end, LOOKBACK)
    if not days:
        sys.exit("找不到最近的交易日資料")
    d0 = days[0]
    print("交易日:", [f"{d:%m/%d}" for d in days])

    inst, price = [], []
    for d in days:
        i = dict(tpex_inst(d) or {})
        mk = {c: "上櫃" for c in i}
        tw = twse_inst(d)
        i.update(tw)
        mk.update({c: "上市" for c in tw})
        inst.append((i, mk))
        p = dict(tpex_price(d) or {})
        p.update(twse_price(d) or {})
        price.append(p)
    mg, margin_missing = margins(d0)
    if margin_missing:
        print("融資融券尚未公布:", margin_missing, "→ 這一項暫不計分,晚上 9 點半後請重跑")
    tdcc_date, big = tdcc_for(d0)
    print("集保資料日:", tdcc_date)

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
        hist = [inst[k][0].get(code, {}).get("total", 0) / 1000 for k in range(len(days))]
        f_hist = [inst[k][0].get(code, {}).get("foreign", 0) for k in range(len(days))]
        t_hist = [inst[k][0].get(code, {}).get("trust", 0) for k in range(len(days))]
        m = mg.get(code, {})
        diff = price[0][code]["diff"]
        series_closes = [px[code]["close"] if code in px else None for px in reversed(price)]
        rows.append({
            "code": code, "name": r["name"], "market": market[code],
            "close": close, "chgPct": round(diff / (close - diff) * 100, 2) if close - diff else 0,
            "avgVol": round(avg_vol), "volume": round(price[0][code]["vol"] / 1000),
            "foreignNet": round(r["foreign"] / 1000), "trustNet": round(r["trust"] / 1000),
            "dealerNet": round(r["dealer"] / 1000), "instNet": round(r["total"] / 1000),
            "instHist": [round(x) for x in hist], "inst5d": round(sum(hist)),
            "foreignStreak": streak(f_hist), "trustStreak": streak(t_hist),
            "marginChg": round(m.get("marginChg", 0)), "marginBal": round(m.get("marginBal", 0)),
            "shortChg": round(m.get("shortChg", 0)),
            "bigPct": big.get(code), "bigChg": None, "brokerNet": None,
            "series": series_closes,
        })
    universe = {mk: sum(1 for x in rows if x["market"] == mk) for mk in MARKETS}
    print("符合流動性條件:", universe)

    # 第一階段:法人、連買、融資(上市、上櫃各自算百分位,分開排名)
    cands = []
    for mk in MARKETS:
        grp = [x for x in rows if x["market"] == mk]
        r1 = pct_rank([x["instNet"] / x["avgVol"] for x in grp])
        r5 = pct_rank([x["inst5d"] / (x["avgVol"] * LOOKBACK) for x in grp])
        rs = pct_rank([x["foreignStreak"] + x["trustStreak"] * 1.5 for x in grp])
        rm = pct_rank([-x["marginChg"] / x["avgVol"] for x in grp])
        w = dict(WEIGHTS)
        if mk in margin_missing:
            scale = 100 / (100 - w["margin"])
            w = {k: (0 if k == "margin" else v * scale) for k, v in w.items()}
        for x, a, b, c, e in zip(grp, r1, r5, rs, rm):
            x["w_big"] = w["big"]
            x["parts"] = {"inst1": round(a * w["inst1"], 1), "inst5": round(b * w["inst5"], 1),
                          "streak": round(c * w["streak"], 1), "margin": round(e * w["margin"], 1),
                          "big": 0, "broker": 0}
            x["pre"] = sum(x["parts"].values())
        cands += sorted([x for x in grp if x["instNet"] > 0], key=lambda x: -x["pre"])[:TDCC_CANDIDATES]

    # 第二階段:候選股查集保上週,算千張大戶週增減
    th = TdccHistory()
    th._form()
    prev_date = next((d for d in th.dates if d < tdcc_date), None)
    for x in cands:
        prev = None
        for attempt in range(3):
            try:
                prev = th.big_pct(x["code"], prev_date)
                break
            except Exception as e:
                print("集保查詢失敗,重試", x["code"], e)
                time.sleep(3)
        if prev is not None and x["bigPct"] is not None:
            x["bigChg"] = round(x["bigPct"] - prev, 2)
    for x in cands:
        chg = x["bigChg"] if x["bigChg"] is not None else 0
        x["parts"]["big"] = round(max(0, min(1, (chg + 1) / 2)) * x.pop("w_big"), 1)
        x["score"] = round(sum(x["parts"].values()), 1)
    picks = []
    for mk in MARKETS:
        top = sorted([x for x in cands if x["market"] == mk], key=lambda x: -x["score"])[:TOP_N]
        for i, x in enumerate(top, 1):
            x["rank"] = i
        picks += top

    idxs = market_indices(d0)
    idx_map = {x["name"]: x.get("chgPct", 0) for x in idxs}

    for x in picks:
        x.pop("pre", None)
        tags = []
        if x["foreignNet"] > 0 and x["trustNet"] > 0:
            tags.append("土洋合買")
        if x["trustStreak"] >= 3:
            tags.append(f"投信連買{x['trustStreak']}日")
        if x["foreignStreak"] >= 3:
            tags.append(f"外資連買{x['foreignStreak']}日")
        if x["bigChg"] is not None and x["bigChg"] >= 0.5:
            tags.append("大戶增持")
        if -x["marginChg"] >= x["avgVol"] * 0.05:
            tags.append("融資大減")
        if x["inst5d"] > x["avgVol"]:
            tags.append("5日買超>均量")
        x["tags"] = tags
        mkt_chg = idx_map.get("加權指數", 0) if x["market"] == "上市" else idx_map.get("櫃買指數", 0)
        x.update(compute_ai_insight(x, mkt_chg_pct=mkt_chg))

    day_rows = daily_stock_rows(d0)
    tw = lambda d: f"{d[:4]}-{d[4:6]}-{d[6:]}"
    doc = {
        "date": f"{d0:%Y-%m-%d}",
        "generatedAt": dt.datetime.now().astimezone().isoformat(timespec="minutes"),
        "tradingDays": [f"{d:%Y-%m-%d}" for d in days],
        "tdccDate": tw(tdcc_date), "tdccPrevDate": tw(prev_date) if prev_date else None,
        "universe": len(rows), "universeByMarket": universe, "topN": TOP_N, "weights": WEIGHTS,
        "marginPending": sorted(margin_missing),
        "turnover": rank_by(day_rows, "turnover", TOP_N),
        "volumeRank": rank_by(day_rows, "volume", TOP_N),
        "indices": idxs,
        "dayTrade": daytrade_candidates(days, TOP_N),
        "filters": {"minAvgLots": MIN_AVG_LOTS, "minPrice": MIN_PRICE, "lookback": LOOKBACK},
        "picks": picks,
    }
    path = os.path.join(OUT, f"day_{doc['date']}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    print("輸出:", path)
    for x in picks:
        tp = x["tradePlan"]
        print(x["market"], x["rank"], x["code"], x["name"], x["score"], x["aiGrade"],
              f"買:{tp['buyZone']} 賣:{tp['sellTarget1']}/{tp['sellTarget2']} 損:{tp['stopLoss']}", x["tags"])
    for mk, rows in doc["turnover"].items():
        print(f"週轉率 {mk} 前 3:", [(x["code"], x["name"], x["turnover"]) for x in rows[:3]])
    print("指數:", [(x["name"], x["close"], x["chgPct"]) for x in doc["indices"]])
    for side, label in (("long", "當沖做多"), ("short", "當沖做空")):
        print(f"{label} 前 5:", [(x["code"], x["name"], x["score"], x["tags"]) for x in doc["dayTrade"][side][:5]])
    for mk, rows in doc["volumeRank"].items():
        print(f"成交量 {mk} 前 3:", [(x["code"], x["name"], x["volume"]) for x in rows[:3]])


if __name__ == "__main__":
    main()
