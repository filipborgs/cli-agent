# Modelo entidade-relacionamento físico da clínica

Representa as **26 tabelas implementadas** no PostgreSQL, até a revisão Alembic
`0010_monthly_agenda_schema`. Os nomes e as relações vêm dos modelos ORM;
colunas completas, índices e constraints estão no [dicionário físico](../database/schema.md).
Os [diagramas conceituais](clinic-database-diagrams.md) explicam os fluxos do produto.

O modelo está dividido em **dez visões**, cada uma com quatro a seis caixas.
Consulte a seção do assunto desejado e use a visão completa apenas para
seguir referências entre domínios.

Fonte Mermaid completa: [clinic-database-er.mmd](clinic-database-er.mmd).

## Leitura do modelo

Cada caixa mostra o nome físico da tabela e uma descrição curta de sua função.

- `PK`: chave primária; `FK`: coluna de chave estrangeira. As colunas marcadas
  como PK em uma associação formam **uma única chave composta**.
- `||`: exatamente um; `o|`: zero ou um; `o{`: zero ou muitos.
- As legendas das ligações indicam a principal coluna local, omitindo `tenant_id`.
  As FKs clínicas incluem esse campo e impedem referências entre organizações.
- Cada visão mostra suas relações principais. Ligações repetidas de tenant,
  autoria e recursos ficam nas visões específicas ou no modelo completo.
- Entidades de apoio aparecem apenas com as chaves necessárias para reconhecer
  a referência; seus demais campos estão na visão proprietária e no dicionário.
- No modelo completo, referências redundantes entre o mesmo par de tabelas
  são representadas pela FK mais completa. Timestamps comuns foram omitidos para facilitar a leitura.
- Os tipos são físicos: UUID, TIMESTAMPTZ, DATE, TIME, TEXT, INTEGER, BOOLEAN e
  JSONB. `weekday` usa SMALLINT no banco, agrupado como integer nesta visão.

As cardinalidades representam a integridade do schema, não a execução de
serviços clínicos. Estados, condições de agendamento e transições de reposição
continuam sujeitos às regras [RN-001 a RN-026](../business/business-rules.md).

## Visões disponíveis

| Visão | Conteúdo |
| --- | --- |
| 1. Organização e acesso | Tenant, usuários, participação administrativa e clínicas |
| 2. Participação nas clínicas | Associações de pacientes e terapeutas às unidades |
| 3. Especialidades e salas | Habilitações e compatibilidades |
| 4. Planos de atendimento | Vínculo, frequência, vigência e clínicas habilitadas |
| 5. Disponibilidades e funcionamento | Janelas semanais de pessoas e clínicas |
| 6. Rotina semanal | Horários fixos e salas |
| 7. Sessões e histórico | Atendimento concreto e eventos |
| 8. Reposições | Sessão original, dívida e tentativas |
| 9. Fechamentos e bloqueios | Impedimentos de clínica ou pessoa |
| 10. Agenda mensal e geração | Agenda, execuções e déficits |

## 1. Organização e acesso

Uma organização reúne clínicas; usuários recebem participação administrativa na organização.

```mermaid
erDiagram
    direction LR
    tenant["tenant — Organização que reúne as clínicas"] {
        uuid id PK
        text name
        boolean active
    }
    user["user — Identidade de acesso ao sistema"] {
        uuid id PK
        text name
        boolean active
    }
    user_tenant["user_tenant — Participação administrativa na organização"] {
        uuid tenant_id PK, FK
        uuid user_id PK, FK
        text role
        boolean active
    }
    clinic["clinic — Unidade de atendimento e suas configurações"] {
        text name
        text timezone
        integer default_duration_minutes
        boolean active
        uuid id PK
        uuid tenant_id FK
    }
    tenant ||--o{ clinic : "tenant_id"
    tenant ||--o{ user_tenant : "tenant_id"
    user ||--o{ user_tenant : "user_id"
```

## 2. Participação nas clínicas

Pacientes e terapeutas têm cadastro por organização e podem participar de várias clínicas.

```mermaid
erDiagram
    direction LR
    patient["patient — Cadastro do paciente na organização"] {
        text name
        boolean active
        uuid id PK
        uuid tenant_id FK
    }
    therapist["therapist — Cadastro do terapeuta na organização"] {
        text name
        boolean active
        uuid id PK
        uuid tenant_id FK
    }
    patient_clinic["patient_clinic — Participação do paciente na clínica"] {
        uuid tenant_id PK, FK
        uuid patient_id PK, FK
        uuid clinic_id PK, FK
        boolean active
    }
    therapist_clinic["therapist_clinic — Participação do terapeuta na clínica"] {
        uuid tenant_id PK, FK
        uuid therapist_id PK, FK
        uuid clinic_id PK, FK
        boolean active
    }
    clinic["clinic — Unidade de atendimento e suas configurações"] {
        uuid id PK
        uuid tenant_id FK
    }
    clinic ||--o{ patient_clinic : "clinic_id"
    clinic ||--o{ therapist_clinic : "clinic_id"
    patient ||--o{ patient_clinic : "patient_id"
    therapist ||--o{ therapist_clinic : "therapist_id"
```

## 3. Especialidades e salas

As associações registram as habilitações do terapeuta e a compatibilidade da sala. A clínica da sala aparece na visão de rotina.

```mermaid
erDiagram
    direction LR
    specialty["specialty — Especialidade de atendimento"] {
        text name
        text normalized_name
        boolean active
        uuid id PK
        uuid tenant_id FK
    }
    room["room — Sala de atendimento de uma clínica"] {
        uuid clinic_id FK
        text name
        text normalized_name
        boolean active
        uuid id PK
        uuid tenant_id FK
    }
    therapist_specialty["therapist_specialty — Especialidade habilitada para o terapeuta"] {
        uuid tenant_id PK, FK
        uuid therapist_id PK, FK
        uuid specialty_id PK, FK
        boolean active
    }
    room_specialty["room_specialty — Especialidade compatível com a sala"] {
        uuid tenant_id PK, FK
        uuid room_id PK, FK
        uuid specialty_id PK, FK
        boolean active
    }
    therapist["therapist — Cadastro do terapeuta na organização"] {
        uuid id PK
        uuid tenant_id FK
    }
    room ||--o{ room_specialty : "room_id"
    specialty ||--o{ room_specialty : "specialty_id"
    specialty ||--o{ therapist_specialty : "specialty_id"
    therapist ||--o{ therapist_specialty : "therapist_id"
```

## 4. Planos de atendimento

O plano fixa paciente, terapeuta, especialidade, frequência e vigência. Sua participação nas clínicas é registrada separadamente.

```mermaid
erDiagram
    direction LR
    treatment_plan["treatment_plan — Vínculo de atendimento, frequência e vigência"] {
        uuid id PK
        uuid tenant_id FK
        uuid patient_id FK
        uuid therapist_id FK
        uuid specialty_id FK
        integer sessions_per_week
        integer duration_minutes "opcional"
        date valid_from
        date valid_until "opcional"
    }
    treatment_plan_clinic["treatment_plan_clinic — Clínica habilitada para o plano"] {
        uuid tenant_id PK, FK
        uuid treatment_plan_id PK, FK
        uuid clinic_id PK, FK
        boolean active
    }
    patient["patient — Cadastro do paciente na organização"] {
        uuid id PK
        uuid tenant_id FK
    }
    therapist["therapist — Cadastro do terapeuta na organização"] {
        uuid id PK
        uuid tenant_id FK
    }
    specialty["specialty — Especialidade de atendimento"] {
        uuid id PK
        uuid tenant_id FK
    }
    clinic["clinic — Unidade de atendimento e suas configurações"] {
        uuid id PK
        uuid tenant_id FK
    }
    clinic ||--o{ treatment_plan_clinic : "clinic_id"
    patient ||--o{ treatment_plan : "patient_id"
    specialty ||--o{ treatment_plan : "specialty_id"
    therapist ||--o{ treatment_plan : "therapist_id"
    treatment_plan ||--o{ treatment_plan_clinic : "treatment_plan_id"
```

## 5. Disponibilidades e funcionamento

Janelas recorrentes representam possibilidades de atendimento; não são reservas de sessões.

```mermaid
erDiagram
    direction LR
    patient_availability["patient_availability — Janelas semanais disponíveis do paciente"] {
        uuid id PK
        uuid tenant_id FK
        uuid clinic_id FK
        uuid patient_id FK
        integer weekday
        time start_time
        time end_time
        date valid_from
        date valid_until "opcional"
    }
    therapist_availability["therapist_availability — Janelas semanais disponíveis do terapeuta"] {
        uuid id PK
        uuid tenant_id FK
        uuid clinic_id FK
        uuid therapist_id FK
        integer weekday
        time start_time
        time end_time
        date valid_from
        date valid_until "opcional"
    }
    clinic_hours["clinic_hours — Janelas semanais de funcionamento da clínica"] {
        uuid id PK
        uuid tenant_id FK
        uuid clinic_id FK
        integer weekday
        time start_time
        time end_time
        date valid_from
        date valid_until "opcional"
    }
    patient["patient — Cadastro do paciente na organização"] {
        uuid id PK
        uuid tenant_id FK
    }
    therapist["therapist — Cadastro do terapeuta na organização"] {
        uuid id PK
        uuid tenant_id FK
    }
    clinic["clinic — Unidade de atendimento e suas configurações"] {
        uuid id PK
        uuid tenant_id FK
    }
    clinic ||--o{ clinic_hours : "clinic_id"
    clinic ||--o{ patient_availability : "clinic_id"
    clinic ||--o{ therapist_availability : "clinic_id"
    patient ||--o{ patient_availability : "patient_id"
    therapist ||--o{ therapist_availability : "therapist_id"
```

## 6. Rotina semanal

O slot é o horário fixo escolhido para repetir semanalmente, com sala, duração e vigência. A FK composta garante a clínica da sala.

```mermaid
erDiagram
    direction LR
    weekly_slot["weekly_slot — Horário fixo escolhido para a rotina semanal"] {
        uuid id PK
        uuid tenant_id FK
        uuid treatment_plan_id FK
        uuid clinic_id FK
        uuid room_id FK
        integer weekday
        time start_time
        integer duration_minutes
        date valid_from
        date valid_until "opcional"
    }
    treatment_plan["treatment_plan — Vínculo de atendimento, frequência e vigência"] {
        uuid id PK
        uuid tenant_id FK
    }
    clinic["clinic — Unidade de atendimento e suas configurações"] {
        uuid id PK
        uuid tenant_id FK
    }
    room["room — Sala de atendimento de uma clínica"] {
        uuid id PK
        uuid tenant_id FK
    }
    clinic ||--o{ room : "clinic_id"
    clinic ||--o{ weekly_slot : "clinic_id"
    room ||--o{ weekly_slot : "clinic_id"
    treatment_plan ||--o{ weekly_slot : "treatment_plan_id"
```

## 7. Sessões e histórico

A sessão mantém vínculo com o plano e, quando é de rotina, com a ocorrência original. Eventos preservam o histórico e a autoria. Recursos e reposições aparecem nas visões relacionadas.

```mermaid
erDiagram
    direction LR
    appointment["appointment — Sessão de rotina ou tentativa de reposição"] {
        uuid id PK
        uuid tenant_id FK
        uuid treatment_plan_id FK
        uuid clinic_id FK
        uuid room_id FK
        uuid patient_id FK
        uuid therapist_id FK
        uuid specialty_id FK
        timestamptz starts_at
        timestamptz ends_at
        integer duration_minutes
        text origin
        text status
        uuid weekly_slot_id FK "opcional"
        date occurrence_date "opcional"
        boolean manually_adjusted
        text replacement_decision
        uuid replacement_due_id FK "opcional"
    }
    appointment_event["appointment_event — Registro histórico de alteração da sessão"] {
        uuid id PK
        uuid tenant_id FK
        uuid appointment_id FK
        uuid actor_id FK "opcional"
        timestamptz recorded_at
        text kind
        jsonb before
        jsonb after
    }
    treatment_plan["treatment_plan — Vínculo de atendimento, frequência e vigência"] {
        uuid id PK
        uuid tenant_id FK
    }
    weekly_slot["weekly_slot — Horário fixo escolhido para a rotina semanal"] {
        uuid id PK
        uuid tenant_id FK
    }
    user_tenant["user_tenant — Participação administrativa na organização"] {
        uuid tenant_id PK, FK
        uuid user_id PK, FK
    }
    appointment ||--o{ appointment_event : "appointment_id"
    treatment_plan ||--o{ appointment : "treatment_plan_id"
    user_tenant o|--o{ appointment_event : "actor_id"
    weekly_slot o|--o{ appointment : "weekly_slot_id"
```

## 8. Reposições

As duas caixas `appointment` representam **papéis da mesma tabela**, não duas
tabelas diferentes. A sessão original pode gerar uma dívida; várias sessões
históricas podem ser tentativas de quitar essa mesma dívida. Apenas tentativas
possuem `replacement_due_id`, obrigatório nesse papel pelo CHECK de origem.

```mermaid
erDiagram
    direction LR
    original_appointment["appointment — Sessão original de rotina"] {
        uuid id PK
        uuid tenant_id FK
        uuid treatment_plan_id FK
        text origin
        text status
        uuid weekly_slot_id FK "opcional"
        date occurrence_date "opcional"
    }
    replacement_attempt["appointment — Tentativa de reposição"] {
        uuid id PK
        uuid tenant_id FK
        uuid treatment_plan_id FK
        text origin
        text status
        uuid replacement_due_id FK "opcional"
    }
    replacement_due["replacement_due — Direito de reposição ligado à sessão original"] {
        uuid id PK
        uuid tenant_id FK
        text original_origin FK "gerado: routine"
        uuid original_appointment_id FK
        uuid treatment_plan_id FK
        text reason
        text status
        uuid decided_by FK "opcional"
        timestamptz decided_at "opcional"
        text closed_reason "opcional"
    }
    user_tenant["user_tenant — Participação administrativa na organização"] {
        uuid tenant_id PK, FK
        uuid user_id PK, FK
        text role
        boolean active
    }
    original_appointment ||--o| replacement_due : "original_appointment_id"
    replacement_due ||--o{ replacement_attempt : "replacement_due_id"
    user_tenant o|--o{ replacement_due : "decided_by"
```

## 9. Fechamentos e bloqueios

Fechamentos pertencem à clínica. Cada bloqueio individual referencia exatamente um paciente ou um terapeuta.

```mermaid
erDiagram
    direction LR
    clinic_closure["clinic_closure — Fechamento da clínica por um período"] {
        uuid id PK
        uuid tenant_id FK
        uuid clinic_id FK
        timestamptz starts_at
        timestamptz ends_at
        text reason
        uuid created_by FK
    }
    person_block["person_block — Indisponibilidade de paciente ou terapeuta"] {
        uuid id PK
        uuid tenant_id FK
        uuid patient_id FK "opcional"
        uuid therapist_id FK "opcional"
        timestamptz starts_at
        timestamptz ends_at
        text reason
        uuid created_by FK
    }
    clinic["clinic — Unidade de atendimento e suas configurações"] {
        uuid id PK
        uuid tenant_id FK
    }
    patient["patient — Cadastro do paciente na organização"] {
        uuid id PK
        uuid tenant_id FK
    }
    therapist["therapist — Cadastro do terapeuta na organização"] {
        uuid id PK
        uuid tenant_id FK
    }
    user_tenant["user_tenant — Participação administrativa na organização"] {
        uuid tenant_id PK, FK
        uuid user_id PK, FK
    }
    clinic ||--o{ clinic_closure : "clinic_id"
    patient o|--o{ person_block : "patient_id"
    therapist o|--o{ person_block : "therapist_id"
    user_tenant ||--o{ clinic_closure : "created_by"
    user_tenant ||--o{ person_block : "created_by"
```

## 10. Agenda mensal e geração

A agenda identifica clínica e mês; cada geração tem seu registro e seus déficits. Déficit de geração não é dívida de reposição.

```mermaid
erDiagram
    direction LR
    monthly_agenda["monthly_agenda — Agenda de uma clínica para um mês"] {
        uuid id PK
        uuid tenant_id FK
        uuid clinic_id FK
        date month
    }
    generation_run["generation_run — Registro de uma execução de geração"] {
        uuid id PK
        uuid tenant_id FK
        uuid monthly_agenda_id FK
        timestamptz started_at
        timestamptz completed_at "opcional"
        text status
        jsonb parameters
    }
    generation_deficit["generation_deficit — Atendimentos faltantes em uma geração"] {
        uuid id PK
        uuid tenant_id FK
        uuid generation_run_id FK
        uuid treatment_plan_id FK
        date week_start
        integer missing_count
        text reason_code
        jsonb details
    }
    clinic["clinic — Unidade de atendimento e suas configurações"] {
        uuid id PK
        uuid tenant_id FK
    }
    treatment_plan["treatment_plan — Vínculo de atendimento, frequência e vigência"] {
        uuid id PK
        uuid tenant_id FK
    }
    clinic ||--o{ monthly_agenda : "clinic_id"
    generation_run ||--o{ generation_deficit : "generation_run_id"
    monthly_agenda ||--o{ generation_run : "monthly_agenda_id"
    treatment_plan ||--o{ generation_deficit : "treatment_plan_id"
```

## Modelo completo para referência

<details>
<summary>Expandir as 26 entidades e todas as relações desenhadas</summary>

A visão completa preserva as ligações entre os domínios. Use as visões menores
acima para a leitura habitual.

```mermaid
erDiagram
    direction TB
    tenant["tenant — Organização que reúne as clínicas"] {
        uuid id PK
        text name
        boolean active
    }
    user["user — Identidade de acesso ao sistema"] {
        uuid id PK
        text name
        boolean active
    }
    user_tenant["user_tenant — Participação administrativa na organização"] {
        uuid tenant_id PK, FK
        uuid user_id PK, FK
        text role
        boolean active
    }
    clinic["clinic — Unidade de atendimento e suas configurações"] {
        text name
        text timezone
        integer default_duration_minutes
        boolean active
        uuid id PK
        uuid tenant_id FK
    }
    patient["patient — Cadastro do paciente na organização"] {
        text name
        boolean active
        uuid id PK
        uuid tenant_id FK
    }
    therapist["therapist — Cadastro do terapeuta na organização"] {
        text name
        boolean active
        uuid id PK
        uuid tenant_id FK
    }
    specialty["specialty — Especialidade de atendimento"] {
        text name
        text normalized_name
        boolean active
        uuid id PK
        uuid tenant_id FK
    }
    patient_clinic["patient_clinic — Participação do paciente na clínica"] {
        uuid tenant_id PK, FK
        uuid patient_id PK, FK
        uuid clinic_id PK, FK
        boolean active
    }
    therapist_clinic["therapist_clinic — Participação do terapeuta na clínica"] {
        uuid tenant_id PK, FK
        uuid therapist_id PK, FK
        uuid clinic_id PK, FK
        boolean active
    }
    room["room — Sala de atendimento de uma clínica"] {
        uuid clinic_id FK
        text name
        text normalized_name
        boolean active
        uuid id PK
        uuid tenant_id FK
    }
    therapist_specialty["therapist_specialty — Especialidade habilitada para o terapeuta"] {
        uuid tenant_id PK, FK
        uuid therapist_id PK, FK
        uuid specialty_id PK, FK
        boolean active
    }
    room_specialty["room_specialty — Especialidade compatível com a sala"] {
        uuid tenant_id PK, FK
        uuid room_id PK, FK
        uuid specialty_id PK, FK
        boolean active
    }
    treatment_plan["treatment_plan — Vínculo de atendimento, frequência e vigência"] {
        uuid id PK
        uuid tenant_id FK
        uuid patient_id FK
        uuid therapist_id FK
        uuid specialty_id FK
        integer sessions_per_week
        integer duration_minutes "opcional"
        date valid_from
        date valid_until "opcional"
    }
    treatment_plan_clinic["treatment_plan_clinic — Clínica habilitada para o plano"] {
        uuid tenant_id PK, FK
        uuid treatment_plan_id PK, FK
        uuid clinic_id PK, FK
        boolean active
    }
    patient_availability["patient_availability — Janelas semanais disponíveis do paciente"] {
        uuid id PK
        uuid tenant_id FK
        uuid clinic_id FK
        uuid patient_id FK
        integer weekday
        time start_time
        time end_time
        date valid_from
        date valid_until "opcional"
    }
    therapist_availability["therapist_availability — Janelas semanais disponíveis do terapeuta"] {
        uuid id PK
        uuid tenant_id FK
        uuid clinic_id FK
        uuid therapist_id FK
        integer weekday
        time start_time
        time end_time
        date valid_from
        date valid_until "opcional"
    }
    clinic_hours["clinic_hours — Janelas semanais de funcionamento da clínica"] {
        uuid id PK
        uuid tenant_id FK
        uuid clinic_id FK
        integer weekday
        time start_time
        time end_time
        date valid_from
        date valid_until "opcional"
    }
    weekly_slot["weekly_slot — Horário fixo escolhido para a rotina semanal"] {
        uuid id PK
        uuid tenant_id FK
        uuid treatment_plan_id FK
        uuid clinic_id FK
        uuid room_id FK
        integer weekday
        time start_time
        integer duration_minutes
        date valid_from
        date valid_until "opcional"
    }
    appointment["appointment — Sessão de rotina ou tentativa de reposição"] {
        uuid id PK
        uuid tenant_id FK
        uuid treatment_plan_id FK
        uuid clinic_id FK
        uuid room_id FK
        uuid patient_id FK
        uuid therapist_id FK
        uuid specialty_id FK
        timestamptz starts_at
        timestamptz ends_at
        integer duration_minutes
        text origin
        text status
        uuid weekly_slot_id FK "opcional"
        date occurrence_date "opcional"
        boolean manually_adjusted
        text replacement_decision
        uuid replacement_due_id FK "opcional"
    }
    appointment_event["appointment_event — Registro histórico de alteração da sessão"] {
        uuid id PK
        uuid tenant_id FK
        uuid appointment_id FK
        uuid actor_id FK "opcional"
        timestamptz recorded_at
        text kind
        jsonb before
        jsonb after
    }
    replacement_due["replacement_due — Direito de reposição ligado à sessão original"] {
        uuid id PK
        uuid tenant_id FK
        text original_origin FK "gerado: routine"
        uuid original_appointment_id FK
        uuid treatment_plan_id FK
        text reason
        text status
        uuid decided_by FK "opcional"
        timestamptz decided_at "opcional"
        text closed_reason "opcional"
    }
    clinic_closure["clinic_closure — Fechamento da clínica por um período"] {
        uuid id PK
        uuid tenant_id FK
        uuid clinic_id FK
        timestamptz starts_at
        timestamptz ends_at
        text reason
        uuid created_by FK
    }
    person_block["person_block — Indisponibilidade de paciente ou terapeuta"] {
        uuid id PK
        uuid tenant_id FK
        uuid patient_id FK "opcional"
        uuid therapist_id FK "opcional"
        timestamptz starts_at
        timestamptz ends_at
        text reason
        uuid created_by FK
    }
    monthly_agenda["monthly_agenda — Agenda de uma clínica para um mês"] {
        uuid id PK
        uuid tenant_id FK
        uuid clinic_id FK
        date month
    }
    generation_run["generation_run — Registro de uma execução de geração"] {
        uuid id PK
        uuid tenant_id FK
        uuid monthly_agenda_id FK
        timestamptz started_at
        timestamptz completed_at "opcional"
        text status
        jsonb parameters
    }
    generation_deficit["generation_deficit — Atendimentos faltantes em uma geração"] {
        uuid id PK
        uuid tenant_id FK
        uuid generation_run_id FK
        uuid treatment_plan_id FK
        date week_start
        integer missing_count
        text reason_code
        jsonb details
    }
    appointment ||--o{ appointment_event : "appointment_id"
    appointment ||--o| replacement_due : "original_appointment_id, treatment_plan_id, original_origin"
    clinic ||--o{ appointment : "clinic_id"
    clinic ||--o{ clinic_closure : "clinic_id"
    clinic ||--o{ clinic_hours : "clinic_id"
    clinic ||--o{ monthly_agenda : "clinic_id"
    clinic ||--o{ patient_availability : "clinic_id"
    clinic ||--o{ patient_clinic : "clinic_id"
    clinic ||--o{ room : "clinic_id"
    clinic ||--o{ therapist_availability : "clinic_id"
    clinic ||--o{ therapist_clinic : "clinic_id"
    clinic ||--o{ treatment_plan_clinic : "clinic_id"
    clinic ||--o{ weekly_slot : "clinic_id"
    generation_run ||--o{ generation_deficit : "generation_run_id"
    monthly_agenda ||--o{ generation_run : "monthly_agenda_id"
    patient ||--o{ appointment : "patient_id"
    patient ||--o{ patient_availability : "patient_id"
    patient ||--o{ patient_clinic : "patient_id"
    patient o|--o{ person_block : "patient_id"
    patient ||--o{ treatment_plan : "patient_id"
    replacement_due o|--o{ appointment : "replacement_due_id, treatment_plan_id"
    room ||--o{ appointment : "clinic_id, room_id"
    room ||--o{ room_specialty : "room_id"
    room ||--o{ weekly_slot : "clinic_id, room_id"
    specialty ||--o{ appointment : "specialty_id"
    specialty ||--o{ room_specialty : "specialty_id"
    specialty ||--o{ therapist_specialty : "specialty_id"
    specialty ||--o{ treatment_plan : "specialty_id"
    tenant ||--o{ clinic : "tenant_id"
    tenant ||--o{ patient : "tenant_id"
    tenant ||--o{ specialty : "tenant_id"
    tenant ||--o{ therapist : "tenant_id"
    tenant ||--o{ user_tenant : "tenant_id"
    therapist ||--o{ appointment : "therapist_id"
    therapist o|--o{ person_block : "therapist_id"
    therapist ||--o{ therapist_availability : "therapist_id"
    therapist ||--o{ therapist_clinic : "therapist_id"
    therapist ||--o{ therapist_specialty : "therapist_id"
    therapist ||--o{ treatment_plan : "therapist_id"
    treatment_plan ||--o{ appointment : "treatment_plan_id, patient_id, therapist_id, specialty_id"
    treatment_plan ||--o{ generation_deficit : "treatment_plan_id"
    treatment_plan ||--o{ replacement_due : "treatment_plan_id"
    treatment_plan ||--o{ treatment_plan_clinic : "treatment_plan_id"
    treatment_plan ||--o{ weekly_slot : "treatment_plan_id"
    treatment_plan_clinic ||--o{ appointment : "treatment_plan_id, clinic_id"
    treatment_plan_clinic ||--o{ weekly_slot : "treatment_plan_id, clinic_id"
    user ||--o{ user_tenant : "user_id"
    user_tenant o|--o{ appointment_event : "actor_id"
    user_tenant ||--o{ clinic_closure : "created_by"
    user_tenant ||--o{ person_block : "created_by"
    user_tenant o|--o{ replacement_due : "decided_by"
    weekly_slot o|--o{ appointment : "weekly_slot_id, treatment_plan_id"
```

</details>

## Restrições importantes para interpretar as relações

- **Organização:** paciente e terapeuta são cadastros do tenant, com participações
  em várias clínicas. Sala pertence a uma clínica — RN-001, RN-002 e RN-004.
- **Atendimento:** o plano determina paciente, terapeuta e especialidade;
  FKs compostas garantem que a sessão mantenha essa combinação — RN-005 e RN-021.
- **Ocorrência:** uma sessão de rotina referencia slot e data original; essa
  combinação é única, mesmo se o horário atual for alterado — RN-014.
- **Reposição:** uma sessão original pode ter no máximo uma dívida. Tentativas
  são outras linhas de `appointment`, ligadas à mesma dívida. A coluna gerada
  `original_origin='routine'` protege a origem com uma FK discriminadora — RN-024.
- **Tentativas:** a ligação dívida → sessões é 1:N para preservar histórico;
  índices parciais limitam a uma tentativa `scheduled` e uma `completed` por
  dívida. Essas condições não aparecem nas cardinalidades simples — RN-024.
- **Reservas:** exclusões GiST impedem sobreposição por paciente, terapeuta e
  sala em `scheduled`/`completed`, incluindo conflitos entre clínicas — RN-012.
- **Bloqueio individual:** `person_block` referencia paciente ou terapeuta;
  um CHECK exige exatamente uma das duas referências — RN-020.
- **Autoria:** referências a `user_tenant` preservam a participação histórica
  do autor, inclusive após inativação — RN-003 e RN-016.
- **Geração:** déficits pertencem a uma execução de geração; são registros
  separados das dívidas de reposição — RN-013.

Atualizar este modelo junto de alterações de tabelas, chaves ou cardinalidades.
A criação das tabelas não implementa os algoritmos e fluxos clínicos.
