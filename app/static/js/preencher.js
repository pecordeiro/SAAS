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

  // Falha sem explicação do servidor (sem internet, página expirada, erro interno): a linha de
  // status diz que NÃO salvou e o que fazer. Erros de validação já chegam do servidor com a
  // mensagem certa (trazem o #salvo-status); aqui não se decide regra nenhuma (ADR-0009).
  var TRANSPORT_MSG = {
    0: "Sem conexão: não salvou. Confira a internet e saia do campo de novo.",
    400: "A página expirou: não salvou. Recarregue a página e digite de novo.",
    429: "Muitas tentativas seguidas: não salvou. Espere um pouco e saia do campo de novo.",
    500: "Erro no servidor: não salvou. Tente de novo em instantes."
  };

  function explainFailure(xhr) {
    var code = xhr ? xhr.status : 0;
    if (code === 401 && xhr.getResponseHeader("HX-Redirect")) return; // sessão caiu: o htmx leva ao login
    if (xhr && /id="salvo-status"/.test(xhr.responseText || "")) return;
    var status = document.getElementById("salvo-status");
    if (!status) return;
    status.textContent = TRANSPORT_MSG[code] || (code >= 500 ? TRANSPORT_MSG[500] : "Não salvou. Recarregue a página e tente de novo.");
    status.classList.add("save-status--error");
    status.setAttribute("role", "alert");
  }

  document.addEventListener("htmx:afterRequest", function (event) {
    var input = event.target;
    if (!isCell(input)) return;
    var xhr = event.detail && event.detail.xhr;
    var ok = !!(xhr && xhr.status >= 200 && xhr.status < 300);
    if (ok) input.setAttribute("data-orig", input.value);
    mark(input, ok);
    if (!ok) explainFailure(xhr);
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

  /* ---------- Responsável: janelinha “Atribuir a” ----------
     Sem JS o <details> abre no lugar e cada pessoa é um botão que envia o formulário. Aqui só se
     posiciona a janelinha sob a bolinha, se filtra a lista pela busca e se fecha com Esc ou clique
     fora. Quem pode atribuir e a quem é decidido no servidor (ADR-0009). */
  var GAP = 8;

  function plain(text) {
    return String(text || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
  }

  function openWhos() {
    return document.querySelectorAll("details.who[open]");
  }

  function closeWhos(except) {
    Array.prototype.forEach.call(openWhos(), function (d) {
      if (d !== except) d.removeAttribute("open");
    });
  }

  function placeWho(details) {
    var summary = details.querySelector("summary");
    var panel = details.querySelector(".who__panel");
    if (!summary || !panel) return;
    var r = summary.getBoundingClientRect();
    var w = panel.offsetWidth;
    var h = panel.offsetHeight;
    var left = Math.max(GAP, Math.min(r.left, window.innerWidth - w - GAP));
    var top = r.bottom + GAP / 2;
    if (top + h > window.innerHeight - GAP && r.top - h - GAP / 2 > GAP) top = r.top - h - GAP / 2;
    panel.style.left = left + "px";
    panel.style.top = top + "px";
  }

  document.addEventListener("toggle", function (event) {
    var d = event.target;
    if (!d || !d.matches || !d.matches("details.who") || !d.open) return;
    closeWhos(d);
    var search = d.querySelector("[data-who-search]");
    if (search) {
      search.value = ""; // abre sempre com todas as pessoas, sem a busca da vez anterior
      filterWho(search);
    }
    placeWho(d);
    if (search) search.focus({ preventScroll: true });
  }, true);

  function filterWho(box) {
    var panel = box.closest(".who__panel");
    var q = plain(box.value);
    var any = false;
    Array.prototype.forEach.call(panel.querySelectorAll("[data-who-item]"), function (li) {
      var hit = !q || plain(li.getAttribute("data-search")).indexOf(q) !== -1;
      li.hidden = !hit;
      any = any || hit;
    });
    var none = panel.querySelector(".who__none");
    if (none) none.hidden = any;
  }

  document.addEventListener("input", function (event) {
    var box = event.target;
    if (box && box.matches && box.matches("[data-who-search]")) filterWho(box);
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Enter" && event.target.matches && event.target.matches("[data-who-search]")) {
      event.preventDefault(); // Enter na busca não atribui ninguém sem querer
      return;
    }
    if (event.key !== "Escape") return;
    var open = openWhos();
    if (!open.length) return;
    var summary = open[0].querySelector("summary");
    closeWhos(null);
    if (summary) summary.focus();
  });

  document.addEventListener("click", function (event) {
    if (!openWhos().length) return;
    closeWhos(event.target.closest ? event.target.closest("details.who") : null);
  });

  // Ao rolar ou redimensionar (no celular, o teclado muda a altura), a janelinha acompanha a bolinha;
  // só fecha se a bolinha saiu da tela.
  function followWhos() {
    Array.prototype.forEach.call(openWhos(), function (d) {
      var r = d.querySelector("summary").getBoundingClientRect();
      if (r.bottom < 0 || r.top > window.innerHeight) d.removeAttribute("open");
      else placeWho(d);
    });
  }

  window.addEventListener("scroll", followWhos, { passive: true });
  window.addEventListener("resize", followWhos);

  // Seletor de projeto e modo de progresso: aplica ao escolher (sem JS, botão “Abrir”/“Salvar”).
  document.addEventListener("change", function (event) {
    var form = event.target && event.target.closest ? event.target.closest("form[data-autosubmit]") : null;
    if (form) form.requestSubmit();
  });
})();
