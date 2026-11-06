from datetime import date, timedelta
from urllib.parse import quote

import base64
import hashlib
import io

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group, User
from django.core.cache import cache
from django.core.paginator import Paginator
from django import forms
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.http import HttpResponse, JsonResponse
from django.utils.functional import cached_property
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import Faixa, Aluno, Assinatura, Doacao, Graduacao, Interessado, Presenca, Turma

COR_FAIXA = {
    "branca": "#f2f2f2", "cinza": "#9a9a9a", "amarela": "#f4c20d", "laranja": "#f08a24",
    "verde": "#2e9e4f", "azul": "#2457d6", "roxa": "#7a3bc2", "marrom": "#6b3f1d", "preta": "#111",
}


class PaginadorEmCache(Paginator):
    """Paginador que guarda a contagem por alguns minutos (o cache é limpo quando algo muda)."""

    @cached_property
    def count(self):
        try:
            chave = "contagem_" + hashlib.md5(str(self.object_list.query).encode()).hexdigest()
        except Exception:
            return super().count
        valor = cache.get(chave)
        if valor is None:
            valor = super().count
            cache.set(chave, valor, 300)
        return valor


class PainelAdmin(admin.ModelAdmin):
    """Base do painel: sem menu 'Ação', com botões simples em cada linha."""

    actions = None
    date_hierarchy = None
    show_full_result_count = False
    paginator = PaginadorEmCache
    ajuda = ""
    texto_novo = ""

    def changelist_view(self, request, extra_context=None):
        extra_context = dict(extra_context or {})
        extra_context.setdefault("ajuda", self.ajuda)
        extra_context.setdefault("texto_novo", self.texto_novo or f"Adicionar {self.model._meta.verbose_name}")
        return super().changelist_view(request, extra_context)

    def _url(self, nome, obj):
        o = self.model._meta
        return reverse(f"admin:{o.app_label}_{o.model_name}_{nome}", args=[obj.pk])

    def botao_post(self, obj, nome, texto, classe=""):
        return format_html(
            '<form method="post" action="{}" class="acao-linha"><button type="submit" class="btn {}">{}</button></form>',
            self._url(nome, obj), classe, texto)

    def botao_link(self, obj, nome, texto, classe="", params=""):
        return format_html('<a class="btn {}" href="{}{}">{}</a>', classe, self._url(nome, obj), params, texto)

    def acoes_html(self, *itens):
        return format_html('<div class="acoes-linha">{}</div>', mark_safe("".join(str(i) for i in itens)))

    # --- menu de três pontinhos ---
    def menu_pontos(self, *itens):
        return format_html(
            '<details class="pontos"><summary aria-label="Mais opções"><svg viewBox="0 0 24 24"><circle cx="12" cy="5" r="1.9"/>'
            '<circle cx="12" cy="12" r="1.9"/><circle cx="12" cy="19" r="1.9"/></svg></summary><ul>{}</ul></details>',
            mark_safe("".join(str(i) for i in itens)))

    def item_link(self, obj, nome, texto, perigo=False):
        return format_html('<li><a href="{}" class="{}">{}</a></li>', self._url(nome, obj), "perigo" if perigo else "", texto)

    def item_post(self, obj, nome, texto):
        return format_html('<li><form method="post" action="{}" class="acao-linha"><button type="submit">{}</button></form></li>',
                           self._url(nome, obj), texto)

    def rota_post(self, nome, funcao, mensagem):
        """Cria uma rota <pk>/<nome>/ que executa `funcao(obj)`. Pelo botão volta para a lista; por fetch responde JSON."""
        o = self.model._meta

        def view(request, pk):
            obj = self.get_object(request, str(pk))
            feito = request.method == "POST" and obj is not None and self.has_change_permission(request, obj)
            if feito:
                funcao(obj)
            if request.headers.get("X-Requested-With") == "fetch":
                return JsonResponse({"ok": bool(feito)})
            if feito:
                self.message_user(request, mensagem.format(obj=obj), messages.SUCCESS)
            return redirect(request.META.get("HTTP_REFERER") or reverse(f"admin:{o.app_label}_{o.model_name}_changelist"))

        return path(f"<int:pk>/{nome}/", self.admin_site.admin_view(view), name=f"{o.app_label}_{o.model_name}_{nome}")


class GraduacaoInline(admin.TabularInline):
    model = Graduacao
    extra = 0


@admin.register(Aluno)
class AlunoAdmin(PainelAdmin):
    texto_novo = "Novo aluno"
    list_display = ("nome", "faixa_visual", "idade", "turma", "situacao", "menu")
    list_filter = ("status", "faixa", "turma")
    search_fields = ("nome", "telefone", "responsavel")
    inlines = [GraduacaoInline]
    list_select_related = ("turma",)
    ajuda = "Aqui ficam todos os alunos. Toque nos três pontinhos para editar as informações ou excluir. Para tirar um certificado, use o menu Certificados."
    change_list_template = "admin/core/aluno/change_list.html"

    def get_urls(self):
        return [path("certificado/", self.admin_site.admin_view(self.certificado), name="core_aluno_certificado")] + super().get_urls()

    def certificado(self, request):
        """Certificados: escolhe o aluno na lista e gera o PDF."""
        from . import certificado as cert

        faixas = Faixa.choices
        if request.method == "POST":
            nome = request.POST.get("nome", "").strip()
            chave = request.POST.get("faixa", "branca")
            nomes = dict(faixas)
            try:
                grau = max(0, min(4, int(request.POST.get("grau", 0))))
                dia = date.fromisoformat(request.POST.get("data", ""))
            except ValueError:
                grau, dia = 0, date.today()
            if nome and chave in nomes:
                ass = Assinatura.objects.first()
                pdf = cert.gerar(
                    nome, chave, nomes[chave].split(" (")[0], grau, dia,
                    ass.nome if ass else "Melino José",
                    ass.titulo if ass else "Faixa preta 1º grau de Jiu-Jitsu",
                    ass.imagem if ass else "")
                resp = HttpResponse(pdf, content_type="application/pdf")
                resp["Content-Disposition"] = f'inline; filename="certificado-{nome.replace(" ", "-")}.pdf"'
                return resp
        ctx = {**self.admin_site.each_context(request), "title": "Certificados", "faixas": faixas,
               "alunos": list(Aluno.objects.select_related("turma").order_by("nome")), "hoje": date.today().isoformat(),
               "abrir": request.GET.get("aluno", ""),
               "tem_assinatura": bool(Assinatura.objects.exclude(imagem="").exists()), "opts": self.model._meta}
        return render(request, "admin/core/aluno/certificado.html", ctx)

    @admin.display(description="Faixa")
    def faixa_visual(self, obj):
        barras = mark_safe("<b></b>" * min(obj.grau, 4))
        return format_html(
            '<span class="faixa-chip"><span class="cinto {}" style="--cor:{}">'
            '<i class="cinto-barra">{}</i></span><em>{}</em></span>',
            "preta" if obj.faixa == "preta" else "", COR_FAIXA.get(obj.faixa, "#444"), barras, obj.get_faixa_display().split(" (")[0])

    @admin.display(description="Situação", ordering="status")
    def situacao(self, obj):
        classe = {"ativa": "ok", "trancada": "novo", "cancelada": "off"}.get(obj.status, "")
        return format_html('<span class="pilula {}">{}</span>', classe, obj.get_status_display())

    @admin.display(description="")
    def menu(self, obj):
        return self.menu_pontos(self.item_link(obj, "change", "Editar informações"), self.item_link(obj, "delete", "Excluir", True))

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}

        def calcula():
            return {
                "total": Aluno.objects.count(),
                "ativos": Aluno.objects.filter(status=Aluno.Status.ATIVA).count(),
                "interessados": Interessado.objects.filter(contatado=False).count(),
            }
        extra_context["resumo"] = cache.get_or_set("resumo_alunos", calcula, 120)
        return super().changelist_view(request, extra_context)


@admin.register(Graduacao)
class GraduacaoAdmin(PainelAdmin):
    texto_novo = "Registrar troca de faixa"
    list_display = ("aluno", "faixa", "grau", "data", "botoes")
    list_select_related = ("aluno",)
    ajuda = ("Cada vez que um aluno troca de faixa ou ganha um grau, registre aqui. "
             "A faixa do aluno é atualizada sozinha e o histórico fica guardado. Clique em Adicionar troca de faixa.")

    @admin.display(description="O que fazer")
    def botoes(self, obj):
        return self.acoes_html(self.botao_link(obj, "change", "Abrir"), self.botao_link(obj, "delete", "Excluir", "perigo"))
    list_filter = ("faixa",)
    search_fields = ("aluno__nome",)
    autocomplete_fields = ("aluno",)


@admin.register(Presenca)
class PresencaAdmin(PainelAdmin):
    texto_novo = "Adicionar presença"
    list_display = ("aluno", "data")
    list_filter = ("data", "aluno__turma")
    list_select_related = ("aluno",)
    autocomplete_fields = ("aluno",)
    ajuda = "Lista de quem veio em cada dia. Para marcar a presença de hoje use a Chamada, no menu."

    def get_urls(self):
        return [path("chamada/", self.admin_site.admin_view(self.chamada), name="core_presenca_chamada")] + super().get_urls()

    def chamada(self, request):
        """Chamada: 1) escolhe a turma, 2) liga ou desliga cada aluno e salva. Mostra a frequência do mês."""
        base = {**self.admin_site.each_context(request), "title": "Chamada", "opts": self.model._meta}
        try:
            dia = date.fromisoformat(request.POST.get("data") or request.GET.get("data") or "")
        except ValueError:
            dia = date.today()
        param = request.POST.get("turma") or request.GET.get("turma") or ""
        if not param:
            turmas = Turma.objects.annotate(n=Count("aluno", filter=Q(aluno__status=Aluno.Status.ATIVA)))
            return render(request, "admin/core/presenca/chamada.html", {
                **base, "passo": 1, "turmas": turmas, "total": Aluno.objects.filter(status=Aluno.Status.ATIVA).count()})
        alunos_qs = Aluno.objects.filter(status=Aluno.Status.ATIVA).select_related("turma").order_by("nome")
        turma = None
        if param != "todos":
            turma = Turma.objects.filter(pk=int(param)).first() if param.isdigit() else None
            if turma is None:
                return redirect(reverse("admin:core_presenca_chamada"))
            alunos_qs = alunos_qs.filter(turma=turma)
        alunos = list(alunos_qs)
        ids = [a.pk for a in alunos]
        if request.method == "POST" and request.POST.get("salvar"):
            marcados = {int(x) for x in request.POST.getlist("aluno") if x.isdigit()} & set(ids)
            Presenca.objects.filter(data=dia, aluno_id__in=set(ids) - marcados).delete()
            for pk in marcados:
                Presenca.objects.get_or_create(aluno_id=pk, data=dia)
            self.message_user(request, f"Chamada de {dia:%d/%m/%Y} salva: {len(marcados)} presente(s) de {len(ids)}.", messages.SUCCESS)
            return redirect(f"{reverse('admin:core_presenca_chamada')}?turma={param}&data={dia.isoformat()}")
        salvos = set(Presenca.objects.filter(data=dia, aluno_id__in=ids).values_list("aluno_id", flat=True))
        ja_salva = bool(salvos)
        ini = dia.replace(day=1)
        no_mes = Presenca.objects.filter(aluno_id__in=ids, data__range=(ini, dia))
        contagem = dict(no_mes.values("aluno_id").annotate(n=Count("id")).values_list("aluno_id", "n"))
        aulas = no_mes.values("data").distinct().count()
        linhas = []
        for a in alunos:
            n = contagem.get(a.pk, 0)
            linhas.append({"aluno": a, "presente": (a.pk in salvos) if ja_salva else True, "n": n,
                           "pct": round(n / aulas * 100) if aulas else None})
        return render(request, "admin/core/presenca/chamada.html", {
            **base, "passo": 2, "turma": turma, "param": param, "linhas": linhas, "aulas": aulas, "ja_salva": ja_salva,
            "dia": dia, "dia_iso": dia.isoformat(), "dia_ant": (dia - timedelta(days=1)).isoformat(),
            "dia_prox": (dia + timedelta(days=1)).isoformat(), "mes": ["janeiro","fevereiro","março","abril","maio","junho","julho","agosto","setembro","outubro","novembro","dezembro"][dia.month - 1]})


@admin.register(Turma)
class TurmaAdmin(PainelAdmin):
    texto_novo = "Nova turma"
    list_display = ("nome", "modalidade", "publico", "dias", "horario", "botoes")
    fields = ("nome", "modalidade", "publico", "dias", "horario")
    ajuda = ("Turma é um grupo de treino com dia e horário fixos, por exemplo: Jiu-jitsu adulto, seg, qua e sex, 19h às 20h30. "
             "As turmas aparecem no site em Horários de treino e são usadas na chamada. Cadastre uma turma para cada horário.")

    @admin.display(description="O que fazer")
    def botoes(self, obj):
        return self.acoes_html(self.botao_link(obj, "change", "Abrir"), self.botao_link(obj, "delete", "Excluir", "perigo"))


@admin.register(Interessado)
class InteressadoAdmin(PainelAdmin):
    texto_novo = "Adicionar interessado"
    ajuda = "Pessoas que preencheram a ficha Quero treinar no site. Toque em WhatsApp para chamar: ao chamar, a pessoa já fica marcada como contatada."
    list_display = ("nome", "telefone", "idade", "situacao", "botoes")
    list_filter = ("contatado",)
    search_fields = ("nome", "telefone")

    def get_urls(self):
        return [self.rota_post("contatado", self._contatado, "{obj} marcado como já contatado.")] + super().get_urls()

    @staticmethod
    def _contatado(obj):
        obj.contatado = True
        obj.save(update_fields=["contatado"])

    @admin.display(description="Situação", ordering="contatado")
    def situacao(self, obj):
        if obj.contatado:
            return mark_safe('<span class="pilula ok">Já contatado</span>')
        return mark_safe('<span class="pilula novo">Novo</span>')

    @admin.display(description="")
    def botoes(self, obj):
        numero = "".join(c for c in obj.telefone if c.isdigit())
        if len(numero) <= 11:
            numero = "55" + numero
        texto = quote(f"Oi {obj.nome}, aqui é do CT Salvação! Recebemos seu pedido para treinar. Vamos combinar sua aula experimental?")
        marca = self._url("contatado", obj) if not obj.contatado else ""
        zap = format_html(
            '<a class="btn btn-zap" href="https://wa.me/{}?text={}" target="_blank" rel="noopener" data-chamar="{}">'
            '<svg viewBox="0 0 24 24"><path d="M21 12a8 8 0 01-11.7 7.1L4 20l1-4.6A8 8 0 1121 12z"/></svg>WhatsApp</a>',
            numero, texto, marca)
        itens = []
        if not obj.contatado:
            itens.append(self.item_post(obj, "contatado", "Marcar como contatado"))
        itens.append(self.item_link(obj, "delete", "Excluir", True))
        return self.acoes_html(zap, self.menu_pontos(*itens))


def brl(v):
    return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


@admin.register(Doacao)
class DoacaoAdmin(PainelAdmin):
    texto_novo = "Registrar doação"
    ajuda = "Anote aqui cada doação recebida (Pix, dinheiro ou outra). O painel soma o total do mês e do ano."
    list_display = ("data", "doador_exibido", "valor_fmt", "forma", "botoes")
    list_filter = ("forma", "data")
    search_fields = ("doador", "observacao")
    change_list_template = "admin/core/doacao/change_list.html"

    @admin.display(description="O que fazer")
    def botoes(self, obj):
        return self.acoes_html(self.botao_link(obj, "change", "Abrir"), self.botao_link(obj, "delete", "Excluir", "perigo"))

    @admin.display(description="Doador", ordering="doador")
    def doador_exibido(self, obj):
        return obj.doador or "Anônimo"

    @admin.display(description="Valor", ordering="valor")
    def valor_fmt(self, obj):
        return brl(obj.valor)

    def changelist_view(self, request, extra_context=None):
        def calcula():
            hoje = date.today()
            soma = lambda qs: qs.aggregate(t=Sum("valor"))["t"] or 0
            return {
                "mes": brl(soma(Doacao.objects.filter(data__year=hoje.year, data__month=hoje.month))),
                "ano": brl(soma(Doacao.objects.filter(data__year=hoje.year))),
                "qtd": Doacao.objects.filter(data__year=hoje.year).count(),
            }
        extra_context = extra_context or {}
        extra_context["resumo"] = cache.get_or_set("resumo_doacoes", calcula, 300)
        return super().changelist_view(request, extra_context)


class AssinaturaForm(forms.ModelForm):
    arquivo = forms.FileField(label="Enviar foto da assinatura", required=False,
                              help_text="Foto ou imagem da assinatura em papel branco. O fundo é removido sozinho.")
    desenho = forms.CharField(widget=forms.HiddenInput, required=False)

    class Meta:
        model = Assinatura
        fields = ("nome", "titulo")


@admin.register(Assinatura)
class AssinaturaAdmin(PainelAdmin):
    form = AssinaturaForm
    change_form_template = "admin/core/assinatura/change_form.html"

    def has_add_permission(self, request):
        # guardado em cache: o menu pergunta isso em toda página
        return not cache.get_or_set("tem_assinatura_registro", Assinatura.objects.exists, 300)

    def save_model(self, request, obj, form, change):
        from PIL import Image

        desenho = form.cleaned_data.get("desenho")
        arquivo = form.cleaned_data.get("arquivo")
        if desenho and desenho.startswith("data:image/png;base64,"):
            obj.imagem = desenho
        elif arquivo:
            im = Image.open(arquivo).convert("L")
            im.thumbnail((900, 360))
            alfa = im.point(lambda v: max(0, min(255, int((235 - v) * 3.2))))
            saida = Image.new("RGBA", im.size, (20, 20, 30, 0))
            saida.putalpha(alfa)
            b = io.BytesIO()
            saida.save(b, "PNG")
            obj.imagem = "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()
        super().save_model(request, obj, form, change)

    def changelist_view(self, request, extra_context=None):
        obj = Assinatura.objects.first()
        if obj:
            return redirect(reverse("admin:core_assinatura_change", args=[obj.pk]))
        return redirect(reverse("admin:core_assinatura_add"))


def _com_zap(i):
    numero = "".join(c for c in i.telefone if c.isdigit())
    if len(numero) <= 11:
        numero = "55" + numero
    i.wa = f"https://wa.me/{numero}?text=" + quote(f"Oi {i.nome}, aqui é do CT Salvação! Recebemos seu pedido para treinar. Vamos combinar sua aula experimental?")
    return i


MESES_CURTOS = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
DIAS_CURTOS = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]


def _dados_painel():
    hoje = date.today()
    # doações dos últimos 6 meses
    meses = []
    ano, mes = hoje.year, hoje.month
    for _ in range(6):
        meses.append((ano, mes))
        mes -= 1
        if mes == 0:
            ano, mes = ano - 1, 12
    meses.reverse()
    inicio = date(meses[0][0], meses[0][1], 1)
    somas = {(r["m"].year, r["m"].month): r["t"] for r in
             Doacao.objects.filter(data__gte=inicio).annotate(m=TruncMonth("data")).values("m").annotate(t=Sum("valor"))}
    maior = max([float(v) for v in somas.values()] + [1])
    barras_doacao = [{"rotulo": MESES_CURTOS[m - 1], "valor": float(somas.get((a, m), 0)),
                      "pct": max(4, round(float(somas.get((a, m), 0)) / maior * 100)) if somas.get((a, m)) else 4,
                      "atual": (a, m) == (hoje.year, hoje.month)} for a, m in meses]
    doado_mes = somas.get((hoje.year, hoje.month), 0)
    anterior = somas.get(meses[-2], 0)
    # presenças dos últimos 7 dias
    dias = [hoje - timedelta(days=n) for n in range(6, -1, -1)]
    cont = {r["data"]: r["n"] for r in Presenca.objects.filter(data__gte=dias[0]).values("data").annotate(n=Count("id"))}
    maior_p = max(list(cont.values()) + [1])
    barras_presenca = [{"rotulo": DIAS_CURTOS[d.weekday()], "valor": cont.get(d, 0),
                        "pct": max(4, round(cont.get(d, 0) / maior_p * 100)) if cont.get(d) else 4, "atual": d == hoje} for d in dias]
    novos_lista = [_com_zap(i) for i in Interessado.objects.filter(contatado=False)[:5]]
    # movimentações recentes
    eventos = []
    for d in Doacao.objects.all()[:4]:
        eventos.append({"tipo": "doacao", "titulo": f"Doação de {brl(d.valor)}", "detalhe": d.doador or "Anônimo", "quando": d.data})
    for i in Interessado.objects.all()[:4]:
        eventos.append({"tipo": "interessado", "titulo": f"{i.nome} quer treinar", "detalhe": "Chegou pelo site", "quando": i.criado_em.date()})
    for g in Graduacao.objects.select_related("aluno")[:4]:
        eventos.append({"tipo": "faixa", "titulo": f"{g.aluno.nome} trocou de faixa", "detalhe": f"Faixa {g.get_faixa_display().split(' (')[0].lower()}, {g.grau}º grau", "quando": g.data})
    eventos.sort(key=lambda e: e["quando"], reverse=True)
    return {
        "stats": {
            "ativos": Aluno.objects.filter(status=Aluno.Status.ATIVA).count(),
            "novos": Interessado.objects.filter(contatado=False).count(),
            "doado_mes": brl(doado_mes),
            "doacoes_qtd": Doacao.objects.filter(data__year=hoje.year, data__month=hoje.month).count(),
            "variacao": (round((float(doado_mes) - float(anterior)) / float(anterior) * 100) if anterior else None),
            "presentes_hoje": cont.get(hoje, 0),
        },
        "barras_doacao": barras_doacao,
        "barras_presenca": barras_presenca,
        "interessados": novos_lista,
        "aniversariantes": list(Aluno.objects.filter(status=Aluno.Status.ATIVA, nascimento__month=hoje.month).order_by("nascimento__day")[:5]),
        "eventos": eventos[:6],
    }


def painel_index(request, extra_context=None):
    """Tela inicial do painel (números guardados por 2 minutos; qualquer alteração limpa o cache)."""
    dados = cache.get("painel_dados")
    if dados is None:
        dados = _dados_painel()
        cache.set("painel_dados", dados, 120)
    ctx = {**dados, "hoje": date.today()}
    ctx.update(extra_context or {})
    return _index_original(request, ctx)


_index_original = admin.site.index
admin.site.index = painel_index


admin.site.unregister(Group)
admin.site.unregister(User)


@admin.register(User)
class UsuarioAdmin(PainelAdmin, UserAdmin):
    texto_novo = "Adicionar usuário"
    list_display = ("username", "first_name", "ativo", "botoes")
    list_filter = ()
    search_fields = ("username", "first_name", "email")
    ajuda = ("Pessoas que podem entrar no painel. Para trocar a sua própria senha vá em Configurações. "
             "Para dar acesso a outra pessoa clique em Adicionar usuário.")
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Dados da pessoa", {"fields": ("first_name", "last_name", "email")}),
        ("Acesso", {"fields": ("is_active", "is_staff", "is_superuser")}),
    )

    @admin.display(description="Conta ativa", boolean=True)
    def ativo(self, obj):
        return obj.is_active

    @admin.display(description="O que fazer")
    def botoes(self, obj):
        itens = [self.botao_link(obj, "change", "Abrir")]
        if not obj.is_superuser:
            itens.append(self.botao_link(obj, "delete", "Excluir", "perigo"))
        return self.acoes_html(*itens)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        rotulos = {"username": "Nome de usuário (para entrar)", "first_name": "Nome", "last_name": "Sobrenome",
                   "is_active": "Conta ativa (pode entrar)", "is_staff": "Pode usar o painel", "is_superuser": "Acesso total"}
        for nome, rotulo in rotulos.items():
            if nome in form.base_fields:
                form.base_fields[nome].label = rotulo
        return form


def configuracoes(request):
    return render(request, "admin/configuracoes.html", {**admin.site.each_context(request), "title": "Configurações"})


_urls_originais = admin.site.get_urls


def _urls_com_configuracoes():
    return [path("configuracoes/", admin.site.admin_view(configuracoes), name="configuracoes")] + _urls_originais()


admin.site.get_urls = _urls_com_configuracoes
