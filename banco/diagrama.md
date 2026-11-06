# Diagrama do banco de dados

Banco: **PostgreSQL no Supabase** (em desenvolvimento local o Django usa SQLite com as mesmas tabelas).

```mermaid
erDiagram
    TURMA ||--o{ ALUNO : "reúne"
    ALUNO ||--o{ GRADUACAO : "tem histórico de"
    ALUNO ||--o{ PRESENCA : "tem"

    TURMA {
        bigint id PK
        varchar nome
        varchar modalidade "jiu-jitsu, muay-thai, luta-livre"
        varchar publico
        varchar dias
        varchar horario
        smallint ordem
    }
    ALUNO {
        bigint id PK
        varchar nome
        date nascimento
        varchar telefone
        varchar responsavel
        varchar faixa "17 faixas (kids e adulto)"
        smallint grau "0 a 4"
        date inicio
        varchar status "ativa, trancada, cancelada"
        text observacoes
        bigint turma_id FK
    }
    GRADUACAO {
        bigint id PK
        bigint aluno_id FK
        varchar faixa
        smallint grau
        date data
        varchar observacao
    }
    PRESENCA {
        bigint id PK
        bigint aluno_id FK
        date data "única por aluno e dia"
    }
    INTERESSADO {
        bigint id PK
        varchar nome
        varchar telefone
        smallint idade
        text mensagem
        boolean contatado
        timestamptz criado_em
    }
    DOACAO {
        bigint id PK
        varchar doador "vazio = anônimo"
        numeric valor
        date data
        varchar forma "pix, dinheiro, outra"
        varchar observacao
    }
    ASSINATURA {
        bigint id PK
        varchar nome
        varchar titulo
        text imagem "PNG em base64"
    }
```

## Como as tabelas se ligam
- **Turma → Aluno:** uma turma tem vários alunos. Se a turma for apagada, os alunos ficam sem turma (não são apagados).
- **Aluno → Troca de faixa (Graduação):** cada troca de faixa fica no histórico. Ao registrar, a faixa e o grau do aluno são atualizados sozinhos.
- **Aluno → Presença:** uma linha por aluno e por dia. A combinação aluno + data é única, então a mesma presença não se repete.
- **Interessado, Doação e Assinatura** não dependem das outras tabelas.

Também existem as tabelas do próprio Django (usuários, sessões, histórico do painel). Todas as tabelas ficam protegidas no Supabase (RLS ligado, sem acesso pela API pública).
