/* Controle de Produção — arrastar etapas e atividades na tela de edição (Etapa D).
   HTML5 drag-and-drop nativo, sem biblioteca, sem estilo inline (CSP default-src 'self').
   O navegador só ENVIA a intenção (nova ordem das etapas, ou etapa+posição da atividade)
   pelos formulários #ordem-etapas e #mover-atividade; o servidor valida (empresa, projeto,
   versão), grava, audita e devolve a tela. Sem JS: botões Subir/Descer e “Mover”. */
(function () {
  "use strict";

  var dragged = null; // .sort-item sendo arrastado
  var origin = null; // {parent, next} para desfazer a prévia se não houver drop
  var dropped = false;

  function listOf(el) {
    return el && el.closest ? el.closest("[data-sort-list]") : null;
  }

  function kindOf(item) {
    var list = listOf(item);
    return list ? list.getAttribute("data-sort-list") : null;
  }

  function items(list) {
    return Array.prototype.filter.call(list.children, function (el) {
      return el.classList && el.classList.contains("sort-item");
    });
  }

  // Só a alça liga o arrastar: campos de texto continuam selecionáveis.
  document.addEventListener("pointerdown", function (event) {
    var handle = event.target.closest && event.target.closest("[data-drag-handle]");
    if (!handle) return;
    var item = handle.closest(".sort-item");
    if (item) item.setAttribute("draggable", "true");
  });

  document.addEventListener("pointerup", function () {
    if (dragged) return;
    var armed = document.querySelectorAll('.sort-item[draggable="true"]');
    for (var i = 0; i < armed.length; i++) armed[i].removeAttribute("draggable");
  });

  document.addEventListener("dragstart", function (event) {
    var item = event.target;
    if (!item || !item.classList || !item.classList.contains("sort-item") || item.getAttribute("draggable") !== "true") return;
    dragged = item;
    dropped = false;
    origin = { parent: item.parentNode, next: item.nextSibling };
    item.classList.add("is-dragging");
    if (event.dataTransfer) {
      event.dataTransfer.effectAllowed = "move";
      event.dataTransfer.setData("text/plain", item.getAttribute("data-sort-id") || "");
    }
    event.stopPropagation();
  });

  function targetList(event) {
    if (!dragged) return null;
    var list = listOf(event.target);
    // Etapa só dentro da lista de etapas; atividade em qualquer lista de atividades.
    while (list && list.getAttribute("data-sort-list") !== kindOf(dragged)) list = listOf(list.parentNode);
    return list;
  }

  document.addEventListener("dragover", function (event) {
    var list = targetList(event);
    if (!list) return;
    event.preventDefault();
    if (event.dataTransfer) event.dataTransfer.dropEffect = "move";
    // Prévia: põe o item antes do primeiro irmão cujo meio fica abaixo do cursor.
    var before = null;
    var siblings = items(list);
    for (var i = 0; i < siblings.length; i++) {
      if (siblings[i] === dragged) continue;
      var box = siblings[i].getBoundingClientRect();
      if (event.clientY < box.top + box.height / 2) {
        before = siblings[i];
        break;
      }
    }
    if (before) {
      if (before !== dragged.nextSibling) list.insertBefore(dragged, before);
    } else if (list.lastElementChild !== dragged) {
      list.appendChild(dragged);
    }
  });

  document.addEventListener("drop", function (event) {
    var list = targetList(event);
    if (!list) return;
    event.preventDefault();
    dropped = true;
    if (kindOf(dragged) === "stages") {
      var form = document.getElementById(list.getAttribute("data-sort-form"));
      if (!form) return;
      var old = form.querySelectorAll('input[name="order"]');
      for (var i = 0; i < old.length; i++) old[i].parentNode.removeChild(old[i]);
      items(list).forEach(function (item) {
        var input = document.createElement("input");
        input.type = "hidden";
        input.name = "order";
        input.value = item.getAttribute("data-sort-id");
        form.appendChild(input);
      });
      form.submit();
      return;
    }
    var move = document.getElementById("mover-atividade");
    if (!move) return;
    move.action = dragged.getAttribute("data-move-url");
    move.elements.stage_id.value = list.getAttribute("data-drop-stage");
    move.elements.position.value = String(items(list).indexOf(dragged));
    move.elements.version.value = dragged.getAttribute("data-version") || "";
    move.submit();
  });

  document.addEventListener("dragend", function () {
    if (!dragged) return;
    dragged.classList.remove("is-dragging");
    dragged.removeAttribute("draggable");
    if (!dropped && origin && origin.parent) origin.parent.insertBefore(dragged, origin.next);
    dragged = null;
    origin = null;
  });
})();
