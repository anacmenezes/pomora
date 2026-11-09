
from typing import Any

from pydantic import ValidationError

from ...schemas.request import UserRequest
from ...schemas.agent_outputs import (
    ProfessoraInput,
    PesquisadoraInput,
    RevisoraInput,
    RedatoraInput,
)
from ...chains.agents.professora import gerar_estrategia_pedagogica
from ...chains.agents.pesquisadora import pesquisar_atividades_pedagogicas
from ...chains.agents.revisora import revisar_planejamento
from ...chains.agents.redatora import redigir_planejamento

from .planning_state import PlanningGraphState


def validar_solicitacao_confirmada(
    state: PlanningGraphState,
) -> dict[str, Any]:
    """
    Valida se a solicitação recebida do Intake foi confirmada
    e converte o dicionário para UserRequest.
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


def executar_professora(
    state: PlanningGraphState,
) -> dict[str, Any]:
    """
    Executa a agente Professora.

    Recebe UserRequest e produz ProfessoraOutput.
    """

    user_request = state.get("user_request")

    if user_request is None:
        raise ValueError(
            "A Professora não recebeu uma solicitação validada."
        )

    entrada = ProfessoraInput(
        user_request=user_request
    )

    resultado = gerar_estrategia_pedagogica(entrada)

    return {
        "professora_output": resultado,
    }


def executar_pesquisadora(
    state: PlanningGraphState,
) -> dict[str, Any]:
    """
    Executa a agente Pesquisadora.

    Recebe a solicitação e a estratégia pedagógica.
    """

    user_request = state.get("user_request")
    professora_output = state.get("professora_output")

    if user_request is None or professora_output is None:
        raise ValueError(
            "A Pesquisadora precisa receber a solicitação "
            "e o resultado da Professora."
        )

    entrada = PesquisadoraInput(
        user_request=user_request,
        professora_output=professora_output,
    )

    resultado = pesquisar_atividades_pedagogicas(entrada)

    return {
        "pesquisadora_output": resultado,
    }


def executar_revisora(
    state: PlanningGraphState,
) -> dict[str, Any]:
    """
    Executa a agente Revisora.

    Recebe a solicitação, a estratégia e os resultados
    da pesquisa pedagógica.
    """

    user_request = state.get("user_request")
    professora_output = state.get("professora_output")
    pesquisadora_output = state.get("pesquisadora_output")

    if (
        user_request is None
        or professora_output is None
        or pesquisadora_output is None
    ):
        raise ValueError(
            "A Revisora precisa receber os resultados "
            "da Professora e da Pesquisadora."
        )

    entrada = RevisoraInput(
        user_request=user_request,
        professora_output=professora_output,
        pesquisadora_output=pesquisadora_output,
    )

    resultado = revisar_planejamento(entrada)

    return {
        "revisora_output": resultado,
    }


def executar_redatora(
    state: PlanningGraphState,
) -> dict[str, Any]:
    """
    Executa a agente Redatora.

    Recebe todos os resultados anteriores e produz
    o planejamento pedagógico semanal final.
    """

    user_request = state.get("user_request")
    professora_output = state.get("professora_output")
    pesquisadora_output = state.get("pesquisadora_output")
    revisora_output = state.get("revisora_output")

    if (
        user_request is None
        or professora_output is None
        or pesquisadora_output is None
        or revisora_output is None
    ):
        raise ValueError(
            "A Redatora precisa receber os resultados "
            "das três agentes anteriores."
        )

    entrada = RedatoraInput(
        user_request=user_request,
        professora_output=professora_output,
        pesquisadora_output=pesquisadora_output,
        revisora_output=revisora_output,
    )

    resultado = redigir_planejamento(entrada)

    return {
        "redatora_output": resultado,
    }
