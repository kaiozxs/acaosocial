from datetime import date, timedelta

from django.contrib import admin, messages
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import Aluno, Graduacao, Interessado, Presenca, Turma

COR_FAIXA = {
    "branca": "#f2f2f2", "cinza": "#9a9a9a", "amarela": "#f4c20d", "laranja": "#f08a24",
    "verde": "#2e9e4f", "azul": "#2457d6", "roxa": "#7a3bc2", "marrom": "#6b3f1d", "preta": "#111",
}


class GraduacaoInline(admin.TabularInline):
    model = Graduacao
    extra = 0


@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    list_display = ("nome", "faixa_visual", "idade", "categoria", "turma", "status", "treinos_30d", "inicio")
    list_filter = ("status", "faixa", "turma")
    search_fields = ("nome", "telefone", "responsavel")
    date_hierarchy = "inicio"
    inlines = [GraduacaoInline]
    actions = ["dar_grau", "ativar", "trancar"]
    change_list_template = "admin/core/aluno/change_list.html"

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
    list_filter = ("data",)
    autocomplete_fields = ("aluno",)


@admin.register(Turma)
class TurmaAdmin(admin.ModelAdmin):
    list_display = ("nome", "publico", "dias", "horario", "ordem")


@admin.register(Interessado)
class InteressadoAdmin(admin.ModelAdmin):
    list_display = ("nome", "telefone", "idade", "contatado", "criado_em")
    list_filter = ("contatado",)
    search_fields = ("nome", "telefone")
    list_editable = ("contatado",)
