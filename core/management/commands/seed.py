import random
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from core.models import Aluno, Graduacao, Presenca, Turma


class Command(BaseCommand):
    help = "Cria turmas, um superusuário de desenvolvimento e alunos de exemplo."

    def handle(self, *args, **opts):
        User = get_user_model()
        if not User.objects.filter(username="professor").exists():
            User.objects.create_superuser("professor", "", "salvacao123")
            self.stdout.write("Superusuário dev: professor / salvacao123 (troque em produção!)")

        turmas = [
            Turma.objects.get_or_create(nome="Adultos", defaults=dict(publico="Adultos", dias="Seg / Qua / Sex", horario="19h às 20h30", ordem=1))[0],
            Turma.objects.get_or_create(nome="Jovens", defaults=dict(publico="Jovens", dias="Ter / Qui", horario="18h às 19h", ordem=2))[0],
            Turma.objects.get_or_create(nome="Adolescentes", defaults=dict(publico="Adolescentes", dias="Ter / Qui", horario="17h às 18h", ordem=3))[0],
        ]

        if Aluno.objects.exists():
            return
        random.seed(7)
        nomes = ["Lucas Andrade", "Rafael Souza", "Mariana Lima", "Pedro Henrique", "Camila Torres", "João Victor",
                 "Gabriel Rocha", "Beatriz Alves", "Thiago Martins", "Larissa Costa", "Diego Ferreira", "Ana Clara"]
        faixas = ["branca", "branca", "branca", "azul", "azul", "roxa", "marrom"]
        for i, nome in enumerate(nomes):
            idade = random.choice([13, 15, 16, 19, 22, 27, 31, 38])
            a = Aluno.objects.create(
                nome=nome,
                nascimento=date.today() - timedelta(days=idade * 365 + random.randint(0, 300)),
                telefone=f"(11) 9{random.randint(1000, 9999)}-{random.randint(1000, 9999)}",
                responsavel="Responsável" if idade < 18 else "",
                turma=turmas[0] if idade >= 18 else turmas[1 if idade < 15 else 2],
                inicio=date.today() - timedelta(days=random.randint(30, 900)),
                status="trancada" if i == 5 else "ativa",
            )
            faixa = random.choice(faixas)
            Graduacao.objects.create(aluno=a, faixa=faixa, grau=random.randint(0, 3),
                                     data=date.today() - timedelta(days=random.randint(20, 300)))
            for d in random.sample(range(0, 30), random.randint(2, 12)):
                Presenca.objects.get_or_create(aluno=a, data=date.today() - timedelta(days=d))
        self.stdout.write("Alunos de exemplo criados.")
