
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .request import Idioma


IntakeField = Literal[
    "escolaridade",
    "ano_serie",
    "modalidade",
    "quantidade_criancas",
    "necessidades_adaptacoes",
    "tema_semana",
    "objetivo_aprendizagem",
    "preferencias_materiais",
    "restricoes_materiais",
    "idioma",
    "curriculo_regiao",
]

ConfirmationDecision = Literal[
    "confirm",
    "correct",
    "cancel",
    "unclear",
]

ConversationStage = Literal[
    "collecting",
    "awaiting_confirmation",
]


class MarciaInput(BaseModel):
    """Contexto enviado pela aplicação para a agente Márcia."""

    model_config = ConfigDict(extra="forbid")

    user_message: str = Field(min_length=1)

    current_data: dict[str, Any] = Field(
        default_factory=dict,
    )

    pending_fields: list[str] = Field(
        default_factory=list,
    )

    conversation_stage: ConversationStage

    language: Idioma = Idioma.PORTUGUES_BR


class MarciaOutput(BaseModel):
    """Resposta estruturada produzida pela agente Márcia."""

    model_config = ConfigDict(extra="forbid")

    updates: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Valores novos ou corrigidos para os campos da solicitação."
        ),
    )

    updated_fields: list[IntakeField] = Field(
        default_factory=list,
        description=(
            "Lista exata dos campos que devem ser atualizados. "
            "Permite distinguir ausência de alteração de um valor nulo."
        ),
    )

    confirmation_decision: ConfirmationDecision | None = Field(
        default=None,
        description=(
            "Decisão identificada quando a aplicação estiver "
            "aguardando confirmação."
        ),
    )

    clarification_question: str | None = Field(
        default=None,
        description=(
            "Pergunta para esclarecer uma informação ambígua, "
            "quando necessário."
        ),
    )
    
    next_question: str | None = Field(
        default=None,
        description=(
            "Próxima pergunta para coletar o primeiro campo "
            "obrigatório ainda não preenchido."
        ),
    )

    @model_validator(mode="after")
    def validar_campos_atualizados(self):
        campos_declarados = set(self.updated_fields)
        campos_recebidos = set(self.updates)

        if len(self.updated_fields) != len(campos_declarados):
            raise ValueError(
                "Não é permitido repetir campos em updated_fields."
            )

        if campos_declarados != campos_recebidos:
            raise ValueError(
                "updated_fields deve corresponder exatamente "
                "às chaves presentes em updates."
            )

        return self
