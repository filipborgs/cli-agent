# Fluxos operacionais e exemplos

Referências: [visão de negócio](README.md) e
[regras de negócio](business-rules.md). Os exemplos ilustram regras aprovadas;
horários e quantidades não são padrões obrigatórios da clínica.

## 1. Preparar os dados da clínica

1. Selecionar a organização autorizada e cadastrar a clínica.
2. Definir funcionamento, fuso, duração padrão, feriados e recessos conhecidos.
3. Cadastrar especialidades, salas e compatibilidades das salas.
4. Cadastrar pacientes e terapeutas, vinculando-os às clínicas em que participam.
5. Informar as especialidades de cada terapeuta.
6. Criar vínculos paciente–terapeuta–especialidade, com frequência semanal,
   duração específica quando necessária e vigência.
7. Registrar as disponibilidades semanais por clínica e bloqueios conhecidos.

Resultado: informações suficientes para buscar horários semanais compatíveis.
Regras: RN-001 a RN-011, RN-017 e RN-020.

## 2. Gerar e revisar a agenda mensal

1. A equipe seleciona a clínica e o mês.
2. O sistema utiliza horários semanais vigentes ou busca horários fixos para
   os vínculos ainda sem rotina definida.
3. Gera as sessões dentro do mês, respeitando recursos e calendário.
4. Não cria sessões em feriados ou recessos.
5. Apresenta a agenda válida e as pendências de geração com seus motivos.
6. A equipe ajusta sessões ou condições cadastrais e pode gerar novamente.

A nova geração preserva o que existe. Uma sessão movida manualmente não é
recriada no horário antigo. Alterar somente uma sessão não muda a rotina semanal.
Regras: RN-009 a RN-017.

### Exemplo: não há capacidade para todos os atendimentos

Um vínculo exige duas sessões por semana. Há apenas um horário comum entre
paciente, terapeuta e sala compatível. O sistema agenda a sessão possível e
apresenta a necessidade não atendida, sem criar uma dívida de reposição.

### Exemplo: semana dividida entre dois meses

Uma rotina tem sessões na segunda e quarta. A segunda está no último dia de
um mês, e a quarta no mês seguinte. Cada agenda contém sua própria ocorrência;
não se acrescenta outra sessão para completar artificialmente a semana.

## 3. Registrar ausência e decidir sobre reposição

1. A equipe identifica o atendimento atingido e registra a ausência.
2. Se for ausência do terapeuta, abre a pendência de reposição.
3. Se o paciente tiver avisado previamente, registra a decisão administrativa.
4. Se o paciente faltar sem aviso, registra a falta sem abrir reposição.
5. O atendimento original permanece no histórico e seu horário deixa de estar
   reservado quando for cancelado/desmarcado.

Ausência antecipada também alcança horários de uma rotina fixa ainda não
materializados no mês. O direito não depende de gerar a agenda primeiro.
Indisponibilidade sem sessão prevista não cria dívida. Regras: RN-016 a RN-021.

## 4. Encaixar e realizar uma reposição

1. A equipe seleciona uma pendência aberta.
2. Consulta horários do paciente, terapeuta original e salas compatíveis.
3. Escolhe um horário habitual ou registra um encaixe excepcional combinado.
4. O sistema valida os recursos, bloqueios, funcionamento e condições cadastrais.
5. Agenda uma tentativa ligada à pendência, sem dar a dívida como quitada.
6. Ao registrar a realização, quita a pendência.

Se a tentativa não acontecer, aplica-se o motivo: falta do terapeuta ou direito
a nova tentativa reabre a mesma pendência; falta do paciente sem aviso encerra
sem realização. Regras: RN-012, RN-015 e RN-021 a RN-026.

### Exemplo: fono ocupa o horário liberado pela psicologia

1. O psicólogo falta e deixa uma reposição de psicologia pendente.
2. O paciente já tinha uma reposição de fono pendente.
3. A equipe encontra o fonoaudiólogo original e uma sala compatível disponíveis
   no horário liberado.
4. Agenda e realiza a reposição de fono nesse horário.
5. A dívida de fono é quitada; a dívida de psicologia continua aberta.
6. A psicologia é reposta em outra data com o psicólogo original, inclusive
   fora da disponibilidade habitual se ambos combinarem e a equipe registrar.

### Exemplo: a reposição também não acontece

O terapeuta falta à tentativa de reposição. A tentativa permanece no histórico
e a mesma pendência volta a ficar aberta. O próximo encaixe não cria uma segunda
dívida pelo mesmo atendimento original.

## 5. Registrar feriado ou recesso

1. A equipe registra o fechamento da clínica com intervalo e motivo.
2. Novas gerações não criam sessões nesse intervalo.
3. Sessões futuras já marcadas são dispensadas, mantendo histórico e liberando recursos.
4. Sessões habituais atingidas não geram reposição ou déficit semanal.
5. Tentativas de reposição atingidas devolvem a pendência original ao estado aberto.

Regras: RN-017, RN-020 e RN-025.

### Exemplo: fechamento atinge dois tipos de sessão

Uma terça-feira tinha uma sessão habitual e uma tentativa de reposição de uma
ausência anterior. A clínica fecha por feriado: a sessão habitual é dispensada,
mas a dívida anterior continua existindo e precisa de novo encaixe. Nenhuma nova
pendência é criada pelo feriado.

## 6. Encerrar um vínculo ou inativar um cadastro

1. A equipe informa o fim de vigência ou a inativação necessária.
2. Os registros históricos e as pendências existentes permanecem consultáveis.
3. Pendências sem condições válidas ficam impedidas de receber novos agendamentos.
4. A equipe regulariza as condições ou encerra a pendência, registrando o motivo.

Regras: RN-016 e RN-026. Esse fluxo não determina automaticamente o destino de
sessões futuras já marcadas; elas devem ser revisadas explicitamente, preservando
as regras de histórico e ajustes.
