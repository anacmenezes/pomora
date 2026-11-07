
from typing import Literal

from .state import IntakeGraphState


def route_after_message(
    state: IntakeGraphState,
) -> Literal[
    "validate_confirmation",
    "check_completeness",
    "end",
    "invalid_state",
]:
    """Define o caminho após interpretar a mensagem do usuário."""

    status = state.get("status")
    decision = state.get("confirmation_decision")

    if status == "awaiting_confirmation":
        if decision in ("confirm", "cancel", "unclear"):
            return "validate_confirmation"

        return "end"

    if status == "collecting":
        return "check_completeness"

    if status == "needs_clarification":
        return "end"

    return "invalid_state"


def route_after_completeness(
    state: IntakeGraphState,
) -> Literal[
    "prepare_confirmation",
    "end",
    "invalid_state",
]:
    """Define o caminho após verificar os campos obrigatórios."""

    status = state.get("status")

    if status == "awaiting_confirmation":
        return "prepare_confirmation"

    if status in ("collecting", "needs_clarification"):
        return "end"

    return "invalid_state"


def route_after_confirmation(
    state: IntakeGraphState,
) -> Literal[
    "recheck_completeness",
    "end",
    "invalid_state",
]:
    """Define o caminho após validar a decisão do usuário."""

    status = state.get("status")

    if status == "collecting":
        return "recheck_completeness"

    if status in ("confirmed", "cancelled", "needs_clarification"):
        return "end"

    return "invalid_state"
