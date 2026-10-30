/* Tour de primeiro acesso (ADR-0021).
 *
 * Os passos vêm prontos do servidor (services/tour.py, por papel). Este arquivo só mostra um
 * passo por vez: destaca o item do menu com o mesmo [data-tour] e posiciona o balão ao lado.
 * Sem o item visível (celular), usa o item de reserva (o botão Mais) ou o centro da tela.
 * Ao começar, grava “visto” (POST com o CSRF do formulário); Pular, Esc e Concluir fecham.
 */
(function () {
  "use strict";

  var root = document.querySelector("[data-tour-root]");
  if (!root) return;

  var spot = root.querySelector(".tour__spot");
  var card = root.querySelector(".tour__card");
  var elN = root.querySelector("[data-tour-n]");
  var elTitle = root.querySelector("[data-tour-title]");
  var elText = root.querySelector("[data-tour-text]");
  var dots = root.querySelectorAll(".tour__dot");
  var btnPrev = root.querySelector("[data-tour-prev]");
  var btnNext = root.querySelector("[data-tour-next]");
  var btnSkip = root.querySelector("[data-tour-skip]");
  var steps = [];
  var items = root.querySelectorAll(".tour__steps li");
  for (var k = 0; k < items.length; k++) {
    steps.push({
      title: items[k].querySelector("strong").textContent,
      text: items[k].querySelector("span").textContent,
      target: items[k].getAttribute("data-alvo"),
      fallback: items[k].getAttribute("data-reserva"),
      fallbackText: items[k].getAttribute("data-reserva-texto") || ""
    });
  }
  if (!steps.length) return;

  var current = 0;
  var lastFocus = null;
  var GAP = 12; // distância entre o item destacado e o balão (px de layout, não de estilo)
  var PAD = 6; // folga do destaque em volta do item

  function visible(el) {
    if (!el || !el.getClientRects().length) return false;
    var r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) return false;
    // Dentro de uma folha fechada (menu Mais) não conta como visível.
    var sheet = el.closest(".sheet");
    return !sheet || sheet.classList.contains("is-open") || location.hash === "#" + sheet.id;
  }

  function findTarget(name) {
    if (!name) return null;
    var all = document.querySelectorAll('[data-tour="' + name + '"]');
    for (var i = 0; i < all.length; i++) {
      if (!root.contains(all[i]) && visible(all[i])) return all[i];
    }
    return null;
  }

  function place() {
    var step = steps[current];
    var target = findTarget(step.target) || findTarget(step.fallback);
    var vw = document.documentElement.clientWidth;
    var vh = document.documentElement.clientHeight;
    root.classList.toggle("tour--center", !target);
    if (!target) {
      spot.style.top = vh / 2 + "px";
      spot.style.left = vw / 2 + "px";
      spot.style.width = "0px";
      spot.style.height = "0px";
      card.style.top = Math.max(GAP, (vh - card.offsetHeight) / 2) + "px";
      card.style.left = Math.max(GAP, (vw - card.offsetWidth) / 2) + "px";
      return;
    }
    var r = target.getBoundingClientRect();
    spot.style.top = r.top - PAD + "px";
    spot.style.left = r.left - PAD + "px";
    spot.style.width = r.width + PAD * 2 + "px";
    spot.style.height = r.height + PAD * 2 + "px";
    var cw = card.offsetWidth;
    var ch = card.offsetHeight;
    var top;
    var left;
    if (r.right + PAD + GAP + cw <= vw - GAP) {
      // Ao lado (menu lateral).
      left = r.right + PAD + GAP;
      top = r.top + r.height / 2 - ch / 2;
    } else if (r.top - PAD - GAP - ch >= GAP) {
      // Acima (navegação inferior do celular).
      top = r.top - PAD - GAP - ch;
      left = r.left + r.width / 2 - cw / 2;
    } else {
      // Abaixo.
      top = r.bottom + PAD + GAP;
      left = r.left + r.width / 2 - cw / 2;
    }
    card.style.top = Math.min(Math.max(GAP, top), Math.max(GAP, vh - ch - GAP)) + "px";
    card.style.left = Math.min(Math.max(GAP, left), Math.max(GAP, vw - cw - GAP)) + "px";
  }

  function render() {
    var step = steps[current];
    elN.textContent = String(current + 1);
    elTitle.textContent = step.title;
    var onFallback = !findTarget(step.target) && step.fallbackText && findTarget(step.fallback);
    elText.textContent = onFallback ? step.text + " " + step.fallbackText : step.text;
    for (var i = 0; i < dots.length; i++) dots[i].classList.toggle("is-on", i === current);
    btnPrev.hidden = current === 0;
    var last = current === steps.length - 1;
    btnNext.querySelector(".btn__label").textContent = current === 0 ? "Começar" : last ? "Concluir" : "Próximo";
    btnSkip.hidden = last;
    var target = findTarget(step.target);
    if (target && target.scrollIntoView) target.scrollIntoView({ block: "nearest" });
    place();
    card.focus();
  }

  function close() {
    root.hidden = true;
    document.documentElement.classList.remove("tour-open");
    window.removeEventListener("resize", place);
    window.removeEventListener("scroll", place, true);
    document.removeEventListener("keydown", onKey, true);
    var back = lastFocus && document.contains(lastFocus) ? lastFocus : document.getElementById("conteudo");
    if (back) back.focus();
  }

  function onKey(event) {
    if (event.key === "Escape") {
      event.preventDefault();
      close();
    } else if (event.key === "ArrowRight" && current < steps.length - 1 && event.target === card) {
      current += 1;
      render();
    } else if (event.key === "ArrowLeft" && current > 0 && event.target === card) {
      current -= 1;
      render();
    } else if (event.key === "Tab") {
      // Foco preso no balão enquanto o tour está aberto.
      var focusable = Array.prototype.filter.call(card.querySelectorAll("button"), function (b) { return !b.hidden; });
      if (!focusable.length) return;
      var first = focusable[0];
      var lastEl = focusable[focusable.length - 1];
      if (event.shiftKey && (document.activeElement === first || document.activeElement === card)) {
        event.preventDefault();
        lastEl.focus();
      } else if (!event.shiftKey && document.activeElement === lastEl) {
        event.preventDefault();
        first.focus();
      }
    }
  }

  function markSeen() {
    var form = root.querySelector("[data-tour-seen]");
    if (!form || !window.fetch || !window.FormData) return;
    fetch(form.action, { method: "POST", body: new FormData(form), credentials: "same-origin" }).catch(function () {
      /* sem rede: o tour abre de novo na próxima visita, nada se perde */
    });
  }

  btnNext.addEventListener("click", function () {
    if (current >= steps.length - 1) {
      close();
      return;
    }
    current += 1;
    render();
  });
  btnPrev.addEventListener("click", function () {
    if (current > 0) {
      current -= 1;
      render();
    }
  });
  btnSkip.addEventListener("click", close);

  function start() {
    // “Rever o tour” (?tutorial=1): tira o parâmetro para recarregar a página não reabrir.
    if (window.history && history.replaceState && /[?&]tutorial=1/.test(location.search)) {
      var url = new URL(location.href);
      url.searchParams.delete("tutorial");
      history.replaceState(history.state, "", url.pathname + url.search + url.hash);
    }
    lastFocus = document.activeElement;
    root.hidden = false;
    document.documentElement.classList.add("tour-open");
    window.addEventListener("resize", place);
    window.addEventListener("scroll", place, true);
    document.addEventListener("keydown", onKey, true);
    markSeen();
    render();
  }

  if (document.readyState === "complete") start();
  else window.addEventListener("load", start);
})();
