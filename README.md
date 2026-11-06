# Projeto Salvação — Sistema de matrículas e site

Site público + painel administrativo para o **Projeto Salvação** (aulas de jiu-jitsu e muay thai para adultos, jovens e adolescentes; o projeto é sem fins lucrativos e funciona dentro do CT Salvação).
Responsável: professor **Melino José** (faixa preta 1º grau de jiu-jitsu, faixa marrom de luta livre).

## O que o sistema faz
- **Site público** (`/`): projeto, turmas e horários, professor, doação via Pix e formulário "quero treinar".
- **Painel do professor** (`/admin`): cadastro de alunos, matrícula (ativa/trancada/cancelada), faixa e grau, histórico de graduações, presenças, interessados vindos do site. Ação em lote "+1 grau".
- Busca por nome/telefone e filtros por status, faixa e turma.
- Faixas do jiu-jitsu: branca; infantis cinza, amarela, laranja e verde (cada uma com listra branca, lisa e com listra preta); e adultas azul, roxa, marrom e preta, com 0 a 4 graus.

## Contato
- Localização: bairro Coelho
- Instagram do CT: https://www.instagram.com/ct.salvacao.sg/
- Instagram do Projeto: https://www.instagram.com/projetosalvacaosg/
- WhatsApp/telefone: +55 21 99841-2052

## Tecnologias
- Python 3.14 + Django 6
- Banco: PostgreSQL no **Supabase** (via `DATABASE_URL`); SQLite local para desenvolvimento
- Bibliotecas: `psycopg`, `dj-database-url`, `whitenoise`, `python-dotenv`, `pillow`, `gunicorn`
- Deploy: Vercel

## Rodando localmente
```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py seed          # turmas, alunos de exemplo e usuário de desenvolvimento
python manage.py runserver
```
Abra http://localhost:8000 e http://localhost:8000/admin (usuário/senha de dev impressos pelo `seed`).
Em produção crie o usuário com `python manage.py createsuperuser`.

## Supabase
1. Crie o projeto em supabase.com → *Project Settings → Database → Connection string* (Session pooler).
2. Coloque em `.env` como `DATABASE_URL=postgresql://...`.
3. `python manage.py migrate` cria as tabelas no Supabase.

## Deploy (Vercel)
Importe o repositório na Vercel e defina as variáveis `SECRET_KEY`, `DEBUG=0`, `DATABASE_URL`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `PIX_CHAVE`. O `vercel.json` e `api/index.py` já apontam para o Django.
Fotos de alunos enviadas pelo painel precisam de armazenamento externo em produção (ex.: Supabase Storage).

## Estrutura
```
config/       configurações Django
core/         modelos, views e admin
templates/    HTML do site e do painel
static/       CSS e imagens (logo.png, icon.svg e professor.jpg em static/img/)
banco/        scripts/diagramas do banco
evidencias/   prints e evidências da entrega
docs/         documentação
```

## Indicadores e métricas
- Impacto: reduzir erros no controle de matrículas e doações (meta: 80%).
- Métricas: nº de usuários cadastrados (painel mostra o total) e tempo médio de busca no sistema.

## Link do repositório
https://github.com/kaiozxs/acaosocial
