# -*- coding: utf-8 -*-
"""
產生簡潔、高效、無贅餘的旗艦版 site_template.html
依使用者指示，完全移除：
1. 我的自選股追蹤清單
2. 歷史推薦勝率回測
3. 台股投資新手到老手看盤指南 (操盤教學)
4. 系統免責聲明
保留純粹、專業、好看易讀且 User-Friendly 的 8 大量化決策工具模組：
- 儀表板總覽 (指數、4大KPI卡、盤後決策指標)
- 量化籌碼精選 40 檔 (上市/上櫃、多因子篩選、卡片/表格、CSV匯出)
- 籌碼五維雷達透視分析 (獨立專區、五維圖形、天梯排行榜)
- 跨日大數據籌碼異常 (由賣轉買、價跌吃貨、連續上榜、警戒)
- 當沖多空標的 (做多/做空各20檔、精準點位、當沖比)
- 個股籌碼全方位健檢 (法人明細、日K技術圖、部位風險試算)
- 多因子策略選股機 (8大策略、產業/價格/分數篩選、CSV匯出)
- 量能與週轉率前 20 名排行 (上市量能前20、週轉率前20)
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

# 自選星號鈕改為空字串，徹底清爽
clean_js = re.sub(r'function starBtn\(code\)\s*\{.*?\n  \}', 'function starBtn(code) { return ""; }', clean_js, flags=re.S)

# 替換 gradeBadge 為純粹量化評級標籤
new_grade_badge = """
  function gradeBadge(grade) {
    if (!grade) return "";
    const g = String(grade).replace(/^AI\\s*/, "").trim();
    if (g === "S+") {
      return `<span class="badge bg-warning text-dark fw-bold px-2 py-0.5"><i class="fas fa-crown me-1"></i>S+ 主力鎖碼</span>`;
    }
    if (g === "A+") {
      return `<span class="badge bg-primary fw-bold px-2 py-0.5"><i class="fas fa-shield-alt me-1"></i>A+ 籌碼集中</span>`;
    }
    if (g === "A") {
      return `<span class="badge bg-info text-dark fw-bold px-2 py-0.5"><i class="fas fa-check-circle me-1"></i>A 穩健多頭</span>`;
    }
    if (g.startsWith("D")) {
      return `<span class="badge bg-danger fw-bold px-2 py-0.5"><i class="fas fa-exclamation-triangle me-1"></i>D 籌碼警戒</span>`;
    }
    return `<span class="badge bg-secondary px-2 py-0.5">${g}</span>`;
  }
"""
clean_js = re.sub(r'function gradeBadge\(grade\)\s*\{.*?\n  \}', lambda m: new_grade_badge.strip(), clean_js, flags=re.S)

# 移除 renderAcademy, renderBacktest, renderWatchlist 函數定義，改為空實現以防萬一
clean_js = re.sub(r'function renderAcademy\(\)\s*\{.*?\n  \}', 'function renderAcademy() {}', clean_js, flags=re.S)
clean_js = re.sub(r'function renderBacktest\(\)\s*\{.*?\n  \}', 'function renderBacktest() {}', clean_js, flags=re.S)
clean_js = re.sub(r'function renderWatchlist\(\)\s*\{.*?\n  \}', 'function renderWatchlist() {}', clean_js, flags=re.S)

# 徹底移除已不存在的自選股監聽器（避免 null.addEventListener 阻斷執行）
clean_js = re.sub(
    r'\$\("btnToggleWatch"\)\.addEventListener[\s\S]*?\$\("btnClearWatch"\)\.addEventListener[\s\S]*?\}\);\s*',
    '',
    clean_js
)

# 檢視模式切換（適配 SB Admin Bootstrap 按鈕風格）
new_view_toggle = """
  if ($("btnViewCards")) {
    $("btnViewCards").addEventListener("click", () => {
      state.viewMode = "cards";
      $("btnViewCards").className = "btn btn-sm btn-light active fw-bold";
      $("btnViewTable").className = "btn btn-sm btn-outline-secondary";
      render();
    });
  }
  if ($("btnViewTable")) {
    $("btnViewTable").addEventListener("click", () => {
      state.viewMode = "table";
      $("btnViewTable").className = "btn btn-sm btn-light active fw-bold";
      $("btnViewCards").className = "btn btn-sm btn-outline-secondary";
      render();
    });
  }
"""
clean_js = re.sub(
    r'\$\("btnViewCards"\)\.addEventListener[\s\S]*?\$\("btnViewTable"\)\.addEventListener[\s\S]*?\}\);\s*',
    lambda m: new_view_toggle.strip(),
    clean_js
)

# 增強 KPI 狀態卡（改為：加權指數、盤後共識、S+ 主力鎖碼、當沖與異動）
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
          <button type="button" data-radar-load="${x.code}" class="btn btn-sm py-0.5 px-2.5 rounded-pill ${x.code === p.code ? 'btn-primary' : 'btn-outline-secondary'}">
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

    if (fNet > 0 && tNet > 0) factorBadges.push(`<span class="badge bg-warning-subtle text-warning border border-warning">土洋合買</span>`);
    if (fStreak >= 2) factorBadges.push(`<span class="badge bg-primary-subtle text-primary border border-primary">外資連買 ${fStreak} 日</span>`);
    if (tStreak >= 2) factorBadges.push(`<span class="badge bg-success-subtle text-success border border-success">投信連買 ${tStreak} 日</span>`);
    if (bigChg != null && bigChg >= 0.3) factorBadges.push(`<span class="badge bg-warning-subtle text-warning border border-warning">大戶週增 +${bigChg.toFixed(2)}%</span>`);
    if (marginChg < -50) factorBadges.push(`<span class="badge bg-success-subtle text-success border border-success">融資清洗 ${Math.abs(marginChg)} 張</span>`);

    if ($("radarStockCard")) {
      $("radarStockCard").innerHTML = `
        <div class="card h-100 shadow-sm border-secondary-subtle">
          <div class="card-header py-3 d-flex align-items-center justify-content-between">
            <div class="d-flex align-items-center gap-2">
              <h5 class="mb-0 fw-bold text-white">${p.name}</h5>
              <span class="text-muted num small">(${p.code})</span>
              <span class="badge bg-secondary small">${p.market}・${p.sector || "其他"}</span>
              ${gradeBadge(p.aiGrade)}
            </div>
            <div>
              <button type="button" data-diagnose="${p.code}" class="btn btn-sm btn-outline-info">
                <i class="fas fa-stethoscope me-1"></i>籌碼健檢
              </button>
            </div>
          </div>
          <div class="card-body p-3">
            <!-- 報價與五維分數環 -->
            <div class="d-flex align-items-center justify-content-between pb-3 mb-3 border-bottom border-secondary-subtle">
              <div>
                <div class="d-flex align-items-baseline gap-2">
                  <span class="fs-2 fw-bold num">${fmt(p.close)}</span>
                  <span class="badge fs-6 num ${p.chg > 0 ? 'up-badge' : p.chg < 0 ? 'down-badge' : 'bg-secondary'}">
                    ${p.chg > 0 ? '+' : ''}${(p.chg || 0).toFixed(2)}%
                  </span>
                </div>
                <div class="small text-muted num mt-1">成交量 ${fmt(p.vol)} 張 ｜ 5日均線: <b class="text-white">${tp.ma5 || '—'}</b></div>
              </div>
              <div class="d-flex align-items-center gap-3">
                <div class="text-end">
                  <span class="text-muted small d-block">籌碼量化總分</span>
                  <b class="fs-4 num text-warning">${p.rawScore || p.score || 0}</b><span class="text-muted small">/100</span>
                </div>
                <div class="ring ${String(p.aiGrade || "").includes("S+") ? 's-plus' : ''}" style="--p:${p.score || 50}" title="總分 ${p.score}">
                  <span class="num font-black">${p.score || '—'}</span>
                </div>
              </div>
            </div>

            <!-- 特徵標籤 -->
            <div class="d-flex flex-wrap gap-1 mb-3">
              ${factorBadges.join("") || '<span class="badge bg-secondary">籌碼結構持平</span>'}
            </div>

            <!-- SVG 五維雷達圖 -->
            <div class="py-2 text-center bg-dark-subtle rounded-3 mb-3 border border-secondary-subtle">
              ${radarSvg(parts)}
            </div>

            <!-- 五維度詳細得分卡 -->
            <div class="row g-2 text-center text-xs num">
              ${PART_DEFS.map(([k, lbl, c, maxV]) => `
                <div class="col">
                  <div class="p-2 rounded bg-dark-subtle border border-secondary-subtle">
                    <span class="text-muted d-block text-truncate" style="font-size:0.75rem;">${lbl}</span>
                    <b class="fs-6 fw-bold text-white">${(parts[k] || 0).toFixed(1)}</b>
                    <span class="text-muted" style="font-size:0.7rem;">/${maxV}</span>
                  </div>
                </div>
              `).join("")}
            </div>

            <!-- 操作區間指引 -->
            <div class="mt-3 p-2.5 rounded bg-dark-subtle border border-secondary-subtle small num">
              <div class="d-flex justify-content-between mb-1">
                <span class="text-muted">建議布局區間:</span>
                <b class="text-emerald-400">${tp.buyZone || "—"} (突破買點: ${tp.breakoutBuy || "—"})</b>
              </div>
              <div class="d-flex justify-content-between mb-1">
                <span class="text-muted">目標價位 1/2:</span>
                <b class="text-warning">${tp.sellTarget1 || "—"} / ${tp.sellTarget2 || "—"}</b>
              </div>
              <div class="d-flex justify-content-between">
                <span class="text-muted">防守停損價位:</span>
                <b class="text-danger">${tp.stopLoss || "—"} (${tp.stopPct || -4}%)</b>
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
          <tr class="${isCurrent ? 'table-primary' : ''} cursor-pointer text-xs" data-radar-load="${x.code}">
            <td class="text-center num fw-bold ${idx < 3 ? 'text-warning' : 'text-muted'}">${idx + 1}</td>
            <td>
              <span class="fw-bold ${isCurrent ? 'text-primary' : 'text-white'}">${x.name}</span>
              <span class="text-muted num small ms-1">(${x.code})</span>
            </td>
            <td class="text-end num">${fmt(x.close)}</td>
            <td class="text-end num ${cls(x.chg)} font-bold">${x.chg > 0 ? '+' : ''}${(x.chg || 0).toFixed(2)}%</td>
            <td style="min-width: 100px;">
              <div class="score-bar">${scoreBar}</div>
            </td>
            <td class="text-end num fw-bold text-warning">${x.rawScore || x.score || 0}</td>
            <td class="text-center">
              <button type="button" data-radar-load="${x.code}" class="btn btn-sm ${isCurrent ? 'btn-primary' : 'btn-outline-secondary'} py-0 px-2 text-xs">
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
        document.querySelectorAll("#radarFactorTabs button").forEach(btn => {
          if (btn.dataset.factor === state.radarFactor) {
            btn.className = "btn btn-sm btn-primary active font-bold";
          } else {
            btn.className = "btn btn-sm btn-outline-secondary";
          }
        });
        renderRadarFactorTable();
      }
    });
  }

  // ===== SB Admin 主題切換與側欄整合 =====
  const themeToggle = document.getElementById("btnThemeToggle");
  const themeIcon = document.getElementById("themeIcon");
  let currentTheme = localStorage.getItem("sb|theme") || "theme-dark";
  document.body.classList.remove("theme-dark", "theme-light");
  document.body.classList.add(currentTheme);
  document.body.classList.add("sb-nav-fixed");
  if (themeIcon) {
    themeIcon.className = currentTheme === "theme-dark" ? "fas fa-moon text-warning" : "fas fa-sun text-warning";
  }
  if (themeToggle) {
    themeToggle.addEventListener("click", () => {
      currentTheme = currentTheme === "theme-dark" ? "theme-light" : "theme-dark";
      document.body.classList.remove("theme-dark", "theme-light");
      document.body.classList.add(currentTheme);
      localStorage.setItem("sb|theme", currentTheme);
      if (themeIcon) {
        themeIcon.className = currentTheme === "theme-dark" ? "fas fa-moon text-warning" : "fas fa-sun text-warning";
      }
    });
  }

  // 行動端點擊側選單時自動收合側欄
  document.querySelectorAll("#layoutSidenav_nav a.nav-link").forEach((link) => {
    link.addEventListener("click", () => {
      const hash = link.getAttribute("href");
      if (hash && hash.startsWith("#")) {
        document.querySelectorAll("#layoutSidenav_nav a.nav-link").forEach((t) => {
          if (t.getAttribute("href") === hash) t.classList.add("active");
          else t.classList.remove("active");
        });
      }
      if (window.innerWidth < 992) {
        document.body.classList.remove("sb-sidenav-toggled");
      }
    });
  });
"""

# 側欄導航高亮監聽器（排除已移除的章節）
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

# 構建全新極簡乾淨的 HTML 介面模板
sb_template_html = f'''<!-- GETSTOCK 台股大戶籌碼與量化決策系統 - 精簡專業版 -->
<title>GETSTOCK 大戶籌碼與量化選股決策系統</title>
<meta charset="utf-8">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
<meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
<link rel="icon" href="images/logo.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+TC:wght@400;500;600;700&family=Roboto+Mono:wght@500;600;700&display=swap" rel="stylesheet">
<link href="css/styles.css" rel="stylesheet" />
<script src="https://use.fontawesome.com/releases/v6.3.0/js/all.js" crossorigin="anonymous"></script>
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
  --up: #ef4444;      /* 台股紅漲 / 買超 */
  --up-bg: rgba(239, 68, 68, 0.12);
  --down: #10b981;    /* 台股綠跌 / 賣超 */
  --down-bg: rgba(16, 185, 129, 0.12);
  --flat: #6c757d;
  --font-num: "Roboto Mono", Consolas, monospace;
  --s1: #3b82f6; --s2: #f97316; --s3: #10b981; --s4: #eab308; --s5: #ec4899;
}}

/* 數字等寬排版與標準配色 */
.num {{ font-family: var(--font-num); font-variant-numeric: tabular-nums; }}
.up {{ color: var(--up) !important; font-weight: 600; }}
.down {{ color: var(--down) !important; font-weight: 600; }}
.flat {{ color: var(--flat) !important; }}
.up-badge {{ color: var(--up) !important; background-color: var(--up-bg) !important; border: 1px solid rgba(239, 68, 68, 0.3); }}
.down-badge {{ color: var(--down) !important; background-color: var(--down-bg) !important; border: 1px solid rgba(16, 185, 129, 0.3); }}

/* 隱藏原生滾動條與隱藏元素 */
.no-scrollbar::-webkit-scrollbar {{ display: none; }}
.no-scrollbar {{ -ms-overflow-style: none; scrollbar-width: none; }}
.hidden {{ display: none !important; }}

/* 籌碼五維條 */
.score-bar {{ display: flex; height: 6px; border-radius: 999px; background: rgba(128,128,128,0.2); overflow: hidden; gap: 1px; }}
.score-bar i {{ display: block; height: 100%; transition: opacity 0.15s; }}
.score-bar i:hover {{ opacity: 0.85; }}

/* 圓環進度圈 */
.ring {{ --p: 80; width: 44px; height: 44px; border-radius: 50%; display: grid; place-items: center; flex: none;
  background: conic-gradient(#38bdf8 calc(var(--p) * 1%), rgba(128,128,128,0.2) 0); }}
.ring.s-plus {{ background: conic-gradient(#f59e0b calc(var(--p) * 1%), rgba(128,128,128,0.2) 0); }}
.ring.danger {{ background: conic-gradient(#ef4444 calc(var(--p) * 1%), rgba(128,128,128,0.2) 0); }}
.ring span {{ width: 34px; height: 34px; border-radius: 50%; background: #0e1524; display: grid; place-items: center; font-weight: 700; font-size: 13px; color: #fff; }}
body.theme-light .ring span {{ background: #ffffff; color: #111827; }}

/* 卡片互動回饋 */
.stock-card {{
  transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
}}
.stock-card:hover {{
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
  border-color: rgba(56, 189, 248, 0.4) !important;
}}

/* ===== 深色主題 (theme-dark) ===== */
body.theme-dark {{
  background-color: #0b0f19;
  color: #e2e8f0;
}}
body.theme-dark #layoutSidenav_content {{
  background-color: #0b0f19;
}}
body.theme-dark .card {{
  background-color: #151d2c;
  border-color: rgba(255, 255, 255, 0.08);
  color: #e2e8f0;
}}
body.theme-dark .card-header {{
  background-color: rgba(255, 255, 255, 0.03);
  border-bottom-color: rgba(255, 255, 255, 0.08);
  color: #f8fafc;
}}
body.theme-dark .card-footer {{
  background-color: rgba(0, 0, 0, 0.2);
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
  background-color: rgba(255, 255, 255, 0.06);
  color: #ffffff;
}}
body.theme-dark .form-control, body.theme-dark .form-select {{
  background-color: #0b0f19;
  border-color: rgba(255, 255, 255, 0.15);
  color: #f8fafc;
}}
body.theme-dark .form-control:focus, body.theme-dark .form-select:focus {{
  background-color: #111827;
  border-color: #3b82f6;
  color: #ffffff;
}}
body.theme-dark .dropdown-menu {{
  background-color: #1e293b;
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
  background-color: #090d16 !important;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}}
body.theme-dark .breadcrumb-item.active {{
  color: #94a3b8;
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

/* 側欄外觀 */
.sb-topnav .navbar-brand {{
  width: 225px;
  margin: 0;
}}
.sb-sidenav-dark .sb-sidenav-menu .sb-sidenav-menu-heading {{
  font-size: 0.7rem;
  letter-spacing: 0.05em;
  padding: 1.25rem 1rem 0.5rem;
}}
.sb-sidenav .nav-link {{
  display: flex;
  align-items: center;
  padding-top: 0.65rem;
  padding-bottom: 0.65rem;
  font-size: 0.85rem;
}}
.sb-sidenav .nav-link.active {{
  color: #fff !important;
  font-weight: 600;
  background-color: rgba(255, 255, 255, 0.08);
}}
</style>

<!-- ==================== SB ADMIN TOPNAV ==================== -->
<nav class="sb-topnav navbar navbar-expand navbar-dark bg-dark sticky-top">
  <!-- Navbar Brand -->
  <a class="navbar-brand ps-3 d-flex align-items-center text-decoration-none" href="#dashboard">
    <i class="fas fa-chart-line text-warning me-2"></i>
    <span class="fw-bold tracking-tight">GETSTOCK</span>
    <span class="badge bg-danger ms-2 font-monospace text-uppercase" style="font-size: 0.65rem;">籌碼量化</span>
  </a>
  <!-- Sidebar Toggle -->
  <button class="btn btn-link btn-sm order-1 order-lg-0 me-3 me-lg-0 text-white-50" id="sidebarToggle" href="#!">
    <i class="fas fa-bars fa-lg"></i>
  </button>

  <!-- Navbar Search (頂部個股即時查詢與健檢) -->
  <div class="d-none d-md-flex form-inline ms-auto me-0 me-md-3 my-2 my-md-0 position-relative" style="width: 320px;">
    <div class="input-group input-group-sm w-100">
      <span class="input-group-text bg-secondary border-secondary text-white-50"><i class="fas fa-search"></i></span>
      <input class="form-control bg-dark text-white border-secondary" type="text" id="docInput" placeholder="輸入代號/名稱 (如 2330)..." autocomplete="off" />
      <button class="btn btn-primary" id="btnDocSearch" type="button"><i class="fas fa-arrow-right"></i></button>
    </div>
    <!-- 搜尋建議清單 Dropdown -->
    <div id="docSuggest" class="dropdown-menu shadow-lg w-100 mt-1" style="display:none; max-height:360px; overflow-y:auto; position:absolute; top:100%; left:0; z-index:1060;"></div>
  </div>

  <!-- Navbar Right Action Items -->
  <ul class="navbar-nav ms-auto ms-md-0 me-3 me-lg-4 align-items-center flex-row gap-2">
    <!-- Chips Radar Direct Link -->
    <li class="nav-item">
      <a class="btn btn-outline-info btn-sm text-nowrap" href="#radarSection" title="直達籌碼五維雷達透視分析">
        <i class="fas fa-crosshairs me-1"></i>籌碼雷達
      </a>
    </li>
    <!-- Theme Toggle (深色 / 淺色切換) -->
    <li class="nav-item">
      <button class="btn btn-outline-secondary btn-sm text-white-50" id="btnThemeToggle" title="切換深色/淺色主題">
        <i class="fas fa-moon" id="themeIcon"></i>
      </button>
    </li>
    <!-- Status Badge -->
    <li class="nav-item d-none d-xl-inline-block">
      <span class="badge bg-success-subtle text-success border border-success d-inline-flex align-items-center py-1.5 px-2">
        <span class="spinner-grow spinner-grow-sm me-1 text-success" style="width:0.45rem;height:0.45rem;" role="status"></span>每日 22:00 定稿更新
      </span>
    </li>
  </ul>
</nav>

<!-- ==================== SB ADMIN LAYOUT ==================== -->
<div id="layoutSidenav">
  <!-- ===== 左側側欄 (Sidenav: 8大核心量化功能) ===== -->
  <div id="layoutSidenav_nav">
    <nav class="sb-sidenav accordion sb-sidenav-dark" id="sidenavAccordion">
      <div class="sb-sidenav-menu">
        <div class="nav">
          <div class="sb-sidenav-menu-heading">核心決策 CORE</div>
          <a class="nav-link active" href="#dashboard">
            <div class="sb-nav-link-icon"><i class="fas fa-tachometer-alt text-primary"></i></div>
            儀表板總覽
          </a>
          <a class="nav-link" href="#picks">
            <div class="sb-nav-link-icon"><i class="fas fa-trophy text-warning"></i></div>
            量化籌碼精選
            <span class="badge bg-warning text-dark ms-auto font-monospace">40檔</span>
          </a>
          <a class="nav-link" href="#radarSection">
            <div class="sb-nav-link-icon"><i class="fas fa-crosshairs text-info"></i></div>
            籌碼五維雷達
            <span class="badge bg-info text-dark ms-auto font-monospace">透視</span>
          </a>

          <div class="sb-sidenav-menu-heading">盤面與異動 MARKET</div>
          <a class="nav-link" href="#daytrade">
            <div class="sb-nav-link-icon"><i class="fas fa-bolt text-danger"></i></div>
            當沖多空標的
            <span class="badge bg-danger ms-auto font-monospace">多空40</span>
          </a>
          <a class="nav-link" href="#anomalies">
            <div class="sb-nav-link-icon"><i class="fas fa-exclamation-triangle text-info"></i></div>
            跨日籌碼異常
            <span class="badge bg-info text-dark ms-auto font-monospace" id="sideAnomBadge">0</span>
          </a>
          <a class="nav-link" href="#rankings">
            <div class="sb-nav-link-icon"><i class="fas fa-fire text-danger"></i></div>
            量能與週轉率前20
          </a>

          <div class="sb-sidenav-menu-heading">分析工具 TOOLS</div>
          <a class="nav-link" href="#doctor">
            <div class="sb-nav-link-icon"><i class="fas fa-stethoscope text-success"></i></div>
            個股籌碼健檢
            <span class="badge bg-success ms-auto font-monospace">550+檔</span>
          </a>
          <a class="nav-link" href="#screener">
            <div class="sb-nav-link-icon"><i class="fas fa-filter text-primary"></i></div>
            多因子策略選股
          </a>
        </div>
      </div>
      <div class="sb-sidenav-footer">
        <div class="small text-muted">GETSTOCK 量化決策</div>
        <div class="small text-white-50">證交所・櫃買每日 22:00</div>
      </div>
    </nav>
  </div>

  <!-- ===== 主內容區塊 (Content Area) ===== -->
  <div id="layoutSidenav_content">
    <main>
      <div class="container-fluid px-4 py-3" id="dashboard">
        <!-- 頂部標題與歷史交易日 -->
        <div class="d-flex flex-wrap align-items-center justify-content-between pt-2 pb-2 mb-3 border-bottom">
          <div>
            <h1 class="h3 fw-bold mb-1">台股大戶籌碼與量化決策系統</h1>
            <div class="text-muted small" id="asof">資料載入中...</div>
          </div>
          <!-- 歷史交易日選擇 Bar -->
          <div class="d-flex align-items-center gap-2 mt-2 mt-sm-0">
            <span class="text-muted small text-nowrap"><i class="fas fa-calendar-alt me-1"></i>歷史交易日:</span>
            <div class="d-flex align-items-center gap-1 overflow-auto" id="history" style="max-width: 480px;"></div>
          </div>
        </div>

        <!-- 大盤指數跑馬燈卡片 -->
        <div class="card mb-3 shadow-sm border-0 bg-dark-subtle">
          <div class="card-body py-2 px-3">
            <div class="d-flex align-items-center gap-3 overflow-auto text-nowrap no-scrollbar" id="indices">
              <span class="text-muted small" id="idxDate">大盤指數</span>
            </div>
          </div>
        </div>

        <!-- SB Admin 4 大實戰指標卡 (Row) -->
        <div class="row g-3 mb-4">
          <!-- Primary Card: 加權指數行情 -->
          <div class="col-xl-3 col-md-6">
            <div class="card bg-primary text-white h-100 shadow-sm border-0">
              <div class="card-body">
                <div class="d-flex justify-content-between align-items-center">
                  <div>
                    <div class="text-white-50 small fw-bold">加權指數行情</div>
                    <div class="fs-4 fw-bold num" id="sbCardIdx">—</div>
                    <div class="small text-white-50" id="sbCardIdxSub">成交金額 — 億</div>
                  </div>
                  <i class="fas fa-chart-line fa-2x text-white-50"></i>
                </div>
              </div>
              <div class="card-footer d-flex align-items-center justify-content-between small py-2 bg-black bg-opacity-25 border-0">
                <a class="text-white stretched-link text-decoration-none" href="#indices">大盤各類股指數</a>
                <i class="fas fa-angle-right"></i>
              </div>
            </div>
          </div>

          <!-- Warning Card: 盤後多因子共識 -->
          <div class="col-xl-3 col-md-6">
            <div class="card bg-warning text-dark h-100 shadow-sm border-0">
              <div class="card-body">
                <div class="d-flex justify-content-between align-items-center">
                  <div>
                    <div class="text-black-50 small fw-bold">盤後多因子共識</div>
                    <div class="fs-5 fw-bold text-truncate" style="max-width:200px;" id="sbCardAi">分析運算中...</div>
                    <div class="small text-black-50" id="sbCardAiSub">推薦平均分: —</div>
                  </div>
                  <i class="fas fa-chart-pie fa-2x text-black-50"></i>
                </div>
              </div>
              <div class="card-footer d-flex align-items-center justify-content-between small py-2 bg-black bg-opacity-10 border-0">
                <a class="text-dark stretched-link text-decoration-none" href="#picks">瀏覽量化精選標的</a>
                <i class="fas fa-angle-right"></i>
              </div>
            </div>
          </div>

          <!-- Success Card: 主力鎖碼焦點 -->
          <div class="col-xl-3 col-md-6">
            <div class="card bg-success text-white h-100 shadow-sm border-0">
              <div class="card-body">
                <div class="d-flex justify-content-between align-items-center">
                  <div>
                    <div class="text-white-50 small fw-bold">S+ 主力鎖碼標的</div>
                    <div class="fs-4 fw-bold num" id="sbCardLock">—</div>
                    <div class="small text-white-50" id="sbCardLockSub">土洋法人合買鎖碼</div>
                  </div>
                  <i class="fas fa-lock fa-2x text-white-50"></i>
                </div>
              </div>
              <div class="card-footer d-flex align-items-center justify-content-between small py-2 bg-black bg-opacity-25 border-0">
                <a class="text-white stretched-link text-decoration-none" href="#radarSection">五維雷達因子拆解</a>
                <i class="fas fa-angle-right"></i>
              </div>
            </div>
          </div>

          <!-- Danger Card: 當沖與異動預警 -->
          <div class="col-xl-3 col-md-6">
            <div class="card bg-danger text-white h-100 shadow-sm border-0">
              <div class="card-body">
                <div class="d-flex justify-content-between align-items-center">
                  <div>
                    <div class="text-white-50 small fw-bold">盤面異常與隔日當沖</div>
                    <div class="fs-4 fw-bold num" id="sbCardAnom">—</div>
                    <div class="small text-white-50" id="sbCardAnomSub">多空各 20 檔精準點位</div>
                  </div>
                  <i class="fas fa-bolt fa-2x text-white-50"></i>
                </div>
              </div>
              <div class="card-footer d-flex align-items-center justify-content-between small py-2 bg-black bg-opacity-25 border-0">
                <a class="text-white stretched-link text-decoration-none" href="#daytrade">查看當沖與異動名單</a>
                <i class="fas fa-angle-right"></i>
              </div>
            </div>
          </div>
        </div>

        <!-- 盤後決策總覽與市場情緒指標卡片 -->
        <div class="card mb-4 shadow-sm border-start border-4 border-primary">
          <div class="card-body py-3">
            <div class="d-flex flex-column flex-lg-row align-items-lg-center justify-content-between gap-2">
              <div>
                <div class="text-muted small fw-bold mb-1"><i class="fas fa-bullhorn text-primary me-1"></i>盤後決策總覽與市場情緒指標</div>
                <h5 class="fw-bold mb-0" id="aiHeadline">大數據量化運算中...</h5>
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
                <i class="fas fa-trophy text-warning fa-lg"></i>
                <h5 class="mb-0 fw-bold" id="listTitle">上市量化精選</h5>
                <span class="badge bg-secondary ms-1">共 <b id="sCount" class="num text-white">20</b> 檔</span>
                <span class="badge bg-warning text-dark ms-1 d-none d-sm-inline">均分: <b id="sAvg" class="num">82.5</b></span>
                <span class="small text-muted ms-2 d-none d-md-inline" id="genAt">資料定稿時間</span>
              </div>

              <!-- 右側工具列：市場切換、篩選、排序、檢視、匯出 -->
              <div class="d-flex flex-wrap align-items-center gap-2">
                <!-- 上市/上櫃切換 -->
                <div class="btn-group btn-group-sm" role="group">
                  <button type="button" data-market="上市" class="mk btn btn-outline-primary active">上市 20 檔</button>
                  <button type="button" data-market="上櫃" class="mk btn btn-outline-primary">上櫃 20 檔</button>
                  <button type="button" data-market="全部" class="mk btn btn-outline-primary">全部 40 檔</button>
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
                  <button type="button" id="btnViewCards" class="btn btn-sm btn-light active font-bold">卡片</button>
                  <button type="button" id="btnViewTable" class="btn btn-sm btn-outline-secondary">表格</button>
                </div>

                <!-- 匯出 CSV -->
                <button type="button" id="btnExportCsv" class="btn btn-sm btn-outline-success" title="匯出推薦清單 CSV">
                  <i class="fas fa-file-csv me-1"></i>匯出 CSV
                </button>
              </div>
            </div>

            <!-- 條件快篩 Tag 列 -->
            <div class="d-flex align-items-center gap-1.5 overflow-auto no-scrollbar pt-2.5 mt-2 border-top text-xs">
              <span class="text-muted me-1 flex-none"><i class="fas fa-filter me-1"></i>快篩:</span>
              <button type="button" data-filter="all" class="af btn btn-sm btn-primary py-0.5 px-2.5 rounded-pill flex-none">全部</button>
              <button type="button" data-filter="splus" class="af btn btn-sm btn-outline-secondary py-0.5 px-2.5 rounded-pill flex-none">S+ 主力鎖碼</button>
              <button type="button" data-filter="dual" class="af btn btn-sm btn-outline-secondary py-0.5 px-2.5 rounded-pill flex-none">土洋合買</button>
              <button type="button" data-filter="reversal" class="af btn btn-sm btn-outline-secondary py-0.5 px-2.5 rounded-pill flex-none">由賣轉買</button>
              <button type="button" data-filter="divergence" class="af btn btn-sm btn-outline-secondary py-0.5 px-2.5 rounded-pill flex-none">價跌吃貨</button>
              <button type="button" data-filter="big" class="af btn btn-sm btn-outline-secondary py-0.5 px-2.5 rounded-pill flex-none">大戶增持 (≥0.4%)</button>
              <button type="button" data-filter="margin" class="af btn btn-sm btn-outline-secondary py-0.5 px-2.5 rounded-pill flex-none">融資減少</button>
              <button type="button" data-filter="streak" class="af btn btn-sm btn-outline-secondary py-0.5 px-2.5 rounded-pill flex-none">連續上榜 (≥3日)</button>
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
                    <th class="py-2 px-2 text-end text-emerald-400">買進區間</th>
                    <th class="py-2 px-2 text-end text-amber-400">目標價 1/2</th>
                    <th class="py-2 px-2 text-end text-rose-400">停損價</th>
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
        <div class="card mb-4 shadow-sm border-info" id="radarSection">
          <div class="card-header py-3">
            <div class="d-flex flex-column flex-lg-row align-items-lg-center justify-content-between gap-2">
              <div>
                <div class="text-muted small">五維度量化因子全方位透視</div>
                <h5 class="mb-0 fw-bold d-flex align-items-center gap-2">
                  <i class="fas fa-crosshairs text-info fa-lg"></i>
                  <span>籌碼五維雷達透視分析</span>
                </h5>
                <small class="text-muted">拆解五大關鍵籌碼維度：法人當日(25%)、法人5日(25%)、連買天數(10%)、大戶週增(25%)、融資退場(15%)</small>
              </div>

              <!-- 快速精選 Pills -->
              <div class="d-flex align-items-center gap-2 flex-wrap">
                <div class="d-flex align-items-center gap-1 overflow-auto no-scrollbar" id="radarQuickPills"></div>
              </div>
            </div>

            <!-- 雷達維度排行 Tab 切換 -->
            <div class="d-flex align-items-center gap-1 overflow-auto no-scrollbar pt-2.5 mt-2 border-top text-xs" id="radarFactorTabs">
              <span class="text-muted me-1 flex-none"><i class="fas fa-list-ol me-1"></i>維度天梯榜:</span>
              <button type="button" data-factor="score" class="btn btn-sm btn-primary active font-bold py-0.5 px-2.5 rounded-pill flex-none">綜合總分榜</button>
              <button type="button" data-factor="big" class="btn btn-sm btn-outline-secondary py-0.5 px-2.5 rounded-pill flex-none">大戶增持榜 (週增)</button>
              <button type="button" data-factor="inst" class="btn btn-sm btn-outline-secondary py-0.5 px-2.5 rounded-pill flex-none">法人買超榜 (今日)</button>
              <button type="button" data-factor="streak" class="btn btn-sm btn-outline-secondary py-0.5 px-2.5 rounded-pill flex-none">連續買超榜 (天數)</button>
              <button type="button" data-factor="margin" class="btn btn-sm btn-outline-secondary py-0.5 px-2.5 rounded-pill flex-none">融資清洗榜 (減幅)</button>
            </div>
          </div>

          <div class="card-body p-3">
            <div class="row g-3">
              <!-- 左欄：當前個股五維雷達圖與操作點位 -->
              <div class="col-lg-5" id="radarStockCard"></div>

              <!-- 右欄：全市場維度天梯榜（點擊任意列立即換雷達） -->
              <div class="col-lg-7">
                <div class="card h-100 shadow-sm border-secondary-subtle">
                  <div class="card-header py-2.5 d-flex align-items-center justify-content-between">
                    <h6 class="mb-0 fw-bold small text-white"><i class="fas fa-chart-line text-warning me-1.5"></i>籌碼維度天梯排行（點擊任意列即可切換雷達）</h6>
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
                <h5 class="mb-0 fw-bold d-flex align-items-center gap-2">
                  <i class="fas fa-exclamation-triangle text-info me-1"></i>
                  <span>跨日大數據籌碼異常偵測</span>
                </h5>
              </div>
              <!-- 異動分類按鈕 -->
              <div class="d-flex align-items-center gap-1 overflow-auto no-scrollbar" id="anomTabs">
                <button type="button" data-atab="all" class="atab btn btn-sm btn-primary py-1 px-2.5 rounded-pill flex-none d-flex align-items-center gap-1.5">
                  <span>全部異動</span>
                  <span id="anomCntAll" class="badge rounded-pill bg-light text-dark num">0</span>
                </button>
                <button type="button" data-atab="reversal" class="atab btn btn-sm btn-outline-secondary py-1 px-2.5 rounded-pill flex-none d-flex align-items-center gap-1.5">
                  <span>由賣轉買</span>
                  <span id="anomCntRev" class="badge rounded-pill bg-warning text-dark num">0</span>
                </button>
                <button type="button" data-atab="divergence" class="atab btn btn-sm btn-outline-secondary py-1 px-2.5 rounded-pill flex-none d-flex align-items-center gap-1.5">
                  <span>價跌吃貨</span>
                  <span id="anomCntDiv" class="badge rounded-pill bg-success text-white num">0</span>
                </button>
                <button type="button" data-atab="consecutive" class="atab btn btn-sm btn-outline-secondary py-1 px-2.5 rounded-pill flex-none d-flex align-items-center gap-1.5">
                  <span>連續上榜</span>
                  <span id="anomCntConsec" class="badge rounded-pill bg-info text-dark num">0</span>
                </button>
                <button type="button" data-atab="newsurge" class="atab btn btn-sm btn-outline-secondary py-1 px-2.5 rounded-pill flex-none d-flex align-items-center gap-1.5">
                  <span>突襲新進</span>
                  <span id="anomCntSurge" class="badge rounded-pill bg-secondary text-white num">0</span>
                </button>
                <button type="button" data-atab="alerts" class="atab btn btn-sm btn-outline-danger py-1 px-2.5 rounded-pill flex-none d-flex align-items-center gap-1.5">
                  <span>籌碼警戒</span>
                  <span id="anomCntAlerts" class="badge rounded-pill bg-danger text-white num">0</span>
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
                <h5 class="mb-0 fw-bold d-flex align-items-center gap-2" id="dtTitle">
                  <i class="fas fa-bolt text-danger me-1"></i>當沖標的（含進場/停利/停損試算）
                </h5>
                <p id="dtDesc" class="text-muted small mb-0 mt-1"></p>
              </div>
              <!-- 做多/做空切換 -->
              <div class="btn-group btn-group-sm flex-none" role="group">
                <button type="button" id="dt-long" data-side="long" class="dts btn btn-primary active">做多 20 檔 (先買後賣)</button>
                <button type="button" id="dt-short" data-side="short" class="dts btn btn-outline-danger">做空 20 檔 (先賣後買)</button>
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
                    <th class="py-2.5 px-2 text-end text-emerald-400" id="dtColEntry">當沖進場點</th>
                    <th class="py-2.5 px-2 text-end text-amber-400" id="dtColTarget">停利目標 1/2</th>
                    <th class="py-2.5 px-2 text-end text-rose-400" id="dtColStop">停損點</th>
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
                <h5 class="mb-0 fw-bold d-flex align-items-center gap-2">
                  <i class="fas fa-stethoscope text-success me-1"></i>個股籌碼全方位健檢與部位試算
                </h5>
                <small class="text-muted">輸入代號或名稱，即時查詢法人持股動向、日K量價圖與操作點位</small>
              </div>
              <!-- 診斷專用搜尋輸入 -->
              <div class="position-relative" style="min-width: 280px;">
                <div class="input-group input-group-sm">
                  <span class="input-group-text bg-secondary text-white-50"><i class="fas fa-search"></i></span>
                  <input type="text" id="docSectionSearch" class="form-control" placeholder="搜尋個股 (如 2330 台積電)..." autocomplete="off" />
                  <button type="button" id="btnClearDocSection" class="btn btn-outline-secondary hidden">✕</button>
                </div>
                <div id="docSectionSuggest" class="dropdown-menu shadow-lg w-100 mt-1" style="display:none; max-height:320px; overflow-y:auto; position:absolute; top:100%; left:0; z-index:1060;"></div>
              </div>
            </div>
            <!-- 快速標的 Pills -->
            <div class="d-flex align-items-center gap-1.5 overflow-auto no-scrollbar pt-2.5 mt-2 border-top text-xs" id="docQuickPills"></div>
          </div>
          <div class="card-body p-3">
            <!-- 診斷主面板 -->
            <div id="docPanel" class="grid grid-cols-1 lg:grid-cols-2 gap-4"></div>

            <!-- 個人部位風險試算工具 -->
            <div class="mt-4 rounded-xl border border-white/10 bg-slate-900/60 p-4">
              <div class="d-flex align-items-center justify-content-between mb-3">
                <h6 class="mb-0 fw-bold text-white"><i class="fas fa-calculator text-primary me-2"></i>個人部位與風險試算</h6>
                <small class="text-muted">依當前選定股票之進場點與停損價試算</small>
              </div>
              <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-sm">
                <div>
                  <label class="text-slate-400 block mb-1 text-xs">投入本金 (元):</label>
                  <input type="number" id="calcCapital" value="300000" step="10000"
                    class="w-full bg-slate-950 border border-white/15 focus:border-sky-400 rounded-lg px-3 py-2 text-white outline-none num font-medium text-sm">
                </div>
                <div>
                  <label class="text-slate-400 block mb-1 text-xs">最大承受風險比率:</label>
                  <select id="calcRiskPct" class="w-full bg-slate-950 border border-white/15 focus:border-sky-400 rounded-lg px-3 py-2 text-white outline-none cursor-pointer text-sm">
                    <option value="1">1% (極保守)</option>
                    <option value="2" selected>2% (標準紀律)</option>
                    <option value="3">3% (波段操作)</option>
                    <option value="5">5% (積極)</option>
                  </select>
                </div>
                <div class="rounded-lg bg-slate-950 p-3 flex flex-col justify-center">
                  <span class="text-slate-400 text-xs">建議買進股數</span>
                  <b id="calcShares" class="text-lg text-emerald-400 num font-bold mt-0.5">—</b>
                  <span id="calcCost" class="text-xs text-slate-500 truncate mt-0.5">—</span>
                </div>
                <div class="rounded-lg bg-slate-950 p-3 flex flex-col justify-center">
                  <span class="text-slate-400 text-xs">觸發停損最大虧損</span>
                  <b id="calcMaxLoss" class="text-lg text-rose-400 num font-bold mt-0.5">—</b>
                  <span id="calcStopPrice" class="text-xs text-slate-500 truncate mt-0.5">—</span>
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
                <h5 class="mb-0 fw-bold d-flex align-items-center gap-2">
                  <i class="fas fa-filter text-primary me-1"></i>多因子策略選股機
                </h5>
              </div>
              <button type="button" id="btnExportScreenerCsv" class="btn btn-sm btn-outline-success">
                <i class="fas fa-file-csv me-1"></i>匯出篩選結果 CSV
              </button>
            </div>
            <!-- 策略快選 Tag -->
            <div class="d-flex align-items-center gap-1.5 overflow-auto no-scrollbar pt-2.5 mt-2 border-top text-xs" id="scrPresets">
              <span class="text-muted me-1 flex-none">策略:</span>
              <button type="button" data-preset="top" class="spreset btn btn-sm btn-primary py-0.5 px-2.5 rounded-pill flex-none">綜合首選</button>
              <button type="button" data-preset="dual" class="spreset btn btn-sm btn-outline-secondary py-0.5 px-2.5 rounded-pill flex-none">土洋合買</button>
              <button type="button" data-preset="trust" class="spreset btn btn-sm btn-outline-secondary py-0.5 px-2.5 rounded-pill flex-none">投信連買</button>
              <button type="button" data-preset="whale" class="spreset btn btn-sm btn-outline-secondary py-0.5 px-2.5 rounded-pill flex-none">大戶增持</button>
              <button type="button" data-preset="squeeze" class="spreset btn btn-sm btn-outline-secondary py-0.5 px-2.5 rounded-pill flex-none">券增資減</button>
              <button type="button" data-preset="dipbuy" class="spreset btn btn-sm btn-outline-secondary py-0.5 px-2.5 rounded-pill flex-none">拉回低接</button>
              <button type="button" data-preset="turnaround" class="spreset btn btn-sm btn-outline-secondary py-0.5 px-2.5 rounded-pill flex-none">由賣轉買</button>
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
                <span id="scrMinScoreVal" class="num text-primary font-bold text-nowrap">0分</span>
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
                    <th class="py-2.5 px-2 text-end text-emerald-400">買進區間</th>
                    <th class="py-2.5 px-2 text-end text-amber-400">目標 / 停損</th>
                    <th class="py-2.5 px-2 text-end">分數</th>
                  </tr>
                </thead>
                <tbody id="scrRows"></tbody>
              </table>
            </div>

            <div class="text-center mt-3">
              <button type="button" id="btnScrMore" class="btn btn-sm btn-outline-secondary px-4">載入更多 ↓</button>
            </div>
          </div>
        </div>

        <!-- ===== 模組 7: 成交量與週轉率前 20 名排行 (Rankings) ===== -->
        <div class="row g-3 mb-4" id="rankings">
          <!-- 成交量排行 -->
          <div class="col-lg-6">
            <div class="card h-100 shadow-sm">
              <div class="card-header py-2.5 d-flex align-items-center justify-content-between">
                <div class="d-flex align-items-center gap-2">
                  <i class="fas fa-chart-bar text-danger"></i>
                  <h6 class="mb-0 fw-bold" id="voTitle">上市成交量前 20 名</h6>
                </div>
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
            <div class="card h-100 shadow-sm">
              <div class="card-header py-2.5 d-flex align-items-center justify-content-between">
                <div class="d-flex align-items-center gap-2">
                  <i class="fas fa-sync-alt text-warning"></i>
                  <h6 class="mb-0 fw-bold" id="toTitle">上市週轉率前 20 名</h6>
                </div>
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

    <!-- ===== 頁尾 (純粹乾淨的版權宣告，無冗長免責文字) ===== -->
    <footer class="py-3 bg-light mt-auto">
      <div class="container-fluid px-4">
        <div class="d-flex flex-wrap align-items-center justify-content-between small text-muted gap-2">
          <div class="fw-bold">
            <i class="fas fa-chart-line text-warning me-1"></i>GETSTOCK 台股量化決策系統 &copy; 2026
          </div>
          <div class="d-flex align-items-center gap-3">
            <a href="#dashboard" class="text-decoration-none">回到頂部 ↑</a>
            <a href="#radarSection" class="text-decoration-none">籌碼五維雷達</a>
            <a href="https://www.twse.com.tw/" target="_blank" rel="noopener" class="text-decoration-none">證交所</a>
            <a href="https://www.tpex.org.tw/" target="_blank" rel="noopener" class="text-decoration-none">櫃買中心</a>
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

print("成功輸出精簡版 site_template.html，總大小:", len(sb_template_html))
