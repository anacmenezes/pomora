from typing import Literal

from .state import IntakeGraphState


# ============================================================
# ROTEAMENTO APOS PROCESSAR A MENSAGEM
# ============================================================

def route_after_message(
    state: IntakeGraphState,
) -> Literal[
    "validate_confirmation",
    "check_completeness",
    "end",
    "invalid_state",
]:
    """
    Define o caminho após interpretar a mensagem do usuário.

    Possibilidades:
    - Validar uma decisão de confirmação.
    - Verificar a completude dos dados.
    - Encerrar aguardando uma nova interação.
    - Direcionar estados inesperados para tratamento de erro.
    """

    status = state.get("status")
    decision = state.get("confirmation_decision")

    # Solicitação já finalizada.
    if status in ("confirmed", "cancelled"):
        return "end"

    # Usuário está na etapa de confirmação.
    if status == "awaiting_confirmation":

        if decision in ("confirm", "cancel", "unclear"):
            return "validate_confirmation"

        # Sem decisão ou aguardando esclarecimento.
        return "end"

    # Usuário ainda está preenchendo os dados.
    if status == "collecting":
        return "check_completeness"

    # É necessário aguardar uma nova mensagem do usuário.
    if status == "needs_clarification":
        return "end"

    return "invalid_state"


# ============================================================
# ROTEAMENTO APOS VERIFICAR COMPLETUDE
# ============================================================

def route_after_completeness(
    state: IntakeGraphState,
) -> Literal[
    "prepare_confirmation",
    "end",
    "invalid_state",
]:
    """
    Define o caminho após verificar os campos obrigatórios.

    Quando os campos estão completos, prepara o resumo
    para confirmação do usuário.
    """

    status = state.get("status")

    if status == "awaiting_confirmation":
        return "prepare_confirmation"

    if status in (
        "collecting",
        "needs_clarification",
        "confirmed",
        "cancelled",
    ):
        return "end"

    return "invalid_state"


# ============================================================
# ROTEAMENTO APOS VALIDAR CONFIRMACAO
# ============================================================

def route_after_confirmation(
    state: IntakeGraphState,
) -> Literal[
    "recheck_completeness",
    "end",
    "invalid_state",
]:
    """
    Define o caminho após validar a decisão do usuário.

    Possibilidades:
    - Retornar à coleta quando houver correções.
    - Encerrar quando confirmar ou cancelar.
    - Encerrar aguardando esclarecimento.
    - Direcionar estados inesperados para tratamento de erro.
    """

    status = state.get("status")

    # Usuário corrigiu informações.
    if status == "collecting":
        return "recheck_completeness"

    # Solicitação finalizada ou aguardando nova interação.
    if status in (
        "confirmed",
        "cancelled",
        "needs_clarification",
    ):
        return "end"

    return "invalid_state"