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
