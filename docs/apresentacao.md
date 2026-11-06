# Roteiro da apresentação (dia 13)

Tempo sugerido: **8 a 10 minutos** (6 de demonstração).

Slides prontos: [apresentacao-projeto-salvacao.pptx](apresentacao-projeto-salvacao.pptx) (10 slides; as anotações de cada slide ficam no campo de notas do PowerPoint).

## Antes de começar (checklist)
- [ ] Site publicado abrindo no celular e no computador.
- [ ] Painel aberto e **logado** em outra aba (para não gastar tempo com senha).
- [ ] Turmas e alguns alunos cadastrados; uma chamada já feita para aparecer a frequência.
- [ ] Assinatura do professor cadastrada (para o certificado sair completo).
- [ ] Pasta `evidencias/` aberta como plano B, se a internet falhar.
- [ ] Tema escuro ligado (é o padrão).

## 1. O problema (1 min)
- O CT Salvação é um projeto social: atende crianças, jovens e adultos de jiu-jitsu e muay thai.
- O controle é feito em papel e conversas soltas: aluno anotado duas vezes, presença esquecida, doação somada errado, certificado refeito à mão.
- A equipe usa o **celular**, não tem computador.

## 2. A solução (1 min)
- **Site público** para divulgar o projeto, receber doações por Pix e pedidos de aula.
- **Painel simples** para o professor gerir tudo pelo celular.
- Pensado para quem tem pouca familiaridade com tecnologia: poucos botões, palavras do dia a dia, confirmação antes de apagar.

## 3. Demonstração (6 min)
1. **Site (1 min):** mostrar a abertura com as logos, a história, a galeria em carrossel, os horários e o Pix (QR code e "copia e cola"). Preencher a ficha **Quero treinar**: aparece o aviso na tela.
2. **Painel no celular (1 min):** abrir no telefone: menu inferior, cartões, botões grandes. Chamar a atenção para o **WhatsApp** do interessado que acabou de chegar.
3. **Chamada (1 min):** Chamada → turma → todos ligados → desligar um → ver a **frequência do mês** → Salvar.
4. **Aluno e faixa (1 min):** Novo aluno em janelinha (telefone já com +55 (21), calendário no campo de data). Mostrar as 17 faixas, com as infantis de listra branca e preta.
5. **Certificado (1 min):** Certificados → escolher o aluno → Gerar PDF → mostrar o PDF com a faixa desenhada e a assinatura.
6. **Doações e início (1 min):** registrar uma doação e voltar ao Início: o gráfico e o total do mês mudam sozinhos.

## 4. Tecnologia (1 min)
Django (Python) · banco PostgreSQL no Supabase · publicado na Vercel · PDF gerado na hora. Segurança: login, cookies só por HTTPS, tabelas do banco protegidas (RLS), confirmação antes de excluir.

## 5. Resultados (1 min)
- **Tempo de busca:** ~120 ms numa base de 2.000 alunos (na prática, instantâneo).
- **Erros evitados:** presença única por dia, registro repetido ignorado, faixa e grau validados, totais automáticos.
- **Meta de impacto:** reduzir **80%** dos erros de matrícula e doação. Como medir: contar os erros por mês antes (papel) e depois (sistema).
- Número de usuários e alunos cadastrados: aparece no painel em tempo real.

## 6. Próximos passos (30 s)
- Foto do aluno (Supabase Storage).
- Aviso automático por WhatsApp para os interessados.
- Banco na região de São Paulo, para ficar ainda mais rápido.
- Relatório mensal de frequência para os responsáveis.

## Perguntas que podem aparecer
- **Por que Django e não outra coisa?** Já traz login, permissões e banco prontos; o foco ficou em deixar o painel simples.
- **Por que Vercel e não Cloudflare?** O Cloudflare não roda Django; a Vercel roda e é gratuita para esse uso.
- **E se a internet cair?** O painel precisa de internet. Sem ela, a chamada pode ser anotada e lançada depois.
- **Os dados estão seguros?** Login obrigatório, conexão HTTPS, chave secreta fora do código e tabelas do banco fechadas para a API pública.
