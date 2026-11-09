
from typing import Any, Literal, TypedDict

from ...schemas.request import UserRequest
from ...schemas.agent_outputs import (
    ProfessoraOutput,
    PesquisadoraOutput,
    RevisoraOutput,
    RedatoraOutput,
)


class PlanningGraphState(TypedDict, total=False):
    """
    Estado compartilhado do fluxo de planejamento pedagógico.

    Recebe a solicitação confirmada pelo Intake e
    armazena os resultados das quatro agentes.
    """

    # Dados recebidos do grafo da Márcia
    intake_status: str | None
    validated_request: dict[str, Any] | None

    # Solicitação convertida e validada pelo Pydantic
    user_request: UserRequest

    # Controle da validação inicial
    planning_status: Literal["ready", "blocked"]
    error_message: str | None
    validation_errors: list[str]

    # Resultados das agentes
    professora_output: ProfessoraOutput
    pesquisadora_output: PesquisadoraOutput
    revisora_output: RevisoraOutput
    redatora_output: RedatoraOutput
