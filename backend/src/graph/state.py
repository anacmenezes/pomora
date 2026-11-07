
from typing import Annotated, Any, Literal

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from ..schemas.agent_outputs import ConfirmationDecision

IntakeStatus = Literal[
    "collecting",
    "awaiting_confirmation",
    "confirmed",
    "cancelled",
    "needs_clarification",
]

class IntakeGraphState(TypedDict, total=False):
    """
    Estado compartilhado do fluxo conversacional da Márcia.

    O estado é persistido pelo checkpointer do LangGraph,
    permitindo a retomada de conversas.
    """

    user_id: str | None
    request_id: str | None

    messages: Annotated[list[AnyMessage], add_messages]

    intake_data: dict[str, Any]

    status: IntakeStatus
    confirmation_decision: ConfirmationDecision | None

    validated_request: dict[str, Any] | None

    pending_fields: list[str]

    validation_errors: list[str]

    response: str
