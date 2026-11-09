from langchain_core.prompts import ChatPromptTemplate

from ...schemas.agent_outputs import MarciaInput, MarciaOutput
from ..models.openai import get_openai_model
from ..prompts.marcia_ppt import MARCIA_SYSTEM_PROMPT


# ============================================================
# CADEIA DA MARCIA
# ============================================================


def criar_cadeia_marcia():
    """
    Cria a cadeia responsável por interpretar as mensagens
    do usuário e identificar informações da solicitação.

    Combina:
    - Modelo de linguagem.
    - Prompt da Márcia.
    - Saída estruturada definida pelo Pydantic.
    """

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                MARCIA_SYSTEM_PROMPT,
            ),
            (
                "human",
                """
                Interprete a mensagem considerando todo o contexto
                abaixo.

                Extraia somente informações efetivamente fornecidas
                pelo usuário.

                Não invente informações ausentes.
                Não considere uma informação como confirmada quando
                o usuário ainda estiver corrigindo ou esclarecendo
                algum dado.

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


# ============================================================
# INTERPRETACAO DA MENSAGEM
# ============================================================


def interpretar_mensagem(
    entrada: MarciaInput,
) -> MarciaOutput:
    """
    Interpreta uma mensagem do usuário e retorna
    informações estruturadas para o fluxo de atendimento.

    Recebe:
        MarciaInput:
            - Mensagem atual do usuário.
            - Dados já coletados.
            - Campos pendentes.
            - Etapa da conversa.
            - Idioma.

    Retorna:
        MarciaOutput:
            - Atualizações identificadas.
            - Campos atualizados.
            - Decisão de confirmação, quando aplicável.
            - Pergunta de esclarecimento, quando necessária.
            - Próxima pergunta para coleta.
    """

    cadeia = criar_cadeia_marcia()

    resultado = cadeia.invoke(
        {
            "contexto": entrada.model_dump_json(
                indent=2,
                exclude_none=True,
            ),
        }
    )

    if not isinstance(resultado, MarciaOutput):
        resultado = MarciaOutput.model_validate(resultado)

    return resultado