# Negócio: agenda de atendimentos da clínica

Status: definição inicial aprovada em 2026-10-09. Funcionalidades ainda não implementadas.

## Objetivo

Montar automaticamente a agenda mensal da clínica a partir dos atendimentos
semanais de cada paciente, conciliando a disponibilidade dos pacientes e
terapeutas com as salas adequadas. A equipe administrativa poderá ajustar a
agenda e acompanhar faltas e reposições sem perder o histórico.

O resultado esperado é uma rotina semanal estável, sem reservas conflitantes,
com indicação clara dos atendimentos que não puderam ser encaixados e das
reposições que ainda precisam acontecer.

## Como ler esta documentação

- [Regras de negócio](business-rules.md): regras identificadas para referência
  em requisitos, testes e entregas.
- [Fluxos e exemplos](workflows.md): operação da clínica e situações concretas.
- [Desenho do banco](../superpowers/specs/2026-10-09-clinic-database-design.md):
  tradução dessas regras para o modelo de dados e decisões técnicas.
- [Diagramas do banco](../architecture/clinic-database-diagrams.md): visão geral,
  entidades, relacionamentos e ciclo de reposição.

Esta pasta é a referência funcional do projeto. O desenho técnico detalha como
preservar as regras no banco. Novas decisões devem atualizar os documentos
afetados juntos, sem tratar funcionalidades planejadas como já entregues.

## Organização e usuários

O primeiro uso terá uma organização e uma clínica. A estrutura admite vários
tenants, cada um com uma ou mais clínicas, mantendo os dados das organizações
isolados. Pacientes e terapeutas têm cadastro único no tenant e podem participar
de várias clínicas da mesma organização.

No MVP, somente usuários administrativos acessam o sistema. Eles cadastram os
recursos, definem os atendimentos, geram a agenda, fazem ajustes e registram os
resultados e as decisões sobre reposição. Um usuário pode estar autorizado em
mais de um tenant, trabalhando no contexto de uma organização por vez.

## Escopo funcional do MVP

- Cadastros de clínicas, pacientes, terapeutas, especialidades e salas.
- Vínculos fixos paciente–terapeuta–especialidade, frequência semanal e duração.
- Disponibilidades semanais, funcionamento e bloqueios de calendário.
- Definição e repetição de horários semanais na agenda mensal.
- Geração parcial com motivos dos atendimentos não encaixados.
- Ajustes manuais e encaixes combinados fora da disponibilidade habitual.
- Registro de realização, cancelamento, falta e dispensa por fechamento.
- Decisão administrativa sobre reposição por aviso prévio do paciente.
- Controle de pendências e de tentativas de reposição com o terapeuta original.
- Preservação do histórico e prevenção de conflitos entre clínicas do tenant.

A rotina será gerada automaticamente. Inicialmente, a equipe agenda as
reposições manualmente, consultando os horários possíveis.

## Vocabulário do domínio

| Conceito | Significado |
| --- | --- |
| Tenant / organização | Grupo proprietário dos dados, que reúne uma ou mais clínicas. |
| Clínica | Unidade com salas, funcionamento, calendário e agenda próprios. |
| Especialidade | Área do atendimento, habilitada para terapeutas e salas. |
| Vínculo de atendimento | Combinação paciente, terapeuta e especialidade, com frequência, duração e vigência. |
| Frequência semanal | Quantidade habitual de sessões por semana de um vínculo. |
| Disponibilidade habitual | Janelas semanais em que a pessoa pode estar em uma clínica; não são reservas. |
| Horário semanal planejado | Dia, horário, clínica e sala escolhidos para repetir um atendimento. |
| Vigência | Período em que um vínculo ou uma configuração semanal vale. |
| Sessão | Atendimento individual com data, horário, paciente, terapeuta, especialidade e sala. |
| Agenda mensal | Conjunto de sessões de uma clínica referentes a um mês. |
| Bloqueio | Intervalo de fechamento da clínica ou indisponibilidade explícita de uma pessoa. |
| Ajuste pontual | Mudança de uma sessão que não altera a rotina das demais semanas. |
| Pendência de geração | Atendimento que o gerador não conseguiu encaixar; não é reposição. |
| Pendência de reposição | Atendimento devido por uma ausência com direito à reposição. |
| Tentativa de reposição | Sessão marcada para quitar uma pendência; só a realização a quita. |
| Dispensa | Atendimento habitual que deixa de ser devido por fechamento da clínica. |

## Limites e evolução

O MVP trata atendimentos individuais, com um paciente, um terapeuta e uma sala.
Prontuário, cobrança, notificações, atendimentos em grupo, acesso de pacientes ou
terapeutas e cálculo de deslocamento entre clínicas não integram este escopo.
O gerador não promete encontrar uma solução matematicamente ótima.

A compatibilidade das salas será definida por especialidade. A exigência de
uma sala específica por sessão é uma evolução reconhecida, ainda não incluída.
O agendamento automático de reposições também poderá ser acrescentado depois.

Campos cadastrais adicionais e o mecanismo de autenticação serão detalhados nas
entregas correspondentes. Não foram definidos valores numéricos de duração
padrão nem limites gerais de frequência: são dados de configuração.

## Decisões e manutenção

As regras foram levantadas e o desenho completo aprovado com o responsável pelo
projeto em 2026-10-09. Os padrões operacionais inicialmente propostos pelo agente
e aprovados estão incorporados às regras, incluindo semana de segunda a domingo,
frequência única por vínculo e tratamento de falta à própria reposição.

Mudanças futuras devem indicar a regra afetada, a nova decisão e o impacto nos
fluxos, no desenho técnico e nos testes. Uma regra alterada não deve reescrever
silenciosamente o histórico dos atendimentos.
