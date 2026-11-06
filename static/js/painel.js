/* Painel CT Salvação: tema claro/escuro, formulários em caixinha, menu de três pontinhos, chamada. */
(function () {
  "use strict";
  var emModal = window.self !== window.top;
  var raiz = document.documentElement;

  function cookie(n) { var m = document.cookie.match("(?:^|; )" + n + "=([^;]*)"); return m ? decodeURIComponent(m[1]) : ""; }


  /* ---------- aviso de carregando: barra no topo e bolinha girando ---------- */
  var barra, bolinha, timer;
  function montaCarregando() {
    if (barra) return;
    barra = document.createElement("div"); barra.id = "carregando"; barra.innerHTML = "<i></i>";
    bolinha = document.createElement("div"); bolinha.id = "girando"; bolinha.setAttribute("role", "status"); bolinha.setAttribute("aria-label", "Carregando");
    document.body.appendChild(barra); document.body.appendChild(bolinha);
  }
  function comecaCarregar() {
    montaCarregando();
    raiz.classList.add("carregando");
    clearTimeout(timer);
    timer = setTimeout(function () { raiz.classList.add("carregando-lento"); }, 350);
  }
  function paraCarregar() {
    raiz.classList.remove("carregando", "carregando-lento");
    clearTimeout(timer);
    document.querySelectorAll(".esperando").forEach(function (b) { b.classList.remove("esperando"); });
  }
  window.addEventListener("pageshow", paraCarregar);
  document.addEventListener("click", function (e) {
    if (e.defaultPrevented) return;
    var a = e.target.closest && e.target.closest("a[href]");
    if (!a || e.ctrlKey || e.metaKey || e.shiftKey || e.button !== 0 || a.target === "_blank" || a.hasAttribute("download")) return;
    var h = a.getAttribute("href") || "";
    if (!h || h.charAt(0) === "#" || h.indexOf("javascript:") === 0 || h.indexOf("mailto:") === 0 || h.indexOf("tel:") === 0) return;
    try { if (new URL(a.href, location.href).origin !== location.origin) return; } catch (err) { return; }
    comecaCarregar();
  });
  document.addEventListener("submit", function (e) {
    var f = e.target;
    if (f.target === "_blank" || e.defaultPrevented) return;
    var b = f.querySelector('button[type="submit"], input[type="submit"]');
    if (b) b.classList.add("esperando");
    comecaCarregar();
  });

  /* ---------- tema: só claro e escuro ---------- */
  function aplicaTema(t) {
    raiz.dataset.theme = t;
    try { localStorage.setItem("theme", t); } catch (e) {}
  }

  /* ---------- dentro da caixinha: esconde o resto e avisa o painel quando terminar ---------- */
  if (emModal) {
    raiz.classList.add("em-modal");
    document.addEventListener("DOMContentLoaded", function () {
      var lista = document.body.classList.contains("change-list") || document.body.classList.contains("dashboard");
      if (lista) { window.parent.postMessage({ painel: "fechar" }, "*"); return; }
      document.querySelectorAll("a.cancel-link, .cancel-link").forEach(function (a) {
        a.addEventListener("click", function (e) { e.preventDefault(); window.parent.postMessage({ painel: "fechar", recarregar: false }, "*"); });
      });
      document.querySelectorAll("a.closelink").forEach(function (a) {
        a.addEventListener("click", function (e) { e.preventDefault(); window.parent.postMessage({ painel: "fechar", recarregar: false }, "*"); });
      });
    });
    return;
  }

  /* ---------- caixinha (modal) para adicionar, editar e excluir ---------- */
  var dlg, quadro, tituloEl;
  function montaCaixinha() {
    if (dlg) return;
    dlg = document.createElement("dialog");
    dlg.className = "caixinha";
    dlg.innerHTML = '<div class="caixinha-topo"><strong id="caixinha-titulo"></strong><button type="button" class="caixinha-x" aria-label="Fechar">×</button></div><iframe title="Formulário" class="caixinha-quadro"></iframe>';
    document.body.appendChild(dlg);
    quadro = dlg.querySelector("iframe");
    tituloEl = dlg.querySelector("#caixinha-titulo");
    dlg.querySelector(".caixinha-x").addEventListener("click", function () { fecha(false); });
    dlg.addEventListener("click", function (e) { if (e.target === dlg) fecha(false); });
    dlg.addEventListener("cancel", function () { quadro.src = "about:blank"; });
    quadro.addEventListener("load", function () {
      dlg.classList.remove("abrindo");
      try {
        var h1 = quadro.contentDocument.querySelector("#content h1, .titles h1");
        if (h1) tituloEl.textContent = h1.textContent.trim();
      } catch (e) {}
    });
  }
  function abre(url) {
    montaCaixinha();
    tituloEl.textContent = "";
    dlg.classList.add("abrindo");
    quadro.src = url + (url.indexOf("?") > -1 ? "&" : "?") + "_modal=1";
    if (!dlg.open) dlg.showModal();
  }
  function fecha(recarregar) {
    if (!dlg) return;
    dlg.close();
    quadro.src = "about:blank";
    if (recarregar) window.location.reload();
  }
  window.addEventListener("message", function (e) {
    if (e.data && e.data.painel === "fechar") fecha(e.data.recarregar !== false);
  });

  var PADRAO = /\/admin\/(core|auth)\/[a-z]+\/(add|\d+\/change|\d+\/delete)\/$/;
  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("a[href]");
    if (!a || e.ctrlKey || e.metaKey || e.shiftKey || a.target === "_blank") return;
    var url;
    try { url = new URL(a.href, location.href); } catch (err) { return; }
    if (url.origin !== location.origin || !PADRAO.test(url.pathname)) return;
    e.preventDefault();
    abre(url.pathname + url.search);
  });

  /* ---------- ao carregar ---------- */
  document.addEventListener("DOMContentLoaded", function () {
    var btn = document.getElementById("tema-btn");
    if (btn) btn.addEventListener("click", function () {
      aplicaTema(raiz.dataset.theme === "light" ? "dark" : "light");
    });

    /* fecha menus de três pontinhos ao clicar fora */
    document.addEventListener("click", function (e) {
      document.querySelectorAll("details.pontos[open]").forEach(function (d) { if (!d.contains(e.target)) d.removeAttribute("open"); });
    });
    document.querySelectorAll("details.pontos").forEach(function (d) {
      d.addEventListener("toggle", function () {
        if (d.open) document.querySelectorAll("details.pontos[open]").forEach(function (o) { if (o !== d) o.removeAttribute("open"); });
      });
    });

    /* botão WhatsApp: abre a conversa e já marca como contatado */
    document.querySelectorAll("a[data-chamar]").forEach(function (a) {
      var url = a.getAttribute("data-chamar");
      if (!url) return;
      a.addEventListener("click", function () {
        fetch(url, { method: "POST", credentials: "same-origin", headers: { "X-CSRFToken": cookie("csrftoken"), "X-Requested-With": "fetch" } })
          .then(function () {
            var linha = a.closest("tr");
            var pilula = linha && linha.querySelector(".pilula");
            if (pilula) { pilula.textContent = "Já contatado"; pilula.className = "pilula ok"; }
            a.removeAttribute("data-chamar");
            var item = linha && linha.querySelector('form[action$="/contatado/"]');
            if (item && item.closest("li")) item.closest("li").remove();
          });
      });
    });

    /* chamada: contador e botões de marcar todos */
    var form = document.getElementById("chamada-form");
    if (form) {
      var caixas = form.querySelectorAll('input[name="aluno"]');
      var conta = document.getElementById("contagem");
      function atualiza() {
        var n = 0; caixas.forEach(function (c) { if (c.checked) n++; });
        if (conta) conta.textContent = n + " de " + caixas.length + " presentes";
      }
      caixas.forEach(function (c) { c.addEventListener("change", atualiza); });
      var sim = document.getElementById("todos-sim"), nao = document.getElementById("todos-nao");
      if (sim) sim.addEventListener("click", function () { caixas.forEach(function (c) { c.checked = true; }); atualiza(); });
      if (nao) nao.addEventListener("click", function () { caixas.forEach(function (c) { c.checked = false; }); atualiza(); });
      atualiza();
    }
  });
})();
