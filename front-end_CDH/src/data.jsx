/* Dados do Benchmark III (N=100, llama3.1:8b unificado, 29/04/2026). */

const RECENT_TASKS = [
  { id: 'PESQ_A4', task: 'O que está acontecendo no mundo da ciência?',                          mode: 'Baseline', status: 'success', duration: '19.3s', ago: 'há 2 min',  worker: 'PESQ', tokens: 5880, cycles: 0 },
  { id: 'ESC_B2',  task: 'Explique o conceito de recursão em programação com exemplo em Python', mode: 'CDH',      status: 'success', duration: '45.7s', ago: 'há 8 min',  worker: 'ESC',  tokens: 4520, cycles: 0 },
  { id: 'CALC_A2', task: 'Me ajude com matemática.',                                             mode: 'Baseline', status: 'failed',  duration: '8.5s',  ago: 'há 15 min', worker: 'CALC', tokens: 0,    cycles: 0 },
  { id: 'PESQ_M1', task: 'Principais avanços em LLMs em 2024 e impacto em IA generativa',        mode: 'CDH',      status: 'success', duration: '26.9s', ago: 'há 23 min', worker: 'PESQ', tokens: 980,  cycles: 0 },
  { id: 'ESC_M3',  task: 'Escreva um artigo de blog sobre o futuro da programação assistida por IA', mode: 'Baseline', status: 'running', duration: '—',  ago: 'agora',     worker: 'ESC',  tokens: 0,    cycles: 0 },
];

const HISTORY = [
  ...RECENT_TASKS.map((t, i) => ({ ...t, n: 100 - i, date: '29/04/2026' })),
  { n: 95, id: 'CALC_M1', task: 'Tenho R$5.000, invisto com juros compostos de 0.8% ao mês por 24 meses. Quanto terei?', mode: 'CDH',      worker: 'CALC', tokens: 848,  duration: '14.5s', cycles: 0, status: 'success', date: '29/04/2026' },
  { n: 94, id: 'PESQ_B6', task: 'Qual é a velocidade da luz no vácuo e em que unidade é medida?',                          mode: 'Baseline', worker: 'PESQ', tokens: 1498, duration: '7.5s',  cycles: 0, status: 'success', date: '29/04/2026' },
  { n: 93, id: 'CALC_A4', task: 'Quero saber quanto vai custar.',                                                          mode: 'Baseline', worker: 'CALC', tokens: 0,    duration: '11.6s', cycles: 0, status: 'failed',  date: '29/04/2026' },
];

const AGENT_LOG = [
  { t: '10:42:01', who: 'Supervisor', msg: 'analisando tarefa recebida — ambiguidade MÉDIA detectada', tone: 'text-text2' },
  { t: '10:42:03', who: 'CDH',        msg: 'desambiguando: escopo da pesquisa sobre LLMs em 2024',    tone: 'text-warning' },
  { t: '10:42:05', who: 'Supervisor', msg: 'instrução gerada → delegando para worker PESQ',             tone: 'text-primary-2' },
  { t: '10:42:08', who: 'PESQ',       msg: 'processando instrução focalizada do Supervisor',           tone: 'text-text2' },
  { t: '10:42:19', who: 'PESQ',       msg: 'resposta gerada — 980 tokens (concisa)',                   tone: 'text-success' },
  { t: '10:42:21', who: 'Supervisor', msg: 'resposta satisfatória — emitindo FINALIZAR',               tone: 'text-text2' },
  { t: '10:42:22', who: 'CDH',        msg: 'tarefa concluída — latência total: 26.9s',                 tone: 'text-success' },
];

const AGENTS = [
  { name: 'Supervisor', model: 'llama3.1:8b', role: 'Orquestrador', state: 'working', cycles: 1, last: 'agora',     desc: 'Gerencia desambiguação e delegação' },
  { name: 'PESQ',       model: 'llama3.1:8b', role: 'Pesquisa',     state: 'working', cycles: 0, last: 'há 2s',     desc: 'Busca web e síntese de fontes' },
  { name: 'CALC',       model: 'llama3.1:8b', role: 'Cálculo',      state: 'idle',    cycles: 0, last: 'há 14 min', desc: 'Execução numérica e expressões' },
  { name: 'ESC',        model: 'llama3.1:8b', role: 'Escrita',      state: 'idle',    cycles: 0, last: 'há 45 min', desc: 'Geração de texto formatado' },
];

/* Tokens totais por categoria — N=17 PESQ, N=17 CALC, N=16 ESC */
const TOKEN_BREAKDOWN = [
  { category: 'PESQ', cdh: 10625, baseline: 35139, deltaPct: '-70%' },
  { category: 'CALC', cdh:  6970, baseline:  4641, deltaPct: '+50%' },
  { category: 'ESC',  cdh: 15008, baseline: 22032, deltaPct: '-32%' },
];

/* Top 5 tarefas por tokens (Benchmark III) */
const TOP_TOKEN_TASKS = [
  { id: 'PESQ_A4', task: 'O que está acontecendo no mundo da ciência?',                               cat: 'PESQ', mode: 'Baseline', tokens: 5880, latency: '19.3s', status: 'success' },
  { id: 'PESQ_A3', task: 'Preciso saber mais sobre tecnologia.',                                      cat: 'PESQ', mode: 'Baseline', tokens: 4597, latency: '17.1s', status: 'success' },
  { id: 'ESC_B2',  task: 'Explique recursão em programação com exemplo funcional em Python',          cat: 'ESC',  mode: 'CDH',      tokens: 4520, latency: '45.7s', status: 'success' },
  { id: 'PESQ_A1', task: 'Me ajude com meu projeto de pesquisa sobre IA.',                           cat: 'PESQ', mode: 'Baseline', tokens: 4247, latency: '16.2s', status: 'success' },
  { id: 'ESC_M3',  task: 'Artigo de blog técnico sobre o futuro da programação assistida por IA',    cat: 'ESC',  mode: 'Baseline', tokens: 3519, latency: '24.5s', status: 'success' },
];

const CYCLE_DETAIL_LOG = [
  '[10:42:01] Supervisor → recebendo tarefa do usuário',
  '[10:42:02] Supervisor → tokens de entrada: 142',
  '[10:42:03] CDH → analisando ambiguidade — complexidade: 6/10',
  '[10:42:04] Supervisor → engenheirando instrução focalizada para PESQ',
  '[10:42:05] Supervisor → delegando para worker PESQ com instrução otimizada',
  '[10:42:08] PESQ → processando com llama3.1:8b (temperature=0)',
  '[10:42:19] PESQ → resposta gerada | tokens: 980 | sem tool calls',
  '[10:42:20] Supervisor → avaliando resposta do Worker',
  '[10:42:21] Supervisor → tokens de saída: 980 | total worker: 980',
  '[10:42:22] DONE → status=success | latency=26.9s | cycles=0',
];

/* Tool calls (ilustrativo — llama3.1:8b usa ferramentas raramente) */
const TOOL_CALLS = [
  { t: '10:44:12', worker: 'PESQ', tool: 'busca_web',  args: 'query="energias renováveis Brasil 2024"', result: '2 resultados · 2.1s', status: 'ok' },
  { t: '10:44:15', worker: 'CALC', tool: 'calcular',   args: 'expressao="5000*(1.008**24)"',           result: '6220.79',              status: 'ok' },
  { t: '10:44:28', worker: 'PESQ', tool: 'busca_web',  args: 'query="LLM multi-agent 2025 survey"',   result: '3 resultados · 1.8s',  status: 'ok' },
];

/* Falhas reais do Baseline no Benchmark III (todas recursion limit) */
const RECURSION_FAILURES = [
  { id: 'CALC_A1', task: 'Preciso fazer alguns cálculos financeiros para o meu negócio.', mode: 'Baseline', worker: 'CALC', recursion: 20, tokensWasted: 0, date: '29/04/2026' },
  { id: 'CALC_A2', task: 'Me ajude com matemática.',                                       mode: 'Baseline', worker: 'CALC', recursion: 20, tokensWasted: 0, date: '29/04/2026' },
  { id: 'CALC_A4', task: 'Quero saber quanto vai custar.',                                 mode: 'Baseline', worker: 'CALC', recursion: 20, tokensWasted: 0, date: '29/04/2026' },
  { id: 'CALC_A5', task: 'Faz as contas para mim.',                                        mode: 'Baseline', worker: 'CALC', recursion: 20, tokensWasted: 0, date: '29/04/2026' },
  { id: 'PESQ_A2', task: 'Pesquise sobre isso para mim.',                                  mode: 'Baseline', worker: 'PESQ', recursion: 20, tokensWasted: 0, date: '29/04/2026' },
  { id: 'ESC_B5',  task: 'Parágrafo introdutório para artigo sobre CNNs em detecção de objetos.', mode: 'Baseline', worker: 'ESC', recursion: 20, tokensWasted: 0, date: '29/04/2026' },
];

/* Sucesso/falha por categoria — N=17 PESQ, N=17 CALC, N=16 ESC */
const CATEGORY_BREAKDOWN = [
  { category: 'PESQ', cdh: { success: 16, failed: 1 }, baseline: { success: 16, failed: 1 } },
  { category: 'CALC', cdh: { success: 15, failed: 2 }, baseline: { success: 13, failed: 4 } },
  { category: 'ESC',  cdh: { success: 16, failed: 0 }, baseline: { success: 15, failed: 1 } },
];

/* Comparações A/B — mesma tarefa em CDH vs Baseline */
const AB_COMPARISONS = [
  {
    id: 'AB-01',
    task: 'Quais são os principais avanços em LLMs em 2024 e como impactam IA generativa?',
    category: 'PESQ',
    cdh:      { status: 'success', latency: '26.9s', tokens:  980, cycles: 0, react: 0, recursion: false, response: 'PESQ_M1' },
    baseline: { status: 'success', latency: '18.5s', tokens: 2781, cycles: 0, react: 0, recursion: false, response: null },
  },
  {
    id: 'AB-02',
    task: 'Pesquise sobre isso para mim.',
    category: 'PESQ',
    cdh:      { status: 'success', latency: '12.3s', tokens: 487, cycles: 0, react: 0, recursion: false, response: null },
    baseline: { status: 'failed',  latency: '10.8s', tokens:   0, cycles: 0, react: 20, recursion: true,  response: 'PESQ_A2' },
  },
  {
    id: 'AB-03',
    task: 'Explique o conceito de recursão em programação, incluindo um exemplo funcional em Python com fatorial.',
    category: 'ESC',
    cdh:      { status: 'success', latency: '45.7s', tokens: 4520, cycles: 0, react: 0, recursion: false, response: 'ESC_B2' },
    baseline: { status: 'success', latency: '17.5s', tokens: 2268, cycles: 0, react: 0, recursion: false, response: null },
  },
];

const CLARIFICATION_TEMPLATES = {
  pesq: {
    question: 'Para refinar a busca, você prefere fontes acadêmicas (papers, arXiv) ou fontes amplas (blogs técnicos, documentação)?',
    options:  ['Apenas fontes acadêmicas', 'Apenas fontes amplas', 'Ambos os tipos'],
  },
  calc: {
    question: 'Você gostaria de ver o passo-a-passo do cálculo ou apenas o resultado final?',
    options:  ['Passo-a-passo completo', 'Apenas o resultado', 'Resultado + breve justificativa'],
  },
  esc: {
    question: 'Qual o tom desejado para a redação?',
    options:  ['Acadêmico formal', 'Didático e acessível', 'Conciso e técnico'],
  },
  generic: {
    question: 'Detectei ambiguidade no escopo. Qual destas interpretações se aproxima mais da sua intenção?',
    options:  ['Foco em profundidade técnica', 'Foco em síntese e visão geral', 'Foco em comparativo prático'],
  },
};

const inferTaskCategory = (text = '') => {
  const t = text.toLowerCase();
  if (/(buscar|pesquis|fonte|referên|artigo|paper)/.test(t)) return 'pesq';
  if (/(calcul|raiz|integr|deriv|equa|código|algoritmo)/.test(t)) return 'calc';
  if (/(escrever|resumir|redigir|introdu|conclus|texto)/.test(t)) return 'esc';
  return 'generic';
};

/* Desempenho por nível de ambiguidade — Benchmark III (N=50 tarefas, 100 execuções) */
const AMB_BREAKDOWN = [
  {
    level: 'BAIXA', n: 17,
    cdh:      { success: 16, rate: 94,  tokens: 696,  tokStd: 1008 },
    baseline: { success: 16, rate: 94,  tokens: 736,  tokStd: 737  },
  },
  {
    level: 'MÉDIA', n: 18,
    cdh:      { success: 18, rate: 100, tokens: 709,  tokStd: 262  },
    baseline: { success: 18, rate: 100, tokens: 1549, tokStd: 1119 },
  },
  {
    level: 'ALTA',  n: 15,
    cdh:      { success: 13, rate: 87,  tokens: 535,  tokStd: 335  },
    baseline: { success: 10, rate: 67,  tokens: 1427, tokStd: 1928 },
  },
];

Object.assign(window, {
  RECENT_TASKS, HISTORY, AGENT_LOG, AGENTS,
  TOKEN_BREAKDOWN, TOP_TOKEN_TASKS, CYCLE_DETAIL_LOG,
  TOOL_CALLS, RECURSION_FAILURES, CATEGORY_BREAKDOWN,
  AB_COMPARISONS, CLARIFICATION_TEMPLATES, inferTaskCategory,
  AMB_BREAKDOWN,
});
