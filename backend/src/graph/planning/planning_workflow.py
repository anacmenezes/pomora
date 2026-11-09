
from langgraph.graph import END, START, StateGraph

from .planning_state import PlanningGraphState

from .planning_nodes import (
    validar_solicitacao_confirmada,
    executar_professora,
    executar_pesquisadora,
    executar_revisora,
    executar_redatora,
)

from .planning_edges import route_after_validation


def criar_workflow_planejamento(checkpointer=None):
    """
    Cria o grafo de planejamento pedagógico semanal.

    Fluxo:
    1. Valida a solicitação recebida do Intake.
    2. Executa a Professora.
    3. Executa a Pesquisadora.
    4. Executa a Revisora.
    5. Executa a Redatora.

    O checkpointer é opcional e pode ser fornecido
    quando houver necessidade de persistência.
    """

    builder = StateGraph(PlanningGraphState)

    # --------------------------------------------------------
    # REGISTRO DOS NÓS
    # --------------------------------------------------------

    builder.add_node(
        "validar_solicitacao",
        validar_solicitacao_confirmada,
    )

    builder.add_node(
        "executar_professora",
        executar_professora,
    )

    builder.add_node(
        "executar_pesquisadora",
        executar_pesquisadora,
    )

    builder.add_node(
        "executar_revisora",
        executar_revisora,
    )

    builder.add_node(
        "executar_redatora",
        executar_redatora,
    )

    # --------------------------------------------------------
    # PONTO INICIAL
    # --------------------------------------------------------

    builder.add_edge(
        START,
        "validar_solicitacao",
    )

    # --------------------------------------------------------
    # VALIDAÇÃO DA SOLICITAÇÃO
    # --------------------------------------------------------

    builder.add_conditional_edges(
        "validar_solicitacao",
        route_after_validation,
        {
            "continue": "executar_professora",
            "end": END,
        },
    )

    # --------------------------------------------------------
    # FLUXO SEQUENCIAL DAS AGENTES
    # --------------------------------------------------------

    builder.add_edge(
        "executar_professora",
        "executar_pesquisadora",
    )

    builder.add_edge(
        "executar_pesquisadora",
        "executar_revisora",
    )

    builder.add_edge(
        "executar_revisora",
        "executar_redatora",
    )

    # --------------------------------------------------------
    # FINALIZAÇÃO
    # --------------------------------------------------------

    builder.add_edge(
        "executar_redatora",
        END,
    )

    # Checkpointer opcional
    if checkpointer is not None:
        return builder.compile(checkpointer=checkpointer)

    return builder.compile()


# Instância compartilhada do grafo de planejamento
planning_graph = criar_workflow_planejamento()
