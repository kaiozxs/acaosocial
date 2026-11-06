# Arquitetura e tecnologias

## Visão geral

```
   Visitante / aluno                    Professor (celular ou computador)
          │                                        │
          ▼                                        ▼
   Site público  (/)                      Painel  (/admin)
   Django · HTML · CSS · JS               Django Admin personalizado
          │                                        │
          └──────────────┬─────────────────────────┘
                         ▼
              Aplicação Django 6 (Python)
              hospedada na Vercel (função serverless)
                         │
                         ▼
              Banco PostgreSQL no Supabase
              (tabelas protegidas com RLS)
```

## Tecnologias

| Camada | Tecnologia | Para quê |
|---|---|---|
| Linguagem | Python 3.14 | Regras do sistema |
| Framework | Django 6 | Site, painel, formulários, login, banco |
| Banco | PostgreSQL (Supabase) | Alunos, turmas, presenças, doações… |
| Banco local | SQLite | Desenvolvimento sem internet |
| Hospedagem | Vercel (região sfo1, perto do banco) | Publica o site e o painel |
| Arquivos estáticos | WhiteNoise | Serve CSS, JS e imagens |
| PDF | ReportLab + Pillow | Certificado de graduação |
| Front-end | HTML, CSS e JavaScript sem bibliotecas | Site e painel (tema claro/escuro, caixinhas, chamada) |
| Fontes | Inter, Archivo, Cinzel, Playfair Display | Visual do painel, site e certificado |

## Pastas do projeto

```
config/        configurações do Django (banco, segurança, URLs)
core/          modelos, telas do site, painel e certificado
  admin.py       painel (listas, botões, chamada, certificados, tela inicial)
  models.py      tabelas e regras (faixas, graus, histórico)
  certificado.py desenho do certificado em PDF
  cinto.py       desenho da faixa (tecido, costura, listras)
  management/    comandos: seed (dados de exemplo) e protege_banco (RLS)
templates/     páginas do site e do painel
static/        CSS, JavaScript, imagens, fontes
api/           ponto de entrada da Vercel
banco/         esquema SQL, diagrama e dicionário de dados
evidencias/    prints do sistema funcionando
docs/          documentação
```

## Decisões principais

- **Painel em cima do Django Admin.** Já traz login, permissões e validação prontos. Foi redesenhado por inteiro (menu lateral, cartões, caixinhas, listas em cartões no celular) para ser simples de usar por quem não tem familiaridade com computador.
- **Celular em primeiro lugar.** O professor e a equipe vão usar principalmente no telefone. O menu vira barra inferior, as tabelas viram cartões e os botões têm tamanho de toque.
- **Velocidade com o banco longe.** O banco fica nos EUA, então cada consulta custa cerca de 0,2 s. Por isso o painel guarda em cache o usuário logado, as contagens e os números da tela inicial por alguns minutos, e o cache é limpo sempre que algo muda. A sessão fica em cookie assinado (sem consulta ao banco).
- **Sem arquivos enviados na Vercel.** A Vercel não guarda arquivos, então a foto do aluno ficou desligada. O certificado e os gráficos são gerados na hora, sem gravar nada em disco. A assinatura do professor fica no banco, como texto (PNG em base64).
- **Segurança.**
  - Login obrigatório no painel; sessões em cookie assinado, só por HTTPS em produção.
  - Tabelas do Supabase com proteção RLS ligada e sem políticas: a API pública do Supabase não consegue ler nem gravar; só o Django.
  - Modo de depuração desligado por padrão na Vercel; chave secreta e senha do banco em variáveis de ambiente.
  - Confirmação antes de excluir; registros idênticos enviados duas vezes são ignorados.
