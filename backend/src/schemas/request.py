
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Escolaridade(str, Enum):
    EDUCACAO_INFANTIL = "educacao_infantil"
    ENSINO_FUNDAMENTAL_I = "ensino_fundamental_i"
    ENSINO_FUNDAMENTAL_II = "ensino_fundamental_ii"


class Modalidade(str, Enum):
    INDIVIDUAL = "individual"
    COLETIVA = "coletiva"


class Idioma(str, Enum):
    PORTUGUES_BR = "pt-BR"
    INGLES = "en"
    ESPANHOL = "es"


class UserRequest(BaseModel):
    """
    Solicitação completa e validada para geração
    de um planejamento pedagógico semanal.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    escolaridade: Escolaridade

    ano_serie: str = Field(
        min_length=2,
        max_length=40,
        description="Ano, série ou turma, conforme a etapa escolar.",
    )

    modalidade: Modalidade

    quantidade_criancas: int = Field(
        ge=1,
        le=100,
    )

    necessidades_adaptacoes: str | None = Field(
        default=None,
        max_length=1000,
        description=(
            "Necessidades de adaptação informadas pelo usuário. "
            "Não exige diagnóstico médico."
        ),
    )

    tema_semana: str = Field(
        min_length=3,
        max_length=120,
    )

    objetivo_aprendizagem: str = Field(
        min_length=10,
        max_length=500,
    )

    preferencias_materiais: list[str] = Field(
        default_factory=list,
        max_length=30,
    )

    restricoes_materiais: list[str] = Field(
        default_factory=list,
        max_length=30,
    )

    idioma: Idioma = Idioma.PORTUGUES_BR

    curriculo_regiao: str = Field(
        default="BR",
        min_length=2,
        max_length=10,
        description="Referência curricular utilizada no planejamento.",
    )

    @model_validator(mode="after")
    def validar_modalidade_e_quantidade(self):
        if (
            self.modalidade == Modalidade.INDIVIDUAL
            and self.quantidade_criancas != 1
        ):
            raise ValueError(
                "Na modalidade individual, a quantidade de crianças deve ser 1."
            )

        if (
            self.modalidade == Modalidade.COLETIVA
            and self.quantidade_criancas < 2
        ):
            raise ValueError(
                "Na modalidade coletiva, a quantidade deve ser maior que 1."
            )

        return self
