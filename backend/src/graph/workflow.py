
from langgraph.graph import END, START, StateGraph

from .checkpointer import postgres_checkpointer
from .edges import (
    route_after_completeness,
    route_after_confirmation,
    route_after_message,
)
from .nodes import (
    preparar_confirmacao,
    processar_mensagem_usuario,
    validar_confirmacao,
    verificar_completude,
)
from .state import IntakeGraphState


def criar_workflow_intake(checkpointer=None):
    """
    Cria o fluxo conversacional da Márcia.

    Utiliza o PostgreSQL para preservar o estado
    das conversas entre diferentes mensagens e reinicializações.
    """

    builder = StateGraph(IntakeGraphState)

    builder.add_node(
        "processar_mensagem",
        processar_mensagem_usuario,
    )

    builder.add_node(
        "verificar_completude",
        verificar_completude,
    )

    builder.add_node(
        "preparar_confirmacao",
        preparar_confirmacao,
    )

    builder.add_node(
        "validar_confirmacao",
        validar_confirmacao,
    )

    builder.add_edge(START, "processar_mensagem")

    builder.add_conditional_edges(
        "processar_mensagem",
        route_after_message,
        {
            "validate_confirmation": "validar_confirmacao",
            "check_completeness": "verificar_completude",
            "end": END,
            "invalid_state": END,
        },
    )

    builder.add_conditional_edges(
        "verificar_completude",
        route_after_completeness,
        {
            "prepare_confirmation": "preparar_confirmacao",
            "end": END,
            "invalid_state": END,
        },
    )

    builder.add_edge("preparar_confirmacao", END)

    builder.add_conditional_edges(
        "validar_confirmacao",
        route_after_confirmation,
        {
            "recheck_completeness": "verificar_completude",
            "end": END,
            "invalid_state": END,
        },
    )

    saver = (
        checkpointer
        if checkpointer is not None
        else postgres_checkpointer
    )

    return builder.compile(checkpointer=saver)

intake_graph = criar_workflow_intake()
