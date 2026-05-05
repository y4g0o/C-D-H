#!/usr/bin/env python3
"""
Benchmark v2 — CDH vs Baseline vs CoT-Baseline com ferramentas reais.

Métricas por execução:
- latencia_s: tempo total de wall clock
- tokens_total: soma de usage_metadata.total_tokens de todos os AIMessages no estado final
- ciclos_react: acumulado via operator.add no estado (cada tool_call = 1 ciclo)
- proximo_final: último valor de 'proximo' (FINALIZAR esperado)
- sucesso: True se não lançou exceção e proximo == FINALIZAR
- resposta: último AIMessage do Worker (filtrado por name != "Supervisor")
- instrucao_cdh: instrução gerada pelo Supervisor CDH/CoT (extraída do conteúdo)

Uso:
  python3 benchmark_v2.py                      # roda todas as 100 tarefas (200-300 execuções)
  python3 benchmark_v2.py --sample             # roda tasks_sample.json (45 tarefas)
  python3 benchmark_v2.py --quick              # roda 1 tarefa de cada categoria
  python3 benchmark_v2.py --test               # testa 1 tarefa sem salvar
  python3 benchmark_v2.py --incremental        # só roda tarefas não presentes no arquivo
  python3 benchmark_v2.py --cot                # inclui condição CoT-Baseline (3 modos)
  python3 benchmark_v2.py --model-tag mistral7b  # salva em benchmark_mistral7b_results.json
"""

import json
import os
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

from langchain_core.messages import HumanMessage, AIMessage

# Configuração de modelos
os.environ.setdefault("SUPERVISOR_MODEL", "llama3.1:8b")
os.environ.setdefault("WORKER_MODEL", "llama3.1:8b")

from src.grafo import construir_grafo  # noqa: E402 — importar após setar env


TASKS_FILE = "tasks_v2.json"
SAMPLE_FILE = "tasks_sample.json"


def _count_tokens(messages) -> int:
    total = 0
    for m in messages:
        if isinstance(m, AIMessage) and m.usage_metadata:
            total += m.usage_metadata.get("total_tokens", 0)
    return total


def _get_worker_response(messages) -> str:
    """Retorna a resposta real do Worker — último AIMessage não-Supervisor com conteúdo."""
    for m in reversed(messages):
        if isinstance(m, AIMessage) and getattr(m, 'name', 'Supervisor') != 'Supervisor' and m.content.strip():
            return m.content[:800]
    return ""


def _extract_instrucao(messages) -> str:
    """Extrai a instrução CDH/CoT da última mensagem do Supervisor."""
    for m in reversed(messages):
        if isinstance(m, AIMessage) and getattr(m, 'name', '') == 'Supervisor':
            content = m.content
            if 'Instrução:' in content:
                return content.split('Instrução:', 1)[1].strip()[:400]
    return ""


TASK_TIMEOUT = 120  # segundos máximos por tarefa


def run_once(task_text: str, modo: str, recursion_limit: int = 20) -> dict:
    os.environ["MODO_BASELINE"] = "true" if modo == "baseline" else "false"
    os.environ["MODO_COT"] = "true" if modo == "cot" else "false"
    app = construir_grafo()

    t0 = time.perf_counter()
    error = None
    estado = None

    def _invoke():
        return app.invoke(
            {
                "messages": [HumanMessage(content=task_text)],
                "proximo": "",
                "ciclos_react": 0,
                "tokens_supervisor": 0,
                "workers_escolhidos": [],
                "tipo_ambiguidade": "nenhuma",
                "confianca": 0,
            },
            config={"recursion_limit": recursion_limit},
        )

    try:
        ex = ThreadPoolExecutor(max_workers=1)
        future = ex.submit(_invoke)
        try:
            estado = future.result(timeout=TASK_TIMEOUT)
        except FuturesTimeout:
            error = f"timeout (>{TASK_TIMEOUT}s)"
        except Exception as e:
            error = str(e)
        finally:
            ex.shutdown(wait=False)  # não bloqueia em threads presas
    except Exception as e:
        error = str(e)
    latencia = round(time.perf_counter() - t0, 2)

    if estado:
        tokens_workers = _count_tokens(estado["messages"])
        tokens_sup = estado.get("tokens_supervisor", 0)
        ciclos = estado.get("ciclos_react", 0)
        proximo = estado.get("proximo", "?")
        resposta = _get_worker_response(estado["messages"])
        instrucao_cdh = _extract_instrucao(estado["messages"]) if modo != "baseline" else ""
        workers_escolhidos = estado.get("workers_escolhidos", [])
        tipo_ambiguidade = estado.get("tipo_ambiguidade", "nenhuma") if modo == "cdh" else ""
        confianca = estado.get("confianca", 0) if modo == "cdh" else 0
        sucesso = (proximo == "FINALIZAR") and error is None
    else:
        tokens_workers = tokens_sup = ciclos = 0
        proximo = "ERRO"
        resposta = ""
        instrucao_cdh = ""
        workers_escolhidos = []
        tipo_ambiguidade = ""
        confianca = 0
        sucesso = False

    return {
        "modo": modo,
        "sucesso": sucesso,
        "erro": error,
        "latencia_s": latencia,
        "tokens_total": tokens_workers,
        "tokens_supervisor": tokens_sup,
        "tokens_grand_total": tokens_workers + tokens_sup,
        "ciclos_react": ciclos,
        "proximo_final": proximo,
        "resposta": resposta,
        "instrucao_cdh": instrucao_cdh,
        "workers_escolhidos": workers_escolhidos,
        "tipo_ambiguidade": tipo_ambiguidade,
        "confianca": confianca,
    }


def main():
    quick       = "--quick"       in sys.argv
    test        = "--test"        in sys.argv
    incremental = "--incremental" in sys.argv
    sample      = "--sample"      in sys.argv
    include_cot = "--cot"         in sys.argv

    # --model-tag TAG → salva em benchmark_TAG_results.json
    model_tag = None
    if "--model-tag" in sys.argv:
        idx = sys.argv.index("--model-tag")
        if idx + 1 < len(sys.argv):
            model_tag = sys.argv[idx + 1]

    # --tasks-file PATH → usa arquivo de tarefas alternativo
    tasks_file_override = None
    if "--tasks-file" in sys.argv:
        idx = sys.argv.index("--tasks-file")
        if idx + 1 < len(sys.argv):
            tasks_file_override = sys.argv[idx + 1]

    if tasks_file_override:
        tasks_file = tasks_file_override
    elif sample:
        tasks_file = SAMPLE_FILE
    else:
        tasks_file = TASKS_FILE
    if model_tag:
        results_file = f"benchmark_{model_tag}_results.json"
    elif sample:
        results_file = "benchmark_sample_results.json"
    else:
        results_file = "benchmark_v3_results.json"

    modos = ["baseline", "cot", "cdh"] if include_cot else ["baseline", "cdh"]

    with open(tasks_file) as f:
        tasks = json.load(f)

    existing = []
    if incremental and os.path.exists(results_file):
        with open(results_file) as f:
            existing = json.load(f)
        done_keys = {(r["id"], r["modo"]) for r in existing}
        tasks_to_run = [(t, m) for t in tasks for m in modos if (t["id"], m) not in done_keys]
        print(f"Modo incremental: {len(done_keys)} execuções já concluídas, {len(tasks_to_run)} pendentes")
    elif sample:
        tasks_to_run = [(t, m) for t in tasks for m in modos]
        print(f"Modo amostra ({tasks_file}): {len(tasks)} tarefas × {len(modos)} modos = {len(tasks_to_run)} execuções")
    elif quick:
        # 1 tarefa por categoria (primeira de cada)
        seen_cats: set = set()
        quick_tasks = []
        for t in tasks:
            if t["cat"] not in seen_cats:
                seen_cats.add(t["cat"])
                quick_tasks.append(t)
        tasks = quick_tasks
        tasks_to_run = [(t, m) for t in tasks for m in modos]
        print(f"Modo rápido: {len(tasks)} tarefas × {len(modos)} modos = {len(tasks_to_run)} execuções")
    elif test:
        tasks = tasks[:1]
        tasks_to_run = [(t, m) for t in tasks for m in modos]
        print(f"Modo teste: 1 tarefa × {len(modos)} modos = {len(tasks_to_run)} execuções")
    else:
        tasks_to_run = [(t, m) for t in tasks for m in modos]
        print(f"Benchmark completo: {len(tasks)} tarefas × {len(modos)} modos = {len(tasks_to_run)} execuções")

    print(f"Supervisor: {os.environ['SUPERVISOR_MODEL']}  Worker: {os.environ['WORKER_MODEL']}")
    print(f"Salvando em: {results_file}")
    print("-" * 72)

    results = list(existing)
    total = len(tasks_to_run)
    idx = 0

    for t, modo in tasks_to_run:
        idx += 1
        print(f"[{idx:3d}/{total}] {t['id']:10s} | {modo.upper():8s} | {t['amb']:5s} | ", end="", flush=True)
        try:
            r = run_once(t["task"], modo)
            marker = "✓" if r["sucesso"] else "✗"
            print(f"{marker} {r['latencia_s']:5.1f}s | {r['tokens_total']:5d} tok | {r['ciclos_react']} ciclos")
        except Exception as e:
            r = {"modo": modo, "sucesso": False, "erro": traceback.format_exc(), "latencia_s": 0,
                 "tokens_total": 0, "tokens_supervisor": 0, "tokens_grand_total": 0,
                 "ciclos_react": 0, "proximo_final": "ERRO", "resposta": "", "instrucao_cdh": "",
                 "workers_escolhidos": [], "tipo_ambiguidade": "", "confianca": 0}
            print(f"✗ FALHA: {e}")

        results.append({**t, **r})

        if not test:
            with open(results_file, "w") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

    if not test:
        print(f"\nResultados salvos em {results_file}")

    # Resumo
    print("\n" + "=" * 72)
    print("RESUMO POR MODO")
    print("=" * 72)
    for modo in modos:
        subset = [r for r in results if r["modo"] == modo]
        n = len(subset)
        if n == 0:
            continue
        ok = sum(1 for r in subset if r["sucesso"])
        avg_wk  = sum(r["tokens_total"] for r in subset) / n
        avg_sup = sum(r.get("tokens_supervisor", 0) for r in subset) / n
        avg_lat = sum(r["latencia_s"] for r in subset) / n
        avg_cic = sum(r["ciclos_react"] for r in subset) / n
        print(f"  {modo.upper():8s}: {ok}/{n} ok | workers {avg_wk:5.0f} tok | sup {avg_sup:5.0f} tok | {avg_lat:5.1f}s | {avg_cic:.2f} ciclos")

    print("\nRESUMO POR CATEGORIA")
    print("-" * 72)
    cats = sorted(set(r["cat"] for r in results))
    for cat in cats:
        for modo in modos:
            subset = [r for r in results if r["cat"] == cat and r["modo"] == modo]
            if not subset:
                continue
            n = len(subset)
            ok = sum(1 for r in subset if r["sucesso"])
            avg_tok = sum(r["tokens_total"] for r in subset) / n
            avg_cic = sum(r["ciclos_react"] for r in subset) / n
            print(f"  {cat} {modo.upper():8s}: {ok}/{n} ok | {avg_tok:6.0f} tok | {avg_cic:.2f} ciclos")


if __name__ == "__main__":
    main()
