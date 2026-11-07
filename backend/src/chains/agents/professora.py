
from langchain_core.prompts import ChatPromptTemplate

from ...schemas.agent_outputs import (
    ProfessoraInput,
    ProfessoraOutput,
)
from ..models.openai import get_openai_model
from ..prompts.professora_ppt import PROFESSORA_SYSTEM_PROMPT


def criar_cadeia_professora():
    """Cria a cadeia responsável pela estratégia pedagógica semanal."""

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", PROFESSORA_SYSTEM_PROMPT),
            (
                "human",
                """
                Analise a solicitação pedagógica validada abaixo.

                SOLICITAÇÃO DO USUÁRIO:
                {user_request}

                Construa uma estratégia pedagógica coerente
                para os cinco dias da semana.

                Considere todas as informações fornecidas.
                Não invente informações ausentes.
                """,
            ),
        ]
    )

    modelo = get_openai_model()

    modelo_estruturado = modelo.with_structured_output(
        ProfessoraOutput,
        method="function_calling",
    )

    return prompt | modelo_estruturado


def gerar_estrategia_pedagogica(
    entrada: ProfessoraInput,
) -> ProfessoraOutput:
    """
    Recebe uma solicitação validada e produz
    uma estratégia pedagógica estruturada.
    """

    cadeia = criar_cadeia_professora()

    resultado = cadeia.invoke(
        {
            "user_request": entrada.user_request.model_dump_json(
                indent=2,
            )
        }
    )

    return resultado
