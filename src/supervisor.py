import os
from typing import Literal
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from pydantic import BaseModel, Field
from .estado import Estado


class _TokenCounter(BaseCallbackHandler):
    """Accumulates total_tokens from ChatOllama usage_metadata via on_llm_end."""
    def __init__(self):
        self.total = 0

    def on_llm_end(self, response: LLMResult, **kwargs) -> None:
        for gen_list in response.generations:
            for gen in gen_list:
                msg = getattr(gen, "message", None)
                if msg and getattr(msg, "usage_metadata", None):
                    self.total += msg.usage_metadata.get("total_tokens", 0)


def _get_supervisor_llm():
    return ChatOllama(model=os.getenv("SUPERVISOR_MODEL", "llama3.1:8b"), temperature=0)


# ── CDH ──────────────────────────────────────────────────────────────────────

class _RoteramentoCDH(BaseModel):
    proximo: Literal["pesquisador_web", "analista", "escritor", "backend", "frontend", "testes", "CLARIFICAR", "FINALIZAR"] = Field(
        description="Próximo agente, CLARIFICAR se faltar info essencial, ou FINALIZAR."
    )
    instrucao: str = Field(
        description="Instrução técnica e desambiguada para o Worker. Se CLARIFICAR, escreva aqui a pergunta ao usuário."
    )
    justificativa: str = Field(description="Breve justificativa da decisão.")
    complexidade: int = Field(
        default=5,
        description="Score 1–10: complexidade da tarefa (1=trivial, 10=multi-domínio extremo)."
    )
    tipo_ambiguidade: Literal["nenhuma", "sintatica", "semantica", "contextual", "multi_dominio"] = Field(
        default="nenhuma",
        description="Tipo principal de ambiguidade identificada: nenhuma/sintatica/semantica/contextual/multi_dominio."
    )
    confianca: int = Field(
        default=80,
        description="Confiança na decisão de roteamento: 0–100 (100 = certeza absoluta)."
    )


_CDH_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """Você é o Supervisor CDH (Ciclo de Desambiguação Hierárquica).
Recebe objetivos possivelmente ambíguos e os transforma em instruções precisas para Workers.

WORKERS DISPONÍVEIS:
- pesquisador_web: busca fatos, documentação, notícias, dados externos. NÃO USE para código ou cálculos puros.
- analista: cálculos matemáticos, estatísticas, conversões numéricas. NÃO USE para pesquisa ou redação.
- escritor: emails, artigos, resumos, textos narrativos. NÃO USE para código ou cálculos.
- backend: APIs REST, banco de dados, scripts server-side (Python/Node/SQL). NÃO USE para interfaces visuais.
- frontend: HTML/CSS/JS/React, componentes UI, prototipação visual. NÃO USE para lógica de negócio pura.
- testes: testes automatizados (pytest/jest), TDD, cobertura. NÃO USE para produzir o código funcional em si.

CICLO DE DESAMBIGUAÇÃO:
1. IDENTIFIQUE a ambiguidade: sintática (palavra com duplo sentido), semântica (domínio incerto), contextual (falta de contexto que muda o resultado), multi_domínio (requer 2+ workers), ou nenhuma.
2. RESOLVA: qual domínio principal completa o objetivo? Se multi_domínio, qual vem PRIMEIRO?
3. INSTRUÇÃO: específica, mensurável, com critério de conclusão claro. Inclua parâmetros concretos quando inferíveis.
4. COMPLEXIDADE: 1–3 tarefa direta (1 worker suficiente); 4–6 análise prévia recomendada; 7–10 múltiplos domínios, sequência obrigatória.

REGRAS:
1. REGRA CRÍTICA: sem resposta de Worker no histórico → NUNCA use FINALIZAR. Delegue sempre.
2. complexidade >= 7 e nenhum Worker respondeu → delegue ao pesquisador_web antes de outros workers.
3. CLARIFICAR somente se a informação ausente for impossível de inferir e bloquear completamente a execução.
4. FINALIZAR somente após Worker responder E o objetivo estiver completamente cumprido."""),
    MessagesPlaceholder(variable_name="messages"),
])


# ── BASELINE ─────────────────────────────────────────────────────────────────

class _RoteramentoBase(BaseModel):
    proximo: Literal["pesquisador_web", "analista", "escritor", "backend", "frontend", "testes", "FINALIZAR"] = Field(
        description="Agente para executar a tarefa, ou FINALIZAR se já concluída."
    )


_BASE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """Você é um roteador de tarefas.
Escolha o agente correto:
- pesquisador_web: buscas na internet
- analista: cálculos e análises numéricas
- escritor: criação e redação de textos
- backend: APIs, banco de dados, lógica server-side
- frontend: interfaces web, HTML/CSS/JS/React
- testes: testes automatizados, pytest/jest
- FINALIZAR: se a tarefa já foi concluída

Responda apenas com o campo 'proximo'."""),
    MessagesPlaceholder(variable_name="messages"),
])


# ── COT-BASELINE ─────────────────────────────────────────────────────────────

class _RoteramentoCOT(BaseModel):
    proximo: Literal["pesquisador_web", "analista", "escritor", "backend", "frontend", "testes", "FINALIZAR"] = Field(
        description="Agente para executar a tarefa, ou FINALIZAR se já concluída."
    )
    instrucao: str = Field(
        description="Instrução reformulada para o Worker após reflexão sobre possíveis ambiguidades."
    )


_COT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """Você é um roteador de tarefas com capacidade de reflexão.
Antes de rotear, pense brevemente: o que pode ser ambíguo ou vago nesta tarefa?
Então formule uma instrução clara e direta para o Worker escolhido.

Agentes disponíveis:
- pesquisador_web: buscas na internet
- analista: cálculos e análises numéricas
- escritor: criação e redação de textos
- backend: APIs, banco de dados, lógica server-side
- frontend: interfaces web, HTML/CSS/JS/React
- testes: testes automatizados, pytest/jest
- FINALIZAR: se a tarefa já foi concluída"""),
    MessagesPlaceholder(variable_name="messages"),
])


# ── Nó do grafo ───────────────────────────────────────────────────────────────

def _worker_responded(msgs) -> bool:
    return any(isinstance(m, AIMessage) and m.name not in (None, "Supervisor") for m in msgs)


def _fallback_worker(instrucao: str, human_text: str = "") -> str:
    """Infer worker from task keywords when model returns premature FINALIZAR/CLARIFICAR."""
    text = (instrucao + " " + human_text).lower()
    if any(w in text for w in ["teste", "testes", "pytest", "unittest", "jest", "tdd", "cobertura", "mock", "assert"]):
        return "testes"
    if any(w in text for w in ["frontend", "front-end", "html", "css", "react", "componente", "interface", "ui ", "ux "]):
        return "frontend"
    if any(w in text for w in ["backend", "back-end", "api", "endpoint", "banco de dados", "servidor", "fastapi", "flask", "django", "node"]):
        return "backend"
    if any(w in text for w in ["python", "script", "função", "funcao", "algoritmo", "código", "codigo", "programa", "debug", "implementa"]):
        return "backend"
    if any(w in text for w in ["calcul", "quanto é", "quanto vale", "matemática", "resultado de", "potência", "juros", "r$", "porcentagem", "área"]):
        return "analista"
    if any(w in text for w in ["escreva", "redija", "email", "artigo", "texto", "resumo", "carta", "poema", "plano de estudos"]):
        return "escritor"
    return "pesquisador_web"


def no_supervisor(estado: Estado) -> dict:
    llm = _get_supervisor_llm()
    msgs = estado["messages"]
    counter = _TokenCounter()
    config = {"callbacks": [counter]}

    if os.getenv("MODO_BASELINE") == "true":
        resultado = (_BASE_PROMPT | llm.with_structured_output(_RoteramentoBase)).invoke(
            {"messages": msgs}, config=config
        )
        objetivo_bruto = next((m.content for m in msgs if m.type == "human"), msgs[0].content)
        diretiva = AIMessage(
            content=f"Delegando para {resultado.proximo}. Tarefa: {objetivo_bruto}",
            name="Supervisor",
        )
    elif os.getenv("MODO_COT") == "true":
        resultado = (_COT_PROMPT | llm.with_structured_output(_RoteramentoCOT)).invoke(
            {"messages": msgs}, config=config
        )
        worker_already_responded = _worker_responded(msgs)
        if resultado.proximo == "FINALIZAR" and not worker_already_responded:
            human_text = next((m.content for m in msgs if m.type == "human"), "")
            resultado.proximo = _fallback_worker(resultado.instrucao, human_text)
        diretiva = AIMessage(
            content=f"Delegando para {resultado.proximo}. [CoT] Instrução: {resultado.instrucao}",
            name="Supervisor",
        )
    else:
        resultado = (_CDH_PROMPT | llm.with_structured_output(_RoteramentoCDH)).invoke(
            {"messages": msgs}, config=config
        )
        worker_already_responded = _worker_responded(msgs)

        # Guard A: prevent FINALIZAR/CLARIFICAR before any worker has responded
        if resultado.proximo in ("FINALIZAR", "CLARIFICAR") and not worker_already_responded:
            human_text = next((m.content for m in msgs if m.type == "human"), "")
            resultado.proximo = _fallback_worker(resultado.instrucao, human_text)
            if not resultado.instrucao.strip():
                resultado.instrucao = human_text

        # Guard B: prevent CLARIFICAR after worker already responded
        elif resultado.proximo == "CLARIFICAR" and worker_already_responded:
            resultado.proximo = "FINALIZAR"

        prefixo = "Solicitando esclarecimento" if resultado.proximo == "CLARIFICAR" else f"Delegando para {resultado.proximo}"
        diretiva = AIMessage(
            content=(
                f"{prefixo}. [Complexidade: {resultado.complexidade}/10]"
                f" [Amb: {resultado.tipo_ambiguidade}] [Confiança: {resultado.confianca}%]"
                f" Instrução: {resultado.instrucao}"
            ),
            name="Supervisor",
        )
        workers_novos = [resultado.proximo] if resultado.proximo not in ("FINALIZAR", "CLARIFICAR") else []
        return {
            "proximo": resultado.proximo,
            "messages": [diretiva],
            "tokens_supervisor": counter.total,
            "workers_escolhidos": workers_novos,
            "tipo_ambiguidade": resultado.tipo_ambiguidade,
            "confianca": resultado.confianca,
        }

    return {"proximo": resultado.proximo, "messages": [diretiva], "tokens_supervisor": counter.total}
