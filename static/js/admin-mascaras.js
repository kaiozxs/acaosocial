/* Máscaras de digitação do painel: data (dd/mm/aaaa) e telefone ((21) 99999-9999). */
(function () {
  function data(v) {
    var d = v.replace(/\D/g, "").slice(0, 8);
    if (d.length > 4) return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
    if (d.length > 2) return d.slice(0, 2) + "/" + d.slice(2);
    return d;
  }
  var PREFIXO = "+55 (21) ";
  function fone(v, apagando) {
    var d = v.replace(/\D/g, "");
    var local = ((v.charAt(0) === "+" || d.length > 11) && d.indexOf("55") === 0) ? d.slice(2) : d;
    local = local.slice(0, 11);
    if (!local.length) return apagando ? "" : "+55 (";
    if (local.length <= 2) return "+55 (" + local + (local.length === 2 && !apagando ? ") " : "");
    var resto = local.slice(2);
    var corpo = resto.length > 4 ? resto.slice(0, resto.length - 4) + "-" + resto.slice(-4) : resto;
    return "+55 (" + local.slice(0, 2) + ") " + corpo;
  }
  function aplica(e) {
    var el = e.target;
    if (!el || el.tagName !== "INPUT") return;
    if (el.classList.contains("vDateField")) {
      if (e.inputType && e.inputType.indexOf("delete") === 0 && /[\/]$/.test(el.value)) return;
      el.value = data(el.value);
    } else if (/telefone/.test(el.name || "")) {
      el.value = fone(el.value, !!(e.inputType && e.inputType.indexOf("delete") === 0));
    }
  }
  document.addEventListener("input", aplica);
  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll('input[name*="telefone"]').forEach(function (el) {
      el.setAttribute("inputmode", "tel");
      el.setAttribute("autocomplete", "tel");
      el.setAttribute("maxlength", "19");
      el.setAttribute("placeholder", PREFIXO + "99999-9999");
      el.value = el.value ? fone(el.value, false) : PREFIXO;
      el.addEventListener("focus", function () { if (!el.value) { el.value = PREFIXO; } });
      var dica = document.createElement("div");
      dica.className = "help";
      dica.textContent = "Brasil (+55) · DDD 21 já preenchido, é só digitar o número.";
      el.insertAdjacentElement("afterend", dica);
      if (el.form) el.form.addEventListener("submit", function () {
        if (el.value.replace(/\D/g, "").length <= 4) el.value = "";
      });
    });
    document.querySelectorAll("input.vDateField").forEach(function (el) {
      el.setAttribute("inputmode", "numeric");
      el.setAttribute("placeholder", "dd/mm/aaaa");
      el.setAttribute("maxlength", "10");
    });
  });
})();

/* Lista em cartões no celular, botões de ação por linha e busca em português. */
(function () {
  function cookie(n) { var m = document.cookie.match("(?:^|; )" + n + "=([^;]*)"); return m ? decodeURIComponent(m[1]) : ""; }
  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("#result_list").forEach(function (tab) {
      var rot = Array.prototype.map.call(tab.querySelectorAll("thead th"), function (th) {
        var t = th.querySelector(".text") || th; return (t.textContent || "").trim();
      });
      tab.querySelectorAll("tbody tr").forEach(function (tr) {
        Array.prototype.forEach.call(tr.children, function (c, i) { if (rot[i]) c.setAttribute("data-label", rot[i]); });
      });
    });
    document.querySelectorAll("form.acao-linha").forEach(function (f) {
      var i = document.createElement("input"); i.type = "hidden"; i.name = "csrfmiddlewaretoken"; i.value = cookie("csrftoken"); f.appendChild(i);
    });
    var b = document.getElementById("searchbar");
    if (b) b.setAttribute("placeholder", "Buscar pelo nome ou telefone");
  });
})();

/* Palavras mais simples nos botões do Django. */
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll("a.deletelink").forEach(function (a) { a.textContent = "Excluir"; });
  document.querySelectorAll('input[name="_save"]').forEach(function (i) { i.value = "Salvar"; });
});

/* Calendário abre ao clicar em qualquer parte do campo de data; textos mais simples nos formulários. */
document.addEventListener("click", function (e) {
  var i = e.target;
  if (i && i.tagName === "INPUT" && i.type === "date" && typeof i.showPicker === "function") { try { i.showPicker(); } catch (err) {} }
});
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".add-row a").forEach(function (a) {
    a.textContent = a.textContent.replace("Adicionar outro(a) ", "Adicionar ").replace("Adicionar outro ", "Adicionar ");
  });
  document.querySelectorAll(".inline-group h2").forEach(function (h) {
    if (/faixa/i.test(h.textContent)) h.textContent = "Histórico de faixas";
  });
});

/* No celular o teclado não abre sozinho ao entrar na lista. */
document.addEventListener("DOMContentLoaded", function () {
  var b = document.getElementById("searchbar");
  if (b && window.innerWidth < 980) { b.removeAttribute("autofocus"); b.blur(); }
});

/* Contagem de resultados mais limpa: "2 resultados · Mostrar tudo". */
document.addEventListener("DOMContentLoaded", function () {
  var c = document.querySelector("#toolbar span.small, #toolbar .quiet");
  if (c) c.innerHTML = c.innerHTML.replace(/\(\s*/, "· ").replace(/\s*\)\s*$/, "");
});

/* Histórico de faixas no celular: cada linha vira um cartão com rótulos; texto do botão de adicionar mais simples. */
(function () {
  function arruma() {
    document.querySelectorAll(".add-row a").forEach(function (a) {
      a.textContent = a.textContent.replace("Adicionar outro(a) ", "Adicionar ").replace("Adicionar outro ", "Adicionar ");
    });
    document.querySelectorAll(".inline-group .tabular table").forEach(function (t) {
      var rot = Array.prototype.map.call(t.querySelectorAll("thead th"), function (th) { return (th.textContent || "").trim().replace(/\*$/, ""); });
      t.querySelectorAll("tbody tr").forEach(function (tr) {
        Array.prototype.forEach.call(tr.children, function (c, i) { if (rot[i] && !c.getAttribute("data-label")) c.setAttribute("data-label", rot[i]); });
      });
    });
  }
  document.addEventListener("DOMContentLoaded", function () { arruma(); setTimeout(arruma, 400); });
  document.addEventListener("click", function (e) { if (e.target.closest && e.target.closest(".add-row")) setTimeout(arruma, 50); });
})();
