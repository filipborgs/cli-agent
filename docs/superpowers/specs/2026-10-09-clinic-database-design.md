# Desenho do banco de dados para a agenda da clínica

Status: desenho aprovado em 2026-10-09, ainda sem implementação.

Representação visual: [diagramas de entidades, relacionamentos e reposições](../../architecture/clinic-database-diagrams.md).

Referência funcional: [documentação de negócio](../../business/README.md),
[regras de negócio](../../business/business-rules.md) e
[fluxos operacionais](../../business/workflows.md).

## 1. Intenção e contexto

O MVP ajuda a equipe administrativa a montar automaticamente a agenda mensal
de uma clínica, mantendo uma rotina semanal estável e permitindo ajustes,
registro de faltas e encaixe de reposições.

O projeto tem frontend React e API Python/FastAPI. Ainda não tem persistência,
autenticação, cadastros ou regras de agenda implementados. O web continua
consumindo a API somente por HTTP; a persistência pertence à API.

Embora o primeiro uso seja em uma clínica, o modelo precisa ser multi-tenant.
Um tenant representa uma organização com uma ou mais clínicas. Pacientes e
terapeutas têm cadastro único por organização e podem frequentar várias clínicas.

## 2. Regras confirmadas

- Inicialmente, apenas a equipe administrativa acessa a aplicação.
- Um paciente tem um ou mais terapeutas fixos, e um terapeuta tem vários pacientes.
- Um terapeuta pode ter várias especialidades e atender o mesmo paciente em
  especialidades diferentes, com frequência semanal própria para cada uma.
- Há duração padrão dos atendimentos e pode haver duração específica por vínculo.
- Pacientes e terapeutas têm disponibilidade habitual que se repete semanalmente.
- A agenda deve priorizar os mesmos dias e horários a cada semana.
- Salas comportam uma ou mais especialidades. No MVP, essa compatibilidade é
  suficiente; exigências de sala por sessão ficam para evolução futura.
- O gerador pode produzir agenda parcial e deve apresentar o que não conseguiu
  agendar e os motivos.
- Falta do terapeuta gera direito à reposição.
- Aviso prévio do paciente pode gerar direito à reposição, conforme decisão da
  equipe, sem prazo automático de antecedência.
- Falta do paciente no horário do atendimento, sem aviso prévio, não gera reposição.
- Feriado ou recesso da clínica dispensa as sessões atingidas, sem reposição e sem
  redistribuição obrigatória na semana.
- Gerar novamente um mês preserva os ajustes manuais e as sessões realizadas.
- Uma reposição de outra especialidade pode ocupar um horário liberado: cada
  pendência continua ligada ao atendimento que a originou.
- A equipe pode combinar uma sessão fora da disponibilidade habitual do paciente
  e do terapeuta, sem mudar a rotina semanal deles.
- No MVP, a reposição é realizada apenas pelo terapeuta original.
- A ausência antecipada do terapeuta gera reposição das sessões já marcadas ou
  previstas em uma rotina fixa, mesmo que a agenda mensal ainda não tenha sido
  gerada. Para ausências antecipadas do paciente, a equipe decide sobre o direito.
  Sem atendimento previsto, indisponibilidade por si só não cria reposição.
- A geração não cria sessões em feriados ou recessos. Se um fechamento atingir
  uma reposição já agendada, a pendência original permanece aberta para outro encaixe.
- O fim do vínculo ou a inativação dos cadastros preserva as pendências, mas impede
  novos agendamentos sem regularização das condições necessárias. A equipe pode
  encerrar uma pendência com motivo registrado.

## 3. Decisões aprovadas a partir das propostas do agente

As recomendações técnicas e os padrões de funcionamento abaixo foram propostos
pelo agente e aprovados pelo responsável pelo projeto junto com o desenho completo
em 2026-10-09.

- PostgreSQL como banco, SQLAlchemy para persistência e Alembic para migrações.
- Banco e esquema compartilhados, com `tenant_id` nas tabelas de negócio e
  isolamento reforçado por chaves estrangeiras compostas e políticas de acesso.
- Frequência semanal única por vínculo paciente–terapeuta–especialidade no tenant,
  podendo ser distribuída entre as clínicas habilitadas para esse vínculo.
- Semana de segunda a domingo; a geração mensal materializa somente as datas
  do mês, sem proporcionalizar a frequência em semanas parciais.
- Um fuso horário configurado por clínica. Horários semanais são locais;
  instantes de sessões e bloqueios são armazenados com fuso (`timestamptz`).
- Atendimentos individuais: uma sessão tem um paciente, um terapeuta e uma sala.
- Uma reposição é extra em relação à rotina da semana em que for realizada.
- Uma pendência permanece aberta quando uma tentativa de reposição não é realizada
  mas continua com direito a novo agendamento; não se cria outra pendência.
- O gerador automático respeita a disponibilidade habitual. Encaixes fora dela
  são uma ação manual com motivo registrado, sem permitir conflitos de ocupação.
- Regeneração é incremental: preserva todos os registros existentes e tenta
  completar lacunas legítimas, sem apagar ou reorganizar automaticamente o mês.
- A geração inicial de rotina é automática; o agendamento de reposições começa
  manual, com consulta dos horários possíveis. Automação de reposições poderá
  ser acrescentada sem mudar a separação entre sessão e pendência.

## 4. Modelo de dados aprovado

Nomes abaixo são conceituais; nomes físicos e índices serão definidos no plano.
Todas as entidades de negócio pertencem a um tenant, diretamente ou por vínculo
validado, sem relações entre organizações diferentes.

### Organização e acesso

- **Tenant:** organização, nome e estado ativo/inativo.
- **Clínica:** tenant, nome, fuso horário, duração padrão e estado ativo/inativo.
- **Usuário:** identidade de acesso, independente de paciente ou terapeuta.
- **Vínculo usuário–tenant:** associa usuário à organização, com perfil
  administrativo no MVP. A identidade pode participar de mais de um tenant;
  a API trabalha sempre com um tenant autorizado explicitamente selecionado.

A forma de autenticação não faz parte deste desenho de domínio; deverá ser
definida antes de disponibilizar endpoints de dados clínicos. O banco prepara
o vínculo de acesso, sem confundir usuário com terapeuta.

### Cadastros

- **Paciente:** tenant, nome e estado ativo/inativo. Outros dados cadastrais
  deverão ser definidos na etapa de cadastro; não presumir prontuário ou documentos.
- **Terapeuta:** tenant, nome e estado ativo/inativo.
- **Especialidade:** catálogo por tenant, nome e estado ativo/inativo.
- **Terapeuta–especialidade:** especialidades habilitadas para o terapeuta.
- **Paciente–clínica / terapeuta–clínica:** unidades em que a pessoa participa.
- **Sala:** clínica, nome e estado ativo/inativo.
- **Sala–especialidade:** compatibilidades da sala.

### Plano de atendimento e rotina

- **Vínculo de atendimento:** paciente, terapeuta, especialidade, quantidade de
  atendimentos por semana, duração específica opcional e período de vigência.
  A especialidade deve estar habilitada para o terapeuta.
- **Vínculo–clínica:** clínicas em que esse atendimento pode acontecer; ambos
  devem estar vinculados à clínica. No primeiro uso haverá apenas uma.
- **Disponibilidade do paciente / do terapeuta:** pessoa, clínica, dia da semana,
  hora inicial, hora final e vigência. Permite várias janelas no mesmo dia.
  Turnos são representados por janelas concretas de horário, não apenas rótulos.
- **Horário de funcionamento:** clínica, dia da semana e janelas de horário.
- **Horário semanal planejado:** vínculo, clínica, dia da semana, horário,
  duração, sala e vigência. Pode haver vários horários para cumprir a frequência.
  É o padrão escolhido para repetir semanalmente, distinto da disponibilidade.
- **Bloqueio de clínica:** intervalo de fechamento por feriado ou recesso e motivo.
- **Bloqueio de pessoa:** paciente ou terapeuta, intervalo e motivo. Como o cadastro
  é único, impede agendamento da pessoa em qualquer clínica no período.

As vigências preservam a rotina anterior quando houver mudanças. Não pode haver
planos de atendimento ativos sobrepostos para a mesma combinação
paciente–terapeuta–especialidade. Uma mudança de rotina não reescreve sessões
históricas nem altera silenciosamente sessões futuras já ajustadas.

### Agenda e execução

- **Agenda mensal:** clínica, mês de referência e histórico de geração.
- **Execução de geração:** agenda, momento, resultado e parâmetros relevantes.
- **Sessão:** vínculo de atendimento, clínica, sala, início, fim, origem
  (rotina ou reposição), horário semanal de origem quando aplicável, pendência de
  origem quando reposição, estado e metadados de ajuste manual.
- **Histórico de sessão:** alteração, valores relevantes anteriores e novos,
  usuário responsável, momento e motivo. Registra reagendamentos, presença,
  falta, dispensa e decisões sobre reposição.
- **Pendência de geração:** vínculo, semana/data esperada, quantidade faltante,
  motivo e execução de geração. É um resultado de planejamento, não uma dívida
  de reposição; deve ser recalculado/resolvido em novas gerações.

A sessão guarda a duração efetiva: mudar o padrão da clínica ou o vínculo não
altera a duração dos atendimentos já marcados. Estados conceituais: agendada,
realizada, cancelada, falta do paciente, falta do terapeuta e dispensada por
fechamento. A decisão sobre reposição é separada do estado da sessão.

Sessões realizadas, faltas e dispensas não são excluídas para liberar horário.
As regras de ocupação devem distinguir estados que reservam recursos de estados
cancelados ou dispensados, permitindo reutilizar um horário liberado.

Bloqueios antecipados de pessoa tratam as sessões já agendadas atingidas pelo
intervalo e as ocorrências de uma rotina fixa ainda não materializadas. A rotina
vigente identifica o atendimento previsto, sem inventar atendimentos para vínculos
que ainda não têm horário definido. A ocorrência atingida deve ter um registro
idempotente da ausência e da decisão sobre reposição, mesmo sem reserva ativa na
agenda. Ela será representada por uma sessão histórica de ausência, com o
horário originalmente previsto, mas sem reserva ativa de recursos. Isso mantém
a referência da pendência à sessão original e não pode depender de executar
primeiro a geração mensal.
Para o terapeuta, abre-se a pendência; para o paciente, a decisão fica aguardando
a equipe quando ainda não tiver sido registrada. Fechamentos da clínica prevalecem:
não havia atendimento devido em um feriado/recesso, portanto não se cria direito
à reposição por uma ausência individual coincidente.

### Reposições

- **Pendência de reposição:** sessão original, vínculo, motivo de origem,
  decisão da equipe quando necessária, responsável, momento e estado.
- **Tentativas de reposição:** são sessões vinculadas à mesma pendência; não
  precisam de um segundo cadastro de sessão.

Uma sessão original pode originar no máximo uma pendência. Uma pendência pode ter
várias tentativas históricas, no máximo uma tentativa agendada ativa e no máximo
uma tentativa realizada. Estados: pendente, agendada, realizada e encerrada sem
realização. Encerrar sem realizar exige decisão e motivo da equipe.

Se a tentativa é realizada, quita a pendência. Se houver falta do terapeuta ou
ausência do paciente com direito a nova tentativa, a mesma pendência reabre. Se
o paciente faltar à reposição sem aviso, ela encerra sem realização, conforme a
regra de ausência sem direito, também aprovada para as tentativas de reposição.

As tentativas mantêm paciente, terapeuta e especialidade do vínculo original.
Podem ocorrer em outra clínica habilitada no mesmo tenant. A pendência pertence
ao tenant e ao vínculo, mesmo que tenha sido originada em outra unidade.

Se um fechamento atingir uma tentativa já agendada, ela é dispensada e a mesma
pendência volta a ficar aberta, sem criar uma nova pendência. A geração nunca
agenda a tentativa em um fechamento já conhecido.

Fim de vigência do vínculo ou inativação de paciente, terapeuta ou habilitações
necessárias não elimina pendências. Novas tentativas exigem vínculo vigente,
cadastros ativos e habilitações válidas na data pretendida. Caso necessário, a
equipe regulariza esses dados antes do agendamento ou encerra a pendência com
motivo, preservando seu histórico.

## 5. Exemplo de funcionamento

1. Uma sessão de psicologia é cancelada pela falta do terapeuta.
2. O sistema mantém a sessão original e abre uma pendência de psicologia.
3. Uma pendência anterior de fono é selecionada pela equipe para o horário livre.
4. Uma nova sessão de fono é agendada com o fonoaudiólogo original e sala
   compatível, após validar os recursos e disponibilidades.
5. Realizar a sessão de fono quita somente a pendência de fono.
6. A pendência de psicologia continua aberta. A equipe pode marcá-la em outro
   horário habitual ou registrar um encaixe combinado fora da rotina.

O mesmo horário pode aparecer em sessões históricas canceladas e em uma nova
sessão ativa. Isso não representa conflito de ocupação.

## 6. Geração mensal e ajustes

O gerador usa vínculos vigentes, frequência, duração, clínicas habilitadas,
disponibilidades, funcionamento e salas compatíveis. Escolhe horários semanais
estáveis para vínculos sem padrão definido e materializa suas ocorrências no mês.
Uma proposta simples de encaixe determinístico é suficiente para o MVP; não há
promessa de solução ótima de todas as combinações.

Fechamentos impedem a geração de sessões nas datas/intervalos atingidos. As
ocorrências semanais suprimidas são explicadas pelo bloqueio de calendário, sem
criar uma sessão dispensada para cada horário que não chegou a ser agendado.
Se uma sessão futura já existir quando o fechamento for registrado, ela é
preservada no histórico como dispensada e deixa de ocupar recursos. Uma tentativa
de reposição assim dispensada reabre sua pendência original. Fechamentos não
geram novos direitos à reposição nem pendências de capacidade pelas ocorrências
habituais suprimidas. Sessões já realizadas não são reclassificadas retroativamente.

Reexecutar não duplica ocorrências, tentativas de reposição ou pendências.
Uma sessão de rotina movida manualmente mantém sua identificação de ocorrência
original: o horário antigo não se torna uma lacuna que o gerador preenche de novo.
Cancelamentos, faltas e dispensas também resolvem a ocorrência original; eventuais
atendimentos devidos são tratados pelo fluxo próprio de reposição.

Déficits reais são apresentados com motivos como falta de interseção de
disponibilidade, ausência de sala compatível ou ocupação dos recursos. A equipe
pode ajustar horários ou cadastrar condições faltantes e executar novamente.

Uma alteração pode mover somente uma sessão ou alterar o padrão semanal, por
ações distintas. Alterar o padrão exige informar a vigência; mudanças em sessões
futuras existentes devem ser explícitas. Reposições não contam como cumprimento
da frequência habitual de outra semana.

## 7. Integridade e concorrência

- IDs e chaves estrangeiras compostas com tenant impedem relações entre tenants.
- Referências à clínica validam seu tenant e a participação dos envolvidos.
- Valores positivos para duração e frequência; início sempre anterior ao fim.
- Intervalos de ocupação são semiabertos: uma sessão pode começar quando outra termina.
- Não há sobreposição de sessões que ocupam recursos para o mesmo paciente,
  terapeuta ou sala. Paciente e terapeuta são verificados entre todas as clínicas
  do tenant; a sala é específica da clínica.
- A sessão usa especialidade do vínculo, terapeuta habilitado e sala compatível.
- Exceção manual pode dispensar a disponibilidade habitual, mas não o funcionamento,
  os bloqueios explícitos, a compatibilidade de sala ou a ausência de conflitos.
  Se um bloqueio estava errado, a equipe precisa corrigi-lo explicitamente.
- Alterações de sessão, decisão de reposição e atualização da pendência são
  transacionais. Restrições de banco impedem dupla reserva concorrente.
- A implementação deve usar constraints de exclusão PostgreSQL para os intervalos
  dos recursos e unicidade para ocorrências e tentativas ativas, ou um mecanismo
  equivalente demonstravelmente seguro; detalhes ficam para o plano.
- Políticas de isolamento (RLS) complementam o filtro na API. O tenant é derivado
  do acesso autorizado, não aceito como permissão a partir do corpo da requisição.
- A configuração de tenant por transação e o papel usado pela API devem ser
  definidos para evitar vazamento por pool de conexões ou bypass de RLS.
- Cadastros referenciados são inativados em vez de excluídos. Histórico e relações
  de atendimento permanecem consultáveis.

## 8. Limites do MVP e evolução

O objetivo é agenda e seus dados operacionais, não prontuário, cobrança,
notificações, acesso de pacientes/terapeutas ou otimização matemática avançada.
O MVP não inclui atendimentos em grupo nem cálculo de deslocamento entre clínicas.

Exigência específica de sala por sessão poderá ser acrescentada à sessão/ao tipo
de atendimento. A compatibilidade atual por especialidade não deve ficar embutida
em nomes ou regras rígidas que impeçam essa extensão.

A infraestrutura multi-tenant e multi-clínica nasce agora, embora a primeira
configuração tenha uma organização e uma clínica. Regras de autenticação e campos
cadastrais adicionais precisam de desenho próprio quando essas entregas começarem.

## 9. O que fica para o plano de implementação

- Nomes físicos, tipos, índices e estratégia de IDs.
- Versões e configuração de PostgreSQL, SQLAlchemy e Alembic.
- DDL exato das constraints, RLS, migrações e teste de isolamento entre tenants.
- Mecanismo de integridade de especialidades, vínculos e bloqueios.
- Identidade idempotente das ocorrências da rotina e tratamento das vigências.
- Ordem determinística de encaixe e apresentação dos motivos de pendência.
- Contratos HTTP, DTOs, limites transacionais e divisão em entregas revisáveis.
- Testes de conflitos concorrentes, geração repetida, fechamentos, exceções manuais
  e ciclo de reposição, escritos antes de mudar comportamento.

O próximo passo é um plano de implementação baseado neste desenho aprovado e
nas regras de negócio documentadas.
