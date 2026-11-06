"""Liga a proteção por linha (RLS) em todas as tabelas do Supabase.

As tabelas criadas pelo Django nascem abertas para a API pública do Supabase (a chave 'publishable'
fica visível no navegador). Com a proteção ligada e sem políticas, só o Django (usuário 'postgres',
que ignora a proteção) consegue ler e gravar. Rode de novo depois de criar tabelas novas (migrate).
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Liga o RLS em todas as tabelas do schema public (somente PostgreSQL/Supabase)."

    def handle(self, *args, **opcoes):
        if connection.vendor != "postgresql":
            self.stdout.write("Banco local (SQLite): nada a fazer.")
            return
        with connection.cursor() as c:
            c.execute("select tablename from pg_tables where schemaname = 'public' and not rowsecurity order by 1")
            tabelas = [t for (t,) in c.fetchall()]
            for t in tabelas:
                c.execute(f'alter table public."{t}" enable row level security')
                self.stdout.write(f"RLS ligado: {t}")
        self.stdout.write(self.style.SUCCESS(f"Pronto. {len(tabelas)} tabela(s) protegida(s)."))
