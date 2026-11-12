# Projeto Salvação — site e painel de gestão

Site público e painel de gestão para o **CT Salvação / Projeto Salvação**: aulas de jiu-jitsu e muay thai para adultos, jovens e crianças, num projeto social sem fins lucrativos que funciona no bairro Coelho. Responsável: professor **Melino José** (faixa preta 1º grau de jiu-jitsu).

O sistema troca o caderno e as anotações soltas por um painel simples de usar **no celular**: cadastro de alunos, chamada, doações, certificados e contato com quem quer treinar.

- **Repositório:** https://github.com/kaiozxs/acaosocial
- **Site publicado:** https://ctsalvacao.vercel.app (painel em https://ctsalvacao.vercel.app/admin)

## O que o sistema faz

**Site público** (`/`)
- História do projeto, galeria de fotos, horários das turmas, professor.
- Doação por **Pix** (chave, "copia e cola" e QR code).
- Formulário **"Quero treinar"** com aviso na tela ao enviar.
- Contatos: WhatsApp e Instagram do CT e do projeto.

**Painel do professor** (`/admin`)
- **Início:** doações do mês com gráfico, alunos ativos, presentes hoje, quem quer treinar, aniversariantes e últimas novidades.
- **Chamada** por turma, com alunos já marcados como presentes, troca de dia e **frequência do mês** de cada aluno.
- **Alunos:** cadastro, edição em janelinha, busca por nome/telefone e filtros por situação, faixa e turma.
- **Faixas do jiu-jitsu:** branca; infantis cinza, amarela, laranja e verde (cada uma com listra branca, lisa e com listra preta); adultas azul, roxa, marrom e preta; graus de 0 a 4.
- **Trocas de faixa:** histórico, e o cadastro do aluno é atualizado sozinho.
- **Interessados:** botão de WhatsApp com mensagem pronta; marca como contatado ao chamar.
- **Certificados:** escolhe o aluno e gera o PDF com a faixa desenhada e a assinatura do professor (desenhada na tela ou enviada por foto).
- **Doações:** registro com totais do mês e do ano.
- **Turmas, usuários e configurações**, com confirmação antes de excluir.
- Tema escuro e claro, menu inferior e listas em cartões no celular.

## Tecnologias
Python 3.14 · Django 6 · PostgreSQL (Supabase) · Vercel · WhiteNoise · ReportLab e Pillow (PDF) · HTML, CSS e JavaScript puros.
Detalhes e decisões: [docs/arquitetura.md](docs/arquitetura.md).

## Como usar
- **Professor e equipe:** [docs/manual-do-professor.md](docs/manual-do-professor.md)
- **Publicar e configurar (Vercel + Supabase):** [docs/deploy.md](docs/deploy.md)

Rodar no computador:
```bash
python -m venv .venv
.venv\Scripts\activate           # Windows
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py seed            # opcional: turmas e alunos de exemplo
python manage.py runserver
```
Site: http://localhost:8000 · Painel: http://localhost:8000/admin

## Estrutura de pastas
```
config/        configurações do Django (banco, segurança, URLs)
core/          modelos, painel, site e certificado
templates/     páginas do site e do painel
static/        CSS, JavaScript, imagens e fontes
api/           ponto de entrada da Vercel
banco/         esquema SQL, diagrama e dicionário de dados
evidencias/    prints do sistema (computador e celular) e certificados de exemplo
docs/          arquitetura, manual, deploy, métricas e apresentação
```

## Banco de dados
Esquema em [banco/schema.sql](banco/schema.sql), diagrama em [banco/diagrama.md](banco/diagrama.md) e dicionário de dados em [banco/dicionario.md](banco/dicionario.md). Tabelas protegidas com RLS no Supabase (`python manage.py protege_banco`).

## Indicadores e métricas
Detalhes e como foram medidos em [docs/metricas.md](docs/metricas.md).
- **Usuários registrados:** o painel mostra, em tempo real, alunos cadastrados, matrículas ativas e usuários do painel.
- **Tempo médio de busca:** **~120 ms** buscando por nome numa base de 2.000 alunos (32 ms por telefone), medido no servidor.
- **Impacto esperado:** reduzir em **80%** os erros no controle de matrículas e doações, com presença única por aluno e dia, bloqueio de registros repetidos, faixa e grau validados, totais automáticos e confirmação antes de excluir. A medição da meta está descrita em `docs/metricas.md`.

## Evidências
Prints em [evidencias/](evidencias/): site no computador e no celular, todas as telas do painel e certificados de exemplo.

## Contato
- Localização: bairro Coelho
- Instagram do CT: https://www.instagram.com/ct.salvacao.sg/
- Instagram do Projeto: https://www.instagram.com/projetosalvacaosg/
- WhatsApp: +55 21 99841-2052
