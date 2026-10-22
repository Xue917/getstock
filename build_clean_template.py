# -*- coding: utf-8 -*-
"""
產生簡潔、護眼、黑白基調且側邊選單具備精緻彩色層次（Modern Financial Sidebar）的 site_template.html
1. 解決「字都是白框根本看不到」問題：
   - 徹底清除瀏覽器原生 buttonface 白色背景與邊框
   - 為所有表格儲存格內的按鈕強制設置 background: transparent !important 與 border: 0 !important
   - 將策略選股、異動分頁、當沖多空、市場切換等按鈕重構為原生 Bootstrap .btn-outline-secondary，告別白色死框
2. 實現「旁邊選單可以有顏色變化」：
   - 側欄三大分組（核心決策 CORE、盤面與異動 MARKET、分析工具 TOOLS）配置發光微光小圓點
   - 8 大功能項目配置專屬彩色微光指示點（藍、金、青、紅、紫、橘、綠、靛）
   - 各功能項目配置獨立彩色 Badge 標籤（如琥珀金 40檔、青藍 透視、玫瑰紅 多空40、翠綠 550+檔）
   - 各功能在 Active 與 Hover 時具備專屬的平滑微光側邊框線與漸層底色
3. 維持「去 AI 化」與「投入本金預設 0」
"""
import os
import re

BASE = r"c:\Users\user\Desktop\GETSTOCK"
backup_path = os.path.join(BASE, "site_template_tailwind_backup.html")

with open(backup_path, "r", encoding="utf-8") as f:
    orig = f.read()

# 提取原始核心 JavaScript (最後一個 script 標籤為主要邏輯)
scripts = re.findall(r'<script(?:\s+[^>]*)?>([\s\S]*?)</script>', orig, re.I)
if not scripts:
    raise ValueError("找不到 JavaScript 區塊")
orig_js = scripts[-1]

# 清理去 AI 化
clean_js = orig_js
clean_js = clean_js.replace("AI S+", "S+")
clean_js = clean_js.replace("AI A+", "A+")
clean_js = clean_js.replace("AI A", "A")
clean_js = clean_js.replace("AI選股", "量化選股")
clean_js = clean_js.replace("AI推薦", "籌碼推薦")
clean_js = clean_js.replace("AI決策", "量化決策")
clean_js = clean_js.replace("AI健檢", "籌碼健檢")
clean_js = clean_js.replace("AI評級", "籌碼評級")
clean_js = clean_js.replace("AI多因子", "多因子量化")
clean_js = clean_js.replace("AI盤後", "盤後量化")
clean_js = clean_js.replace("AI買賣點", "量價策略點位")

# 自選星號鈕改為空字串
clean_js = re.sub(r'function starBtn\(code\)\s*\{.*?\n  \}', 'function starBtn(code) { return ""; }', clean_js, flags=re.S)

# 替換 gradeBadge 為極簡黑白高對比標籤
new_grade_badge = """
  function gradeBadge(grade) {
    if (!grade) return "";
    const g = String(grade).replace(/^AI\\s*/, "").trim();
    if (g === "S+") {
      return `<span class="badge border border-light text-white bg-dark fw-bold px-2 py-0.5 font-monospace">S+ 主力鎖碼</span>`;
    }
    if (g === "A+") {
      return `<span class="badge border border-secondary text-light bg-dark px-2 py-0.5 font-monospace">A+ 籌碼集中</span>`;
    }
    if (g === "A") {
      return `<span class="badge border border-secondary text-secondary bg-dark px-2 py-0.5 font-monospace">A 穩健多頭</span>`;
    }
    if (g.startsWith("D")) {
      return `<span class="badge border border-secondary text-muted bg-dark px-2 py-0.5 font-monospace">D 籌碼警戒</span>`;
    }
    return `<span class="badge border border-secondary text-muted bg-dark px-2 py-0.5 font-monospace">${g}</span>`;
  }
"""
clean_js = re.sub(r'function gradeBadge\(grade\)\s*\{.*?\n  \}', lambda m: new_grade_badge.strip(), clean_js, flags=re.S)

# 替換 radarSvg 為極簡黑白灰階風格 (無刺眼霓虹青色)
new_radar_svg = """
  function radarSvg(parts) {
    const p = parts || {};
    const axes = [
      { label: "法人當日", val: (p.inst1 || 0) / 25 },
      { label: "法人5日", val: (p.inst5 || 0) / 25 },
      { label: "連買天數", val: (p.streak || 0) / 10 },
      { label: "大戶週增", val: (p.big || 0) / 25 },
      { label: "融資退場", val: (p.margin || 0) / 15 },
    ];
    const cx = 115, cy = 100, R = 60;
    const pt = (i, ratio) => {
      const ang = -Math.PI / 2 + (i * 2 * Math.PI) / 5;
      return [cx + R * ratio * Math.cos(ang), cy + R * ratio * Math.sin(ang)];
    };
    const grids = [0.25, 0.5, 0.75, 1].map((r) => {
      const poly = axes.map((_, i) => pt(i, r).map((v) => v.toFixed(1)).join(",")).join(" ");
      return `<polygon points="${poly}" fill="none" stroke="rgba(255,255,255,${r === 1 ? 0.2 : 0.08})" stroke-width="1"/>`;
    }).join("");
    const spokes = axes.map((a, i) => {
      const [x, y] = pt(i, 1);
      const [lx, ly] = pt(i, 1.30);
      return `<line x1="${cx}" y1="${cy}" x2="${x.toFixed(1)}" y2="${y.toFixed(1)}" stroke="rgba(255,255,255,0.1)"/>
        <text x="${lx.toFixed(1)}" y="${ly.toFixed(1)}" fill="#94a3b8" font-size="11" font-weight="500" text-anchor="middle" dominant-baseline="middle">${a.label}</text>`;
    }).join("");
    const dataPoly = axes.map((a, i) => pt(i, Math.max(0.08, Math.min(1, a.val))).map((v) => v.toFixed(1)).join(",")).join(" ");
    const dots = axes.map((a, i) => {
      const [x, y] = pt(i, Math.max(0.08, Math.min(1, a.val)));
      return `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="2.5" fill="#f1f5f9"/>`;
    }).join("");
    return `<svg viewBox="0 0 230 200" class="w-full max-w-[210px] mx-auto block" role="img">
      ${grids}${spokes}
      <polygon points="${dataPoly}" fill="rgba(255,255,255,0.12)" stroke="rgba(255,255,255,0.7)" stroke-width="1.5"/>
      ${dots}
    </svg>`;
  }
"""
clean_js = re.sub(r'function radarSvg\(parts\)\s*\{.*?\n  \}', lambda m: new_radar_svg.strip(), clean_js, flags=re.S)

# 重構部位計算機：預設 0 元且平穩處理本金為 0 之情況
new_calc = """
  function updatePositionCalculator() {
    const p = findStock(state.docCode);
    if (!p || !p.tradePlan) return;
    const tp = p.tradePlan;
    const rawVal = $("calcCapital") ? $("calcCapital").value : "0";
    const capital = rawVal === "" ? 0 : Math.max(0, Number(rawVal) || 0);
    const riskPct = Number($("calcRiskPct").value) || 2;
    const entry = tp.buyHigh || p.close || 1;
    const stop = tp.stopLoss || entry * 0.96;

    if (capital <= 0) {
      $("calcShares").textContent = "0 股 (0.00 張)";
      $("calcCost").textContent = `參考買點 ${entry} 元，需投入本金 $0 元`;
      $("calcMaxLoss").textContent = "$0 元";
      $("calcStopPrice").textContent = `防守停損價位 ${stop} 元`;
      return;
    }

    const riskPerShare = Math.max(entry * 0.01, entry - stop);
    const maxAllowedLoss = capital * (riskPct / 100);

    const sharesByCap = Math.floor(capital / entry);
    const sharesByRisk = Math.floor(maxAllowedLoss / riskPerShare);
    const recShares = Math.max(0, Math.min(sharesByCap, sharesByRisk));
    const lots = (recShares / 1000).toFixed(2);
    const totalCost = Math.round(recShares * entry);
    const estLoss = Math.round(recShares * Math.max(0, entry - stop));

    $("calcShares").textContent = `${fmt(recShares)} 股 (${lots} 張)`;
    $("calcCost").textContent = `買點 ${entry} 試算，需本金 ${fmt(totalCost)} 元`;
    $("calcMaxLoss").textContent = `-${fmt(estLoss)} 元`;
    $("calcStopPrice").textContent = `停損 ${stop} 元 (風險佔比 ${(estLoss / capital * 100).toFixed(1)}%)`;
  }
"""
clean_js = re.sub(r'function updatePositionCalculator\(\)\s*\{.*?\n  \}', lambda m: new_calc.strip(), clean_js, flags=re.S)

# 按鈕彩色化系統 (按鈕的都可以有顏色來區分，不再全都是灰白底)
# 1. 策略選股機 presets (金、紅、青、綠、橘、水藍、紫、深紅)
spreset_code = """
    const scrStyles = {
      top: { active: "btn-amber fw-bold text-dark shadow-sm", inactive: "btn-outline-amber" },
      dual: { active: "btn-danger fw-bold text-white shadow-sm", inactive: "btn-outline-danger" },
      trust: { active: "btn-info fw-bold text-white shadow-sm", inactive: "btn-outline-info" },
      whale: { active: "btn-success fw-bold text-white shadow-sm", inactive: "btn-outline-success" },
      squeeze: { active: "btn-orange fw-bold text-white shadow-sm", inactive: "btn-outline-orange" },
      dipbuy: { active: "btn-cyan fw-bold text-white shadow-sm", inactive: "btn-outline-cyan" },
      turnaround: { active: "btn-purple fw-bold text-white shadow-sm", inactive: "btn-outline-purple" },
      blacklist: { active: "btn-danger fw-bold text-white shadow-sm", inactive: "btn-outline-danger" },
    };
    document.querySelectorAll(".spreset").forEach((b) => {
      const on = b.dataset.preset === state.scrPreset;
      const s = scrStyles[b.dataset.preset] || { active: "btn-light fw-bold text-dark", inactive: "btn-outline-secondary text-light" };
      b.className = `spreset btn btn-sm py-1 px-3 rounded-pill text-xs whitespace-nowrap ${
        on ? s.active : s.inactive
      }`;
    });
"""
clean_js = re.sub(
    r'document\.querySelectorAll\("\.spreset"\)\.forEach\(\(b\) => \{[\s\S]*?\}\);',
    lambda m: spreset_code.strip(),
    clean_js
)

# 2. 異動分類 tabs (灰、青、紫、靛、金、紅)
atab_code = """
    const anomStyles = {
      all: { active: "btn-light fw-bold text-dark shadow-sm", inactive: "btn-outline-secondary text-light" },
      reversal: { active: "btn-info fw-bold text-white shadow-sm", inactive: "btn-outline-info" },
      divergence: { active: "btn-purple fw-bold text-white shadow-sm", inactive: "btn-outline-purple" },
      consecutive: { active: "btn-indigo fw-bold text-white shadow-sm", inactive: "btn-outline-indigo" },
      newsurge: { active: "btn-amber fw-bold text-dark shadow-sm", inactive: "btn-outline-amber" },
      alerts: { active: "btn-danger fw-bold text-white shadow-sm", inactive: "btn-outline-danger" },
    };
    document.querySelectorAll(".atab").forEach((b) => {
      const on = b.dataset.atab === state.anomTab;
      const s = anomStyles[b.dataset.atab] || anomStyles.all;
      b.className = `atab btn btn-sm py-1 px-3 rounded-pill flex-none d-flex align-items-center gap-1.5 ${
        on ? s.active : s.inactive
      }`;
    });
"""
clean_js = re.sub(
    r'document\.querySelectorAll\("\.atab"\)\.forEach\(\(b\) => \{[\s\S]*?\}\);',
    lambda m: atab_code.strip(),
    clean_js
)

# 3. 當沖多空切換 (做多亮紅 / 做空亮綠)
dts_code = """
    document.querySelectorAll(".dts").forEach((b) => {
      const on = b.dataset.side === state.dtSide;
      const isLong = b.dataset.side === "long";
      if (isLong) {
        b.className = `dts btn btn-sm px-3.5 py-1.5 text-xs font-semibold ${
          on ? "btn-danger active fw-bold text-white shadow-sm" : "btn-outline-danger"
        }`;
      } else {
        b.className = `dts btn btn-sm px-3.5 py-1.5 text-xs font-semibold ${
          on ? "btn-success active fw-bold text-white shadow-sm" : "btn-outline-success"
        }`;
      }
    });
"""
clean_js = re.sub(
    r'document\.querySelectorAll\("\.dts"\)\.forEach\(\(b\) => \{[\s\S]*?\}\);',
    lambda m: dts_code.strip(),
    clean_js
)

# 4. 上市/上櫃市場切換 (上市亮藍 / 上櫃亮紫 / 全部亮靛)
mk_code = """
    const mkMap = {
      "上市": { active: "btn-primary active fw-bold text-white shadow-sm", inactive: "btn-outline-primary" },
      "上櫃": { active: "btn-purple active fw-bold text-white shadow-sm", inactive: "btn-outline-purple" },
      "全部": { active: "btn-indigo active fw-bold text-white shadow-sm", inactive: "btn-outline-indigo" },
    };
    document.querySelectorAll(".mk").forEach((b) => {
      const on = b.dataset.market === state.market;
      const s = mkMap[b.dataset.market] || { active: "btn-light fw-bold text-dark", inactive: "btn-outline-secondary text-light" };
      b.className = `mk btn btn-sm px-3 py-1 text-xs font-semibold ${
        on ? s.active : s.inactive
      }`;
    });
"""
clean_js = re.sub(
    r'document\.querySelectorAll\("\.mk"\)\.forEach\(\(b\) => \{[\s\S]*?\}\);',
    lambda m: mk_code.strip(),
    clean_js
)

# 5. 條件快篩 pills (全部/S+金/合買紅/反轉青/價跌吃貨紫/大戶綠/融資橘/連買靛)
af_code = """
    const afStyles = {
      all: { active: "btn-light fw-bold text-dark shadow-sm", inactive: "btn-outline-secondary text-light" },
      splus: { active: "btn-amber fw-bold text-dark shadow-sm", inactive: "btn-outline-amber" },
      dual: { active: "btn-danger fw-bold text-white shadow-sm", inactive: "btn-outline-danger" },
      reversal: { active: "btn-info fw-bold text-white shadow-sm", inactive: "btn-outline-info" },
      divergence: { active: "btn-purple fw-bold text-white shadow-sm", inactive: "btn-outline-purple" },
      big: { active: "btn-success fw-bold text-white shadow-sm", inactive: "btn-outline-success" },
      margin: { active: "btn-orange fw-bold text-white shadow-sm", inactive: "btn-outline-orange" },
      streak: { active: "btn-indigo fw-bold text-white shadow-sm", inactive: "btn-outline-indigo" },
    };
    document.querySelectorAll(".af").forEach((b) => {
      const on = b.dataset.filter === state.filter;
      const s = afStyles[b.dataset.filter] || { active: "btn-light fw-bold text-dark", inactive: "btn-outline-secondary text-light" };
      b.className = `af btn btn-sm flex-none px-2.5 py-0.5 rounded-pill text-xs whitespace-nowrap ${
        on ? s.active : s.inactive
      }`;
    });
"""
clean_js = re.sub(
    r'document\.querySelectorAll\("\.af"\)\.forEach\(\(b\) => \{[\s\S]*?\}\);',
    lambda m: af_code.strip(),
    clean_js
)

# 6. 表格內股票代號與名稱按鈕：確保其具有透明背景與無邊框類別
clean_js = clean_js.replace(
    '<button type="button" data-diagnose="${x.code}" class="text-left group">',
    '<button type="button" data-diagnose="${x.code}" class="text-left group bg-transparent border-0 p-0 shadow-none text-decoration-none d-block">'
)
clean_js = clean_js.replace(
    '<button type="button" data-diagnose="${p.code}" class="font-bold text-white hover:text-slate-200 text-left text-sm">',
    '<button type="button" data-diagnose="${p.code}" class="font-bold text-white hover:text-slate-200 text-left text-sm bg-transparent border-0 p-0 shadow-none text-decoration-none d-block">'
)

# 移除 renderAcademy, renderBacktest, renderWatchlist 函數定義
clean_js = re.sub(r'function renderAcademy\(\)\s*\{.*?\n  \}', 'function renderAcademy() {}', clean_js, flags=re.S)
clean_js = re.sub(r'function renderBacktest\(\)\s*\{.*?\n  \}', 'function renderBacktest() {}', clean_js, flags=re.S)
clean_js = re.sub(r'function renderWatchlist\(\)\s*\{.*?\n  \}', 'function renderWatchlist() {}', clean_js, flags=re.S)

# 徹底移除已不存在的自選股監聽器
clean_js = re.sub(
    r'\$\("btnToggleWatch"\)\.addEventListener[\s\S]*?\$\("btnClearWatch"\)\.addEventListener[\s\S]*?\}\);\s*',
    '',
    clean_js
)

# 檢視模式切換（極簡黑白按鈕）
new_view_toggle = """
  if ($("btnViewCards")) {
    $("btnViewCards").addEventListener("click", () => {
      state.viewMode = "cards";
      $("btnViewCards").className = "btn btn-sm btn-info active fw-bold text-white shadow-sm";
      $("btnViewTable").className = "btn btn-sm btn-outline-secondary text-light";
      render();
    });
  }
  if ($("btnViewTable")) {
    $("btnViewTable").addEventListener("click", () => {
      state.viewMode = "table";
      $("btnViewTable").className = "btn btn-sm btn-info active fw-bold text-white shadow-sm";
      $("btnViewCards").className = "btn btn-sm btn-outline-secondary text-light";
      render();
    });
  }
"""
clean_js = re.sub(
    r'\$\("btnViewCards"\)\.addEventListener[\s\S]*?\$\("btnViewTable"\)\.addEventListener[\s\S]*?\}\);\s*',
    lambda m: new_view_toggle.strip(),
    clean_js
)

# 柔和灰階文字替換
clean_js = clean_js.replace('border-amber-400/30', 'border-white/15')
clean_js = clean_js.replace('bg-amber-400 text-slate-950', 'bg-slate-200 text-slate-950')
clean_js = clean_js.replace('text-emerald-400', 'text-slate-100')
clean_js = clean_js.replace('text-amber-300', 'text-slate-200')
clean_js = clean_js.replace('text-rose-400', 'text-slate-300')
clean_js = clean_js.replace('text-sky-400', 'text-slate-300')
clean_js = clean_js.replace('text-amber-300 bg-amber-500/10', 'text-slate-200 bg-slate-800')
clean_js = clean_js.replace('border-emerald-500/30 bg-emerald-500/[0.04]', 'border-white/10 bg-slate-900/60')
clean_js = clean_js.replace('border-sky-400/25', 'border-white/10')
clean_js = clean_js.replace('text-sky-300', 'text-slate-200')
clean_js = clean_js.replace('"text-amber-400"', '"text-slate-100"')
clean_js = clean_js.replace('"text-emerald-400"', '"text-slate-100"')
clean_js = clean_js.replace('"text-purple-400"', '"text-slate-100"')
clean_js = clean_js.replace('"text-sky-400"', '"text-slate-100"')
clean_js = clean_js.replace('"text-pink-400"', '"text-slate-100"')

# 診斷與個股快捷按鈕彩色化
clean_js = clean_js.replace(
    '''<button type="button" id="btnDocTabKline" class="doc-rtab px-3 py-1.5 rounded-lg ${state.docRightTab === 'kline' ? 'bg-white text-black font-bold shadow-sm' : 'text-slate-400 hover:text-white'} transition-all">''',
    '''<button type="button" id="btnDocTabKline" class="doc-rtab btn btn-sm px-3 py-1 rounded-pill ${state.docRightTab === 'kline' ? 'btn-info active fw-bold text-white shadow-sm' : 'btn-outline-secondary text-light'} transition-all">'''
)
clean_js = clean_js.replace(
    '''<button type="button" id="btnDocTabRadar" class="doc-rtab px-3 py-1.5 rounded-lg ${state.docRightTab === 'radar' ? 'bg-white text-black font-bold shadow-sm' : 'text-slate-400 hover:text-white'} transition-all">''',
    '''<button type="button" id="btnDocTabRadar" class="doc-rtab btn btn-sm px-3 py-1 rounded-pill ${state.docRightTab === 'radar' ? 'btn-indigo active fw-bold text-white shadow-sm' : 'btn-outline-secondary text-light'} transition-all">'''
)
clean_js = clean_js.replace(
    'class="px-3 py-1 rounded-lg border transition-colors whitespace-nowrap text-xs ${active ? \"bg-white text-black font-bold border-white\" : isBad ? \"border-rose-500/30 text-rose-300 hover:bg-rose-500/10\" : \"border-white/10 text-slate-300 hover:text-white hover:bg-white/5\"}"',
    'class="btn btn-sm py-0.5 px-2.5 rounded-pill whitespace-nowrap text-xs ${active ? \"btn-primary active fw-bold text-white shadow-sm\" : isBad ? \"btn-outline-danger\" : \"btn-outline-info text-cyan-300\"}"'
)
clean_js = clean_js.replace(
    '<button type="button" data-diagnose="${p.code}" class="text-slate-300 hover:text-slate-200 font-semibold">',
    '<button type="button" data-diagnose="${p.code}" class="btn btn-sm btn-outline-info text-cyan-300 py-1 px-2.5 rounded-pill text-xs font-semibold">'
)
clean_js = clean_js.replace(
    'class="text-xs px-2.5 py-1 rounded-lg bg-sky-500/15 hover:bg-sky-500/25 border border-sky-500/30 text-slate-200 font-semibold transition-colors"',
    'class="btn btn-sm btn-outline-info text-cyan-300 py-0.5 px-2.5 rounded-pill text-xs font-semibold"'
)


# 歷史交易日：只顯示近一週 (5 個交易日)，選中以深色高對比白字顯示
new_history_js = """
    // 日期選單 (近一週 5 個交易日)
    const recentDays = days.slice(0, 5);
    if (day && !recentDays.some(d => d.date === day.date)) {
      recentDays.push(day);
    }
    $("history").innerHTML = recentDays.map((dd) => {
      const d = parseDay(dd.date), on = dd.date === day.date;
      return `<button type="button" data-day="${dd.date}"
        class="btn btn-sm flex-none px-3 py-1 rounded-pill text-xs transition-all ${
          on
            ? "btn-primary active fw-bold text-white shadow-sm"
            : "btn-outline-secondary text-light"
        }">
        <span class="num font-bold">${d.getMonth() + 1}/${d.getDate()}</span> <span class="${on ? "text-white-50 ms-0.5" : "text-muted ms-0.5"}">週${WEEK[d.getDay()]}</span>
      </button>`;
    }).join("");
"""
clean_js = re.sub(
    r'// 日期選單\s*\$\("history"\)\.innerHTML = days\.map\([\s\S]*?\}\)\.join\(""\);',
    lambda m: new_history_js.strip(),
    clean_js
)


# 更新指標卡
render_indices_patch = """
    // 更新 SB Admin 4 大狀態指標卡
    try {
      const twseIdx = (day.indices || []).find(x => x.name && (x.name.includes("加權") || x.name.includes("發行量加權"))) || (day.indices || [])[0];
      if (twseIdx && $("sbCardIdx")) {
        const s = twseIdx.change > 0 ? "+" : "";
        $("sbCardIdx").innerHTML = `${fmt(twseIdx.close)} <small class="${cls(twseIdx.change)} fs-6 ms-1">${s}${(twseIdx.changePct || 0).toFixed(2)}%</small>`;
        if ($("sbCardIdxSub")) $("sbCardIdxSub").textContent = twseIdx.change != null ? `點數變動: ${s}${fmt(twseIdx.change)} 點` : "收盤行情定稿";
      }
      const ov = day.aiOverview || {};
      if ($("sbCardAi")) {
        $("sbCardAi").textContent = ov.marketStance || ov.headline || "多因子量化共識";
      }
      if ($("sbCardAiSub")) {
        const sAvg = (day.picks || []).length ? ((day.picks || []).reduce((s, p) => s + p.score, 0) / day.picks.length).toFixed(1) : "—";
        $("sbCardAiSub").textContent = `精選平均籌碼分: ${sAvg} 分`;
      }
      
      // 卡片 3：S+ 主力鎖碼標的焦點
      const sPlusPicks = (day.picks || []).filter(x => String(x.aiGrade || "").includes("S+"));
      if ($("sbCardLock")) {
        $("sbCardLock").textContent = `${sPlusPicks.length} 檔`;
      }
      if ($("sbCardLockSub")) {
        $("sbCardLockSub").textContent = sPlusPicks.length ? `最高分: ${sPlusPicks[0].name} (${sPlusPicks[0].score}分)` : "法人大戶合力鎖碼";
      }

      // 卡片 4：當沖與異動監控
      const anomCount = (day.crossDayAnomalies && day.crossDayAnomalies.stocks) ? day.crossDayAnomalies.stocks.length : 0;
      if ($("sbCardAnom")) {
        $("sbCardAnom").textContent = `${anomCount} 檔`;
        if ($("sbCardAnomSub")) $("sbCardAnomSub").textContent = `當沖標的 40 檔 (多空各半)`;
      }
      if ($("sideAnomBadge")) {
        $("sideAnomBadge").textContent = anomCount;
      }
    } catch(err) {
      console.warn("指標卡更新提示:", err);
    }
"""
if "sbCardIdx" not in clean_js:
    clean_js = clean_js.replace(
        '  function renderIndices(day) {',
        '  function renderIndices(day) {\n' + render_indices_patch
    )

# 籌碼五維雷達專區引擎
radar_section_engine = """
  // ===== 籌碼五維雷達專區核心引擎 =====
  state.radarCode = null;
  state.radarFactor = "score";

  function renderRadarSection(code) {
    const day = days.find((d) => d.date === state.day) || days[0];
    if (!day) return;

    if (!code) {
      if (state.radarCode) {
        code = state.radarCode;
      } else if (day.picks && day.picks.length) {
        code = day.picks[0].code;
      } else {
        code = "2330";
      }
    }

    const p = findStock(code);
    if (!p) return;
    state.radarCode = p.code;

    // 1. 更新雷達快速選股 Pills
    const topPicks = (day.picks || []).slice(0, 6);
    if ($("radarQuickPills")) {
      $("radarQuickPills").innerHTML = `
        <span class="small text-muted text-nowrap align-self-center me-1">精選快選:</span>
        ${topPicks.map(x => `
          <button type="button" data-radar-load="${x.code}" class="btn btn-sm py-0.5 px-2.5 rounded-pill ${x.code === p.code ? 'btn-info text-white fw-bold shadow-sm' : 'btn-outline-info text-cyan-300'}">
            ${x.name}(${x.code})
          </button>
        `).join("")}
      `;
    }

    // 2. 左側：五維雷達圖表與個股多因子拆解
    const parts = p.parts || {};
    const tp = p.tradePlan || {};
    const factorBadges = [];
    const fNet = p.foreign ?? p.foreignNet ?? 0;
    const tNet = p.trust ?? p.trustNet ?? 0;
    const fStreak = p.foreignStreak ?? 0;
    const tStreak = p.trustStreak ?? 0;
    const bigChg = p.bigChg;
    const marginChg = p.marginChg ?? 0;

    if (fNet > 0 && tNet > 0) factorBadges.push(`<span class="badge border border-secondary text-light bg-dark px-2 py-0.5 font-monospace">土洋合買</span>`);
    if (fStreak >= 2) factorBadges.push(`<span class="badge border border-secondary text-light bg-dark px-2 py-0.5 font-monospace">外資連買 ${fStreak} 日</span>`);
    if (tStreak >= 2) factorBadges.push(`<span class="badge border border-secondary text-light bg-dark px-2 py-0.5 font-monospace">投信連買 ${tStreak} 日</span>`);
    if (bigChg != null && bigChg >= 0.3) factorBadges.push(`<span class="badge border border-secondary text-light bg-dark px-2 py-0.5 font-monospace">大戶週增 +${bigChg.toFixed(2)}%</span>`);
    if (marginChg < -50) factorBadges.push(`<span class="badge border border-secondary text-light bg-dark px-2 py-0.5 font-monospace">融資清洗 ${Math.abs(marginChg)} 張</span>`);

    if ($("radarStockCard")) {
      $("radarStockCard").innerHTML = `
        <div class="card h-100 shadow-sm border border-secondary-subtle" style="background:#181b20;">
          <div class="card-header py-3 d-flex align-items-center justify-content-between border-bottom border-secondary-subtle">
            <div class="d-flex align-items-center gap-2">
              <h5 class="mb-0 fw-bold text-white">${p.name}</h5>
              <span class="text-muted num small">(${p.code})</span>
              <span class="badge border border-secondary text-muted bg-dark small">${p.market}・${p.sector || "其他"}</span>
              ${gradeBadge(p.aiGrade)}
            </div>
            <div>
              <button type="button" data-diagnose="${p.code}" class="btn btn-sm btn-outline-info text-cyan-300">
                籌碼健檢
              </button>
            </div>
          </div>
          <div class="card-body p-3">
            <!-- 報價與五維分數環 -->
            <div class="d-flex align-items-center justify-content-between pb-3 mb-3 border-bottom border-secondary-subtle">
              <div>
                <div class="d-flex align-items-baseline gap-2">
                  <span class="fs-2 fw-bold num text-white">${fmt(p.close)}</span>
                  <span class="badge fs-6 num ${p.chg > 0 ? 'up-badge' : p.chg < 0 ? 'down-badge' : 'border border-secondary text-muted'}">
                    ${p.chg > 0 ? '+' : ''}${(p.chg || 0).toFixed(2)}%
                  </span>
                </div>
                <div class="small text-muted num mt-1">成交量 ${fmt(p.vol)} 張 ｜ 5日均線: <b class="text-light">${tp.ma5 || '—'}</b></div>
              </div>
              <div class="d-flex align-items-center gap-3">
                <div class="text-end">
                  <span class="text-muted small d-block">籌碼量化總分</span>
                  <b class="fs-4 num text-white">${p.rawScore || p.score || 0}</b><span class="text-muted small">/100</span>
                </div>
                <div class="ring ${String(p.aiGrade || "").includes("S+") ? 's-plus' : ''}" style="--p:${p.score || 50}" title="總分 ${p.score}">
                  <span class="num font-black">${p.score || '—'}</span>
                </div>
              </div>
            </div>

            <!-- 特徵標籤 -->
            <div class="d-flex flex-wrap gap-1 mb-3">
              ${factorBadges.join("") || '<span class="badge border border-secondary text-muted bg-dark">籌碼結構持平</span>'}
            </div>

            <!-- SVG 五維雷達圖 -->
            <div class="py-2 text-center rounded-3 mb-3 border border-secondary-subtle" style="background:#131519;">
              ${radarSvg(parts)}
            </div>

            <!-- 五維度詳細得分卡 -->
            <div class="row g-2 text-center text-xs num">
              ${PART_DEFS.map(([k, lbl, c, maxV]) => `
                <div class="col">
                  <div class="p-2 rounded border border-secondary-subtle" style="background:#131519;">
                    <span class="text-muted d-block text-truncate" style="font-size:0.75rem;">${lbl}</span>
                    <b class="fs-6 fw-bold text-white">${(parts[k] || 0).toFixed(1)}</b>
                    <span class="text-muted" style="font-size:0.7rem;">/${maxV}</span>
                  </div>
                </div>
              `).join("")}
            </div>

            <!-- 操作區間指引 -->
            <div class="mt-3 p-2.5 rounded border border-secondary-subtle small num" style="background:#131519;">
              <div class="d-flex justify-content-between mb-1">
                <span class="text-muted">建議布局區間:</span>
                <b class="text-light">${tp.buyZone || "—"} (突破買點: ${tp.breakoutBuy || "—"})</b>
              </div>
              <div class="d-flex justify-content-between mb-1">
                <span class="text-muted">目標價位 1/2:</span>
                <b class="text-light">${tp.sellTarget1 || "—"} / ${tp.sellTarget2 || "—"}</b>
              </div>
              <div class="d-flex justify-content-between">
                <span class="text-muted">防守停損價位:</span>
                <b class="text-muted">${tp.stopLoss || "—"} (${tp.stopPct || -4}%)</b>
              </div>
            </div>
          </div>
        </div>
      `;
    }

    // 3. 右側：天梯排行榜
    renderRadarFactorTable();
  }

  function renderRadarFactorTable() {
    const day = days.find((d) => d.date === state.day) || days[0];
    if (!day) return;

    const pool = (day.picks && day.picks.length) ? day.picks : universeDB;
    const factor = state.radarFactor || "score";

    let sorted = [...pool];
    if (factor === "score") {
      sorted.sort((a, b) => (b.rawScore || b.score || 0) - (a.rawScore || a.score || 0));
    } else if (factor === "big") {
      sorted.sort((a, b) => ((b.parts && b.parts.big) || b.bigChg || 0) - ((a.parts && a.parts.big) || a.bigChg || 0));
    } else if (factor === "inst") {
      sorted.sort((a, b) => ((b.parts && b.parts.inst1) || b.inst || 0) - ((a.parts && a.parts.inst1) || a.inst || 0));
    } else if (factor === "streak") {
      sorted.sort((a, b) => ((b.parts && b.parts.streak) || b.trustStreak || 0) - ((a.parts && a.parts.streak) || a.trustStreak || 0));
    } else if (factor === "margin") {
      sorted.sort((a, b) => ((b.parts && b.parts.margin) || -(b.marginChg || 0)) - ((a.parts && a.parts.margin) || -(a.marginChg || 0)));
    }

    const rows = sorted.slice(0, 15);
    if ($("radarRankRows")) {
      $("radarRankRows").innerHTML = rows.map((x, idx) => {
        const parts = x.parts || {};
        const scoreBar = PART_DEFS.map(([k, label, c]) => {
          const v = parts[k] || 0;
          return v > 0 ? `<i style="width:${v}%;background:var(${c})" title="${label}: ${v.toFixed(1)}分"></i>` : "";
        }).join("");
        const isCurrent = x.code === state.radarCode;

        return `
          <tr class="${isCurrent ? 'table-active' : ''} cursor-pointer text-xs" data-radar-load="${x.code}">
            <td class="text-center num fw-bold ${idx < 3 ? 'text-white' : 'text-muted'}">${idx + 1}</td>
            <td>
              <span class="fw-bold ${isCurrent ? 'text-white' : 'text-slate-200'}">${x.name}</span>
              <span class="text-muted num small ms-1">(${x.code})</span>
            </td>
            <td class="text-end num text-white">${fmt(x.close)}</td>
            <td class="text-end num ${cls(x.chg)} font-bold">${x.chg > 0 ? '+' : ''}${(x.chg || 0).toFixed(2)}%</td>
            <td style="min-width: 100px;">
              <div class="score-bar">${scoreBar}</div>
            </td>
            <td class="text-end num fw-bold text-white">${x.rawScore || x.score || 0}</td>
            <td class="text-center">
              <button type="button" data-radar-load="${x.code}" class="btn btn-sm ${isCurrent ? 'btn-success text-white fw-bold shadow-sm' : 'btn-outline-info text-cyan-400'} py-0 px-2 text-xs">
                ${isCurrent ? '檢視中' : '載入'}
              </button>
            </td>
          </tr>
        `;
      }).join("");
    }
  }
"""

# 事件掛接：雷達點擊與維度切換
init_events = """
  // 籌碼雷達維度按鈕切換
  if ($("radarFactorTabs")) {
    $("radarFactorTabs").addEventListener("click", (e) => {
      const b = e.target.closest("button[data-factor]");
      if (b) {
        state.radarFactor = b.dataset.factor;
        const factorStyles = {
          score: { active: "btn-amber fw-bold text-dark shadow-sm", inactive: "btn-outline-amber" },
          inst: { active: "btn-info fw-bold text-white shadow-sm", inactive: "btn-outline-info" },
          big: { active: "btn-success fw-bold text-white shadow-sm", inactive: "btn-outline-success" },
          streak: { active: "btn-purple fw-bold text-white shadow-sm", inactive: "btn-outline-purple" },
          margin: { active: "btn-orange fw-bold text-white shadow-sm", inactive: "btn-outline-orange" },
        };
        document.querySelectorAll("#radarFactorTabs button").forEach(btn => {
          const fac = btn.dataset.factor;
          const s = factorStyles[fac] || { active: "btn-light fw-bold text-dark", inactive: "btn-outline-secondary text-light" };
          btn.className = `btn btn-sm py-0.5 px-2.5 rounded-pill flex-none ${btn === b ? s.active : s.inactive}`;
        });
        renderRadarFactorTable();
      }
    });
  }

  // 主題切換 (支援黑白深色 / 淺色切換)
  const themeToggle = document.getElementById("btnThemeToggle");
  let currentTheme = localStorage.getItem("sb|theme") || "theme-dark";
  document.body.classList.remove("theme-dark", "theme-light");
  document.body.classList.add(currentTheme);

  if (themeToggle) {
    themeToggle.addEventListener("click", () => {
      currentTheme = currentTheme === "theme-dark" ? "theme-light" : "theme-dark";
      document.body.classList.remove("theme-dark", "theme-light");
      document.body.classList.add(currentTheme);
      localStorage.setItem("sb|theme", currentTheme);
    });
  }

  // 點擊側選單時高亮項目與收合側欄
  document.querySelectorAll("#layoutSidenav_nav a.nav-link").forEach((link) => {
    link.addEventListener("click", () => {
      const hash = link.getAttribute("href");
      if (hash && hash.startsWith("#")) {
        document.querySelectorAll("#layoutSidenav_nav a.nav-link").forEach((t) => {
          if (t.getAttribute("href") === hash) {
            t.classList.add("active");
          } else {
            t.classList.remove("active");
          }
        });
      }
      if (window.innerWidth < 992) {
        document.body.classList.remove("sb-sidenav-toggled");
      }
    });
  });
"""

# 側欄導航滾動高亮監聽器
clean_js = re.sub(
    r'\["academy", "picks",.*?\]\.forEach\(\(id\) => \{',
    '["dashboard", "picks", "radarSection", "daytrade", "anomalies", "doctor", "screener", "rankings"].forEach((id) => {',
    clean_js
)

# 插入事件與初始化到主 closure
clean_js = clean_js.replace(
    'initScreenerSectors();',
    radar_section_engine + '\n' + init_events + '\n  initScreenerSectors();'
)

clean_js = clean_js.replace(
    'renderDayTrade(day);',
    'renderDayTrade(day);\n    renderRadarSection();'
)

clean_js = clean_js.replace(
    'renderDoctor();',
    'renderDoctor();\n  renderRadarSection();'
)

# 在全局點擊代理中掛接雷達載入
clean_js = clean_js.replace(
    'const dBtn = e.target.closest("[data-diagnose]");',
    'const rBtn = e.target.closest("[data-radar-load]");\n    if (rBtn) {\n      e.stopPropagation();\n      renderRadarSection(rBtn.dataset.radarLoad);\n      scrollToSection("radarSection");\n      return;\n    }\n    const dBtn = e.target.closest("[data-diagnose]");'
)

# 構建全新極簡黑白舒適且側欄富色彩層次的 HTML 介面模板
sb_template_html = f'''<!-- GETSTOCK 台股大戶籌碼與量化決策系統 -->
<title>GETSTOCK 大戶籌碼與量化選股決策系統</title>
<meta charset="utf-8">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
<meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
<link rel="icon" href="images/logo.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+TC:wght@400;500;600;700&family=Roboto+Mono:wght@500;600;700&display=swap" rel="stylesheet">
<link href="css/styles.css" rel="stylesheet" />
<script src="https://cdn.tailwindcss.com/3.4.17"></script>
<script>
  tailwind.config = {{
    corePlugins: {{ preflight: false }},
    darkMode: 'class',
    theme: {{
      extend: {{
        fontFamily: {{
          sans: ["Inter", "Noto Sans TC", "system-ui", "-apple-system", "sans-serif"],
          mono: ["Roboto Mono", "ui-monospace", "monospace"]
        }}
      }}
    }}
  }};
</script>

<style>
:root {{
  /* 黑白灰階與柔和對比設計 (舒適不刺眼) */
  --bg-main: #121417;
  --bg-card: #181b20;
  --bg-card-sub: #1f232b;
  --border-subtle: rgba(255, 255, 255, 0.08);
  
  /* 台股漲跌 (柔和低飽和度) */
  --up: #f87171;
  --up-bg: rgba(248, 113, 113, 0.12);
  --down: #34d399;
  --down-bg: rgba(52, 211, 153, 0.12);
  --flat: #94a3b8;
  --font-num: "Roboto Mono", Consolas, monospace;

  /* 五維籌碼條：黑白灰階階梯 */
  --s1: #f1f5f9;
  --s2: #cbd5e1;
  --s3: #94a3b8;
  --s4: #64748b;
  --s5: #475569;
}}

/* 數字等寬排版與標準配色 */
.num {{ font-family: var(--font-num); font-variant-numeric: tabular-nums; }}
.up {{ color: var(--up) !important; font-weight: 600; }}
.down {{ color: var(--down) !important; font-weight: 600; }}
.flat {{ color: var(--flat) !important; }}
.up-badge {{ color: var(--up) !important; background-color: var(--up-bg) !important; border: 1px solid rgba(248, 113, 113, 0.25); }}
.down-badge {{ color: var(--down) !important; background-color: var(--down-bg) !important; border: 1px solid rgba(52, 211, 153, 0.25); }}

/* 徹底消除瀏覽器原生按鈕白色 buttonface 與外框干擾 (解決「字都是白框根本看不到」) */
button,
[type='button'],
[type='reset'],
[type='submit'] {{
  background-color: transparent;
  background-image: none;
  border-color: transparent;
  color: inherit;
  font: inherit;
  box-shadow: none;
  outline: none;
}}
button:not(.btn),
[type='button']:not(.btn) {{
  background: transparent !important;
  background-color: transparent !important;
  border: 0 !important;
  border-color: transparent !important;
  box-shadow: none !important;
  padding: 0;
  margin: 0;
}}
table td button,
table td button:hover,
table td button:focus,
table td button:active {{
  background: transparent !important;
  background-color: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
  outline: none !important;
  color: inherit !important;
  padding: 0 !important;
}}

/* 隱藏原生滾動條與隱藏元素 */
.no-scrollbar::-webkit-scrollbar {{ display: none; }}
.no-scrollbar {{ -ms-overflow-style: none; scrollbar-width: none; }}
.hidden {{ display: none !important; }}

/* 籌碼五維條 (黑白灰階) */
.score-bar {{ display: flex; height: 5px; border-radius: 999px; background: rgba(255,255,255,0.08); overflow: hidden; gap: 1px; }}
.score-bar i {{ display: block; height: 100%; transition: opacity 0.15s; }}
.score-bar i:hover {{ opacity: 0.85; }}

/* 圓環進度圈 */
.ring {{ --p: 80; width: 42px; height: 42px; border-radius: 50%; display: grid; place-items: center; flex: none;
  background: conic-gradient(#e2e8f0 calc(var(--p) * 1%), rgba(255,255,255,0.1) 0); }}
.ring.s-plus {{ background: conic-gradient(#ffffff calc(var(--p) * 1%), rgba(255,255,255,0.1) 0); }}
.ring.danger {{ background: conic-gradient(#f87171 calc(var(--p) * 1%), rgba(255,255,255,0.1) 0); }}
.ring span {{ width: 32px; height: 32px; border-radius: 50%; background: #181b20; display: grid; place-items: center; font-weight: 700; font-size: 13px; color: #f1f5f9; }}
body.theme-light .ring span {{ background: #ffffff; color: #111827; }}

/* 卡片互動回饋 */
.stock-card {{
  transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
}}
.stock-card:hover {{
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.35);
  border-color: rgba(255, 255, 255, 0.22) !important;
}}

/* ===== 黑白深色主題 (theme-dark) 柔和舒適 ===== */
body.theme-dark {{
  background-color: #121417;
  color: #e2e8f0;
}}
body.theme-dark #layoutSidenav_content {{
  background-color: #121417;
}}
body.theme-dark .card {{
  background-color: #181b20;
  border-color: rgba(255, 255, 255, 0.08);
  color: #e2e8f0;
}}
body.theme-dark .card-header {{
  background-color: #1c2027;
  border-bottom-color: rgba(255, 255, 255, 0.08);
  color: #f8fafc;
}}
body.theme-dark .card-footer {{
  background-color: rgba(0, 0, 0, 0.15);
  border-top-color: rgba(255, 255, 255, 0.08);
}}
body.theme-dark .table {{
  color: #e2e8f0;
  border-color: rgba(255, 255, 255, 0.08);
}}
body.theme-dark .table-striped > tbody > tr:nth-of-type(odd) > * {{
  background-color: rgba(255, 255, 255, 0.02);
  color: #e2e8f0;
}}
body.theme-dark .table-hover > tbody > tr:hover > * {{
  background-color: rgba(255, 255, 255, 0.05);
  color: #ffffff;
}}
body.theme-dark .form-control, body.theme-dark .form-select {{
  background-color: #15181d;
  border-color: rgba(255, 255, 255, 0.14);
  color: #f8fafc;
}}
body.theme-dark .form-control:focus, body.theme-dark .form-select:focus {{
  background-color: #1a1e24;
  border-color: rgba(255, 255, 255, 0.35);
  color: #ffffff;
}}
body.theme-dark .dropdown-menu {{
  background-color: #1c2027;
  border-color: rgba(255, 255, 255, 0.12);
  color: #e2e8f0;
}}
body.theme-dark .dropdown-item {{
  color: #e2e8f0;
}}
body.theme-dark .dropdown-item:hover {{
  background-color: rgba(255, 255, 255, 0.08);
  color: #ffffff;
}}
body.theme-dark footer {{
  background-color: #121417 !important;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}}

/* ===== 淺色主題 (theme-light) ===== */
body.theme-light {{
  background-color: #f8f9fa;
  color: #212529;
}}
body.theme-light #layoutSidenav_content {{
  background-color: #f8f9fa;
}}
body.theme-light .card {{
  background-color: #ffffff;
  border-color: rgba(0, 0, 0, 0.1);
  color: #212529;
}}
body.theme-light .card-header {{
  background-color: #f8f9fa;
  border-bottom-color: rgba(0, 0, 0, 0.1);
  color: #212529;
}}
body.theme-light .table {{
  color: #212529;
  border-color: rgba(0, 0, 0, 0.08);
}}
body.theme-light footer {{
  background-color: #f8f9fa !important;
}}
body.theme-light .stock-card {{
  background: #ffffff !important;
  border-color: rgba(0, 0, 0, 0.1) !important;
}}

/* ==================== 旁邊選單顏色變化 (Modern Colored Financial Sidenav) ==================== */
.sb-topnav .navbar-brand {{
  width: 225px;
  margin: 0;
}}
.sb-sidenav-dark .sb-sidenav-menu .sb-sidenav-menu-heading {{
  font-size: 0.72rem;
  letter-spacing: 0.08em;
  padding: 1.15rem 1rem 0.4rem;
}}
.sb-sidenav .nav-link {{
  color: #cbd5e1 !important;
  padding: 0.65rem 1rem !important;
  font-size: 0.875rem !important;
  font-weight: 500 !important;
  border-left: 3px solid transparent !important;
  transition: all 0.15s ease-in-out !important;
}}
.sb-sidenav .nav-link:hover {{
  color: #ffffff !important;
  background: rgba(255, 255, 255, 0.06) !important;
  border-left-color: rgba(255, 255, 255, 0.4) !important;
}}

/* 各項目彩色微光圓點 */
.side-dot {{
  display: inline-block;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  margin-right: 10px;
  flex-shrink: 0;
  opacity: 0.9;
  transition: transform 0.2s, box-shadow 0.2s;
}}
.sb-sidenav .nav-link:hover .side-dot {{
  transform: scale(1.35);
}}

/* 8 大功能項目專屬 Active 狀態色彩 */
.sb-sidenav .nav-link.side-item-blue.active {{
  color: #93c5fd !important;
  background: linear-gradient(90deg, rgba(59, 130, 246, 0.18) 0%, transparent 100%) !important;
  border-left-color: #3b82f6 !important;
}}
.sb-sidenav .nav-link.side-item-blue.active .side-dot {{
  box-shadow: 0 0 8px #3b82f6;
  transform: scale(1.3);
}}

.sb-sidenav .nav-link.side-item-amber.active {{
  color: #fde68a !important;
  background: linear-gradient(90deg, rgba(245, 158, 11, 0.18) 0%, transparent 100%) !important;
  border-left-color: #f59e0b !important;
}}
.sb-sidenav .nav-link.side-item-amber.active .side-dot {{
  box-shadow: 0 0 8px #f59e0b;
  transform: scale(1.3);
}}

.sb-sidenav .nav-link.side-item-cyan.active {{
  color: #a5f3fc !important;
  background: linear-gradient(90deg, rgba(6, 182, 212, 0.18) 0%, transparent 100%) !important;
  border-left-color: #06b6d4 !important;
}}
.sb-sidenav .nav-link.side-item-cyan.active .side-dot {{
  box-shadow: 0 0 8px #06b6d4;
  transform: scale(1.3);
}}

.sb-sidenav .nav-link.side-item-rose.active {{
  color: #fecdd3 !important;
  background: linear-gradient(90deg, rgba(244, 63, 94, 0.18) 0%, transparent 100%) !important;
  border-left-color: #f43f5e !important;
}}
.sb-sidenav .nav-link.side-item-rose.active .side-dot {{
  box-shadow: 0 0 8px #f43f5e;
  transform: scale(1.3);
}}

.sb-sidenav .nav-link.side-item-purple.active {{
  color: #e9d5ff !important;
  background: linear-gradient(90deg, rgba(168, 85, 247, 0.18) 0%, transparent 100%) !important;
  border-left-color: #a855f7 !important;
}}
.sb-sidenav .nav-link.side-item-purple.active .side-dot {{
  box-shadow: 0 0 8px #a855f7;
  transform: scale(1.3);
}}

.sb-sidenav .nav-link.side-item-orange.active {{
  color: #fed7aa !important;
  background: linear-gradient(90deg, rgba(249, 115, 22, 0.18) 0%, transparent 100%) !important;
  border-left-color: #f97316 !important;
}}
.sb-sidenav .nav-link.side-item-orange.active .side-dot {{
  box-shadow: 0 0 8px #f97316;
  transform: scale(1.3);
}}

.sb-sidenav .nav-link.side-item-emerald.active {{
  color: #a7f3d0 !important;
  background: linear-gradient(90deg, rgba(16, 185, 129, 0.18) 0%, transparent 100%) !important;
  border-left-color: #10b981 !important;
}}
.sb-sidenav .nav-link.side-item-emerald.active .side-dot {{
  box-shadow: 0 0 8px #10b981;
  transform: scale(1.3);
}}

.sb-sidenav .nav-link.side-item-indigo.active {{
  color: #c7d2fe !important;
  background: linear-gradient(90deg, rgba(99, 102, 241, 0.18) 0%, transparent 100%) !important;
  border-left-color: #6366f1 !important;
}}
.sb-sidenav .nav-link.side-item-indigo.active .side-dot {{
  box-shadow: 0 0 8px #6366f1;
  transform: scale(1.3);
}}

/* 側欄專屬徽章色彩 (高辨識度、不刺眼) */
.side-badge-amber {{
  background: rgba(245, 158, 11, 0.18) !important;
  color: #fbbf24 !important;
  border: 1px solid rgba(245, 158, 11, 0.4) !important;
}}
.side-badge-cyan {{
  background: rgba(6, 182, 212, 0.18) !important;
  color: #22d3ee !important;
  border: 1px solid rgba(6, 182, 212, 0.4) !important;
}}
.side-badge-rose {{
  background: rgba(244, 63, 94, 0.18) !important;
  color: #fb7185 !important;
  border: 1px solid rgba(244, 63, 94, 0.4) !important;
}}
.side-badge-purple {{
  background: rgba(168, 85, 247, 0.18) !important;
  color: #c084fc !important;
  border: 1px solid rgba(168, 85, 247, 0.4) !important;
}}
.side-badge-emerald {{
  background: rgba(16, 185, 129, 0.18) !important;
  color: #34d399 !important;
  border: 1px solid rgba(16, 185, 129, 0.4) !important;
}}
.side-badge-indigo {{
  background: rgba(99, 102, 241, 0.18) !important;
  color: #818cf8 !important;
  border: 1px solid rgba(99, 102, 241, 0.4) !important;
}}

/* ==================== 深色沉浸式彩色按鈕系統 (Deep Tonal Active Buttons) ==================== */
.btn {{
  font-weight: 600 !important;
  transition: all 0.15s ease-in-out;
  border-width: 1px !important;
}}
.btn-sm {{
  font-size: 0.78rem !important;
  letter-spacing: 0.02em;
}}

/* 點選（Active）深色系按鈕：深邃底色、鮮豔外框邊條、純白高對比文字 (清晰易看、護眼不刺眼) */
/* 1. 藍色系 (Blue / TWSE / History Date) */
.btn-outline-primary {{
  background-color: transparent !important;
  border-color: rgba(59, 130, 246, 0.45) !important;
  color: #93c5fd !important;
}}
.btn-outline-primary:hover {{
  background-color: rgba(30, 58, 138, 0.4) !important;
  color: #ffffff !important;
}}
.btn-primary, .btn-outline-primary.active, .btn-primary.active {{
  background-color: #1e3a8a !important; /* 深海軍藍 */
  border-color: #3b82f6 !important;
  color: #ffffff !important;
  box-shadow: 0 0 10px rgba(59, 130, 246, 0.35) !important;
}}

/* 2. 翡翠綠系 (Emerald / Green / Export CSV / 做空 / 大戶增持) */
.btn-outline-success {{
  background-color: transparent !important;
  border-color: rgba(16, 185, 129, 0.45) !important;
  color: #6ee7b7 !important;
}}
.btn-outline-success:hover {{
  background-color: rgba(6, 78, 59, 0.4) !important;
  color: #ffffff !important;
}}
.btn-success, .btn-outline-success.active, .btn-success.active {{
  background-color: #064e3b !important; /* 深森林綠 */
  border-color: #10b981 !important;
  color: #ffffff !important;
  box-shadow: 0 0 10px rgba(16, 185, 129, 0.35) !important;
}}

/* 3. 玫瑰紅系 (Rose / Red / 多頭 / 做多 / 土洋合買 / 籌碼警戒) */
.btn-outline-danger {{
  background-color: transparent !important;
  border-color: rgba(244, 63, 94, 0.45) !important;
  color: #fca5a5 !important;
}}
.btn-outline-danger:hover {{
  background-color: rgba(136, 19, 55, 0.4) !important;
  color: #ffffff !important;
}}
.btn-danger, .btn-outline-danger.active, .btn-danger.active {{
  background-color: #881337 !important; /* 深酒紅 */
  border-color: #f43f5e !important;
  color: #ffffff !important;
  box-shadow: 0 0 10px rgba(244, 63, 94, 0.35) !important;
}}

/* 4. 琥珀金系 (Amber / Gold / S+ 主力鎖碼 / 總分排行 / 突襲新進 / 首選) */
.btn-outline-amber, .btn-outline-warning {{
  background-color: transparent !important;
  border-color: rgba(245, 158, 11, 0.45) !important;
  color: #fde68a !important;
}}
.btn-outline-amber:hover, .btn-outline-warning:hover {{
  background-color: rgba(120, 53, 15, 0.4) !important;
  color: #ffffff !important;
}}
.btn-amber, .btn-warning, .btn-outline-amber.active, .btn-outline-warning.active, .btn-amber.active, .btn-warning.active {{
  background-color: #78350f !important; /* 深琥珀古銅金 */
  border-color: #f59e0b !important;
  color: #ffffff !important;
  box-shadow: 0 0 10px rgba(245, 158, 11, 0.35) !important;
}}

/* 5. 天空青/水藍系 (Cyan / Sky / 由賣轉買 / 日K圖 / 籌碼雷達 / 檢視切換 / 診斷) */
.btn-outline-info, .btn-outline-cyan {{
  background-color: transparent !important;
  border-color: rgba(6, 182, 212, 0.45) !important;
  color: #67e8f9 !important;
}}
.btn-outline-info:hover, .btn-outline-cyan:hover {{
  background-color: rgba(7, 89, 133, 0.4) !important;
  color: #ffffff !important;
}}
.btn-info, .btn-cyan, .btn-outline-info.active, .btn-outline-cyan.active, .btn-info.active, .btn-cyan.active {{
  background-color: #075985 !important; /* 深湛藍 */
  border-color: #0284c7 !important;
  color: #ffffff !important;
  box-shadow: 0 0 10px rgba(2, 132, 199, 0.35) !important;
}}

/* 6. 魅紫系 (Purple / TPEx 上櫃 / 價跌吃貨 / 投信連買) */
.btn-outline-purple {{
  background-color: transparent !important;
  border-color: rgba(168, 85, 247, 0.45) !important;
  color: #d8b4fe !important;
}}
.btn-outline-purple:hover {{
  background-color: rgba(88, 28, 135, 0.4) !important;
  color: #ffffff !important;
}}
.btn-purple, .btn-outline-purple.active, .btn-purple.active {{
  background-color: #581c87 !important; /* 深邃紫 */
  border-color: #a855f7 !important;
  color: #ffffff !important;
  box-shadow: 0 0 10px rgba(168, 85, 247, 0.35) !important;
}}

/* 7. 靛藍系 (Indigo / 全部市場 / 連買連霸 / 五維雷達標籤) */
.btn-outline-indigo {{
  background-color: transparent !important;
  border-color: rgba(99, 102, 241, 0.45) !important;
  color: #a5b4fc !important;
}}
.btn-outline-indigo:hover {{
  background-color: rgba(49, 46, 129, 0.4) !important;
  color: #ffffff !important;
}}
.btn-indigo, .btn-outline-indigo.active, .btn-indigo.active {{
  background-color: #312e81 !important; /* 深靛藍 */
  border-color: #6366f1 !important;
  color: #ffffff !important;
  box-shadow: 0 0 10px rgba(99, 102, 241, 0.35) !important;
}}

/* 8. 活力橘系 (Orange / 融資清洗 / 券增資減) */
.btn-outline-orange {{
  background-color: transparent !important;
  border-color: rgba(249, 115, 22, 0.45) !important;
  color: #fdba74 !important;
}}
.btn-outline-orange:hover {{
  background-color: rgba(124, 45, 18, 0.4) !important;
  color: #ffffff !important;
}}
.btn-orange, .btn-outline-orange.active, .btn-orange.active {{
  background-color: #7c2d12 !important; /* 深赤橘 */
  border-color: #f97316 !important;
  color: #ffffff !important;
  box-shadow: 0 0 10px rgba(249, 115, 22, 0.35) !important;
}}

/* 9. 中性深石板灰色 (Slate / 全部篩選 / 全部異動) */
.btn-outline-secondary {{
  background-color: transparent !important;
  border-color: rgba(255, 255, 255, 0.16) !important;
  color: #cbd5e1 !important;
}}
.btn-outline-secondary:hover {{
  background-color: rgba(255, 255, 255, 0.08) !important;
  color: #ffffff !important;
}}
.btn-slate, .btn-slate.active, .btn-light.active, .btn-secondary.active {{
  background-color: #334155 !important; /* 深石板灰 */
  border-color: #64748b !important;
  color: #ffffff !important;
  box-shadow: 0 0 8px rgba(100, 116, 139, 0.3) !important;
}}

/* 異動按鈕內數量徽章樣式優化 */
.atab .badge {{
  font-size: 0.72rem;
  padding: 0.2em 0.55em;
  border-radius: 999px;
  background-color: rgba(255, 255, 255, 0.12) !important;
  color: #e2e8f0 !important;
}}
.atab.active .badge {{
  background-color: rgba(0, 0, 0, 0.45) !important;
  color: #ffffff !important;
  border: 1px solid rgba(255, 255, 255, 0.25) !important;
}}
</style>

<!-- ==================== SB ADMIN TOPNAV ==================== -->
<nav class="sb-topnav navbar navbar-expand navbar-dark bg-dark sticky-top border-bottom border-secondary-subtle">
  <!-- Navbar Brand -->
  <a class="navbar-brand ps-3 d-flex align-items-center text-decoration-none" href="#dashboard">
    <span class="fw-bold tracking-tight text-white fs-5">GETSTOCK</span>
    <span class="badge border border-secondary text-secondary ms-2 font-monospace" style="font-size: 0.65rem;">量化決策</span>
  </a>
  <!-- Sidebar Toggle -->
  <button class="btn btn-outline-secondary btn-sm order-1 order-lg-0 me-3 me-lg-0 text-light" id="sidebarToggle" type="button">
    選單
  </button>

  <!-- Navbar Search (頂部個股即時查詢與健檢) -->
  <div class="d-none d-md-flex form-inline ms-auto me-0 me-md-3 my-2 my-md-0 position-relative" style="width: 320px;">
    <div class="input-group input-group-sm w-100">
      <span class="input-group-text bg-dark border-secondary text-muted">搜尋</span>
      <input class="form-control bg-dark text-white border-secondary" type="text" id="docInput" placeholder="輸入代號/名稱 (如 2330)..." autocomplete="off" />
      <button class="btn btn-primary btn-sm fw-bold text-white" id="btnDocSearch" type="button">查詢</button>
    </div>
    <!-- 搜尋建議清單 Dropdown -->
    <div id="docSuggest" class="dropdown-menu shadow-lg w-100 mt-1" style="display:none; max-height:360px; overflow-y:auto; position:absolute; top:100%; left:0; z-index:1060;"></div>
  </div>

  <!-- Navbar Right Action Items -->
  <ul class="navbar-nav ms-auto ms-md-0 me-3 me-lg-4 align-items-center flex-row gap-2">
    <!-- Chips Radar Direct Link -->
    <li class="nav-item">
      <a class="btn btn-outline-info btn-sm text-nowrap text-cyan-300" href="#radarSection" title="直達籌碼五維雷達透視分析">
        籌碼雷達
      </a>
    </li>
    <!-- Theme Toggle (深色 / 淺色切換) -->
    <li class="nav-item">
      <button class="btn btn-outline-warning btn-sm text-warning" id="btnThemeToggle" title="切換深色/淺色主題">
        主題
      </button>
    </li>
    <!-- Status Badge -->
    <li class="nav-item d-none d-xl-inline-block">
      <span class="badge border border-secondary text-muted d-inline-flex align-items-center py-1.5 px-2">
        每日 22:00 定稿更新
      </span>
    </li>
  </ul>
</nav>

<!-- ==================== SB ADMIN LAYOUT ==================== -->
<div id="layoutSidenav">
  <!-- ===== 左側側欄 (Sidenav: 8大核心量化功能，精緻彩色層次指標) ===== -->
  <div id="layoutSidenav_nav">
    <nav class="sb-sidenav accordion sb-sidenav-dark" id="sidenavAccordion">
      <div class="sb-sidenav-menu">
        <div class="nav py-2">
          <!-- 分組 1: 核心決策 CORE (藍色微光指示) -->
          <div class="sb-sidenav-menu-heading px-3 py-2 text-uppercase fw-bold d-flex align-items-center" style="color: #93c5fd;">
            <span style="display:inline-block; width:7px; height:7px; border-radius:50%; background:#3b82f6; margin-right:8px; box-shadow:0 0 8px #3b82f6;"></span>
            核心決策 CORE
          </div>
          <a class="nav-link active py-2 px-3 side-item-blue" href="#dashboard">
            <span class="side-dot" style="background:#3b82f6;"></span>
            儀表板總覽
          </a>
          <a class="nav-link py-2 px-3 side-item-amber" href="#picks">
            <span class="side-dot" style="background:#f59e0b;"></span>
            量化籌碼精選
            <span class="badge ms-auto font-monospace side-badge-amber">40檔</span>
          </a>
          <a class="nav-link py-2 px-3 side-item-cyan" href="#radarSection">
            <span class="side-dot" style="background:#06b6d4;"></span>
            籌碼五維雷達
            <span class="badge ms-auto font-monospace side-badge-cyan">透視</span>
          </a>

          <!-- 分組 2: 盤面與異動 MARKET (琥珀金微光指示) -->
          <div class="sb-sidenav-menu-heading px-3 py-2 text-uppercase fw-bold d-flex align-items-center" style="color: #fcd34d;">
            <span style="display:inline-block; width:7px; height:7px; border-radius:50%; background:#f59e0b; margin-right:8px; box-shadow:0 0 8px #f59e0b;"></span>
            盤面與異動 MARKET
          </div>
          <a class="nav-link py-2 px-3 side-item-rose" href="#daytrade">
            <span class="side-dot" style="background:#f43f5e;"></span>
            當沖多空標的
            <span class="badge ms-auto font-monospace side-badge-rose">多空40</span>
          </a>
          <a class="nav-link py-2 px-3 side-item-purple" href="#anomalies">
            <span class="side-dot" style="background:#a855f7;"></span>
            跨日籌碼異常
            <span class="badge ms-auto font-monospace side-badge-purple" id="sideAnomBadge">0</span>
          </a>
          <a class="nav-link py-2 px-3 side-item-orange" href="#rankings">
            <span class="side-dot" style="background:#f97316;"></span>
            量能與週轉率前20
          </a>

          <!-- 分組 3: 分析工具 TOOLS (翠綠微光指示) -->
          <div class="sb-sidenav-menu-heading px-3 py-2 text-uppercase fw-bold d-flex align-items-center" style="color: #6ee7b7;">
            <span style="display:inline-block; width:7px; height:7px; border-radius:50%; background:#10b981; margin-right:8px; box-shadow:0 0 8px #10b981;"></span>
            分析工具 TOOLS
          </div>
          <a class="nav-link py-2 px-3 side-item-emerald" href="#doctor">
            <span class="side-dot" style="background:#10b981;"></span>
            個股籌碼健檢
            <span class="badge ms-auto font-monospace side-badge-emerald">550+檔</span>
          </a>
          <a class="nav-link py-2 px-3 side-item-indigo" href="#screener">
            <span class="side-dot" style="background:#6366f1;"></span>
            多因子策略選股
            <span class="badge ms-auto font-monospace side-badge-indigo">選股機</span>
          </a>
        </div>
      </div>
      <div class="sb-sidenav-footer border-top border-secondary-subtle">
        <div class="small text-muted">GETSTOCK 量化決策</div>
        <div class="small text-muted">證交所・櫃買每日 22:00</div>
      </div>
    </nav>
  </div>

  <!-- ===== 主內容區塊 (Content Area) ===== -->
  <div id="layoutSidenav_content">
    <main>
      <div class="container-fluid px-4 py-3" id="dashboard">
        <!-- 頂部標題與歷史交易日 -->
        <div class="d-flex flex-wrap align-items-center justify-content-between pt-2 pb-2 mb-3 border-bottom border-secondary-subtle">
          <div>
            <h1 class="h3 fw-bold mb-1 text-light">台股大戶籌碼與量化決策系統</h1>
            <div class="text-muted small" id="asof">資料載入中...</div>
          </div>
          <!-- 歷史交易日選擇 Bar -->
          <div class="d-flex align-items-center gap-2 mt-2 mt-sm-0">
            <span class="text-muted small text-nowrap">近一週交易日:</span>
            <div class="d-flex align-items-center gap-1 overflow-auto" id="history" style="max-width: 480px;"></div>
          </div>
        </div>

        <!-- 大盤指數跑馬燈卡片 -->
        <div class="card mb-3 shadow-sm border border-secondary-subtle" style="background:#181b20;">
          <div class="card-body py-2 px-3">
            <div class="d-flex align-items-center gap-3 overflow-auto text-nowrap no-scrollbar" id="indices">
              <span class="text-muted small" id="idxDate">大盤指數</span>
            </div>
          </div>
        </div>

        <!-- 4 大實戰指標卡 (黑白深灰極簡舒適，不刺眼) -->
        <div class="row g-3 mb-4">
          <!-- Card 1: 加權指數行情 -->
          <div class="col-xl-3 col-md-6">
            <div class="card h-100 shadow-sm border border-secondary-subtle" style="background:#181b20;">
              <div class="card-body p-3">
                <div class="text-muted small fw-medium">加權指數行情</div>
                <div class="fs-4 fw-bold num text-light mt-1" id="sbCardIdx">—</div>
                <div class="small text-muted mt-0.5" id="sbCardIdxSub">成交金額 — 億</div>
              </div>
              <div class="card-footer d-flex align-items-center justify-content-between small py-2 border-top border-secondary-subtle" style="background:rgba(0,0,0,0.15);">
                <a class="text-muted stretched-link text-decoration-none" href="#indices">大盤各類股指數 →</a>
              </div>
            </div>
          </div>

          <!-- Card 2: 盤後多因子共識 -->
          <div class="col-xl-3 col-md-6">
            <div class="card h-100 shadow-sm border border-secondary-subtle" style="background:#181b20;">
              <div class="card-body p-3">
                <div class="text-muted small fw-medium">盤後多因子共識</div>
                <div class="fs-5 fw-bold text-light text-truncate mt-1" style="max-width:240px;" id="sbCardAi">分析運算中...</div>
                <div class="small text-muted mt-0.5" id="sbCardAiSub">推薦平均分: —</div>
              </div>
              <div class="card-footer d-flex align-items-center justify-content-between small py-2 border-top border-secondary-subtle" style="background:rgba(0,0,0,0.15);">
                <a class="text-muted stretched-link text-decoration-none" href="#picks">瀏覽量化精選標的 →</a>
              </div>
            </div>
          </div>

          <!-- Card 3: 主力鎖碼焦點 -->
          <div class="col-xl-3 col-md-6">
            <div class="card h-100 shadow-sm border border-secondary-subtle" style="background:#181b20;">
              <div class="card-body p-3">
                <div class="text-muted small fw-medium">S+ 主力鎖碼標的</div>
                <div class="fs-4 fw-bold num text-light mt-1" id="sbCardLock">—</div>
                <div class="small text-muted mt-0.5" id="sbCardLockSub">土洋法人合買鎖碼</div>
              </div>
              <div class="card-footer d-flex align-items-center justify-content-between small py-2 border-top border-secondary-subtle" style="background:rgba(0,0,0,0.15);">
                <a class="text-muted stretched-link text-decoration-none" href="#radarSection">五維雷達因子拆解 →</a>
              </div>
            </div>
          </div>

          <!-- Card 4: 當沖與異動預警 -->
          <div class="col-xl-3 col-md-6">
            <div class="card h-100 shadow-sm border border-secondary-subtle" style="background:#181b20;">
              <div class="card-body p-3">
                <div class="text-muted small fw-medium">盤面異常與隔日當沖</div>
                <div class="fs-4 fw-bold num text-light mt-1" id="sbCardAnom">—</div>
                <div class="small text-muted mt-0.5" id="sbCardAnomSub">多空各 20 檔精準點位</div>
              </div>
              <div class="card-footer d-flex align-items-center justify-content-between small py-2 border-top border-secondary-subtle" style="background:rgba(0,0,0,0.15);">
                <a class="text-muted stretched-link text-decoration-none" href="#daytrade">查看當沖與異動名單 →</a>
              </div>
            </div>
          </div>
        </div>

        <!-- 盤後決策總覽與市場情緒指標卡片 -->
        <div class="card mb-4 shadow-sm border border-secondary-subtle" style="background:#181b20;">
          <div class="card-body py-3">
            <div class="d-flex flex-column flex-lg-row align-items-lg-center justify-content-between gap-2">
              <div>
                <div class="text-muted small fw-medium mb-1">盤後決策總覽與市場情緒指標</div>
                <h5 class="fw-bold mb-0 text-light" id="aiHeadline">大數據量化運算中...</h5>
              </div>
              <div class="d-flex flex-wrap gap-1" id="aiBadges"></div>
            </div>
          </div>
        </div>

        <!-- ===== 模組 1: 今日量化精選 40 檔 (Picks) ===== -->
        <div class="card mb-4 shadow-sm" id="picks">
          <div class="card-header py-3">
            <div class="d-flex flex-column flex-lg-row align-items-lg-center justify-content-between gap-3">
              <!-- 左側標題與統計 -->
              <div class="d-flex align-items-center gap-2">
                <h5 class="mb-0 fw-bold text-light" id="listTitle">上市量化精選</h5>
                <span class="badge border border-secondary text-light ms-1">共 <b id="sCount" class="num text-white">20</b> 檔</span>
                <span class="badge border border-secondary text-muted ms-1 d-none d-sm-inline">均分: <b id="sAvg" class="num text-light">82.5</b></span>
                <span class="small text-muted ms-2 d-none d-md-inline" id="genAt">資料定稿時間</span>
              </div>

              <!-- 右側工具列：市場切換、篩選、排序、檢視、匯出 -->
              <div class="d-flex flex-wrap align-items-center gap-2">
                <!-- 上市/上櫃切換 -->
                <div class="btn-group btn-group-sm" role="group">
                  <button type="button" data-market="上市" class="mk btn btn-outline-primary active">上市 20 檔</button>
                  <button type="button" data-market="上櫃" class="mk btn btn-outline-purple">上櫃 20 檔</button>
                  <button type="button" data-market="全部" class="mk btn btn-outline-indigo">全部 40 檔</button>
                </div>

                <!-- 排序選擇 -->
                <div class="input-group input-group-sm" style="width: auto;">
                  <label class="input-group-text bg-transparent text-muted small" for="sortBy">排序</label>
                  <select id="sortBy" class="form-select form-select-sm">
                    <option value="score">籌碼總分</option>
                    <option value="inst">法人買超</option>
                    <option value="big">大戶增持</option>
                    <option value="chg">今日漲幅</option>
                    <option value="vol">今日成交量</option>
                  </select>
                </div>

                <!-- 檢視模式切換 (卡片 / 表格) -->
                <div class="btn-group btn-group-sm" role="group">
                  <button type="button" id="btnViewCards" class="btn btn-sm btn-info active fw-bold text-white">卡片</button>
                  <button type="button" id="btnViewTable" class="btn btn-sm btn-outline-secondary text-light">表格</button>
                </div>

                <!-- 匯出 CSV -->
                <button type="button" id="btnExportCsv" class="btn btn-sm btn-outline-success font-medium" title="匯出推薦清單 CSV">
                  匯出 CSV
                </button>
              </div>
            </div>

            <!-- 條件快篩 Tag 列 -->
            <div class="d-flex align-items-center gap-1.5 overflow-auto no-scrollbar pt-2.5 mt-2 border-top border-secondary-subtle text-xs">
              <span class="text-muted me-1 flex-none">快篩:</span>
              <button type="button" data-filter="all" class="af btn btn-sm btn-slate active fw-bold py-0.5 px-2.5 rounded-pill flex-none">全部</button>
              <button type="button" data-filter="splus" class="af btn btn-sm btn-outline-amber py-0.5 px-2.5 rounded-pill flex-none">S+ 主力鎖碼</button>
              <button type="button" data-filter="dual" class="af btn btn-sm btn-outline-danger py-0.5 px-2.5 rounded-pill flex-none">土洋合買</button>
              <button type="button" data-filter="reversal" class="af btn btn-sm btn-outline-info py-0.5 px-2.5 rounded-pill flex-none">由賣轉買</button>
              <button type="button" data-filter="divergence" class="af btn btn-sm btn-outline-purple py-0.5 px-2.5 rounded-pill flex-none">價跌吃貨</button>
              <button type="button" data-filter="big" class="af btn btn-sm btn-outline-success py-0.5 px-2.5 rounded-pill flex-none">大戶增持 (≥0.4%)</button>
              <button type="button" data-filter="margin" class="af btn btn-sm btn-outline-orange py-0.5 px-2.5 rounded-pill flex-none">融資減少</button>
              <button type="button" data-filter="streak" class="af btn btn-sm btn-outline-indigo py-0.5 px-2.5 rounded-pill flex-none">連續上榜 (≥3日)</button>
            </div>
          </div>

          <div class="card-body p-3">
            <!-- 1. 卡片檢視模式 -->
            <div id="list" class="grid grid-cols-1 md:grid-cols-2 gap-3.5"></div>

            <!-- 2. 表格檢視模式 -->
            <div id="tableViewWrap" class="hidden table-responsive">
              <table class="table table-bordered table-hover align-middle mb-0 text-xs">
                <thead class="table-dark text-nowrap">
                  <tr>
                    <th class="py-2 px-2 text-center" style="width: 48px;">名次</th>
                    <th class="py-2 px-2">代號 / 股票</th>
                    <th class="py-2 px-2 text-end">收盤</th>
                    <th class="py-2 px-2 text-end">漲跌幅</th>
                    <th class="py-2 px-2 text-end text-light">買進區間</th>
                    <th class="py-2 px-2 text-end text-light">目標價 1/2</th>
                    <th class="py-2 px-2 text-end text-muted">停損價</th>
                    <th class="py-2 px-2 text-end">法人合計</th>
                    <th class="py-2 px-2 text-end">大戶週增</th>
                    <th class="py-2 px-2 text-end">融資增減</th>
                    <th class="py-2 px-2 text-end">總分</th>
                  </tr>
                </thead>
                <tbody id="tableRows"></tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- ===== 模組 2: 籌碼五維雷達透視分析 (獨立專區) ===== -->
        <div class="card mb-4 shadow-sm border border-secondary-subtle" id="radarSection">
          <div class="card-header py-3">
            <div class="d-flex flex-column flex-lg-row align-items-lg-center justify-content-between gap-2">
              <div>
                <div class="text-muted small">五維度量化因子全方位透視</div>
                <h5 class="mb-0 fw-bold text-light">
                  <span>籌碼五維雷達透視分析</span>
                </h5>
                <small class="text-muted">拆解五大關鍵籌碼維度：法人當日(25%)、法人5日(25%)、連買天數(10%)、大戶週增(25%)、融資退場(15%)</small>
              </div>

              <!-- 快速精選 Pills -->
              <div class="d-flex align-items-center gap-1.5 overflow-auto no-scrollbar" id="radarQuickPills"></div>
            </div>

            <!-- 維度切換列 -->
            <div class="d-flex align-items-center gap-1.5 overflow-auto no-scrollbar pt-2.5 mt-2 border-top border-secondary-subtle text-xs" id="radarFactorTabs">
              <span class="text-muted me-1 flex-none">維度排行:</span>
              <button type="button" data-factor="score" class="btn btn-sm btn-amber active fw-bold py-0.5 px-2.5 rounded-pill flex-none">總分排行</button>
              <button type="button" data-factor="inst" class="btn btn-sm btn-outline-info py-0.5 px-2.5 rounded-pill flex-none">法人當日</button>
              <button type="button" data-factor="big" class="btn btn-sm btn-outline-success py-0.5 px-2.5 rounded-pill flex-none">大戶週增</button>
              <button type="button" data-factor="streak" class="btn btn-sm btn-outline-purple py-0.5 px-2.5 rounded-pill flex-none">投信連買</button>
              <button type="button" data-factor="margin" class="btn btn-sm btn-outline-orange py-0.5 px-2.5 rounded-pill flex-none">融資清洗</button>
            </div>
          </div>

          <div class="card-body p-3">
            <div class="row g-3">
              <!-- 左側: 雷達圖與指標卡 (Col 6) -->
              <div class="col-lg-6" id="radarStockCard">
                <div class="p-4 text-center text-muted">載入五維雷達數據中...</div>
              </div>

              <!-- 右側: 維度天梯排行榜 (Col 6) -->
              <div class="col-lg-6">
                <div class="card h-100 shadow-sm border border-secondary-subtle" style="background:#181b20;">
                  <div class="card-header py-2.5 d-flex align-items-center justify-content-between border-bottom border-secondary-subtle">
                    <h6 class="mb-0 fw-bold small text-light">籌碼維度天梯排行（點擊任意列即可切換雷達）</h6>
                    <small class="text-muted">即時連動</small>
                  </div>
                  <div class="card-body p-0">
                    <div class="table-responsive" style="max-height: 520px; overflow-y: auto;">
                      <table class="table table-bordered table-hover align-middle mb-0 text-xs">
                        <thead class="table-dark sticky-top text-nowrap">
                          <tr>
                            <th class="py-2 text-center" style="width: 36px;">名次</th>
                            <th class="py-2">代號 / 股票</th>
                            <th class="py-2 text-end">收盤</th>
                            <th class="py-2 text-end">漲跌幅</th>
                            <th class="py-2" style="width: 100px;">五維細條</th>
                            <th class="py-2 text-end">總分</th>
                            <th class="py-2 text-center" style="width: 60px;">操作</th>
                          </tr>
                        </thead>
                        <tbody id="radarRankRows"></tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ===== 模組 3: 跨日籌碼異動追蹤 (Anomalies) ===== -->
        <div class="card mb-4 shadow-sm" id="anomalies">
          <div class="card-header py-3">
            <div class="d-flex flex-column flex-md-row align-items-md-center justify-content-between gap-2">
              <div>
                <div class="text-muted small" id="anomCompareDate">跨日籌碼軌跡追蹤</div>
                <h5 class="mb-0 fw-bold text-light">
                  <span>跨日大數據籌碼異常偵測</span>
                </h5>
              </div>
              <!-- 異動分類按鈕 -->
              <div class="d-flex align-items-center gap-1 overflow-auto no-scrollbar" id="anomTabs">
                <button type="button" data-atab="all" class="atab btn btn-sm btn-slate active fw-bold py-1 px-2.5 rounded-pill flex-none d-flex align-items-center gap-1.5">
                  <span>全部異動</span>
                  <span id="anomCntAll" class="badge rounded-pill bg-secondary text-white num">0</span>
                </button>
                <button type="button" data-atab="reversal" class="atab btn btn-sm btn-outline-info py-1 px-2.5 rounded-pill flex-none d-flex align-items-center gap-1.5">
                  <span>由賣轉買</span>
                  <span id="anomCntRev" class="badge rounded-pill bg-secondary text-white num">0</span>
                </button>
                <button type="button" data-atab="divergence" class="atab btn btn-sm btn-outline-purple py-1 px-2.5 rounded-pill flex-none d-flex align-items-center gap-1.5">
                  <span>價跌吃貨</span>
                  <span id="anomCntDiv" class="badge rounded-pill bg-secondary text-white num">0</span>
                </button>
                <button type="button" data-atab="consecutive" class="atab btn btn-sm btn-outline-indigo py-1 px-2.5 rounded-pill flex-none d-flex align-items-center gap-1.5">
                  <span>連續上榜</span>
                  <span id="anomCntConsec" class="badge rounded-pill bg-secondary text-white num">0</span>
                </button>
                <button type="button" data-atab="newsurge" class="atab btn btn-sm btn-outline-amber py-1 px-2.5 rounded-pill flex-none d-flex align-items-center gap-1.5">
                  <span>突襲新進</span>
                  <span id="anomCntSurge" class="badge rounded-pill bg-secondary text-white num">0</span>
                </button>
                <button type="button" data-atab="alerts" class="atab btn btn-sm btn-outline-danger py-1 px-2.5 rounded-pill flex-none d-flex align-items-center gap-1.5">
                  <span>籌碼警戒</span>
                  <span id="anomCntAlerts" class="badge rounded-pill bg-secondary text-white num">0</span>
                </button>
              </div>
            </div>
          </div>
          <div class="card-body p-3">
            <!-- 異動統計 KPI 列 -->
            <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2.5 mb-3" id="anomKpiBar"></div>
            <!-- 產業資金輪動列 -->
            <div class="rounded-xl border border-white/10 bg-slate-900/60 p-2.5 mb-3 text-xs flex flex-wrap items-center gap-2" id="sectorShiftBar"></div>
            <!-- 異動卡片列表 -->
            <div id="anomGrid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3"></div>
          </div>
        </div>

        <!-- ===== 模組 4: 當沖標的 (Day Trade) ===== -->
        <div class="card mb-4 shadow-sm" id="daytrade">
          <div class="card-header py-3">
            <div class="d-flex flex-column flex-md-row align-items-md-center justify-content-between gap-2">
              <div>
                <div class="text-muted small" id="dtAsof">隔日當沖參考名單</div>
                <h5 class="mb-0 fw-bold text-light" id="dtTitle">
                  當沖標的（含進場/停利/停損試算）
                </h5>
                <p id="dtDesc" class="text-muted small mb-0 mt-1"></p>
              </div>
              <!-- 做多/做空切換 -->
              <div class="btn-group btn-group-sm flex-none" role="group">
                <button type="button" id="dt-long" data-side="long" class="dts btn btn-danger active fw-bold">做多 20 檔 (先買後賣)</button>
                <button type="button" id="dt-short" data-side="short" class="dts btn btn-outline-success">做空 20 檔 (先賣後買)</button>
              </div>
            </div>
          </div>
          <div class="card-body p-0">
            <div class="table-responsive">
              <table class="table table-bordered table-hover align-middle mb-0 text-xs">
                <thead class="table-dark text-nowrap">
                  <tr>
                    <th class="py-2.5 px-2 text-center" style="width: 44px;">名次</th>
                    <th class="py-2.5 px-2">代號 / 股票 / 當沖理由</th>
                    <th class="py-2.5 px-2 text-end">收盤</th>
                    <th class="py-2.5 px-2 text-end">漲跌幅</th>
                    <th class="py-2.5 px-2 text-end text-light" id="dtColEntry">當沖進場點</th>
                    <th class="py-2.5 px-2 text-end text-light" id="dtColTarget">停利目標 1/2</th>
                    <th class="py-2.5 px-2 text-end text-muted" id="dtColStop">停損點</th>
                    <th class="py-2.5 px-2 text-end">週轉/當沖比</th>
                    <th class="py-2.5 px-2 text-end">量增/法人</th>
                    <th class="py-2.5 px-2 text-end">分數</th>
                  </tr>
                </thead>
                <tbody id="dtRows"></tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- ===== 模組 5: 個股籌碼全方位健檢與部位試算 (Doctor) ===== -->
        <div class="card mb-4 shadow-sm" id="doctor">
          <div class="card-header py-3">
            <div class="d-flex flex-column flex-md-row align-items-md-center justify-content-between gap-3">
              <div>
                <div class="text-muted small" id="docPoolCount">全市場 550+ 檔即時數據</div>
                <h5 class="mb-0 fw-bold text-light">
                  個股籌碼全方位健檢與部位試算
                </h5>
                <small class="text-muted">輸入代號或名稱，即時查詢法人持股動向、日K量價圖與操作點位</small>
              </div>
              <!-- 診斷專用搜尋輸入 -->
              <div class="position-relative" style="min-width: 280px;">
                <div class="input-group input-group-sm">
                  <span class="input-group-text bg-secondary text-white-50">搜尋</span>
                  <input type="text" id="docSectionSearch" class="form-control" placeholder="搜尋個股 (如 2330 台積電)..." autocomplete="off" />
                  <button type="button" id="btnClearDocSection" class="btn btn-outline-danger text-danger hidden">✕</button>
                </div>
                <div id="docSectionSuggest" class="dropdown-menu shadow-lg w-100 mt-1" style="display:none; max-height:320px; overflow-y:auto; position:absolute; top:100%; left:0; z-index:1060;"></div>
              </div>
            </div>
            <!-- 快速標的 Pills -->
            <div class="d-flex align-items-center gap-1.5 overflow-auto no-scrollbar pt-2.5 mt-2 border-top border-secondary-subtle text-xs" id="docQuickPills"></div>
          </div>
          <div class="card-body p-3">
            <!-- 診斷主面板 -->
            <div id="docPanel" class="grid grid-cols-1 lg:grid-cols-2 gap-4"></div>

            <!-- 個人部位風險試算工具 (預設本金 0 元) -->
            <div class="mt-4 rounded-xl border border-white/10 bg-slate-900/60 p-4">
              <div class="d-flex align-items-center justify-content-between mb-3">
                <h6 class="mb-0 fw-bold text-light">個人部位與風險試算</h6>
                <small class="text-muted">依當前選定股票之進場點與停損價試算</small>
              </div>
              <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-sm">
                <div>
                  <label class="text-slate-400 block mb-1 text-xs">投入本金 (元):</label>
                  <input type="number" id="calcCapital" value="0" step="10000"
                    class="w-full bg-slate-950 border border-white/15 focus:border-white rounded-lg px-3 py-2 text-white outline-none num font-medium text-sm">
                </div>
                <div>
                  <label class="text-slate-400 block mb-1 text-xs">最大承受風險比率:</label>
                  <select id="calcRiskPct" class="w-full bg-slate-950 border border-white/15 focus:border-white rounded-lg px-3 py-2 text-white outline-none cursor-pointer text-sm">
                    <option value="1">1% (極保守)</option>
                    <option value="2" selected>2% (標準紀律)</option>
                    <option value="3">3% (波段操作)</option>
                    <option value="5">5% (積極)</option>
                  </select>
                </div>
                <div class="rounded-lg bg-slate-950 p-3 flex flex-col justify-center border border-white/5">
                  <span class="text-slate-400 text-xs">建議買進股數</span>
                  <b id="calcShares" class="text-lg text-white num font-bold mt-0.5">0 股 (0.00 張)</b>
                  <span id="calcCost" class="text-xs text-slate-400 truncate mt-0.5">需投入本金 $0 元</span>
                </div>
                <div class="rounded-lg bg-slate-950 p-3 flex flex-col justify-center border border-white/5">
                  <span class="text-slate-400 text-xs">觸發停損最大虧損</span>
                  <b id="calcMaxLoss" class="text-lg text-slate-300 num font-bold mt-0.5">$0 元</b>
                  <span id="calcStopPrice" class="text-xs text-slate-400 truncate mt-0.5">—</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ===== 模組 6: 多因子策略選股 (Screener) ===== -->
        <div class="card mb-4 shadow-sm" id="screener">
          <div class="card-header py-3">
            <div class="d-flex flex-column flex-md-row align-items-md-center justify-content-between gap-2">
              <div>
                <div class="text-muted small" id="scrCountInfo">全市場多因子條件篩選</div>
                <h5 class="mb-0 fw-bold text-light">
                  多因子策略選股機
                </h5>
              </div>
              <button type="button" id="btnExportScreenerCsv" class="btn btn-sm btn-outline-success font-medium">
                匯出篩選結果 CSV
              </button>
            </div>
            <!-- 策略快選 Tag -->
            <div class="d-flex align-items-center gap-1.5 overflow-auto no-scrollbar pt-2.5 mt-2 border-top border-secondary-subtle text-xs" id="scrPresets">
              <span class="text-muted me-1 flex-none">策略:</span>
              <button type="button" data-preset="top" class="spreset btn btn-sm btn-amber active fw-bold py-0.5 px-2.5 rounded-pill flex-none">綜合首選</button>
              <button type="button" data-preset="dual" class="spreset btn btn-sm btn-outline-danger py-0.5 px-2.5 rounded-pill flex-none">土洋合買</button>
              <button type="button" data-preset="trust" class="spreset btn btn-sm btn-outline-info py-0.5 px-2.5 rounded-pill flex-none">投信連買</button>
              <button type="button" data-preset="whale" class="spreset btn btn-sm btn-outline-success py-0.5 px-2.5 rounded-pill flex-none">大戶增持</button>
              <button type="button" data-preset="squeeze" class="spreset btn btn-sm btn-outline-orange py-0.5 px-2.5 rounded-pill flex-none">券增資減</button>
              <button type="button" data-preset="dipbuy" class="spreset btn btn-sm btn-outline-cyan py-0.5 px-2.5 rounded-pill flex-none">拉回低接</button>
              <button type="button" data-preset="turnaround" class="spreset btn btn-sm btn-outline-purple py-0.5 px-2.5 rounded-pill flex-none">由賣轉買</button>
              <button type="button" data-preset="blacklist" class="spreset btn btn-sm btn-outline-danger py-0.5 px-2.5 rounded-pill flex-none">法人連續賣超</button>
            </div>
          </div>
          <div class="card-body p-3">
            <!-- 自訂條件過濾表單 -->
            <div class="row g-2 mb-3 text-xs">
              <div class="col-6 col-md-2">
                <select id="scrMarket" class="form-select form-select-sm">
                  <option value="全部">全部市場</option>
                  <option value="上市">上市</option>
                  <option value="上櫃">上櫃</option>
                </select>
              </div>
              <div class="col-6 col-md-2">
                <select id="scrSector" class="form-select form-select-sm">
                  <option value="全部">全部產業</option>
                </select>
              </div>
              <div class="col-6 col-md-2">
                <select id="scrPrice" class="form-select form-select-sm">
                  <option value="all">不限股價</option>
                  <option value="low">10~50 元</option>
                  <option value="mid">50~150 元</option>
                  <option value="high">150 元以上</option>
                </select>
              </div>
              <div class="col-6 col-md-2">
                <select id="scrSort" class="form-select form-select-sm">
                  <option value="score">依籌碼總分排序</option>
                  <option value="inst">依法人買超排序</option>
                  <option value="big">依大戶週增排序</option>
                  <option value="chg">依今日漲幅排序</option>
                  <option value="vol">依成交量排序</option>
                </select>
              </div>
              <div class="col-6 col-md-2 d-flex align-items-center gap-1.5 px-2">
                <span class="text-muted text-nowrap">分數≥</span>
                <input type="range" id="scrMinScore" min="0" max="90" step="5" value="0" class="form-range">
                <span id="scrMinScoreVal" class="num text-white font-bold text-nowrap">0分</span>
              </div>
              <div class="col-6 col-md-2">
                <input type="text" id="scrQuery" placeholder="過濾代號/名稱..." class="form-control form-control-sm">
              </div>
            </div>

            <!-- 選股結果表格 -->
            <div class="table-responsive">
              <table class="table table-bordered table-hover align-middle mb-0 text-xs">
                <thead class="table-dark text-nowrap">
                  <tr>
                    <th class="py-2.5 px-2 text-center" style="width: 40px;">名次</th>
                    <th class="py-2.5 px-2">代號 / 股票</th>
                    <th class="py-2.5 px-2">產業</th>
                    <th class="py-2.5 px-2 text-end">收盤</th>
                    <th class="py-2.5 px-2 text-end">漲跌幅</th>
                    <th class="py-2.5 px-2 text-end">今日法人</th>
                    <th class="py-2.5 px-2 text-end">5日法人</th>
                    <th class="py-2.5 px-2 text-end">大戶週增</th>
                    <th class="py-2.5 px-2 text-end">融資增減</th>
                    <th class="py-2.5 px-2 text-end text-light">買進區間</th>
                    <th class="py-2.5 px-2 text-end text-light">目標 / 停損</th>
                    <th class="py-2.5 px-2 text-end">分數</th>
                  </tr>
                </thead>
                <tbody id="scrRows"></tbody>
              </table>
            </div>

            <div class="text-center mt-3">
              <button type="button" id="btnScrMore" class="btn btn-sm btn-outline-info px-4">載入更多 ↓</button>
            </div>
          </div>
        </div>

        <!-- ===== 模組 7: 成交量與週轉率前 20 名排行 (Rankings) ===== -->
        <div class="row g-3 mb-4" id="rankings">
          <!-- 成交量排行 -->
          <div class="col-lg-6">
            <div class="card h-100 shadow-sm border border-secondary-subtle">
              <div class="card-header py-2.5 d-flex align-items-center justify-content-between border-bottom border-secondary-subtle">
                <h6 class="mb-0 fw-bold text-light" id="voTitle">上市成交量前 20 名</h6>
                <small class="text-muted">市場資金最集中標的（張）</small>
              </div>
              <div class="card-body p-0">
                <div class="table-responsive">
                  <table class="table table-bordered table-hover align-middle mb-0 text-xs">
                    <thead class="table-dark text-nowrap">
                      <tr>
                        <th class="py-2 px-2 text-center" style="width: 40px;">名次</th>
                        <th class="py-2 px-2">股票</th>
                        <th class="py-2 px-2 text-end">收盤</th>
                        <th class="py-2 px-2 text-end">漲跌幅</th>
                        <th class="py-2 px-2 text-end">金額(億)</th>
                        <th class="py-2 px-2 text-end">週轉率</th>
                        <th class="py-2 px-2 text-end">成交量(張)</th>
                      </tr>
                    </thead>
                    <tbody id="voRows"></tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>

          <!-- 週轉率排行 -->
          <div class="col-lg-6">
            <div class="card h-100 shadow-sm border border-secondary-subtle">
              <div class="card-header py-2.5 d-flex align-items-center justify-content-between border-bottom border-secondary-subtle">
                <h6 class="mb-0 fw-bold text-light" id="toTitle">上市週轉率前 20 名</h6>
                <small class="text-muted">換手最熱絡標的（成交÷發行）</small>
              </div>
              <div class="card-body p-0">
                <div class="table-responsive">
                  <table class="table table-bordered table-hover align-middle mb-0 text-xs">
                    <thead class="table-dark text-nowrap">
                      <tr>
                        <th class="py-2 px-2 text-center" style="width: 40px;">名次</th>
                        <th class="py-2 px-2">股票</th>
                        <th class="py-2 px-2 text-end">收盤</th>
                        <th class="py-2 px-2 text-end">漲跌幅</th>
                        <th class="py-2 px-2 text-end">成交量(張)</th>
                        <th class="py-2 px-2 text-end">金額(億)</th>
                        <th class="py-2 px-2 text-end">週轉率</th>
                      </tr>
                    </thead>
                    <tbody id="toRows"></tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- ===== 頁尾 ===== -->
    <footer class="py-3 mt-auto border-top border-secondary-subtle" style="background:#121417;">
      <div class="container-fluid px-4">
        <div class="d-flex flex-wrap align-items-center justify-content-between small text-muted gap-2">
          <div class="fw-bold">
            GETSTOCK 台股量化決策系統 &copy; 2026
          </div>
          <div class="d-flex align-items-center gap-3">
            <a href="#dashboard" class="text-muted text-decoration-none">回到頂部 ↑</a>
            <a href="#radarSection" class="text-muted text-decoration-none">籌碼五維雷達</a>
            <a href="https://www.twse.com.tw/" target="_blank" rel="noopener" class="text-muted text-decoration-none">證交所</a>
            <a href="https://www.tpex.org.tw/" target="_blank" rel="noopener" class="text-muted text-decoration-none">櫃買中心</a>
          </div>
        </div>
      </div>
    </footer>
  </div>
</div>

<!-- ==================== 前端核心 JAVASCRIPT ==================== -->
<script>
{clean_js}
</script>
'''

output_path = os.path.join(BASE, "site_template.html")
with open(output_path, "w", encoding="utf-8") as f:
    f.write(sb_template_html)

print("成功輸出 site_template.html，總大小:", len(sb_template_html))
