# Métricas e impacto

## 1. Número de usuários registrados
O painel conta e mostra os cadastros em tempo real:
- **Alunos cadastrados** e **matrículas ativas**: cartões no topo da lista de Alunos e na tela Início.
- **Usuários do painel** (quem tem login): Configurações → Quem acessa o painel.

No momento da medição (banco em produção, ainda com dados de teste): **2 usuários do painel**, 2 alunos e 1 turma. Esses números passam a valer de verdade quando o professor cadastrar os alunos reais.

## 2. Tempo médio de busca
Medido buscando por **nome** e por **telefone** na lista de alunos (`/admin/core/aluno/?q=...`), 40 repetições cada, com uma base de **2.000 alunos** gerada só para o teste.

| Busca | Tempo médio | Pior caso |
|---|---|---|
| Por nome (`Ana`, muitos resultados) | **118 ms** | 227 ms |
| Por telefone (`9876`) | **32 ms** | 73 ms |
| Sem resultado | **17 ms** | 25 ms |
| Lista inteira, sem busca | **91 ms** | 129 ms |

Condições: SQLite local, tempo medido no servidor (sem a rede do usuário). **Na prática, o tempo médio de busca é de décimos de segundo**, mesmo com 2.000 alunos, muito mais que o suficiente para uma turma real (dezenas de alunos).

Em produção o banco está nos EUA e cada consulta leva cerca de 0,2 s. Medindo direto no banco real, uma busca leva em média **~0,4 s** quando os números já estão em cache e **~1,6 s** na primeira vez. Para a Vercel foi fixada a região `sfo1`, perto do banco, o que reduz esse tempo. Trocar o banco para a região de São Paulo reduziria ainda mais.

Para comparar com o controle em papel: achar um aluno num caderno ou numa planilha leva em geral dezenas de segundos. Essa comparação precisa ser medida com o professor (cronometrar 10 buscas no caderno e 10 no sistema).

## 3. Impacto esperado: reduzir erros de matrícula e doação (meta de 80%)
A meta é medida comparando o **número de erros por mês** antes e depois (a contagem "antes" é do controle em papel e precisa ser levantada com o professor). O que o sistema faz para evitar cada tipo de erro:

| Erro comum no controle manual | Como o sistema evita |
|---|---|
| Aluno anotado duas vezes | Cadastro único, com busca por nome e telefone |
| Presença marcada em duplicidade ou esquecida | Uma presença por aluno por dia (restrição no banco); chamada com todos já ligados |
| Doação lançada duas vezes | Doação idêntica enviada em poucos segundos é ignorada |
| Faixa e grau desatualizados | Ao registrar a troca de faixa, o cadastro do aluno é atualizado sozinho, com histórico |
| Faixa digitada errada | Escolha só entre as 17 faixas; grau limitado a 0–4 |
| Total de doações errado | O painel soma o mês e o ano automaticamente |
| Telefone ou data em formato errado | Máscaras no formulário (`+55 (21)…`, calendário) |
| Exclusão por engano | Tela de confirmação antes de apagar |
| Certificado com dados errados | Gerado a partir do cadastro, com a assinatura salva |

### Como medir a meta
1. Durante 1 mês no papel: contar os erros (nome duplicado, presença errada, doação somada errado…).
2. Durante 1 mês no sistema: contar os mesmos erros.
3. Redução = (erros antes − erros depois) ÷ erros antes.
