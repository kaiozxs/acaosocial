"""Cria (ou atualiza) o usuário mestre e, se pedido, apaga todos os outros logins.

Exemplo:  python manage.py mestre --senha NOVA --apagar-outros
O nome do usuário mestre vem de settings.USUARIO_MESTRE (padrão: Melino).
"""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Cria ou atualiza o usuário mestre (acesso total, não pode ser apagado)."

    def add_arguments(self, parser):
        parser.add_argument("--senha", required=True, help="Senha do usuário mestre")
        parser.add_argument("--apagar-outros", action="store_true", help="Apaga todos os outros usuários (reseta os logins)")

    def handle(self, *args, **o):
        U = get_user_model()
        nome = settings.USUARIO_MESTRE
        if o["apagar_outros"]:
            n, _ = U.objects.exclude(username__iexact=nome).delete()
            self.stdout.write(f"Outros usuários apagados: {n}")
        mestre = U.objects.filter(username__iexact=nome).first() or U(username=nome)
        mestre.username = nome
        mestre.is_staff = mestre.is_superuser = mestre.is_active = True
        mestre.set_password(o["senha"])
        mestre.save()
        self.stdout.write(self.style.SUCCESS(f"Usuário mestre pronto: {nome}"))
