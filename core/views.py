from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .models import Aluno, Interessado, Turma


def home(request):
    turmas = Turma.objects.all()
    return render(request, "home.html", {
        "turmas": turmas,
        "n_turmas": turmas.count(),
        "n_ativos": Aluno.objects.filter(status=Aluno.Status.ATIVA).count(),
    })


@require_POST
def interesse(request):
    nome = request.POST.get("nome", "").strip()[:120]
    telefone = request.POST.get("telefone", "").strip()[:20]
    if nome and telefone:
        idade = request.POST.get("idade", "").strip()
        Interessado.objects.create(
            nome=nome,
            telefone=telefone,
            idade=int(idade) if idade.isdigit() else None,
            mensagem=request.POST.get("mensagem", "").strip()[:500],
        )
        messages.success(request, "Recebemos! O professor vai entrar em contato. OSS!")
    else:
        messages.error(request, "Preencha nome e telefone.")
    return redirect("/#treinar")
