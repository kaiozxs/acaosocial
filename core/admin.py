from datetime import date, timedelta
from urllib.parse import quote

import base64
import io

from django.contrib import admin, messages
from django import forms
from django.db.models import Sum
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


class GraduacaoInline(admin.TabularInline):
    model = Graduacao
    extra = 0


@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    list_display = ("nome", "faixa_visual", "idade", "categoria", "turma", "status", "treinos_30d", "inicio", "link_certificado")
    list_filter = ("status", "faixa", "turma")
    search_fields = ("nome", "telefone", "responsavel")
    date_hierarchy = "inicio"
    inlines = [GraduacaoInline]
    actions = ["dar_grau", "ativar", "trancar"]
    change_list_template = "admin/core/aluno/change_list.html"

    def get_urls(self):
        return [path("certificado/", self.admin_site.admin_view(self.certificado), name="core_aluno_certificado")] + super().get_urls()

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

    @admin.display(description="Certificado")
    def link_certificado(self, obj):
        return format_html('<a class="btn-zap" style="background:#555" href="{}?aluno={}">Gerar</a>',
                           reverse("admin:core_aluno_certificado"), obj.pk)

    @admin.display(description="Treinos (30d)")
    def treinos_30d(self, obj):
        return obj.presencas.filter(data__gte=date.today() - timedelta(days=30)).count()

    @admin.action(description="Dar +1 grau (listra)")
    def dar_grau(self, request, queryset):
        n = 0
        for a in queryset:
            if a.grau < 4:
                Graduacao.objects.create(aluno=a, faixa=a.faixa, grau=a.grau + 1, observacao="Grau pelo painel")
                n += 1
        self.message_user(request, f"{n} aluno(s) ganharam grau.", messages.SUCCESS)

    @admin.action(description="Marcar matrícula como ativa")
    def ativar(self, request, queryset):
        queryset.update(status=Aluno.Status.ATIVA)

    @admin.action(description="Trancar matrícula")
    def trancar(self, request, queryset):
        queryset.update(status=Aluno.Status.TRANCADA)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["resumo"] = {
            "total": Aluno.objects.count(),
            "ativos": Aluno.objects.filter(status=Aluno.Status.ATIVA).count(),
            "interessados": Interessado.objects.filter(contatado=False).count(),
        }
        return super().changelist_view(request, extra_context)


@admin.register(Graduacao)
class GraduacaoAdmin(admin.ModelAdmin):
    list_display = ("aluno", "faixa", "grau", "data")
    list_filter = ("faixa",)
    search_fields = ("aluno__nome",)
    autocomplete_fields = ("aluno",)


@admin.register(Presenca)
class PresencaAdmin(admin.ModelAdmin):
    list_display = ("aluno", "data")
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
class TurmaAdmin(admin.ModelAdmin):
    list_display = ("nome", "publico", "dias", "horario", "ordem")


@admin.register(Interessado)
class InteressadoAdmin(admin.ModelAdmin):
    list_display = ("nome", "telefone", "idade", "chamar", "contatado", "criado_em")
    list_filter = ("contatado",)
    search_fields = ("nome", "telefone")
    list_editable = ("contatado",)
    actions = ["marcar_contatado"]

    @admin.display(description="WhatsApp")
    def chamar(self, obj):
        numero = "".join(c for c in obj.telefone if c.isdigit())
        if len(numero) <= 11:
            numero = "55" + numero
        texto = quote(f"Oi {obj.nome}, aqui é do CT Salvação! Recebemos seu pedido para treinar. Vamos combinar sua aula experimental?")
        return format_html(
            '<a class="btn-zap" href="https://wa.me/{}?text={}" target="_blank" rel="noopener">Chamar</a>', numero, texto)

    @admin.action(description="Marcar como já contatado")
    def marcar_contatado(self, request, queryset):
        queryset.update(contatado=True)


def brl(v):
    return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


@admin.register(Doacao)
class DoacaoAdmin(admin.ModelAdmin):
    list_display = ("data", "doador_exibido", "valor_fmt", "forma", "observacao")
    list_filter = ("forma", "data")
    search_fields = ("doador", "observacao")
    date_hierarchy = "data"
    change_list_template = "admin/core/doacao/change_list.html"

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
class AssinaturaAdmin(admin.ModelAdmin):
    form = AssinaturaForm
    change_form_template = "admin/core/assinatura/change_form.html"

    def has_add_permission(self, request):
        return not Assinatura.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

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


def painel_index(request, extra_context=None):
    """Tela inicial do painel: números do dia, atalhos e interessados para chamar."""
    hoje = date.today()
    mes = Doacao.objects.filter(data__year=hoje.year, data__month=hoje.month).aggregate(t=Sum("valor"))["t"] or 0
    ctx = {
        "stats": {
            "ativos": Aluno.objects.filter(status=Aluno.Status.ATIVA).count(),
            "novos": Interessado.objects.filter(contatado=False).count(),
            "doacoes_mes": brl(mes),
            "presentes_hoje": Presenca.objects.filter(data=hoje).count(),
        },
        "interessados": [_com_zap(i) for i in Interessado.objects.filter(contatado=False)[:5]],
        "aniversariantes": Aluno.objects.filter(status=Aluno.Status.ATIVA, nascimento__month=hoje.month).order_by("nascimento__day")[:6],
        "hoje": hoje,
    }
    ctx.update(extra_context or {})
    return _index_original(request, ctx)


_index_original = admin.site.index
admin.site.index = painel_index
