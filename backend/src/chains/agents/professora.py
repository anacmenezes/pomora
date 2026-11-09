
from langchain_core.prompts import ChatPromptTemplate
from pydantic import ValidationError

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

            INSTRUÇÃO DE CORREÇÃO:
            {correcao_validacao}
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

    Realiza uma única tentativa de correção
    caso o retorno não cumpra o schema.
    """

    cadeia = criar_cadeia_professora()

    dados = {
        "user_request": entrada.user_request.model_dump_json(
            indent=2,
        ),
        "correcao_validacao": "",
    }

    try:
        return cadeia.invoke(dados)

    except ValidationError as erro:
        print(
            "Retorno da Professora inválido. "
            "Realizando uma tentativa de correção."
        )

        dados["correcao_validacao"] = (
            "A resposta anterior não cumpriu o schema. "
            "Corrija os seguintes erros:\n"
            f"{erro}\n\n"
            "Gere novamente a estrutura completa. "
            "Não omita nenhum campo obrigatório. "
            "Especialmente, cada um dos cinco dias deve "
            "conter pelo menos uma adaptação concreta "
            "em adaptacoes_inclusao. "
            "Não utilize listas vazias para campos obrigatórios."
        )

        return cadeia.invoke(dados)
