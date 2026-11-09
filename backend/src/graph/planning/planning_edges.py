
from typing import Literal

from .planning_state import PlanningGraphState


def route_after_validation(
    state: PlanningGraphState,
) -> Literal["continue", "end"]:
    """
    Define se o planejamento pode começar.

    Solicitações inválidas ou não confirmadas
    encerram o fluxo.
    """

    if state.get("planning_status") == "ready":
        return "continue"

    return "end"
