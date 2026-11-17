
from langgraph.graph import END, START, StateGraph

from .planning_state import PlanningGraphState

from .planning_nodes import (
    validar_solicitacao_confirmada,
    executar_professora,
    executar_assistente,
    executar_revisora,
)

from .planning_edges import route_after_validation


def criar_workflow_planejamento(checkpointer):
    """
    Cria o grafo de planejamento pedagógico semanal do POMORA.

    Recebe o checkpointer PostgreSQL já inicializado.
    """

    builder = StateGraph(PlanningGraphState)

    builder.add_node(
        "validar_solicitacao",
        validar_solicitacao_confirmada,
    )

    builder.add_node(
        "executar_professora",
        executar_professora,
    )

    builder.add_node(
        "executar_assistente",
        executar_assistente,
    )

    builder.add_node(
        "executar_revisora",
        executar_revisora,
    )

    builder.add_edge(START, "validar_solicitacao")

    builder.add_conditional_edges(
        "validar_solicitacao",
        route_after_validation,
        {
            "continue": "executar_professora",
            "end": END,
        },
    )

    builder.add_edge(
        "executar_professora",
        "executar_assistente",
    )

    builder.add_edge(
        "executar_assistente",
        "executar_revisora",
    )

    builder.add_edge(
        "executar_revisora",
        END,
    )

    return builder.compile(checkpointer=checkpointer)


planning_graph = None
