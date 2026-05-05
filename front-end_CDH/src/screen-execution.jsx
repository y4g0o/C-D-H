/* Execution screen — animated progress between submit and graph view. */

const EXEC_STEPS_CDH = [
  { t: 600,  label: 'Supervisor analisando entrada',           tag: 'Supervisor' },
  { t: 1100, label: 'Ciclo CDH 1 — desambiguação aplicada',    tag: 'CDH' },
  { t: 1700, label: 'Roteamento determinado · delegando',      tag: 'Supervisor' },
  { t: 2400, label: 'Worker executando · react step 1/4',      tag: 'Worker' },
  { t: 3200, label: 'Tool call · web_search retornado',        tag: 'Tool' },
  { t: 3900, label: 'Worker compilando observação final',      tag: 'Worker' },
  { t: 4600, label: 'Supervisor sintetizando resposta',        tag: 'Supervisor' },
  { t: 5200, label: 'Concluído',                               tag: 'Done' },
];

const TAG_TONE = {
  Supervisor: 'text-primary-2',
  CDH:        'text-warning',
  Worker:     'text-sky-400',
  Tool:       'text-fuchsia-400',
  Done:       'text-success',
};

const ExecutionScreen = ({ taskText, mode, onComplete, onCancel }) => {
  const [now, setNow] = React.useState(0);
  const [aborted, setAborted] = React.useState(false);
  const startRef = React.useRef(Date.now());

  React.useEffect(() => {
    if (aborted) return;
    let raf;
    const tick = () => {
      const elapsed = Date.now() - startRef.current;
      setNow(elapsed);
      if (elapsed < EXEC_STEPS_CDH[EXEC_STEPS_CDH.length - 1].t + 600) {
        raf = requestAnimationFrame(tick);
      } else {
        onComplete && onComplete();
      }
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [aborted]);

  const total = EXEC_STEPS_CDH[EXEC_STEPS_CDH.length - 1].t;
  const pct = Math.min(100, (now / total) * 100);
  const currentIdx = EXEC_STEPS_CDH.findIndex((s) => s.t > now);
  const liveIdx = currentIdx === -1 ? EXEC_STEPS_CDH.length - 1 : Math.max(0, currentIdx - 1);

  const tokensSoFar = Math.floor((now / total) * 3120);
  const reactSteps = Math.min(4, Math.floor((now / total) * 5));

  return (
    <div className="screen-enter max-w-[920px] mx-auto">
      <PageHeader
        eyebrow="Em andamento"
        title="Executando tarefa"
        subtitle="Acompanhe o ciclo em tempo real. A interface do grafo abre quando concluir."
        action={
          <Button variant="outline" size="sm" icon={IconStop} onClick={() => { setAborted(true); onCancel && onCancel(); }}>
            Abortar
          </Button>
        }
      />

      <Card className="mb-4">
        <div className="flex items-start gap-4">
          <div className="relative h-14 w-14 shrink-0">
            <svg viewBox="0 0 56 56" className="h-14 w-14 -rotate-90">
              <circle cx="28" cy="28" r="24" stroke="#293548" strokeWidth="4" fill="none" />
              <circle
                cx="28" cy="28" r="24"
                stroke="url(#execGrad)" strokeWidth="4" fill="none"
                strokeDasharray={2 * Math.PI * 24}
                strokeDashoffset={(1 - pct / 100) * 2 * Math.PI * 24}
                strokeLinecap="round"
                style={{ transition: 'stroke-dashoffset 200ms linear' }}
              />
              <defs>
                <linearGradient id="execGrad" x1="0" x2="1" y1="0" y2="1">
                  <stop offset="0%" stopColor="#6366F1" />
                  <stop offset="100%" stopColor="#818CF8" />
                </linearGradient>
              </defs>
            </svg>
            <span className="absolute inset-0 flex items-center justify-center font-mono text-[11px] text-text1 font-semibold">
              {Math.round(pct)}%
            </span>
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <ModeBadge mode={mode} />
              <span className="text-[11px] text-text3 font-mono">cycle {mode === 'CDH' ? '1/3' : '—'}</span>
              <Tag tone="warning"><span className="dot-pulse">●</span> live</Tag>
            </div>
            <div className="text-[14px] text-text1 leading-snug truncate font-medium">{taskText || 'Tarefa em execução…'}</div>
            <div className="text-[12px] text-text3 mt-0.5 truncate font-mono">
              {EXEC_STEPS_CDH[liveIdx]?.label}
            </div>
          </div>
          <div className="hidden sm:grid grid-cols-3 gap-5 text-right">
            <div>
              <div className="text-[10px] uppercase tracking-wider text-text3">Elapsed</div>
              <div className="font-mono text-[15px] text-text1 font-semibold">{(now / 1000).toFixed(1)}s</div>
            </div>
            <div>
              <div className="text-[10px] uppercase tracking-wider text-text3">Tokens</div>
              <div className="font-mono text-[15px] text-primary-2 font-semibold">{tokensSoFar.toLocaleString('pt-BR')}</div>
            </div>
            <div>
              <div className="text-[10px] uppercase tracking-wider text-text3">React</div>
              <div className="font-mono text-[15px] text-warning font-semibold">{reactSteps}/10</div>
            </div>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Timeline */}
        <Card>
          <SectionTitle title="Linha do tempo do ciclo" icon={IconClock} />
          <div className="space-y-0.5">
            {EXEC_STEPS_CDH.map((s, i) => {
              const passed = now >= s.t;
              const isLive = i === liveIdx && now < total;
              return (
                <div key={i} className={`flex items-center gap-3 py-2 transition-opacity ${passed ? 'opacity-100' : 'opacity-45'}`}>
                  <span className={`h-5 w-5 rounded-full flex items-center justify-center shrink-0 ${
                    passed && !isLive ? 'bg-success/20 text-success ring-1 ring-inset ring-success/30' :
                    isLive            ? 'bg-primary/15 ring-2 ring-primary text-primary-2 dot-pulse' :
                                        'bg-surface2 text-text3 ring-1 ring-inset ring-white/5'
                  }`}>
                    {passed && !isLive ? <IconCheck size={11} /> : <span className="h-1.5 w-1.5 rounded-full bg-current" />}
                  </span>
                  <span className={`text-[13px] flex-1 ${passed ? 'text-text1' : 'text-text2'}`}>{s.label}</span>
                  <span className={`font-mono text-[10px] ${TAG_TONE[s.tag] || 'text-text3'}`}>{s.tag}</span>
                </div>
              );
            })}
          </div>
        </Card>

        {/* Live log preview */}
        <Card padded={false}>
          <div className="px-5 pt-5 pb-3 flex items-center justify-between border-b border-white/5">
            <h2 className="text-[15px] font-semibold tracking-tight text-text1">Log ao vivo</h2>
            <Tag tone="warning">stream</Tag>
          </div>
          <div className="px-5 py-3 font-mono text-[12px] leading-relaxed max-h-[320px] overflow-auto">
            {AGENT_LOG.slice(0, Math.max(2, Math.floor((now / total) * AGENT_LOG.length))).map((l, i) => (
              <div key={i} className="flex gap-2 py-0.5">
                <span className="text-text3 shrink-0">[{l.t}]</span>
                <span className={`${l.tone} font-semibold shrink-0`}>{l.who}</span>
                <span className="text-text3">›</span>
                <span className="text-text2">{l.msg}</span>
              </div>
            ))}
            {now < total && (
              <div className="flex items-center gap-2 py-1.5">
                <span className="text-text3">»</span>
                <span className="text-text2 italic">processando…</span>
                <span className="inline-block h-3 w-1.5 bg-primary-2 animate-pulse" />
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
};

Object.assign(window, { ExecutionScreen });
