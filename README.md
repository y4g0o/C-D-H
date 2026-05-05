# CDH — Ciclo de Desambiguação Hierárquica

> *"Da Ambiguidade à Ação: Um Ciclo de Desambiguação Hierárquica para Sistemas Multiagente"*  
> TCC — Ciência da Computação — IFCE Campus Aracati  
> Orientador: Prof. Dr. Raimundo Valter Costa Filho

---

## O que é o CDH?

O **Ciclo de Desambiguação Hierárquica (CDH)** é um padrão arquitetural para sistemas multiagente com LLMs locais. O Supervisor não repassa o objetivo bruto ao Worker — ele primeiro **identifica o tipo de ambiguidade**, calcula um escore de complexidade e **engenheira uma instrução precisa** antes de delegar.

```
Usuário → Supervisor (CDH) → Worker especializado → Supervisor → FINALIZAR
                ↑
      Desambiguação estruturada
      tipo_ambiguidade · complexidade · instrucao · confianca
```

**Três condições experimentais:**

| Condição | Descrição |
|---|---|
| **Baseline** | Supervisor roteia o objetivo bruto sem análise |
| **CoT-Baseline** | Supervisor reflete internamente, formula instrução, mas sem estrutura CDH |
| **CDH** | Desambiguação estruturada completa (Pydantic tipado + Guards A/B) |

---

## Arquitetura

6 Workers especializados orquestrados por um Supervisor via **LangGraph** (StateGraph). Todos os modelos rodam localmente via **Ollama** — sem API externa.

| Worker | Ferramenta | Domínio |
|---|---|---|
| Pesquisador Web | DuckDuckGo (timeout 15 s) | Pesquisa e síntese |
| Analista | Calculadora AST segura | Cálculo e análise numérica |
| Escritor | — | Redação e comunicação |
| Backend | Execução de código (sandbox) | APIs, scripts, banco de dados |
| Frontend | — | HTML/CSS/JS/React |
| Testes | — | pytest/jest, TDD, cobertura |

---

## Instalação

**Pré-requisitos:** Python 3.11+, [Ollama](https://ollama.com)

```bash
git clone git@github.com:y4g0o/C-D-H.git
cd C-D-H
pip install -r requirements.txt
ollama pull llama3.1:8b
```

---

## Uso

```bash
# Modo interativo
python3 main.py

# Objetivo direto
python3 main.py "Calcule o valor futuro de R$1000 a 5% ao mês por 12 meses"

# Modos alternativos
MODO_BASELINE=true python3 main.py "Pesquise sobre energia solar no Brasil"
MODO_COT=true python3 main.py "Escreva um email formal"

# Modelo diferente
SUPERVISOR_MODEL=mistral:7b WORKER_MODEL=mistral:7b python3 main.py
```

---

## Benchmark

100 tarefas × 3 condições (Baseline / CoT / CDH), replicável com qualquer modelo local.

```bash
# Rodar (3 condições, ~4h com llama3.1:8b)
python3 benchmark_v2.py --cot

# Tarefas de programação (BACK/FRONT/TEST)
python3 benchmark_v2.py --cot --tasks-file tasks_prog.json --model-tag meu_modelo

# Analisar resultados
python3 analisar_v2.py benchmark_v3_results.json
python3 analisar_multimodelo.py
```

---

## Resultados

### Benchmark II — Llama 3.1 8B (N = 200)

| Categoria | N | CDH | Baseline | Δ tokens |
|---|---|---|---|---|
| Pesquisa | 34 | 97% | 91% | **−69%** |
| Cálculo | 34 | 94% | 82% | **−85%** |
| Escrita | 32 | 100% | 94% | −35% |
| **Total** | 100 | **97%** | **89%** | **−71%** |

Fisher p = 0,049 · MWU p = 0,049 · Alta ambiguidade: CDH 93% vs. Baseline 67% (p = 0,021, h = 0,709)

### Benchmark IV — Multi-modelo (N = 1 800, 6 modelos × 3 condições)

| Modelo | Baseline | CoT | CDH | Δ tokens | Achado |
|---|---|---|---|---|---|
| Llama 3.1 8B | 89% | 99% | 97% | −71% | ✅ CDH beneficia |
| Llama 3.2 3B | 90% | 98% | 61% | +359% | ❌ CDH prejudica |
| Mistral 7B | 98% | 100% | 97% | +181% | ➖ Neutro (sem margem) |
| Qwen 2.5 7B | 20% | 41% | 36% | +443% | ⚠️ Melhora sucesso |
| Gemma 2 9B | 7% | 17% | 6% | +51% | ❌ Sem structured output |
| Phi 3 Mini | 18% | 5% | 3% | −90% | ❌ CDH prejudica |

**Zona de eficácia:** CDH beneficia modelos com capacidade mínima de *structured output* e com margem de melhoria disponível.

Os JSONs de resultado estão versionados no repositório para reprodutibilidade.

---

## Testes

```bash
pytest tests/ -v
```

---

## Dashboard

```bash
cd front-end_CDH
python3 -m http.server 8080
# → http://localhost:8080
```

Telas: Overview · Execução · Histórico · Métricas · Avaliação Likert · Grafo

---

## Licença

MIT © 2026 Yago Macambira
