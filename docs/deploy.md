# Publicação (deploy) e configuração

## 1. Banco de dados (Supabase)
1. Crie o projeto no Supabase e copie a **Session pooler** em *Connect*:
   `postgresql://postgres.<ref-do-projeto>:<SENHA>@<host-do-pooler>:5432/postgres`
   > Use o pooler. O endereço direto (`db.<ref>.supabase.co`) só funciona com IPv6 e falha na Vercel e em muitas redes.
2. Crie as tabelas: `python manage.py migrate`
3. **Proteja as tabelas:** `python manage.py protege_banco`
   As tabelas criadas pelo Django nascem abertas para a API pública do Supabase. Esse comando liga o RLS em todas. Rode de novo sempre que criar tabelas novas.
4. Crie o usuário do professor: `python manage.py createsuperuser`

## 2. Site (Vercel)
1. Em vercel.com, **Add New → Project** e importe o repositório do GitHub.
2. Deixe o framework que a Vercel detectar (Django). O `vercel.json` só fixa a região `sfo1` (perto do banco). **Não** coloque redirecionamentos (`rewrites`) para `/api/index`: o Django já recebe o caminho original, e com o redirecionamento todas as páginas dão 404.
3. Em **Settings → Environment Variables**, defina:

| Variável | Valor | Observação |
|---|---|---|
| `SECRET_KEY` | texto longo e aleatório | **obrigatório**. Gere com `python -c "import secrets; print(secrets.token_urlsafe(60))"` |
| `DEBUG` | `0` | já é o padrão na Vercel |
| `DATABASE_URL` | a string do pooler do passo 1 | |
| `ALLOWED_HOSTS` | `seu-projeto.vercel.app` | (ou `*`) |
| `CSRF_TRUSTED_ORIGINS` | `https://seu-projeto.vercel.app` | já aceita `https://*.vercel.app` por padrão |
| `PIX_CHAVE`, `PIX_COPIA_COLA`, `PIX_FAVORECIDO` | dados do Pix | opcionais: já vêm configurados |
| `WHATSAPP`, `WHATSAPP_EXIBIR`, `INSTAGRAM_URL`, `INSTAGRAM_CT_URL` | contatos | opcionais |

4. **Deploy.** A cada `git push` na branch `main` a Vercel publica de novo sozinha.

## 3. Depois de publicar
- Abra `/admin`, entre e **troque a senha** (Configurações → Trocar minha senha).
- Cadastre as **turmas** (aparecem no site em *Horários de treino*).
- Cadastre a **assinatura do professor** (Configurações → Assinatura do professor).
- Apague os dados de teste.

## Rodar no computador
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py seed            # opcional: turmas e alunos de exemplo
python manage.py runserver
```
Site: http://localhost:8000 · Painel: http://localhost:8000/admin

Sem `DATABASE_URL`, o sistema usa um SQLite local. Para testar com o banco real, coloque a `DATABASE_URL` no `.env` (o arquivo `.env` nunca vai para o GitHub).

## Cuidados
- Fotos de alunos: a Vercel não guarda arquivos enviados. O campo está desligado até haver armazenamento (Supabase Storage).
- Chaves e senhas nunca vão no código: ficam em variáveis de ambiente. Se alguma vazar, gere outra no Supabase.
