from datetime import date, timedelta
from urllib.parse import quote

import base64
import io

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group, User
from django.core.cache import cache
from django import forms
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import Faixa, Aluno, Assinatura, Doacao, Graduacao, Interessado, Presenca, Turma

COR_FAIXA = {
    "branca": "#f2f2f2", "cinza": "#9a9a9a", "amarela": "#f4c20d", "laranja": "#f08a24",
    "verde": "#2e9e4f", "azul": "#2457d6", "roxa": "#7a3bc2", "marrom": "#6b3f1d", "preta": "#111",
}


class PainelAdmin(admin.ModelAdmin):
    """Base do painel: sem menu 'Ação', com botões simples em cada linha."""

    actions = None
    date_hierarchy = None
    show_full_result_count = False
    ajuda = ""

    def changelist_view(self, request, extra_context=None):
        extra_context = dict(extra_context or {})
        extra_context.setdefault("ajuda", self.ajuda)
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

    def rota_post(self, nome, funcao, mensagem):
        """Cria uma rota <pk>/<nome>/ que executa `funcao(obj)` e volta para a lista."""
        o = self.model._meta

        def view(request, pk):
            obj = self.get_object(request, str(pk))
            if request.method == "POST" and obj is not None and self.has_change_permission(request, obj):
                funcao(obj)
                self.message_user(request, mensagem.format(obj=obj), messages.SUCCESS)
            return redirect(request.META.get("HTTP_REFERER") or reverse(f"admin:{o.app_label}_{o.model_name}_changelist"))

        return path(f"<int:pk>/{nome}/", self.admin_site.admin_view(view), name=f"{o.app_label}_{o.model_name}_{nome}")


class GraduacaoInline(admin.TabularInline):
    model = Graduacao
    extra = 0


@admin.register(Aluno)
class AlunoAdmin(PainelAdmin):
    list_display = ("nome", "faixa_visual", "idade", "turma", "status", "botoes")
    list_filter = ("status", "faixa", "turma")
    search_fields = ("nome", "telefone", "responsavel")
    inlines = [GraduacaoInline]
    list_select_related = ("turma",)
    ajuda = "Aqui ficam todos os alunos. Clique em Abrir para ver ou mudar os dados. Use +1 grau quando o aluno ganhar uma listra e Certificado para imprimir o certificado."
    change_list_template = "admin/core/aluno/change_list.html"

    def get_urls(self):
        return [
            path("certificado/", self.admin_site.admin_view(self.certificado), name="core_aluno_certificado"),
            self.rota_post("grau", self._mais_um_grau, "{obj} ganhou mais um grau."),
        ] + super().get_urls()

    @staticmethod
    def _mais_um_grau(a):
        if a.grau < 4:
            Graduacao.objects.create(aluno=a, faixa=a.faixa, grau=a.grau + 1, observacao="Grau pelo painel")

    def certificado(self, request):
        """Formulário para gerar o certificado em PDF (nome, faixa, grau e data)."""
        from . import certificado as cert

        faixas = Faixa.choices
        aluno = None
        pk = request.GET.get("aluno") or request.POST.get("aluno")
        if pk and str(pk).isdigit():
            aluno = Aluno.objects.filter(pk=int(pk)).first()
        if request.method == "POST":
            nome = request.POST.get("nome", "").strip() or (aluno.nome if aluno else "")
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
            self.message_user(request, "Informe o nome do aluno.", messages.ERROR)
        ctx = {**self.admin_site.each_context(request), "title": "Gerar certificado", "faixas": faixas,
               "aluno": aluno, "alunos": Aluno.objects.all(), "hoje": date.today().isoformat(),
               "tem_assinatura": bool(Assinatura.objects.exclude(imagem="").exists()), "opts": self.model._meta}
        return render(request, "admin/core/aluno/certificado.html", ctx)

    @admin.display(description="Faixa")
    def faixa_visual(self, obj):
        riscas = mark_safe('<i style="display:inline-block;width:3px;height:12px;background:#fff;margin-left:3px"></i>' * obj.grau)
        return format_html(
            '<span style="display:inline-flex;align-items:center;gap:8px">'
            '<span style="display:inline-flex;align-items:center;justify-content:flex-end;width:74px;height:14px;'
            'background:{};border:1px solid #666;padding-right:6px">'
            '<span style="background:#111;display:inline-flex;height:100%;padding:0 2px;align-items:center">{}</span></span>{}</span>',
            COR_FAIXA.get(obj.faixa, "#444"), riscas, obj.get_faixa_display(),
        )

    @admin.display(description="O que fazer")
    def botoes(self, obj):
        itens = [self.botao_link(obj, "change", "Abrir")]
        if obj.grau < 4:
            itens.append(self.botao_post(obj, "grau", "+1 grau"))
        itens.append(format_html('<a class="btn" href="{}?aluno={}">Certificado</a>', reverse("admin:core_aluno_certificado"), obj.pk))
        return self.acoes_html(*itens)

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
    list_display = ("aluno", "data")
    list_select_related = ("aluno",)
    ajuda = "Lista de quem veio em cada dia. Para marcar a presença de hoje use o botão Chamada rápida."
    list_filter = ("data", "aluno__turma")
    autocomplete_fields = ("aluno",)
    change_list_template = "admin/core/presenca/change_list.html"

    def get_urls(self):
        return [path("chamada/", self.admin_site.admin_view(self.chamada), name="core_presenca_chamada")] + super().get_urls()

    def chamada(self, request):
        """Chamada rápida: marca a presença de vários alunos de uma turma de uma vez."""
        turmas = Turma.objects.all()
        turma_id = request.POST.get("turma") or request.GET.get("turma") or ""
        try:
            dia = date.fromisoformat(request.POST.get("data") or request.GET.get("data") or "")
        except ValueError:
            dia = date.today()
        alunos = Aluno.objects.filter(status=Aluno.Status.ATIVA)
        if turma_id.isdigit():
            alunos = alunos.filter(turma_id=int(turma_id))
        if request.method == "POST" and request.POST.get("salvar"):
            marcados = {int(x) for x in request.POST.getlist("aluno") if x.isdigit()}
            ids = set(alunos.values_list("pk", flat=True))
            Presenca.objects.filter(data=dia, aluno_id__in=ids - marcados).delete()
            for pk in marcados & ids:
                Presenca.objects.get_or_create(aluno_id=pk, data=dia)
            self.message_user(request, f"Chamada de {dia:%d/%m/%Y} salva: {len(marcados & ids)} presente(s).", messages.SUCCESS)
            return redirect(f"{reverse('admin:core_presenca_chamada')}?turma={turma_id}&data={dia.isoformat()}")
        presentes = set(Presenca.objects.filter(data=dia).values_list("aluno_id", flat=True))
        ctx = {**self.admin_site.each_context(request), "title": "Chamada rápida", "turmas": turmas,
               "turma_id": turma_id, "dia": dia.isoformat(), "alunos": alunos, "presentes": presentes,
               "opts": self.model._meta}
        return render(request, "admin/core/presenca/chamada.html", ctx)


@admin.register(Turma)
class TurmaAdmin(PainelAdmin):
    list_display = ("nome", "modalidade", "publico", "dias", "horario", "botoes")
    fields = ("nome", "modalidade", "publico", "dias", "horario")
    ajuda = ("Turma é um grupo de treino com dia e horário fixos, por exemplo: Jiu-jitsu adulto, seg, qua e sex, 19h às 20h30. "
             "As turmas aparecem no site em Horários de treino e são usadas na chamada. Cadastre uma turma para cada horário.")

    @admin.display(description="O que fazer")
    def botoes(self, obj):
        return self.acoes_html(self.botao_link(obj, "change", "Abrir"), self.botao_link(obj, "delete", "Excluir", "perigo"))


@admin.register(Interessado)
class InteressadoAdmin(PainelAdmin):
    ajuda = "Pessoas que preencheram a ficha Quero treinar no site. Chame no WhatsApp e depois toque em Já falei com a pessoa."
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

    @admin.display(description="O que fazer")
    def botoes(self, obj):
        numero = "".join(c for c in obj.telefone if c.isdigit())
        if len(numero) <= 11:
            numero = "55" + numero
        texto = quote(f"Oi {obj.nome}, aqui é do CT Salvação! Recebemos seu pedido para treinar. Vamos combinar sua aula experimental?")
        itens = [format_html('<a class="btn btn-zap" href="https://wa.me/{}?text={}" target="_blank" rel="noopener">Chamar no WhatsApp</a>', numero, texto)]
        if not obj.contatado:
            itens.append(self.botao_post(obj, "contatado", "Já falei com a pessoa", "ok"))
        itens.append(self.botao_link(obj, "delete", "Excluir", "perigo"))
        return self.acoes_html(*itens)


def brl(v):
    return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


@admin.register(Doacao)
class DoacaoAdmin(PainelAdmin):
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
        hoje = date.today()
        soma = lambda qs: qs.aggregate(t=Sum("valor"))["t"] or 0
        extra_context = extra_context or {}
        extra_context["resumo"] = {
            "mes": brl(soma(Doacao.objects.filter(data__year=hoje.year, data__month=hoje.month))),
            "ano": brl(soma(Doacao.objects.filter(data__year=hoje.year))),
            "qtd": Doacao.objects.filter(data__year=hoje.year).count(),
        }
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
        return not Assinatura.objects.exists()

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
