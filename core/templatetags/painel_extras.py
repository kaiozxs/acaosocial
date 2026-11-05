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
