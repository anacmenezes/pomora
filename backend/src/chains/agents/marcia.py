
from langchain_core.prompts import ChatPromptTemplate

from ...schemas.agent_outputs import MarciaInput, MarciaOutput
from ..models.openai import get_openai_model
from ..prompts.marcia_ppt import MARCIA_SYSTEM_PROMPT


def criar_cadeia_marcia():
    """
    Cria a cadeia de interpretação da agente Márcia.

    Combina o modelo OpenAI, o prompt e a saída
    estruturada definida pelo Pydantic.
    """

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", MARCIA_SYSTEM_PROMPT),
            (
                "human",
                """
                Interprete a mensagem considerando todo o contexto
                abaixo. Extraia somente informações efetivamente
                fornecidas pelo usuário.

                CONTEXTO DA CONVERSA:
                {contexto}
                """,
            ),
        ]
    )

    modelo = get_openai_model()

    modelo_estruturado = modelo.with_structured_output(
        MarciaOutput,
        method="function_calling",
    )

    return prompt | modelo_estruturado


def interpretar_mensagem(entrada: MarciaInput) -> MarciaOutput:
    """
    Interpreta uma mensagem do usuário e retorna
    informações estruturadas.
    """

    cadeia = criar_cadeia_marcia()

    return cadeia.invoke(
        {
            "contexto": entrada.model_dump_json(exclude_none=True),
        }
    )
