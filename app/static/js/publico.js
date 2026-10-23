/* Controle de Produção — animações do site público (ADR-0016).
   Melhoria progressiva: sem este arquivo (ou com "reduzir movimento") a página aparece inteira e parada.
   Carregado no <head> sem defer só para marcar a classe pub-reveal antes da primeira pintura; o resto
   espera o DOM. Sem eval, sem estilo inline, sem bibliotecas (CSP default-src 'self'). */
(function () {
  "use strict";
  var root = document.documentElement;
  var reduce = !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  var canObserve = "IntersectionObserver" in window;

  // Esconde os blocos .rv só se der para revelá-los depois.
  if (canObserve && !reduce) root.classList.add("pub-reveal");

  function each(list, fn) {
    for (var i = 0; i < list.length; i++) fn(list[i], i);
  }

  // Reveal ao rolar: cada bloco .rv ganha .is-in quando entra na tela.
  function setupReveal() {
    var blocks = document.querySelectorAll(".rv");
    if (!canObserve || reduce) {
      each(blocks, function (el) { el.classList.add("is-in"); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      each(entries, function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-in");
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -4% 0px" });
    each(blocks, function (el) { io.observe(el); });
  }

  // Números do painel de exemplo contam de zero até o valor final (decimal com vírgula).
  function setupCounters() {
    if (reduce) return;
    each(document.querySelectorAll("[data-count]"), function (el) {
      var to = parseFloat(el.getAttribute("data-count"));
      var dec = parseInt(el.getAttribute("data-dec") || "0", 10);
      if (isNaN(to)) return;
      function show(value) { el.textContent = value.toFixed(dec).replace(".", ","); }
      show(0);
      var start = null;
      function frame(t) {
        if (start === null) start = t;
        var p = Math.min(1, (t - start) / 1600);
        show(to * (1 - Math.pow(1 - p, 3)));
        if (p < 1) window.requestAnimationFrame(frame);
      }
      window.setTimeout(function () { window.requestAnimationFrame(frame); }, 900);
    });
  }

  // Os três passos se destacam um de cada vez; passar o mouse pausa, clicar escolhe.
  function setupSteps() {
    each(document.querySelectorAll("[data-steps]"), function (group) {
      var steps = group.querySelectorAll(".pub-step");
      var current = 0;
      var timer = null;
      function go(i) {
        each(steps, function (step, k) {
          step.classList.remove("is-on");
          if (k === i) {
            void step.offsetWidth; // reinicia a barra de tempo
            step.classList.add("is-on");
          }
        });
        current = i;
      }
      function stop() { if (timer) { window.clearInterval(timer); timer = null; } }
      function start() {
        stop();
        if (reduce) return;
        timer = window.setInterval(function () { go((current + 1) % steps.length); }, 3200);
      }
      each(steps, function (step, i) {
        step.addEventListener("click", function () { go(i); start(); });
      });
      group.addEventListener("mouseenter", stop);
      group.addEventListener("mouseleave", start);
      start();
    });
  }

  function ready() {
    setupReveal();
    setupCounters();
    setupSteps();
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", ready);
  else ready();
})();
