from typing import Any

from pydantic import ValidationError

from ...schemas.request import UserRequest

from ...schemas.agent_outputs import (
    ProfessoraInput,
    AssistenteInput,
    RevisoraInput,
)

from ...chains.agents.professora import (
    gerar_planejamento_pedagogico,
)

from ...chains.agents.assistente import (
    gerar_recursos_apoio,
)

from ...chains.agents.revisora import (
    revisar_planejamento,
)

from .planning_state import PlanningGraphState


# ============================================================
# VALIDACAO DA SOLICITACAO
# ============================================================

def validar_solicitacao_confirmada(
    state: PlanningGraphState,
) -> dict[str, Any]:
    """
    Valida se a solicitação recebida do Intake foi confirmada
    e converte os dados para UserRequest.

    O planejamento somente pode começar depois da confirmação
    explícita do usuário.
    """

    if state.get("intake_status") != "confirmed":
        return {
            "planning_status": "blocked",
            "error_message": (
                "O planejamento só pode começar após "
                "a confirmação da solicitação."
            ),
            "validation_errors": [],
        }

    validated_request = state.get("validated_request")

    if not validated_request:
        return {
            "planning_status": "blocked",
            "error_message": (
                "A solicitação confirmada não contém "
                "os dados necessários para o planejamento."
            ),
            "validation_errors": [],
        }

    try:
        user_request = UserRequest.model_validate(
            validated_request
        )

    except ValidationError as exc:

        erros = [
            error["msg"]
            for error in exc.errors(include_input=False)
        ]

        return {
            "planning_status": "blocked",
            "error_message": (
                "A solicitação recebida não passou "
                "pela validação do planejamento."
            ),
            "validation_errors": erros,
        }

    return {
        "planning_status": "ready",
        "user_request": user_request,
        "error_message": None,
        "validation_errors": [],
    }


# ============================================================
# EXECUCAO DA PROFESSORA
# ============================================================

def executar_professora(
    state: PlanningGraphState,
) -> dict[str, Any]:
    """
    Executa a agente Professora.

    Recebe UserRequest e produz ProfessoraOutput
    com o planejamento pedagógico completo dos cinco dias.
    """

    user_request = state.get("user_request")

    if user_request is None:
        raise ValueError(
            "A Professora não recebeu uma solicitação validada."
        )

    if not isinstance(user_request, UserRequest):
        user_request = UserRequest.model_validate(user_request)

    entrada = ProfessoraInput(
        user_request=user_request
    )

    resultado = gerar_planejamento_pedagogico(entrada)

    return {
        "professora_output": resultado,
    }


# ============================================================
# EXECUCAO DO ASSISTENTE
# ============================================================

def executar_assistente(
    state: PlanningGraphState,
) -> dict[str, Any]:
    """
    Executa o agente Assistente.

    Recebe a solicitação e o planejamento completo da Professora.

    Produz AssistenteOutput com imagens ilustrativas,
    sugestões de músicas, vídeos e orientações de uso.
    """

    user_request = state.get("user_request")
    professora_output = state.get("professora_output")

    if user_request is None or professora_output is None:
        raise ValueError(
            "O Assistente precisa receber a solicitação "
            "e o planejamento da Professora."
        )

    if not isinstance(user_request, UserRequest):
        user_request = UserRequest.model_validate(user_request)

    entrada = AssistenteInput(
        user_request=user_request,
        professora_output=professora_output,
    )

    resultado = gerar_recursos_apoio(entrada)

    return {
        "assistente_output": resultado,
    }


# ============================================================
# EXECUCAO DA REVISORA
# ============================================================

def executar_revisora(
    state: PlanningGraphState,
) -> dict[str, Any]:
    """
    Executa a agente Revisora.

    Recebe:
    - Solicitação validada.
    - Planejamento da Professora.
    - Recursos de apoio do Assistente.

    Produz RevisoraOutput, que representa o planejamento
    semanal final do POMORA.
    """

    user_request = state.get("user_request")
    professora_output = state.get("professora_output")
    assistente_output = state.get("assistente_output")

    if (
        user_request is None
        or professora_output is None
        or assistente_output is None
    ):
        raise ValueError(
            "A Revisora precisa receber os resultados "
            "da Professora e do Assistente."
        )

    if not isinstance(user_request, UserRequest):
        user_request = UserRequest.model_validate(user_request)

    entrada = RevisoraInput(
        user_request=user_request,
        professora_output=professora_output,
        assistente_output=assistente_output,
    )

    resultado = revisar_planejamento(entrada)

    return {
        "revisora_output": resultado,
        "planning_status": "completed",
        "error_message": None,
        "validation_errors": [],
    }