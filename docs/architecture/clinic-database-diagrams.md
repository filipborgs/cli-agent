# Diagramas do banco de dados da clínica

Status: diagramas aprovados em 2026-10-09, ainda sem implementação.

Representação visual do [desenho aprovado do banco](../superpowers/specs/2026-10-09-clinic-database-design.md).
Referência funcional: [documentação de negócio](../business/README.md).

Os diagramas são conceituais: os nomes representam entidades, não DDL definitivo.
As visões detalhadas mostram cardinalidades e tabelas associativas. As entidades
repetidas em várias visões representam o mesmo cadastro.

Nos diagramas de entidades: `||` significa exatamente um, `o|` significa zero
ou um e `o{` significa zero ou muitos. Os atributos exibidos são um recorte dos
dados relevantes; seus tipos são conceituais, não tipos SQL definitivos.

## 1. Visão geral

As setas desta visão indicam organização e dependências do domínio, não cardinalidades.

```mermaid
flowchart TB
    TENANT["Tenant / organização"]
    TENANT --> CLINICA["Uma ou mais clínicas"]
    TENANT --> PACIENTE["Pacientes — cadastro único"]
    TENANT --> TERAPEUTA["Terapeutas — cadastro único"]
    TENANT --> ESPECIALIDADE["Especialidades"]

    CLINICA --> SALA["Salas e especialidades permitidas"]
    CLINICA --> CALENDARIO["Funcionamento, feriados e recessos"]

    PACIENTE --> VINCULO["Vínculo de atendimento<br/>Paciente + terapeuta + especialidade<br/>Frequência semanal + duração + vigência"]
    TERAPEUTA --> VINCULO
    ESPECIALIDADE --> VINCULO

    PACIENTE --> DISP["Disponibilidades semanais por clínica"]
    TERAPEUTA --> DISP
    VINCULO --> ROTINA["Horários semanais planejados"]
    DISP -. "condiciona" .-> ROTINA
    SALA -. "condiciona" .-> ROTINA
    CALENDARIO -. "condiciona" .-> ROTINA

    ROTINA --> SESSAO["Sessões com data e horário<br/>na agenda mensal da clínica"]
    SESSAO --> HISTORICO["Histórico de ajustes e resultados"]
    SESSAO --> DECISAO{"Ausência com direito<br/>à reposição?"}
    DECISAO -->|Sim| PENDENCIA["Pendência de reposição"]
    PENDENCIA --> TENTATIVA["Tentativa de reposição<br/>Outra sessão, mesmo vínculo"]
    TENTATIVA -->|Realizada| QUITADA["Pendência quitada"]

    classDef organizacao fill:#dbeafe,stroke:#2563eb,color:#172554;
    classDef planejamento fill:#fef3c7,stroke:#d97706,color:#451a03;
    classDef atendimento fill:#dcfce7,stroke:#16a34a,color:#052e16;
    classDef reposicao fill:#f3e8ff,stroke:#9333ea,color:#3b0764;
    class TENANT,CLINICA,PACIENTE,TERAPEUTA,ESPECIALIDADE organizacao;
    class SALA,CALENDARIO,VINCULO,DISP,ROTINA planejamento;
    class SESSAO,HISTORICO atendimento;
    class DECISAO,PENDENCIA,TENTATIVA,QUITADA reposicao;
```

## 2. Organização, acesso e cadastros

```mermaid
erDiagram
    TENANT ||--o{ CLINICA : possui
    TENANT ||--o{ USUARIO_TENANT : autoriza
    USUARIO ||--o{ USUARIO_TENANT : participa

    TENANT ||--o{ PACIENTE : cadastra
    TENANT ||--o{ TERAPEUTA : cadastra
    TENANT ||--o{ ESPECIALIDADE : define

    PACIENTE ||--o{ PACIENTE_CLINICA : participa
    CLINICA ||--o{ PACIENTE_CLINICA : recebe
    TERAPEUTA ||--o{ TERAPEUTA_CLINICA : participa
    CLINICA ||--o{ TERAPEUTA_CLINICA : recebe

    TERAPEUTA ||--o{ TERAPEUTA_ESPECIALIDADE : habilitado
    ESPECIALIDADE ||--o{ TERAPEUTA_ESPECIALIDADE : habilita

    CLINICA ||--o{ SALA : possui
    SALA ||--o{ SALA_ESPECIALIDADE : permite
    ESPECIALIDADE ||--o{ SALA_ESPECIALIDADE : compativel
```

- `USUARIO_TENANT` representa o acesso administrativo no MVP.
- `PACIENTE_CLINICA` e `TERAPEUTA_CLINICA` permitem compartilhar cadastros entre unidades.
- `TERAPEUTA_ESPECIALIDADE` e `SALA_ESPECIALIDADE` representam relações muitos-para-muitos.
- As cardinalidades permitem cadastros ainda em configuração. Para agendar, a
  clínica precisa ter os participantes habilitados e uma sala compatível.

## 3. Vínculos e rotina semanal

```mermaid
erDiagram
    PACIENTE ||--o{ VINCULO_ATENDIMENTO : recebe
    TERAPEUTA ||--o{ VINCULO_ATENDIMENTO : atende
    ESPECIALIDADE ||--o{ VINCULO_ATENDIMENTO : classifica

    VINCULO_ATENDIMENTO ||--o{ VINCULO_CLINICA : permitido
    CLINICA ||--o{ VINCULO_CLINICA : habilita

    VINCULO_ATENDIMENTO ||--o{ HORARIO_SEMANAL : planeja
    CLINICA ||--o{ HORARIO_SEMANAL : recebe
    SALA ||--o{ HORARIO_SEMANAL : alocada

    VINCULO_ATENDIMENTO {
        referencia paciente
        referencia terapeuta
        referencia especialidade
        inteiro atendimentos_por_semana
        duracao duracao_especifica_opcional
        periodo vigencia
    }

    HORARIO_SEMANAL {
        referencia vinculo
        referencia clinica
        referencia sala
        dia dia_da_semana
        horario hora_inicial
        duracao duracao
        periodo vigencia
    }
```

O vínculo é único por **paciente + terapeuta + especialidade** em cada período
de vigência. Sua frequência é única no tenant, mesmo que distribuída entre clínicas.
A duração específica, quando ausente, usa o padrão da clínica do atendimento.

Um vínculo pode existir sem horários definidos; por isso a relação com
`HORARIO_SEMANAL` permite zero registros. Um horário semanal é o padrão de
repetição, enquanto a disponibilidade é apenas uma janela possível.

## 4. Disponibilidades e calendário

```mermaid
erDiagram
    PACIENTE ||--o{ DISPONIBILIDADE_PACIENTE : informa
    CLINICA ||--o{ DISPONIBILIDADE_PACIENTE : local
    TERAPEUTA ||--o{ DISPONIBILIDADE_TERAPEUTA : informa
    CLINICA ||--o{ DISPONIBILIDADE_TERAPEUTA : local

    CLINICA ||--o{ FUNCIONAMENTO : define
    CLINICA ||--o{ BLOQUEIO_CLINICA : fecha

    PACIENTE o|--o{ BLOQUEIO_PESSOA : indisponivel
    TERAPEUTA o|--o{ BLOQUEIO_PESSOA : indisponivel

    DISPONIBILIDADE_PACIENTE {
        dia dia_da_semana
        horario hora_inicial
        horario hora_final
        periodo vigencia
    }

    DISPONIBILIDADE_TERAPEUTA {
        dia dia_da_semana
        horario hora_inicial
        horario hora_final
        periodo vigencia
    }

    BLOQUEIO_CLINICA {
        instante inicio
        instante fim
        texto motivo_feriado_ou_recesso
    }

    BLOQUEIO_PESSOA {
        instante inicio
        instante fim
        texto motivo
    }
```

Cada `BLOQUEIO_PESSOA` pertence **a um paciente ou a um terapeuta, nunca aos dois**.
As duas relações opcionais precisam dessa restrição adicional de exclusividade;
o mecanismo físico será definido na implementação. O bloqueio vale em todas as
clínicas do tenant.

O fechamento da clínica impede a geração de sessões. Não cria reposição de
atendimentos habituais nem obriga a completar a frequência em outro dia.

## 5. Agenda, sessões e pendências

```mermaid
erDiagram
    CLINICA ||--o{ AGENDA_MENSAL : organiza
    AGENDA_MENSAL ||--o{ EXECUCAO_GERACAO : registra
    EXECUCAO_GERACAO ||--o{ PENDENCIA_GERACAO : identifica
    VINCULO_ATENDIMENTO ||--o{ PENDENCIA_GERACAO : nao_encaixado

    VINCULO_ATENDIMENTO ||--o{ SESSAO : origina
    CLINICA ||--o{ SESSAO : recebe
    SALA ||--o{ SESSAO : alocada
    HORARIO_SEMANAL o|--o{ SESSAO : origem_da_rotina

    SESSAO ||--o{ HISTORICO_SESSAO : registra
    USUARIO ||--o{ HISTORICO_SESSAO : responsavel

    SESSAO ||--o| PENDENCIA_REPOSICAO : atendimento_original
    VINCULO_ATENDIMENTO ||--o{ PENDENCIA_REPOSICAO : mantem
    USUARIO o|--o{ PENDENCIA_REPOSICAO : decide
    PENDENCIA_REPOSICAO o|--o{ SESSAO : tentativas

    SESSAO {
        instante inicio
        instante fim
        duracao duracao_efetiva
        categoria origem_rotina_ou_reposicao
        estado resultado
        booleano ajustada_manualmente
    }

    PENDENCIA_REPOSICAO {
        referencia sessao_original
        referencia vinculo
        texto motivo
        decisao direito_a_reposicao
        estado situacao
    }
```

- `PENDENCIA_GERACAO`: o gerador não encontrou capacidade; não representa uma dívida.
- `PENDENCIA_REPOSICAO`: um atendimento previsto não aconteceu e há direito a repô-lo.
- A mesma entidade `SESSAO` representa a rotina e as tentativas de reposição.
- Uma sessão pode ter zero ou uma pendência de origem de reposição:
  zero para rotina; exatamente uma para uma tentativa de reposição.
- A relação `atendimento_original` é diferente de `tentativas`: a primeira
  identifica a sessão que gerou o direito; a segunda aponta os novos encaixes.
- Falta em uma tentativa reabre ou encerra a pendência existente conforme a regra;
  não cria uma pendência filha.
- No máximo uma tentativa ativa agendada e uma realizada por pendência.
- A agenda mensal reúne sessões por clínica e mês. A visão não impõe uma FK
  obrigatória de sessão para agenda: ajustes e registros de ausências antecipadas
  precisam existir independentemente de uma execução de geração.
- Responsável pela decisão é opcional quando o direito decorre automaticamente
  da falta do terapeuta; decisões administrativas exigem responsável registrado.

## 6. Ciclo da reposição

```mermaid
flowchart TD
    ORIGINAL["Atendimento original não realizado"] --> DIREITO{"Há direito à reposição?"}
    DIREITO -->|Não| HISTORICO["Manter histórico sem abrir pendência"]
    DIREITO -->|Sim| PENDENTE["Pendência aberta"]

    PENDENTE --> VALIDAR{"Cadastros, vínculo e<br/>habilitações válidos?"}
    VALIDAR -->|Não| REGULARIZAR["Regularizar ou encerrar com motivo"]
    REGULARIZAR -->|Regularizado| PENDENTE
    REGULARIZAR -->|Encerrado| ENCERRADA["Encerrada sem realização"]
    VALIDAR -->|Sim| AGENDADA["Agendar tentativa<br/>com terapeuta original"]

    AGENDADA --> RESULTADO{"O que aconteceu?"}
    RESULTADO -->|Realizada| QUITADA["Pendência realizada / quitada"]
    RESULTADO -->|Falta do terapeuta| PENDENTE
    RESULTADO -->|Fechamento da clínica| PENDENTE
    RESULTADO -->|Paciente avisou| EQUIPE{"Equipe concede<br/>nova tentativa?"}
    EQUIPE -->|Sim| PENDENTE
    EQUIPE -->|Não| ENCERRADA
    RESULTADO -->|Paciente faltou sem aviso| ENCERRADA
```

## 7. Restrições que acompanham os diagramas

As cardinalidades não expressam todas as regras. A implementação também deve garantir:

- Isolamento por tenant e referências que não misturem organizações.
- Vínculos e participantes habilitados para a clínica escolhida.
- Especialidade habilitada para terapeuta e sala.
- Ausência de sobreposição de paciente, terapeuta ou sala, mesmo entre clínicas.
- Vigências válidas, frequência e duração positivas e início anterior ao fim.
- Identidade da ocorrência original preservada nos ajustes e novas gerações.
- Reposição com o mesmo paciente, terapeuta e especialidade do atendimento original.
- Ausência de duplicação de sessões, pendências e tentativas ativas.
- Encaixe fora da disponibilidade apenas por ajuste manual registrado, sem
  desrespeitar funcionamento, bloqueios ou conflitos.

Os diagramas podem ser visualizados em um renderizador Mermaid, como o GitHub
ou uma prévia Markdown com suporte a Mermaid.
