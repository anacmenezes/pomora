
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .request import Idioma, UserRequest


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



class ProfessoraInput(BaseModel):
    """Solicitação validada recebida pela agente Professora."""

    model_config = ConfigDict(extra="forbid")

    user_request: UserRequest = Field(
        description="Solicitação completa e validada pela Márcia."
    )


class EstrategiaDiaria(BaseModel):
    """Estratégia pedagógica definida para um dia da semana."""

    model_config = ConfigDict(extra="forbid")

    dia: int = Field(
        ge=1,
        le=5,
        description="Número do dia no planejamento, de 1 a 5.",
    )

    foco: str = Field(
        min_length=3,
        max_length=150,
        description="Foco pedagógico do dia.",
    )

    objetivo_especifico: str = Field(
        min_length=10,
        max_length=300,
        description="Aprendizagem específica esperada para o dia.",
    )

    intencao_pedagogica: str = Field(
        min_length=10,
        max_length=500,
        description="O que se pretende desenvolver pedagogicamente.",
    )

    estrategia_aprendizagem: str = Field(
        min_length=10,
        max_length=500,
        description=(
            "Abordagem de aprendizagem que deverá orientar "
            "a seleção das atividades."
        ),
    )

    orientacoes_pesquisa: list[str] = Field(
        min_length=1,
        max_length=10,
        description=(
            "Orientações para a Pesquisadora encontrar "
            "atividades adequadas ao foco do dia."
        ),
    )
    
    cuidados_seguranca: list[str] = Field(
        min_length=1,
        max_length=8,
        description=(
            "Cuidados concretos de segurança para executar "
            "as experiências propostas neste dia."
        ),
    )

    adaptacoes_inclusao: list[str] = Field(
        min_length=1,
        max_length=8,
        description=(
            "Alternativas para permitir a participação de "
            "crianças com diferentes ritmos e habilidades."
        ),
    )


class ProfessoraOutput(BaseModel):
    """Plano pedagógico estratégico produzido pela Professora."""

    model_config = ConfigDict(extra="forbid")

    objetivo_geral: str = Field(
        min_length=10,
        max_length=500,
        description="Objetivo pedagógico central da semana.",
    )

    objetivos_especificos: list[str] = Field(
        min_length=2,
        max_length=8,
        description="Aprendizagens específicas esperadas ao longo da semana.",
    )

    justificativa_pedagogica: str = Field(
        min_length=20,
        max_length=1000,
        description=(
            "Justificativa da organização pedagógica proposta, "
            "considerando o contexto da solicitação."
        ),
    )

    progressao_semanal: str = Field(
        min_length=20,
        max_length=1000,
        description=(
            "Explicação de como as aprendizagens evoluem "
            "ao longo dos cinco dias."
        ),
    )

    estrategias_diarias: list[EstrategiaDiaria] = Field(
        min_length=5,
        max_length=5,
        description=(
            "Estratégia pedagógica para cada um dos cinco dias."
        ),
    )

    criterios_selecao_atividades: list[str] = Field(
        min_length=3,
        max_length=10,
        description=(
            "Critérios que a Pesquisadora deverá utilizar "
            "para selecionar as atividades."
        ),
    )

    @model_validator(mode="after")
    def validar_sequencia_dias(self):
        dias = [estrategia.dia for estrategia in self.estrategias_diarias]

        if dias != [1, 2, 3, 4, 5]:
            raise ValueError(
                "As estratégias devem conter exatamente os dias "
                "1, 2, 3, 4 e 5, nessa ordem."
            )

        return self
