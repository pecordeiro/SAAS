/* Controle de Produção — melhorias progressivas (a página funciona sem este arquivo).
   Carregado no <head> sem defer: só marca a classe "js" agora; o resto espera o DOM.
   Sem eval, sem estilo inline, sem dependências (CSP default-src 'self'). */
(function () {
  "use strict";
  var root = document.documentElement;
  root.classList.remove("no-js");
  root.classList.add("js");

  var THEME_COOKIE = "tema";
  var ONE_YEAR = 60 * 60 * 24 * 365;

  /* ---------- Tema: aplica na hora e grava o mesmo cookie da rota /tema ---------- */
  function applyTheme(value) {
    if (value === "light" || value === "dark") {
      root.setAttribute("data-theme", value);
    } else {
      root.removeAttribute("data-theme");
    }
    var secure = location.protocol === "https:" ? "; Secure" : "";
    if (value === "light" || value === "dark") {
      document.cookie = THEME_COOKIE + "=" + value + "; Path=/; Max-Age=" + ONE_YEAR + "; SameSite=Lax" + secure;
    } else {
      document.cookie = THEME_COOKIE + "=; Path=/; Max-Age=0; SameSite=Lax" + secure;
    }
    // Mantém os outros seletores de tema da página em sincronia.
    var radios = document.querySelectorAll('[data-theme-form] input[name="tema"]');
    for (var i = 0; i < radios.length; i++) radios[i].checked = radios[i].value === (value || "system");
  }

  document.addEventListener("change", function (event) {
    var input = event.target;
    if (input && input.name === "tema" && input.closest("[data-theme-form]")) applyTheme(input.value);
  });

  /* ---------- Stepper (− / +) e rótulo “Registrar +N (→ X de Y)” ---------- */
  function clampInput(input) {
    var min = parseInt(input.min || "1", 10);
    var max = input.max ? parseInt(input.max, 10) : Infinity;
    var value = parseInt(input.value, 10);
    if (isNaN(value)) return null;
    return Math.min(Math.max(value, min), max);
  }

  function syncStepper(group) {
    var input = group.querySelector(".stepper__input");
    if (!input) return;
    var min = parseInt(input.min || "1", 10);
    var max = input.max ? parseInt(input.max, 10) : Infinity;
    var value = parseInt(input.value, 10);
    var dec = group.querySelector('[data-step="-1"]');
    var inc = group.querySelector('[data-step="1"]');
    if (dec) dec.disabled = !(value > min);
    if (inc) inc.disabled = !(value < max);
    var sheet = group.closest("[data-register]");
    if (sheet) updateRegisterLabel(sheet, value);
  }

  function updateRegisterLabel(sheet, value) {
    var label = sheet.querySelector("[data-register-label]");
    var done = parseInt(sheet.getAttribute("data-done"), 10);
    var planned = parseInt(sheet.getAttribute("data-planned"), 10);
    var faltam = planned - done;
    var input = sheet.querySelector(".stepper__input");
    var error = sheet.querySelector("[data-register-live]");
    if (!label) return;
    if (isNaN(value) || value < 1) {
      label.textContent = "";
      return;
    }
    if (value > faltam) {
      label.textContent = "";
      if (input) input.setAttribute("aria-invalid", "true");
      if (error) error.textContent = "Faltam só " + faltam + " peças nesta atividade.";
      return;
    }
    if (input) input.removeAttribute("aria-invalid");
    if (error) error.textContent = "";
    label.textContent = "+" + value + " (→ " + (done + value) + " de " + planned + ")";
  }

  document.addEventListener("click", function (event) {
    var button = event.target.closest && event.target.closest("[data-step]");
    if (button) {
      var group = button.closest("[data-stepper]");
      var input = group && group.querySelector(".stepper__input");
      if (!input) return;
      var step = parseInt(button.getAttribute("data-step"), 10);
      var current = parseInt(input.value, 10);
      if (isNaN(current)) current = parseInt(input.min || "1", 10) - step;
      input.value = String(current + step);
      var clamped = clampInput(input);
      if (clamped !== null) input.value = String(clamped);
      syncStepper(group);
      return;
    }
    var toggle = event.target.closest && event.target.closest("[data-password-toggle]");
    if (toggle) {
      var field = document.getElementById(toggle.getAttribute("data-password-toggle"));
      if (!field) return;
      var show = field.type === "password";
      field.type = show ? "text" : "password";
      toggle.textContent = show ? "Ocultar" : "Mostrar";
      toggle.setAttribute("aria-pressed", show ? "true" : "false");
      return;
    }
    var closeToast = event.target.closest && event.target.closest("[data-toast-close]");
    if (closeToast) {
      var toast = closeToast.closest("[data-toast]");
      if (toast) toast.classList.add("is-dismissed");
    }
  });

  document.addEventListener("input", function (event) {
    var input = event.target;
    if (input && input.classList && input.classList.contains("stepper__input")) {
      syncStepper(input.closest("[data-stepper]"));
    }
  });

  // Tocar no número seleciona o conteúdo (digitar substitui o 1).
  document.addEventListener("focusin", function (event) {
    var input = event.target;
    if (input && input.classList && input.classList.contains("stepper__input") && input.select) {
      setTimeout(function () { input.select(); }, 0);
    }
  });

  /* ---------- Folhas (:target): foco, Esc, devolver o foco ---------- */
  var lastTrigger = null;

  document.addEventListener("click", function (event) {
    var link = event.target.closest && event.target.closest('a[href^="#"]');
    if (!link) return;
    var id = link.getAttribute("href").slice(1);
    var target = id && document.getElementById(id);
    if (target && target.classList.contains("sheet")) lastTrigger = link;
  });

  // Fechar/backdrop de uma folha aberta pelo servidor (.is-open, ex.: erro de registro).
  document.addEventListener("click", function (event) {
    var closer = event.target.closest && event.target.closest(".sheet__close, .sheet__backdrop, [data-dialog-cancel]");
    if (!closer) return;
    var sheet = closer.closest(".sheet");
    if (sheet) sheet.classList.remove("is-open");
    if (lastTrigger && document.contains(lastTrigger)) {
      var trigger = lastTrigger;
      setTimeout(function () { trigger.focus(); }, 0);
    }
  });

  function openSheet() {
    var id = location.hash.slice(1);
    if (!id) return null;
    var el = document.getElementById(id);
    return el && el.classList.contains("sheet") ? el : null;
  }

  function isOverlayVisible(sheet) {
    // A folha de registro é inline no desktop: lá ela não “abre” nem prende o foco.
    var backdrop = sheet.querySelector(".sheet__backdrop");
    return !!backdrop && backdrop.offsetParent !== null;
  }

  function focusSheet() {
    var sheet = openSheet();
    if (!sheet) return;
    if (!isOverlayVisible(sheet)) {
      var inline = sheet.querySelector(".stepper__input");
      if (inline) inline.focus();
      return;
    }
    var first = sheet.querySelector(".register__submit, [data-dialog-cancel], .sheet__panel button, .sheet__panel input:not([type=hidden]), .sheet__panel a");
    if (first) first.focus();
  }

  function closeSheet(sheet) {
    var back = sheet.getAttribute("data-return") || "#fechar";
    sheet.classList.remove("is-open");
    location.replace(back);
    if (lastTrigger && document.contains(lastTrigger)) lastTrigger.focus();
  }

  window.addEventListener("hashchange", focusSheet);

  document.addEventListener("keydown", function (event) {
    if (event.key !== "Escape") return;
    var sheet = openSheet() || document.querySelector(".sheet.is-open");
    if (sheet && isOverlayVisible(sheet)) {
      event.preventDefault();
      closeSheet(sheet);
    }
  });

  // Foco preso dentro da folha aberta (Tab / Shift+Tab).
  document.addEventListener("keydown", function (event) {
    if (event.key !== "Tab") return;
    var sheet = openSheet() || document.querySelector(".sheet.is-open");
    if (!sheet || !isOverlayVisible(sheet)) return;
    var focusables = Array.prototype.filter.call(
      sheet.querySelectorAll(".sheet__panel a[href], .sheet__panel button:not([disabled]), .sheet__panel input:not([type=hidden]):not([disabled])"),
      function (el) { return el.offsetParent !== null; }
    );
    if (!focusables.length) return;
    var first = focusables[0];
    var last = focusables[focusables.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  });

  /* ---------- HTMX: registro sem recarregar ----------
     O formulário faz hx-post com hx-swap="none": o servidor devolve só pedaços com
     hx-swap-oob (atividade, resumo da etapa, indicadores, toast). Aqui só cuidamos de
     fechar a folha (hash da âncora), do estado de “ocupado” e do foco. */
  document.addEventListener("htmx:beforeRequest", function (event) {
    var form = event.target;
    if (form && form.classList && form.classList.contains("register__form")) form.setAttribute("aria-busy", "true");
  });

  // beforeSwap: o formulário ainda está no DOM (depois do swap oob ele sai e o evento não chega ao document).
  document.addEventListener("htmx:beforeSwap", function (event) {
    var form = event.target;
    if (!form || !form.classList || !form.classList.contains("register__form")) return;
    form.removeAttribute("aria-busy");
    var xhr = event.detail && event.detail.xhr;
    if (xhr && xhr.status >= 200 && xhr.status < 400) {
      // Sucesso: tira o #registrar-<id> da URL (a folha nova já vem fechada) e destaca a linha.
      var sheet = form.closest("[data-register]");
      var back = sheet ? sheet.getAttribute("data-return") : null;
      if (back) location.replace(back);
    }
  });

  document.addEventListener("htmx:afterSettle", function () {
    init(document);
  });

  /* ---------- Atualização leve do detalhe a cada 30 s (só com a aba visível) ---------- */
  function startAutoRefresh() {
    var panel = document.getElementById("painel");
    var url = panel && panel.getAttribute("data-refresh-url");
    if (!url) return;
    var seconds = parseInt(panel.getAttribute("data-refresh-seconds") || "30", 10);
    var last = Date.now();

    function busy() {
      // Não mexe na tela enquanto alguém registra: folha aberta ou foco dentro de um registrador.
      if (document.querySelector(".sheet.is-open") || openSheet()) return true;
      var active = document.activeElement;
      return !!(active && active.closest && active.closest(".register__form"));
    }

    function refresh() {
      if (document.visibilityState !== "visible" || !window.htmx || busy()) return;
      last = Date.now();
      window.htmx.ajax("GET", url, { source: panel, swap: "none" });
    }

    setInterval(refresh, seconds * 1000);
    document.addEventListener("visibilitychange", function () {
      if (document.visibilityState === "visible" && Date.now() - last >= seconds * 1000) refresh();
    });
  }

  /* ---------- Ao carregar ---------- */
  function init(scope) {
    var groups = scope.querySelectorAll("[data-stepper]");
    for (var i = 0; i < groups.length; i++) syncStepper(groups[i]);
    var alert = scope.querySelector("[data-autofocus]");
    if (alert) alert.focus();
    var open = scope.querySelector(".sheet.is-open");
    if (open && isOverlayVisible(open)) {
      var input = open.querySelector(".stepper__input");
      if (input) input.focus();
    } else {
      focusSheet();
    }
  }

  function boot() {
    init(document);
    startAutoRefresh();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
