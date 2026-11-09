from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from .planning_state import PlanningGraphState

from .planning_nodes import (
    validar_solicitacao_confirmada,
    executar_professora,
    executar_assistente,
    executar_revisora,
)

from .planning_edges import route_after_validation


def criar_workflow_planejamento(checkpointer=None):
    """
    Cria o grafo de planejamento pedagógico semanal do POMORA.

    Fluxo:
    1. Valida a solicitação recebida do Intake.
    2. Executa a Professora.
    3. Executa o Assistente.
    4. Executa a Revisora.
    5. Finaliza com o planejamento semanal consolidado.

    O checkpointer permite recuperar o resultado de uma execução
    associada ao mesmo thread_id.
    """

    builder = StateGraph(PlanningGraphState)

    # Registro dos nós
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

    # Ponto inicial
    builder.add_edge(START, "validar_solicitacao")

    # Validação da solicitação
    builder.add_conditional_edges(
        "validar_solicitacao",
        route_after_validation,
        {
            "continue": "executar_professora",
            "end": END,
        },
    )

    # Fluxo sequencial
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

    # Checkpointer
    saver = checkpointer if checkpointer is not None else InMemorySaver()

    return builder.compile(checkpointer=saver)


# Instância compartilhada do grafo
planning_graph = criar_workflow_planejamento()