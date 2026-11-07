
from pydantic import BaseModel, ConfigDict, Field

from .request import (
    Escolaridade,
    Idioma,
    Modalidade,
)


class IntakeDraft(BaseModel):
    """
    Armazena os dados parciais coletados pela Márcia.

    Todos os campos podem permanecer vazios durante
    a conversa. A validação de completude acontece
    antes da criação de UserRequest.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    escolaridade: Escolaridade | None = None

    ano_serie: str | None = Field(
        default=None,
        min_length=2,
        max_length=40,
    )

    modalidade: Modalidade | None = None

    quantidade_criancas: int | None = Field(
        default=None,
        ge=1,
        le=100,
    )

    necessidades_adaptacoes: str | None = Field(
        default=None,
        max_length=1000,
    )

    tema_semana: str | None = Field(
        default=None,
        min_length=3,
        max_length=120,
    )

    objetivo_aprendizagem: str | None = Field(
        default=None,
        min_length=10,
        max_length=500,
    )

    preferencias_materiais: list[str] | None = Field(
        default=None,
        max_length=30,
    )

    restricoes_materiais: list[str] | None = Field(
        default=None,
        max_length=30,
    )

    idioma: Idioma | None = None

    curriculo_regiao: str | None = Field(
        default=None,
        min_length=2,
        max_length=10,
    )

    @property
    def campos_pendentes(self) -> list[str]:
        """
        Retorna os campos obrigatórios ainda não preenchidos.
        """

        campos_obrigatorios = [
            "escolaridade",
            "ano_serie",
            "modalidade",
            "quantidade_criancas",
            "tema_semana",
            "objetivo_aprendizagem",
        ]

        return [
            campo
            for campo in campos_obrigatorios
            if getattr(self, campo) is None
        ]

    @property
    def esta_completo(self) -> bool:
        """
        Indica se todos os campos obrigatórios foram preenchidos.
        Não significa que o usuário já confirmou os dados.
        """

        return len(self.campos_pendentes) == 0
