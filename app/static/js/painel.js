/* Painel (reestruturação R2): desenha os gráficos com o ECharts servido pelo próprio site.
   SÓ DESENHA: todos os números e textos vêm prontos do servidor no JSON #painel-dados
   (app/services/dashboard.py → calc.py). Nenhuma conta de negócio aqui (ADR-0009).
   Cores e fonte lidas dos tokens CSS (tokens.css), então acompanham o tema claro/escuro.
   CSP: sem eval, sem estilo inline em HTML (tooltip só com classes), renderizador canvas. */
(function () {
  "use strict";

  var dataEl = document.getElementById("painel-dados");
  if (!dataEl || !window.echarts) return;
  var DATA;
  try {
    DATA = JSON.parse(dataEl.textContent);
  } catch (e) {
    return;
  }

  var charts = {};

  function css(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }

  function esc(text) {
    return String(text == null ? "" : text).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function tokens() {
    return {
      font: getComputedStyle(document.body).fontFamily,
      text: css("--color-text"),
      muted: css("--color-text-muted"),
      subtle: css("--color-text-subtle"),
      surface: css("--color-surface"),
      grid: css("--color-chart-grid"),
      axis: css("--color-chart-axis"),
      tasks: css("--color-series-tasks"),
      tasksSoft: css("--color-series-tasks-soft"),
      units: css("--color-series-units"),
      done: css("--color-status-done"),
      doing: css("--color-status-doing"),
      waiting: css("--color-status-waiting"),
      late: css("--color-status-late"),
      todo: css("--color-status-todo"),
      neutral: css("--color-series-neutral"),
      border: css("--color-border-subtle"),
    };
  }

  function narrow() {
    return window.matchMedia("(max-width: 47.99em)").matches;
  }

  // Texto de eixo e rótulos: 12px; nunca abaixo de 11px.
  var AXIS_FONT = 12;
  var LABEL_FONT = 11;

  // O gráfico desenha uma vez (curto), na primeira exibição; trocar de tema ou girar o aparelho não repete.
  // Com movimento reduzido não anima nada.
  var firstDraw = !(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);

  function base(t) {
    return {
      animation: firstDraw,
      animationDuration: 400,
      animationEasing: "cubicOut",
      animationDurationUpdate: 0,
      aria: { show: false },
      textStyle: { fontFamily: t.font, color: t.muted, fontSize: AXIS_FONT },
      tooltip: {
        confine: true,
        backgroundColor: t.surface,
        borderColor: t.border,
        borderWidth: 1,
        padding: [8, 10],
        textStyle: { color: t.text, fontFamily: t.font, fontSize: AXIS_FONT },
        extraCssText: "box-shadow: none; border-radius: 6px;",
        className: "chart-tip",
      },
    };
  }

  // Números dos eixos no formato brasileiro (vírgula decimal): só apresentação.
  var NUM = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 1 });
  function axisNum(suffix) {
    return function (v) { return NUM.format(v) + suffix; };
  }

  function dot(kind) {
    return '<span class="chart-tip__dot chart-tip__dot--' + kind + '"></span>';
  }

  function categoryAxis(t, labels) {
    var width = narrow() ? 112 : 200;
    return {
      type: "category",
      inverse: true,
      data: labels,
      axisTick: { show: false },
      axisLine: { lineStyle: { color: t.axis } },
      axisLabel: { color: t.text, fontSize: AXIS_FONT, width: width, overflow: "truncate", ellipsis: "…" },
    };
  }

  function valueAxis(t, opts) {
    return Object.assign(
      {
        type: "value",
        axisLine: { show: false },
        axisTick: { show: false },
        splitNumber: narrow() ? 3 : 5,
        splitLine: { lineStyle: { color: t.grid, width: 1 } },
        axisLabel: { color: t.subtle, fontSize: AXIS_FONT },
      },
      opts || {}
    );
  }

  function rowsHeight(n, perRow) {
    return Math.max(120, n * perRow + 40);
  }

  function init(el) {
    var key = el.getAttribute("data-chart");
    if (charts[key]) charts[key].dispose();
    charts[key] = window.echarts.init(el, null, { renderer: "canvas" });
    if (window.ResizeObserver) new ResizeObserver(function () { charts[key].resize(); }).observe(el);
    return charts[key];
  }

  function go(href) {
    if (href) window.location.href = href;
  }

  // Mistura duas cores #rrggbb (só apresentação: o quanto cada bloco está pronto vem do servidor).
  function mix(from, to, k) {
    function p(hex) { var h = hex.replace("#", ""); return [0, 2, 4].map(function (i) { return parseInt(h.substr(i, 2), 16); }); }
    var a = p(from), b = p(to);
    return "rgb(" + a.map(function (v, i) { return Math.round(v + (b[i] - v) * k); }).join(",") + ")";
  }

  /* ---------- 4. Tarefas × unidades (por etapa ou por projeto) ---------- */
  function drawTasks(el, t) {
    var rows = DATA.rows || [];
    el.style.height = rowsHeight(rows.length, 48) + "px";
    var chart = init(el);
    var pct = function (p) { return p.value > 0 ? Math.round(p.value * 100) + "%" : ""; };
    var track = { show: true, itemStyle: { color: t.grid, opacity: 0.55, borderRadius: 6 } };
    chart.setOption(Object.assign(base(t), {
      grid: { left: 8, right: 44, top: 8, bottom: 8, containLabel: true },
      xAxis: valueAxis(t, { min: 0, max: 1, interval: narrow() ? 0.5 : 0.25, splitLine: { lineStyle: { color: t.grid, width: 1, type: "dashed" } },
        axisLabel: { color: t.subtle, fontSize: AXIS_FONT, formatter: function (v) { return Math.round(v * 100) + "%"; } } }),
      yAxis: categoryAxis(t, rows.map(function (r) { return r.label; })),
      tooltip: Object.assign(base(t).tooltip, {
        trigger: "axis",
        axisPointer: { type: "shadow", shadowStyle: { color: t.grid, opacity: 0.35 } },
        formatter: function (ps) {
          var r = rows[ps[0].dataIndex];
          return "<strong>" + esc(r.label) + "</strong><br>" + dot("tasks") + "Pelas tarefas: <strong>" + esc(r.tasksText) +
            "</strong><br>" + dot("units") + "Unidades: <strong>" + esc(r.unitsFrac) + "</strong> (" + esc(r.unitsText) + ")";
        },
      }),
      series: [
        { name: "Pelas tarefas", type: "bar", barWidth: 12, barGap: "25%", showBackground: true, backgroundStyle: track.itemStyle,
          itemStyle: { color: t.tasks, borderRadius: 6 },
          data: rows.map(function (r) { return r.tasks; }),
          label: { show: true, position: "right", color: t.text, fontSize: LABEL_FONT, fontWeight: 600, formatter: pct } },
        { name: "Unidades", type: "bar", barWidth: 12, showBackground: true, backgroundStyle: track.itemStyle,
          itemStyle: { color: t.units, borderRadius: 6 },
          data: rows.map(function (r) { return r.units; }),
          label: { show: true, position: "right", color: t.muted, fontSize: LABEL_FONT, formatter: pct } },
      ],
    }));
    chart.on("click", function (p) { go(rows[p.dataIndex] && rows[p.dataIndex].href); });
    chart.getZr().on("click", function (e) {
      if (e.target) return;
      var point = [e.offsetX, e.offsetY];
      if (!chart.containPixel("grid", point)) return;
      var idx = chart.convertFromPixel({ seriesIndex: 0 }, point)[1];
      if (rows[idx]) go(rows[idx].href);
    });
  }

  /* ---------- 4. Situação das etapas (rosca) ---------- */
  function drawStatus(el, t) {
    var items = DATA.status || [];
    var colors = { done: t.done, doing: t.doing, waiting: t.waiting, late: t.late, todo: t.todo };
    var total = 0, done = 0;
    items.forEach(function (s) { total += s.value; if (s.key === "done") done = s.value; });
    var chart = init(el);
    chart.setOption(Object.assign(base(t), {
      tooltip: Object.assign(base(t).tooltip, {
        trigger: "item",
        formatter: function (p) { return dot(p.data.key) + esc(p.name) + ": <strong>" + p.value + "</strong> " + (p.value === 1 ? "etapa" : "etapas"); },
      }),
      graphic: [
        { type: "text", left: "center", top: "37%", style: { text: done + "/" + total, fill: t.text, font: "600 26px " + t.font, textAlign: "center" } },
        { type: "text", left: "center", top: "56%", style: { text: "concluídas", fill: t.muted, font: "400 12px " + t.font, textAlign: "center" } },
      ],
      series: [{
        type: "pie", radius: ["62%", "90%"], center: ["50%", "50%"], padAngle: total > 1 ? 3 : 0,
        itemStyle: { borderRadius: 8 }, label: { show: false }, labelLine: { show: false },
        emphasis: { scale: false },
        data: items.filter(function (s) { return s.value > 0; }).map(function (s) {
          return { name: s.name, value: s.value, key: s.key, itemStyle: { color: colors[s.key] } };
        }),
      }],
    }));
  }

  /* ---------- 4b. Quanto cada etapa representa (mapa de blocos) ---------- */
  function drawWeight(el, t) {
    var rows = (DATA.rows || []).filter(function (r) { return r.weight > 0; });
    var chart = init(el);
    var data = rows.map(function (r) {
      var k = Math.min(Math.max(r.tasks, 0), 1);
      return { name: r.label, value: r.weight, row: r,
        itemStyle: { color: mix(t.tasksSoft, t.tasks, k) },
        label: { color: k > 0.55 ? t.surface : t.text } };
    });
    chart.setOption(Object.assign(base(t), {
      tooltip: Object.assign(base(t).tooltip, {
        trigger: "item",
        formatter: function (p) {
          var r = p.data && p.data.row;
          if (!r) return "";
          return "<strong>" + esc(r.label) + "</strong><br>Peso no projeto: <strong>" + esc(r.weightText) +
            "</strong><br>" + dot("tasks") + "Progresso: <strong>" + esc(r.tasksText) + "</strong>";
        },
      }),
      series: [{
        type: "treemap", roam: false, nodeClick: false, breadcrumb: { show: false },
        left: 0, right: 0, top: 0, bottom: 0, squareRatio: 1.2,
        itemStyle: { borderColor: t.surface, borderWidth: 3, gapWidth: 3, borderRadius: 8 },
        label: { show: true, position: "insideTopLeft", padding: [8, 10], fontSize: AXIS_FONT, fontWeight: 600, overflow: "truncate",
          formatter: function (p) { var r = p.data && p.data.row; return r ? p.name.replace(/^\d+\.\s*/, "") + "\n" + r.weightText : ""; } },
        emphasis: { itemStyle: { shadowBlur: 0 } },
        data: data,
      }],
    }));
    chart.on("click", function (p) { go(p.data && p.data.row && p.data.row.href); });
  }

  /* ---------- 5. Horas (trabalhadas × faltam), colunas empilhadas por etapa ---------- */
  function drawHours(el, t) {
    var rows = DATA.rows || [];
    el.style.height = narrow() ? "260px" : "320px";
    var chart = init(el);
    chart.setOption(Object.assign(base(t), {
      grid: { left: 8, right: 16, top: 16, bottom: 8, containLabel: true },
      xAxis: { type: "category", data: rows.map(function (r) { return r.n != null ? String(r.n) : r.label; }), axisTick: { show: false },
        axisLine: { lineStyle: { color: t.axis } }, axisLabel: { color: t.muted, fontSize: AXIS_FONT } },
      yAxis: valueAxis(t, { splitLine: { lineStyle: { color: t.grid, width: 1, type: "dashed" } },
        axisLabel: { color: t.subtle, fontSize: AXIS_FONT, formatter: axisNum(" h") } }),
      tooltip: Object.assign(base(t).tooltip, {
        trigger: "axis",
        axisPointer: { type: "shadow", shadowStyle: { color: t.grid, opacity: 0.35 } },
        formatter: function (ps) {
          var r = rows[ps[0].dataIndex];
          return "<strong>" + esc(r.label) + "</strong><br>" + dot("worked") + "Trabalhadas: <strong>" + esc(r.workedText) +
            "</strong><br>" + dot("left") + "Faltam: <strong>" + esc(r.leftText) + "</strong>";
        },
      }),
      series: [
        { name: "Trabalhadas", type: "bar", stack: "h", barMaxWidth: 36, itemStyle: { color: t.tasks, borderColor: t.surface, borderWidth: 1 },
          data: rows.map(function (r) { return r.worked; }) },
        { name: "Faltam", type: "bar", stack: "h", barMaxWidth: 36, itemStyle: { color: t.tasksSoft, borderColor: t.surface, borderWidth: 1, borderRadius: [8, 8, 0, 0] },
          data: rows.map(function (r) { return r.left; }) },
      ],
    }));
    chart.on("click", function (p) { go(rows[p.dataIndex] && rows[p.dataIndex].href); });
  }

  /* ---------- 6. Equipe × prazo (um projeto) ---------- */
  function drawTeam(el, t) {
    var team = DATA.team || { rows: [] };
    el.style.height = narrow() ? "240px" : "280px";
    var rows = team.rows;
    var chart = init(el);
    // A linha do prazo só entra quando cabe na escala sem achatar as colunas (até 1,5× a maior).
    var maxDays = 0;
    rows.forEach(function (r) { if (r.days != null && r.days > maxDays) maxDays = r.days; });
    var markLine = team.due == null || team.due > maxDays * 1.5 ? undefined : {
      silent: true, symbol: "none",
      lineStyle: { color: t.text, type: "dashed", width: 1.5 },
      label: { color: t.text, fontSize: LABEL_FONT, formatter: "prazo: " + NUM.format(team.due) + " d", position: "insideEndTop" },
      data: [{ yAxis: team.due }],
    };
    chart.setOption(Object.assign(base(t), {
      grid: { left: 8, right: 16, top: 28, bottom: 8, containLabel: true },
      xAxis: { type: "category", data: rows.map(function (r) { return narrow() ? String(r.people) : r.label; }), axisTick: { show: false },
        axisLine: { lineStyle: { color: t.axis } }, axisLabel: { color: t.muted, fontSize: AXIS_FONT } },
      yAxis: valueAxis(t, { splitLine: { lineStyle: { color: t.grid, width: 1, type: "dashed" } },
        axisLabel: { color: t.subtle, fontSize: AXIS_FONT, formatter: axisNum(" d") } }),
      tooltip: Object.assign(base(t).tooltip, {
        trigger: "item",
        formatter: function (p) {
          var r = rows[p.dataIndex];
          return "<strong>" + esc(r.label) + (r.current ? " (hoje)" : "") + "</strong><br>" + esc(r.teamHours) + " h de equipe por dia<br>Dias úteis: <strong>" + esc(r.daysText) + "</strong>";
        },
      }),
      series: [{
        type: "bar", barMaxWidth: 44, barCategoryGap: "35%",
        data: rows.map(function (r) {
          return { value: r.days == null ? 0 : r.days, itemStyle: { color: r.current ? t.done : t.tasksSoft, borderRadius: [8, 8, 0, 0] } };
        }),
        label: { show: true, position: "top", color: t.text, fontSize: LABEL_FONT, fontWeight: 600, formatter: function (p) { return rows[p.dataIndex].daysText; } },
        markLine: markLine,
      }],
    }));
  }

  /* ---------- 6. Prazo por projeto (painel da operação) ---------- */
  function drawDeadline(el, t) {
    var rows = (DATA.deadline && DATA.deadline.rows) || [];
    el.style.height = rowsHeight(rows.length, 44) + "px";
    var chart = init(el);
    chart.setOption(Object.assign(base(t), {
      grid: { left: 8, right: 40, top: 8, bottom: 8, containLabel: true },
      xAxis: valueAxis(t, { axisLabel: { color: t.subtle, fontSize: AXIS_FONT, formatter: axisNum(" d") } }),
      yAxis: categoryAxis(t, rows.map(function (r) { return r.label; })),
      tooltip: Object.assign(base(t).tooltip, {
        trigger: "axis",
        axisPointer: { type: "shadow", shadowStyle: { color: t.grid, opacity: 0.4 } },
        formatter: function (ps) {
          var r = rows[ps[0].dataIndex];
          return "<strong>" + esc(r.label) + "</strong><br>" + dot("need") + "Trabalho que falta: <strong>" + esc(r.needText) +
            " dias úteis</strong><br>" + dot("until") + "Até o prazo: <strong>" + esc(r.untilText) + "</strong>";
        },
      }),
      series: [
        { name: "Trabalho que falta", type: "bar", barWidth: 14, barGap: "15%", itemStyle: { color: t.tasks, borderRadius: [0, 3, 3, 0] },
          data: rows.map(function (r) { return r.need == null ? 0 : r.need; }),
          label: { show: true, position: "right", color: t.text, fontSize: LABEL_FONT, formatter: function (p) { return rows[p.dataIndex].needText; } } },
        { name: "Até o prazo", type: "bar", barWidth: 14, itemStyle: { color: t.neutral, borderRadius: [0, 3, 3, 0] },
          data: rows.map(function (r) { return r.until == null ? 0 : r.until; }),
          label: { show: true, position: "right", color: t.muted, fontSize: LABEL_FONT, formatter: function (p) { return rows[p.dataIndex].untilText; } } },
      ],
    }));
    chart.on("click", function (p) { go(rows[p.dataIndex] && rows[p.dataIndex].href); });
  }

  var DRAW = { tasks: drawTasks, status: drawStatus, weight: drawWeight, hours: drawHours, team: drawTeam, deadline: drawDeadline };

  function drawAll() {
    var t = tokens();
    var boxes = document.querySelectorAll("[data-chart]");
    for (var i = 0; i < boxes.length; i++) {
      var fn = DRAW[boxes[i].getAttribute("data-chart")];
      // Um gráfico com problema não pode deixar os outros em branco.
      if (fn) { try { fn(boxes[i], t); } catch (e) { if (window.console) console.error("painel: gráfico", boxes[i].getAttribute("data-chart"), e); } }
    }
  }

  var resizeTimer = null;
  var wasNarrow = null;
  window.addEventListener("resize", function () {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function () {
      // Trocar de celular para desktop muda rótulos: redesenha; senão só ajusta o tamanho.
      if (narrow() !== wasNarrow) {
        wasNarrow = narrow();
        drawAll();
        return;
      }
      Object.keys(charts).forEach(function (k) { charts[k].resize(); });
    }, 120);
  });

  // Tema: o seletor troca data-theme no <html>; o sistema troca prefers-color-scheme.
  new MutationObserver(drawAll).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
  if (window.matchMedia) {
    var scheme = window.matchMedia("(prefers-color-scheme: dark)");
    if (scheme.addEventListener) scheme.addEventListener("change", drawAll);
  }

  function start() {
    wasNarrow = narrow();
    drawAll();
    firstDraw = false;
  }

  // Espera a fonte do site (DM Sans) para medir os rótulos certo.
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(start, start);
  } else {
    start();
  }
})();
