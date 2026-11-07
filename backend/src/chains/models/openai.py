
from langchain_openai import ChatOpenAI

from ...config.settings import settings


def get_openai_model(
    temperature: float = 0.0,
) -> ChatOpenAI:
    """
    Inicializa o modelo OpenAI utilizado pelas agentes do POMORA.
    """

    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key.get_secret_value(),
        temperature=temperature,
    )
