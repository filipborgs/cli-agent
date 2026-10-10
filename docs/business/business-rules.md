# Regras de negócio

Referência: [visão de negócio](README.md) e
[fluxos operacionais](workflows.md). Regras aprovadas em 2026-10-09.

Os identificadores são referências estáveis para a implementação e os testes.

## Organização, acesso e recursos

### RN-001 — Isolamento por organização

Cada tenant possui uma ou mais clínicas. Dados e relacionamentos de uma
organização não podem ser consultados ou usados por outra organização.

### RN-002 — Cadastro único e participação nas clínicas

Paciente e terapeuta têm cadastro único por tenant. Podem participar de várias
clínicas da organização; os atendimentos devem ocorrer em clínicas habilitadas
para o vínculo e para os envolvidos. As salas pertencem a uma clínica.

### RN-003 — Acesso administrativo

Somente a equipe administrativa acessa o MVP. O usuário precisa estar autorizado
no tenant selecionado. Ser terapeuta ou paciente não cria uma identidade de
acesso nem uma autorização administrativa.

### RN-004 — Especialidades e salas

Um terapeuta pode ter várias especialidades. Uma sala pode comportar várias
especialidades. Cada sessão exige terapeuta habilitado e sala compatível com
a especialidade do atendimento.

## Plano de atendimento e rotina

### RN-005 — Vínculo fixo por especialidade

O plano é definido por paciente, terapeuta fixo e especialidade. O mesmo par
paciente–terapeuta pode ter planos de especialidades diferentes. Não pode haver
vigências sobrepostas para a mesma combinação paciente–terapeuta–especialidade.

### RN-006 — Frequência semanal

Cada vínculo tem uma quantidade positiva de atendimentos por semana, única no
tenant. Essa quantidade pode ser distribuída entre as clínicas habilitadas,
sem multiplicar a frequência a cada unidade.

### RN-007 — Duração

A clínica tem duração padrão. O vínculo pode definir uma duração específica,
que prevalece sobre o padrão. A duração deve ser positiva e a sessão guarda
o tempo efetivamente reservado; mudanças de configuração não alteram sessões
já marcadas automaticamente.

### RN-008 — Disponibilidade semanal

Paciente e terapeuta possuem janelas recorrentes de disponibilidade por clínica,
dia da semana e horário, com vigência. Pode haver várias janelas no mesmo dia.
Turnos precisam corresponder a intervalos concretos de horário.

### RN-009 — Horários fixos e vigência

A agenda prioriza manter os mesmos dias e horários toda semana. Disponibilidade
é uma possibilidade; o horário planejado é o compromisso escolhido para
repetição. Alterar uma sessão e alterar a rotina semanal são ações distintas.
A nova rotina precisa de vigência e não reescreve o histórico.

### RN-010 — Calendário mensal

A semana vai de segunda a domingo. A agenda mensal gera apenas as datas do mês,
sem proporcionalizar ou concentrar a frequência em semanas parciais. Uma rotina
de segunda e quarta gera as ocorrências desses dias que caem no mês. Os horários
seguem o fuso da clínica.

## Geração e ajustes da agenda

### RN-011 — Condições de agendamento

A geração considera vigência do vínculo, frequência, duração, clínica,
disponibilidade de ambos, funcionamento, bloqueios e sala compatível. Uma sessão
é individual e precisa caber integralmente nos intervalos permitidos.

### RN-012 — Sem conflitos de recursos

Paciente, terapeuta e sala não podem ter reservas simultâneas. Os conflitos de
paciente e terapeuta são verificados entre todas as clínicas do tenant. Uma
sessão pode começar quando outra termina. Encaixes manuais não podem ignorar
esses conflitos, inclusive quando dois usuários agendam ao mesmo tempo.

### RN-013 — Agenda parcial e pendências de geração

Se não for possível encaixar tudo, o sistema entrega a parte válida e informa
os atendimentos faltantes e os motivos, como ausência de horários em comum ou
de sala compatível disponível. Isso não gera uma pendência de reposição.

### RN-014 — Geração repetida e preservação dos ajustes

Gerar novamente o mês preserva registros existentes, ajustes e histórico,
tentando completar somente lacunas legítimas. Não pode duplicar sessões,
pendências ou tentativas. Uma sessão movida, cancelada ou com falta mantém sua
ocorrência de origem; seu horário antigo não é uma nova sessão devida.

### RN-015 — Encaixe combinado fora da disponibilidade habitual

A equipe pode autorizar uma sessão fora da disponibilidade habitual do paciente
e do terapeuta, registrando responsável e motivo, sem alterar a rotina semanal.
Funcionamento, bloqueios explícitos, compatibilidade da sala e conflitos
continuam obrigatórios. Um bloqueio incorreto precisa ser corrigido explicitamente.

### RN-016 — Histórico

Realização, cancelamento, falta, dispensa, reagendamento e decisão sobre
reposição precisam manter histórico, responsável, momento e motivo quando
aplicável. Sessões canceladas ou dispensadas liberam recursos sem serem excluídas.
Cadastros usados no histórico são inativados, não removidos.

## Fechamentos e ausências

### RN-017 — Feriados e recessos

A geração não cria sessões durante fechamentos da clínica. Os atendimentos
habituais atingidos são dispensados: não geram reposição, déficit de capacidade
ou obrigação de encaixe em outro dia da semana.

Se o fechamento for registrado depois da geração, sessões futuras atingidas
são dispensadas e deixam de reservar recursos, mantendo o histórico. Sessões
já realizadas não são reclassificadas retroativamente.

### RN-018 — Ausência do terapeuta

A falta do terapeuta gera reposição de atendimento marcado ou previsto em uma
rotina fixa. Isso também vale para ausência informada antes de gerar a agenda
mensal. Uma indisponibilidade sem atendimento previsto não cria reposição.

### RN-019 — Ausência do paciente

Quando o paciente avisa antes, a equipe decide se há direito à reposição,
sem prazo automático de antecedência. A decisão e seu responsável são registrados;
enquanto não houver decisão, o direito não pode ser presumido pelo gerador.
Falta sem aviso prévio, constatada no horário, não gera reposição.

### RN-020 — Bloqueios individuais

Uma indisponibilidade explícita do paciente ou terapeuta impede seu agendamento
em qualquer clínica do tenant naquele período. Os atendimentos atingidos são
tratados pelas RN-018 e RN-019. Se também houver fechamento da clínica, prevalece
a dispensa da RN-017: a coincidência com ausência individual não cria reposição.

## Reposições

### RN-021 — Origem e responsável pela reposição

A pendência mantém referência ao atendimento original e ao seu vínculo.
No MVP, a reposição mantém paciente, especialidade e terapeuta originais.
Pode acontecer em outra clínica habilitada dentro do mesmo tenant.

### RN-022 — Reposição é adicional à rotina

A reposição não substitui a frequência habitual da semana em que é realizada.
Inicialmente a equipe escolhe e agenda seu encaixe, com consulta dos horários
possíveis e as mesmas verificações de recursos.

### RN-023 — Reutilização de horário liberado

Uma reposição de qualquer especialidade pode ocupar um horário liberado por
outro atendimento, desde que seus próprios recursos sejam válidos. Isso não
troca a origem das pendências nem quita o atendimento que liberou o horário.

### RN-024 — Uma pendência, várias tentativas

Cada atendimento original gera no máximo uma pendência. Ela pode ter várias
tentativas históricas, no máximo uma tentativa agendada ativa e no máximo uma
realizada. Agendar não quita a pendência; realizar a reposição a quita.

Se a tentativa não acontecer e permanecer o direito a atendimento, reabre-se
a mesma pendência, sem criar outra. Os estados são pendente, agendada, realizada
e encerrada sem realização. O encerramento registra decisão e motivo da equipe.

### RN-025 — Falta e fechamento em tentativa de reposição

Falta do terapeuta reabre a mesma pendência. Aviso do paciente exige decisão da
equipe sobre nova tentativa. Falta do paciente sem aviso encerra a pendência
sem realização, com o motivo registrado.

Se feriado ou recesso atingir uma reposição já agendada, a tentativa é dispensada,
mas o direito anterior permanece: a mesma pendência volta a ficar aberta.
O fechamento não cria uma nova pendência.

### RN-026 — Pendências após encerramento ou inativação

Fim de vigência do vínculo ou inativação de cadastros/habilitações não apaga
pendências. Novos agendamentos exigem condições válidas na data pretendida.
A equipe precisa regularizar a situação ou encerrar a pendência com motivo,
mantendo seu histórico.
