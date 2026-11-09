from typing import Any, Literal, TypedDict

from ...schemas.request import UserRequest
from ...schemas.agent_outputs import (
    ProfessoraOutput,
    AssistenteOutput,
    RevisoraOutput,
)


# ============================================================
# STATUS DO PLANEJAMENTO
# ============================================================

PlanningStatus = Literal[
    "ready",
    "blocked",
    "completed",
]


# ============================================================
# ESTADO COMPARTILHADO DO PLANEJAMENTO
# ============================================================

class PlanningGraphState(TypedDict, total=False):
    """
    Estado compartilhado do fluxo de planejamento pedagógico.

    Recebe a solicitação confirmada pelo grafo da Márcia
    e armazena os resultados das três agentes do planejamento:

    1. Professora
    2. Assistente
    3. Revisora

    O resultado final é armazenado em revisora_output.
    """

    # --------------------------------------------------------
    # DADOS RECEBIDOS DO GRAFO DA MARCIA
    # --------------------------------------------------------

    intake_status: str | None

    validated_request: dict[str, Any] | None

    # --------------------------------------------------------
    # SOLICITACAO VALIDADA
    # --------------------------------------------------------

    user_request: UserRequest

    # --------------------------------------------------------
    # CONTROLE DO PLANEJAMENTO
    # --------------------------------------------------------

    planning_status: PlanningStatus

    error_message: str | None

    validation_errors: list[str]

    # --------------------------------------------------------
    # RESULTADOS DOS AGENTES
    # --------------------------------------------------------

    professora_output: ProfessoraOutput

    assistente_output: AssistenteOutput

    revisora_output: RevisoraOutput