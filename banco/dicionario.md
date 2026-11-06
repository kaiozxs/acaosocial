# Dicionário de dados

| Tabela | Para que serve |
|---|---|
| `core_turma` | Grupos de treino com dia e horário fixos (ex.: Jiu-jitsu adulto, seg/qua/sex, 19h). Aparecem no site em "Horários de treino" e na chamada. |
| `core_aluno` | Alunos matriculados: dados pessoais, turma, faixa, grau e situação da matrícula. |
| `core_graduacao` | Histórico de trocas de faixa e de grau de cada aluno. |
| `core_presenca` | Quem veio em cada dia. Alimenta a frequência do mês. |
| `core_interessado` | Pessoas que preencheram a ficha "Quero treinar" no site. |
| `core_doacao` | Doações anotadas pelo professor (Pix, dinheiro ou outra). |
| `core_assinatura` | Assinatura e título do professor, usados nos certificados. Uma linha só. |

## Campos principais

### core_aluno
| Campo | Tipo | Observação |
|---|---|---|
| `nome` | texto (120) | obrigatório |
| `nascimento` | data | a idade e a categoria (Kids, Jovem, Adolescente, Adulto) são calculadas |
| `telefone` | texto (20) | formato `+55 (21) 99999-9999` |
| `responsavel` | texto (120) | obrigatório para menores |
| `faixa` | texto (20) | uma das 17 faixas, veja abaixo |
| `grau` | número 0 a 4 | listras na ponta da faixa |
| `inicio` | data | início dos treinos |
| `status` | texto | `ativa`, `trancada` ou `cancelada` |
| `turma_id` | chave estrangeira | opcional |

### Faixas (`faixa`)
`branca` · `cinza-branca`, `cinza`, `cinza-preta` · `amarela-branca`, `amarela`, `amarela-preta` · `laranja-branca`, `laranja`, `laranja-preta` · `verde-branca`, `verde`, `verde-preta` · `azul`, `roxa`, `marrom`, `preta`

As infantis (cinza, amarela, laranja e verde) têm três etapas: com listra branca, lisa e com listra preta.

### core_presenca
| Campo | Observação |
|---|---|
| `aluno_id` + `data` | combinação única: não existe duas presenças do mesmo aluno no mesmo dia |

### core_doacao
| Campo | Observação |
|---|---|
| `valor` | decimal (9,2), em reais |
| `forma` | `pix`, `dinheiro` ou `outra` |
| `doador` | em branco = anônimo |

## Regras que evitam erro
- **Presença única** por aluno e por dia (restrição no banco).
- **Sem duplicar por clique duplo:** troca de faixa, doação e ficha de interessado idênticas enviadas em poucos segundos viram um registro só.
- **Grau limitado a 0–4** e faixa só entre as 17 opções.
- **Faixa do aluno sempre em dia:** ao registrar uma troca de faixa, o cadastro do aluno é atualizado automaticamente.
- **Confirmação antes de excluir**, com aviso do que mais será apagado.
