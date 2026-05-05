from langgraph.graph import StateGraph, START, END
from .estado import Estado
from .supervisor import no_supervisor
from .workers import no_pesquisador, no_analista, no_escritor, no_backend, no_frontend, no_testes


def _roteador(estado: Estado) -> str:
    proximo = estado["proximo"]
    if proximo in ("FINALIZAR", "CLARIFICAR"):
        return END
    return proximo


def construir_grafo():
    grafo = StateGraph(Estado)

    grafo.add_node("supervisor", no_supervisor)
    grafo.add_node("pesquisador_web", no_pesquisador)
    grafo.add_node("analista", no_analista)
    grafo.add_node("escritor", no_escritor)
    grafo.add_node("backend", no_backend)
    grafo.add_node("frontend", no_frontend)
    grafo.add_node("testes", no_testes)

    grafo.add_edge(START, "supervisor")
    grafo.add_conditional_edges("supervisor", _roteador)

    grafo.add_edge("pesquisador_web", "supervisor")
    grafo.add_edge("analista", "supervisor")
    grafo.add_edge("escritor", "supervisor")
    grafo.add_edge("backend", "supervisor")
    grafo.add_edge("frontend", "supervisor")
    grafo.add_edge("testes", "supervisor")

    return grafo.compile()


app = construir_grafo()
