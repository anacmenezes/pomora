from typing import Any

from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from .workflow import intake_graph
from .planning.planning_workflow import planning_graph


# ============================================================
# SERIALIZACAO DOS RESULTADOS
# ============================================================

def serializar_resultado(valor: Any) -> Any:
    """
    Converte objetos Pydantic em estruturas serializáveis.
    """

    if isinstance(valor, BaseModel):
        return valor.model_dump(mode="json")

    return valor


# ============================================================
# PROCESSAMENTO INTEGRADO DO POMORA
# ============================================================

def processar_mensagem_pomora(
    mensagem: str,
    thread_id: str,
) -> dict[str, Any]:
    """
    Executa o fluxo completo do POMORA.

    ETAPA 1:
        Recebe a mensagem do usuário e executa o grafo da Márcia.

    ETAPA 2:
        Se a solicitação ainda não estiver confirmada,
        retorna a resposta de atendimento.

    ETAPA 3:
        Quando a solicitação estiver confirmada, transfere
        o UserRequest para o grafo de planejamento.

    ETAPA 4:
        Executa Professora, Assistente e Revisora.

    ETAPA 5:
        Retorna o planejamento semanal final.

    O thread_id permite manter a continuidade da conversa
    e recuperar o resultado de planejamento já concluído.
    """

    if not mensagem or not mensagem.strip():
        raise ValueError("A mensagem do usuário não pode estar vazia.")

    if not thread_id or not thread_id.strip():
        raise ValueError("O thread_id é obrigatório.")

    # --------------------------------------------------------
    # 1. EXECUCAO DO GRAFO DA MARCIA
    # --------------------------------------------------------

    intake_config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    intake_resultado = intake_graph.invoke(
        {
            "messages": [
                HumanMessage(content=mensagem.strip())
            ],
        },
        config=intake_config,
    )

    intake_status = intake_resultado.get("status")

    # --------------------------------------------------------
    # 2. PREPARACAO DA RESPOSTA DO ATENDIMENTO
    # --------------------------------------------------------

    resposta_intake = {
        "status": intake_status,
        "response": intake_resultado.get("response"),
        "pending_fields": intake_resultado.get("pending_fields", []),
        "validation_errors": intake_resultado.get(
            "validation_errors",
            [],
        ),
    }

    # Enquanto a solicitação não estiver confirmada,
    # não executa o planejamento.
    if intake_status != "confirmed":
        return {
            "intake": resposta_intake,
            "planning": None,
        }

    validated_request = intake_resultado.get("validated_request")

    if not validated_request:
        raise ValueError(
            "A solicitação foi confirmada, mas o UserRequest "
            "não foi encontrado no estado do Intake."
        )

    # --------------------------------------------------------
    # 3. IDENTIFICACAO DO ESTADO DO PLANEJAMENTO
    # --------------------------------------------------------

    planning_thread_id = f"{thread_id}:planning"

    planning_config = {
        "configurable": {
            "thread_id": planning_thread_id,
        }
    }

    # Verifica se o planejamento já foi concluído nesta conversa.
    snapshot = planning_graph.get_state(planning_config)

    planning_state_anterior = snapshot.values or {}

    planejamento_concluido = (
        planning_state_anterior.get("planning_status") == "completed"
    )

    if planejamento_concluido:
        # Recupera o planejamento já produzido.
        planning_resultado = planning_state_anterior

    else:
        # ----------------------------------------------------
        # 4. EXECUCAO DO GRAFO DE PLANEJAMENTO
        # ----------------------------------------------------

        planning_resultado = planning_graph.invoke(
            {
                "intake_status": intake_status,
                "validated_request": validated_request,
            },
            config=planning_config,
        )

    # --------------------------------------------------------
    # 5. EXTRAÇÃO DO PLANO FINAL
    # --------------------------------------------------------

    revisora_output = planning_resultado.get("revisora_output")

    planejamento_final = serializar_resultado(revisora_output)

    planning_status = planning_resultado.get("planning_status")

    # --------------------------------------------------------
    # 6. RESPOSTA INTEGRADA
    # --------------------------------------------------------

    return {
        "intake": resposta_intake,
        "planning": {
            "status": planning_status,
            "error_message": planning_resultado.get("error_message"),
            "validation_errors": planning_resultado.get(
                "validation_errors",
                [],
            ),
            "planejamento_final": planejamento_final,
        },
    }