from django import template

register = template.Library()


@register.simple_tag
def filtro_opcoes(cl, spec):
    """Opções de um filtro da lista (Todos, Branca, Azul...), para montar o menu suspenso."""
    return list(spec.choices(cl))


@register.simple_tag
def filtro_escolhido(opcoes):
    """Texto da opção marcada, ou vazio se estiver em 'Todos'."""
    for i, o in enumerate(opcoes):
        if o.get("selected") and i > 0:
            return o.get("display", "")
    return ""


TITULOS = {"contatado": "Já contatado?", "status": "Situação da matrícula", "turma": "Turma", "faixa": "Faixa", "forma": "Forma"}


@register.simple_tag
def filtro_titulo(spec):
    """Nome do filtro em linguagem simples."""
    chave = getattr(spec, "lookup_kwarg", "") or getattr(spec, "field_path", "") or ""
    chave = str(chave).split("__")[0]
    return TITULOS.get(chave) or str(spec.title).capitalize()


@register.simple_tag
def versao_arquivo(caminho):
    """Número que muda quando o arquivo muda: o navegador baixa a versão nova."""
    from django.conf import settings
    arq = settings.BASE_DIR / "static" / caminho
    try:
        return int(arq.stat().st_mtime)
    except OSError:
        return 0


CORES_FAIXA = {
    "branca": "#f2f2f2", "cinza": "#9a9a9a", "amarela": "#f4c20d", "laranja": "#f08a24",
    "verde": "#2e9e4f", "azul": "#2457d6", "roxa": "#7a3bc2", "marrom": "#6b3f1d", "preta": "#161618",
}


@register.filter
def cor_faixa(faixa):
    """Cor principal da faixa (a das faixas infantis com listra é a da base)."""
    return CORES_FAIXA.get(str(faixa).split("-")[0], "#555")


@register.filter
def cinto_classe(faixa):
    """Classes do desenho da faixa: barra vermelha na preta; listra branca ou preta nas infantis."""
    partes = str(faixa).split("-")
    classes = []
    if partes[0] == "preta":
        classes.append("preta")
    if len(partes) > 1:
        classes.append("listra-" + partes[1])
    return " ".join(classes)


@register.filter
def listras(grau):
    from django.utils.safestring import mark_safe
    try:
        n = max(0, min(4, int(grau)))
    except (TypeError, ValueError):
        n = 0
    return mark_safe("<b></b>" * n)
