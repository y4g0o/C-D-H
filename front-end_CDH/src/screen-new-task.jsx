/* Screen 2 — Submit New Task */

const NewTaskScreen = ({ onNavigate, setExecPayload }) => {
  const [mode, setMode] = React.useState('CDH');
  const [task, setTask] = React.useState('');
  const [supModel, setSupModel] = React.useState('llama3.1:8b');
  const [wkrModel, setWkrModel] = React.useState('qwen2.5-coder:7b');
  const [submitting, setSubmitting] = React.useState(false);
  const [showClarif, setShowClarif] = React.useState(false);

  const exampleClick = (txt) => setTask(txt);

  const submit = (e) => {
    e.preventDefault();
    if (!task.trim()) return;
    if (mode === 'CDH') {
      setShowClarif(true);
      return;
    }
    runTask(null);
  };

  const runTask = (clarification) => {
    setSubmitting(true);
    setTimeout(() => {
      setSubmitting(false);
      setShowClarif(false);
      if (setExecPayload) setExecPayload({ task, mode, supModel, wkrModel, clarification });
      onNavigate('execution');
    }, 350);
  };

  return (
    <div className="screen-enter max-w-[860px] mx-auto">
      <PageHeader
        eyebrow="Execução"
        title="Nova Tarefa"
        subtitle="Envie uma instrução em linguagem natural. Escolha o modo de execução e os modelos."
      />

      <Card>
        <form onSubmit={submit} className="space-y-6">
          <div>
            <label className="block text-[12px] uppercase tracking-wider text-text3 font-medium mb-2">
              Descrição da tarefa
            </label>
            <Textarea
              value={task}
              onChange={(e) => setTask(e.target.value)}
              placeholder="Descreva sua tarefa..."
              rows={5}
            />
            <div className="mt-3 flex flex-wrap gap-2">
              <span className="text-[11px] text-text3 self-center mr-1">Exemplos:</span>
              {[
                'Calcular a raiz quadrada de 2048 e explicar o método.',
                'Escrever um resumo sobre LangGraph.',
                'Buscar artigos recentes sobre arquiteturas multi-agente.',
              ].map((ex) => (
                <button
                  key={ex}
                  type="button"
                  onClick={() => exampleClick(ex)}
                  className="text-[11px] text-text2 hover:text-text1 bg-surface2/60 hover:bg-surface2 px-2.5 py-1 rounded-md ring-1 ring-inset ring-white/5 transition"
                >
                  “{ex.length > 48 ? ex.slice(0, 48) + '…' : ex}”
                </button>
              ))}
            </div>
          </div>

          {/* Mode selector */}
          <div>
            <label className="block text-[12px] uppercase tracking-wider text-text3 font-medium mb-2">
              Modo de execução
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {[
                { id: 'CDH',      title: 'Modo CDH',      desc: 'Ciclo de desambiguação ativo — maior precisão',     tag: 'Recomendado', icon: IconBolt },
                { id: 'Baseline', title: 'Modo Baseline', desc: 'Execução direta — mais rápido, sem desambiguação',  tag: 'Comparativo', icon: IconArrowRight },
              ].map((opt) => {
                const active = mode === opt.id;
                const Icon = opt.icon;
                return (
                  <button
                    key={opt.id}
                    type="button"
                    onClick={() => setMode(opt.id)}
                    className={`relative text-left p-4 rounded-md transition-all ${
                      active
                        ? 'bg-primary/10 ring-2 ring-primary shadow-glow-primary'
                        : 'bg-surface2/40 ring-1 ring-inset ring-white/5 hover:bg-surface2/70'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <div className={`h-7 w-7 rounded-md flex items-center justify-center ${active ? 'bg-primary text-white' : 'bg-surface text-text2'}`}>
                          <Icon size={14} />
                        </div>
                        <span className={`text-[15px] font-semibold ${active ? 'text-text1' : 'text-text1'}`}>{opt.title}</span>
                      </div>
                      <Tag tone={active ? 'primary' : 'default'}>{opt.tag}</Tag>
                    </div>
                    <p className="text-[12.5px] text-text2 leading-snug">{opt.desc}</p>
                    {active && (
                      <div className="absolute top-3 right-3 h-4 w-4 rounded-full bg-primary text-white flex items-center justify-center">
                        <IconCheck size={10} />
                      </div>
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Model row */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-[12px] uppercase tracking-wider text-text3 font-medium mb-2">
                Modelo do Supervisor
              </label>
              <Select
                value={supModel}
                onChange={(e) => setSupModel(e.target.value)}
                options={[
                  { value: 'llama3.1:8b', label: 'llama3.1:8b   (padrão)' },
                  { value: 'llama3.2:3b', label: 'llama3.2:3b   (rápido)' },
                  { value: 'mistral:7b',  label: 'mistral:7b' },
                ]}
              />
            </div>
            <div>
              <label className="block text-[12px] uppercase tracking-wider text-text3 font-medium mb-2">
                Modelo dos Workers
              </label>
              <Select
                value={wkrModel}
                onChange={(e) => setWkrModel(e.target.value)}
                options={[
                  { value: 'qwen2.5-coder:7b', label: 'qwen2.5-coder:7b   (padrão)' },
                  { value: 'codellama:7b',     label: 'codellama:7b' },
                  { value: 'llama3.1:8b',      label: 'llama3.1:8b' },
                ]}
              />
            </div>
          </div>

          {/* Submit */}
          <Button
            type="submit"
            size="lg"
            className="w-full"
            iconRight={IconArrowRight}
            disabled={!task.trim() || submitting}
          >
            {submitting ? 'Enviando…' : 'Executar Tarefa'}
          </Button>
        </form>
      </Card>

      <ClarificationDialog
        open={showClarif}
        taskText={task}
        mode={mode}
        onCancel={() => setShowClarif(false)}
        onConfirm={(payload) => runTask(payload)}
      />

      {/* Last 3 tasks */}
      <div className="mt-8">
        <SectionTitle icon={IconClock} title="Últimas 3 execuções" />
        <Card padded={false}>
          <ul className="divide-y divide-white/[0.04]">
            {RECENT_TASKS.slice(0, 3).map((t) => (
              <li key={t.id} className="px-5 py-3 flex items-center gap-3 hover:bg-white/[0.025] transition">
                <span className="font-mono text-[11px] text-text3 w-14">{t.id}</span>
                <span className="flex-1 text-[13px] text-text1 truncate">{t.task}</span>
                <ModeBadge mode={t.mode} />
                <StatusBadge status={t.status} />
                <span className="text-[11px] text-text3 w-16 text-right">{t.ago}</span>
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </div>
  );
};

Object.assign(window, { NewTaskScreen });
