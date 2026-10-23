/* Controle de Produção — células amarelas de “Preencher etapas” e “Meta e equipe” (R3–R5).
   Igual à planilha/painel antigo: o campo salva AO SAIR (Tab, Enter ou clique fora); Enter vai
   ao próximo campo; Esc desfaz o que foi digitado. Cada saída manda UM campo (POST pequeno via
   HTMX, com o CSRF e a versão que a tela leu). O servidor valida, grava e devolve, fora de banda,
   os números recalculados e o “Salvo · quem, hora” — o navegador não calcula nada (ADR-0009).
   Sem JS: cada linha tem o botão “Salvar”. Sem estilo inline (CSP). */
(function () {
  "use strict";

  var refocusNew = false;

  function isCell(el) {
    return el && el.classList && el.classList.contains("cell") && !el.classList.contains("cell--new");
  }

  function cells() {
    return Array.prototype.filter.call(document.querySelectorAll("input.cell"), function (el) {
      return !el.disabled && el.offsetParent !== null;
    });
  }

  function mark(input, ok) {
    input.removeAttribute("aria-busy");
    input.classList.toggle("is-invalid", !ok);
    if (ok) {
      input.removeAttribute("aria-invalid");
      input.classList.add("is-saved");
      setTimeout(function () { input.classList.remove("is-saved"); }, 1600);
    } else {
      input.setAttribute("aria-invalid", "true");
    }
  }

  function save(input) {
    var form = input.form;
    if (!form || !window.htmx) return;
    var values = { campo: input.name };
    values[input.name] = input.value;
    // Campos escondidos do formulário da linha: csrf_token, version, activity_version.
    Array.prototype.forEach.call(form.elements, function (el) {
      if (el.type === "hidden" && el.name) values[el.name] = el.value;
    });
    input.setAttribute("aria-busy", "true");
    window.htmx.ajax("POST", form.getAttribute("action"), { source: input, values: values, swap: "none" });
  }

  document.addEventListener("htmx:afterRequest", function (event) {
    var input = event.target;
    if (!isCell(input)) return;
    var xhr = event.detail && event.detail.xhr;
    var ok = !!(xhr && xhr.status >= 200 && xhr.status < 300);
    if (ok) input.setAttribute("data-orig", input.value);
    mark(input, ok);
  });

  document.addEventListener("focusin", function (event) {
    var input = event.target;
    if (isCell(input) && !input.hasAttribute("aria-busy")) {
      if (!input.hasAttribute("data-orig")) input.setAttribute("data-orig", input.defaultValue);
    }
  });

  document.addEventListener("keydown", function (event) {
    var input = event.target;
    if (!isCell(input)) return;
    if (event.key === "Enter") {
      event.preventDefault();
      var all = cells();
      var next = all[all.indexOf(input) + 1];
      if (next) {
        next.focus();
        if (next.select) next.select();
      } else {
        input.blur();
      }
    } else if (event.key === "Escape") {
      event.preventDefault();
      input.value = input.getAttribute("data-orig") || "";
      input.classList.remove("is-invalid");
      input.removeAttribute("aria-invalid");
      input.blur();
    }
  });

  document.addEventListener("focusout", function (event) {
    var input = event.target;
    if (isCell(input)) {
      var orig = input.hasAttribute("data-orig") ? input.getAttribute("data-orig") : input.defaultValue;
      if (input.value !== orig) save(input);
      return;
    }
    // Linha vazia do fim: inclui a subatividade quando o foco sai da linha com o nome preenchido.
    if (input && input.classList && input.classList.contains("cell--new")) {
      var row = input.closest("tr");
      setTimeout(function () {
        if (row && row.contains(document.activeElement)) return;
        var name = document.getElementById("nova-nome");
        var form = document.getElementById("f-nova");
        if (name && form && name.value.trim()) {
          refocusNew = true;
          form.requestSubmit();
        }
      }, 0);
    }
  });

  // Depois de incluir uma subatividade (painel novo), volta para a linha vazia.
  document.addEventListener("htmx:afterSettle", function () {
    if (!refocusNew) return;
    refocusNew = false;
    var name = document.getElementById("nova-nome");
    if (name && !name.value) name.focus();
  });

  document.addEventListener("submit", function (event) {
    if (event.target && event.target.matches && event.target.matches("[data-new-form]")) refocusNew = true;
  });

  // Seletor de projeto e modo de progresso: aplica ao escolher (sem JS, botão “Abrir”/“Salvar”).
  document.addEventListener("change", function (event) {
    var form = event.target && event.target.closest ? event.target.closest("form[data-autosubmit]") : null;
    if (form) form.requestSubmit();
  });
})();
