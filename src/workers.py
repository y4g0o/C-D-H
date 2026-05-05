import json
import os
from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from .estado import Estado
from .ferramentas import busca_web, calcular, executar_codigo


def _get_worker_llm():
    return ChatOllama(model=os.getenv("WORKER_MODEL", "llama3.1:8b"), temperature=0)


def _fix_tool_calls(response: AIMessage) -> AIMessage:
    """Convert JSON-in-content tool calls to proper tool_calls for models that ignore the API."""
    if response.tool_calls:
        return response
    content = response.content
    brace = content.find("{")
    if brace == -1:
        return response
    try:
        data = json.loads(content[brace:])
    except json.JSONDecodeError:
        return response

    # Support {"name": ..., "arguments": ...} and {"function_call": {"name": ..., "arguments": ...}}
    if "function_call" in data:
        data = data["function_call"]
    name = data.get("name")
    args = data.get("arguments") or data.get("parameters") or {}
    if not name:
        return response
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except json.JSONDecodeError:
            return response

    tool_id = f"call_{abs(hash(content[brace:])) % 10000:04d}"
    return AIMessage(
        content=content[:brace].strip(),
        tool_calls=[{"name": name, "args": args, "id": tool_id}],
        usage_metadata=response.usage_metadata,
    )


def _run_react(llm, tools: list, system: str, existing_messages: list, max_cycles: int = 8, agent_name: str = None):
    """
    Custom ReAct loop that handles JSON-in-content tool calls.
    Returns (new_messages, ciclos_react) where new_messages are to be added to state.
    """
    tools_by_name = {t.name: t for t in tools}
    llm_with_tools = llm.bind_tools(tools)
    context = [SystemMessage(content=system)] + list(existing_messages)
    new_messages = []
    ciclos = 0

    for _ in range(max_cycles):
        raw = llm_with_tools.invoke(context)
        response = _fix_tool_calls(raw)

        if not response.tool_calls and agent_name:
            response = AIMessage(
                content=response.content,
                name=agent_name,
                usage_metadata=response.usage_metadata,
            )

        context.append(response)
        new_messages.append(response)

        if not response.tool_calls:
            break

        for tc in response.tool_calls:
            ciclos += 1
            tool_fn = tools_by_name.get(tc["name"])
            if tool_fn:
                try:
                    result = str(tool_fn.invoke(tc["args"]))
                except Exception as e:
                    result = f"Erro ao executar ferramenta: {e}"
            else:
                result = f"Ferramenta '{tc['name']}' não encontrada."
            tool_msg = ToolMessage(content=result, tool_call_id=tc["id"])
            context.append(tool_msg)
            new_messages.append(tool_msg)

    return new_messages, ciclos


_PESQUISADOR_SYSTEM = (
    "Você é um Agente Pesquisador Web especialista. "
    "Use busca_web para encontrar informações precisas e atualizadas. "
    "Se a primeira busca for insuficiente, refine os termos e busque novamente. "
    "Sintetize as fontes em uma resposta coesa — cite URLs quando disponíveis. "
    "Priorize fontes primárias (documentação oficial, artigos, sites de referência). "
    "Responda em português, preservando termos técnicos em inglês quando necessário."
)

_ANALISTA_SYSTEM = (
    "Você é um Agente Analista especialista em cálculos e análise numérica. "
    "Use calcular para avaliar expressões matemáticas — não faça aritmética mental. "
    "Mostre cada etapa: dados de entrada → transformação → resultado. "
    "Inclua unidades e arredondamentos quando relevante. "
    "Se houver ambiguidade nos dados (ex.: 'taxa de juros' sem período), adote a interpretação mais comum e explicite o pressuposto. "
    "Responda em português."
)

_ESCRITOR_SYSTEM = (
    "Você é um Escritor Profissional especialista em comunicação escrita. "
    "Produza conteúdo bem estruturado: introdução, desenvolvimento e conclusão quando aplicável. "
    "Adapte tom e formato ao contexto: formal para emails corporativos, narrativo para artigos, direto para resumos. "
    "Não repita a instrução recebida — vá direto ao conteúdo. "
    "Responda em português."
)

_BACKEND_SYSTEM = (
    "Você é um Agente de Desenvolvimento Backend especialista. "
    "Implemente APIs REST, lógica de negócio, acesso a banco de dados e serviços server-side. "
    "Use a ferramenta executar_codigo para validar o código antes de entregar. "
    "Se houver erro, corrija e teste novamente. "
    "Prefira Python (FastAPI/Flask) salvo especificação contrária. "
    "Entregue o código final completo com instruções de uso."
)

_FRONTEND_SYSTEM = (
    "Você é um Agente de Desenvolvimento Frontend especialista. "
    "Crie interfaces, componentes e interações client-side com HTML, CSS e JavaScript/TypeScript. "
    "Use React quando não houver especificação de framework. "
    "Use executar_codigo para validar lógica JavaScript pura quando possível. "
    "Entregue o código completo com estrutura de arquivos clara e comentários nos pontos-chave."
)

_TESTES_SYSTEM = (
    "Você é um Agente de Testes especialista. "
    "Escreva testes automatizados claros e cobrindo casos limite (edge cases). "
    "Use pytest para Python, Jest para JavaScript salvo especificação contrária. "
    "Use executar_codigo para rodar os testes e confirmar que passam. "
    "Se um teste falhar, analise a causa, corrija o código de teste ou sinalize o bug no código principal. "
    "Entregue os testes completos com relatório de cobertura dos cenários."
)


def no_pesquisador(estado: Estado) -> dict:
    new_msgs, ciclos = _run_react(
        _get_worker_llm(), [busca_web], _PESQUISADOR_SYSTEM,
        estado["messages"], agent_name="pesquisador_web",
    )
    return {"messages": new_msgs, "ciclos_react": ciclos}


def no_analista(estado: Estado) -> dict:
    new_msgs, ciclos = _run_react(
        _get_worker_llm(), [calcular], _ANALISTA_SYSTEM,
        estado["messages"], agent_name="analista",
    )
    return {"messages": new_msgs, "ciclos_react": ciclos}


def no_escritor(estado: Estado) -> dict:
    llm = _get_worker_llm()
    result = llm.invoke([SystemMessage(content=_ESCRITOR_SYSTEM)] + list(estado["messages"]))
    msg = AIMessage(content=result.content, name="escritor", usage_metadata=result.usage_metadata)
    return {"messages": [msg], "ciclos_react": 0}


def no_backend(estado: Estado) -> dict:
    new_msgs, ciclos = _run_react(
        _get_worker_llm(), [executar_codigo], _BACKEND_SYSTEM,
        estado["messages"], agent_name="backend",
    )
    return {"messages": new_msgs, "ciclos_react": ciclos}


def no_frontend(estado: Estado) -> dict:
    new_msgs, ciclos = _run_react(
        _get_worker_llm(), [executar_codigo], _FRONTEND_SYSTEM,
        estado["messages"], agent_name="frontend",
    )
    return {"messages": new_msgs, "ciclos_react": ciclos}


def no_testes(estado: Estado) -> dict:
    new_msgs, ciclos = _run_react(
        _get_worker_llm(), [executar_codigo], _TESTES_SYSTEM,
        estado["messages"], agent_name="testes",
    )
    return {"messages": new_msgs, "ciclos_react": ciclos}
