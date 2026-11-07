
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

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

    O checkpointer permite preservar o estado entre
    diferentes mensagens da mesma conversa.
    """

    builder = StateGraph(IntakeGraphState)

    # Registro dos nós
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

    # Ponto inicial
    builder.add_edge(START, "processar_mensagem")

    # Roteamento após a interpretação da Márcia
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

    # Roteamento após verificar os campos obrigatórios
    builder.add_conditional_edges(
        "verificar_completude",
        route_after_completeness,
        {
            "prepare_confirmation": "preparar_confirmacao",
            "end": END,
            "invalid_state": END,
        },
    )

    # Após preparar o resumo, aguarda a próxima mensagem
    builder.add_edge("preparar_confirmacao", END)

    # Roteamento após validar a decisão do usuário
    builder.add_conditional_edges(
        "validar_confirmacao",
        route_after_confirmation,
        {
            "recheck_completeness": "verificar_completude",
            "end": END,
            "invalid_state": END,
        },
    )

    # Checkpointer padrão para desenvolvimento e testes
    saver = checkpointer or InMemorySaver()

    return builder.compile(checkpointer=saver)


# Instância compartilhada durante a execução da aplicação
intake_graph = criar_workflow_intake()
