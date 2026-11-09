
from urllib.parse import urlparse

import httpx

from ...config.settings import settings


SERPER_SEARCH_URL = "https://google.serper.dev/search"
DEFAULT_TIMEOUT = 15.0


class SerperAPIError(RuntimeError):
    """Erro ocorrido durante a comunicação com a API do Serper."""


def buscar_na_web(
    query: str,
    num_results: int = 5,
    gl: str = "br",
    hl: str = "pt-br",
) -> list[dict[str, str | int]]:
    """
    Pesquisa na web utilizando a API do Serper.

    Args:
        query: Termos da pesquisa.
        num_results: Quantidade de resultados desejada (1 a 10).
        gl: País utilizado para localização dos resultados.
        hl: Idioma da pesquisa.

    Returns:
        Lista de resultados com título, URL, trecho, domínio e posição.

    Raises:
        ValueError: Se os parâmetros forem inválidos.
        RuntimeError: Se a chave do Serper não estiver configurada.
        SerperAPIError: Se ocorrer uma falha na comunicação ou resposta.
    """

    if not query or not query.strip():
        raise ValueError("A consulta de pesquisa não pode ser vazia.")

    if not isinstance(num_results, int) or isinstance(num_results, bool):
        raise ValueError("num_results deve ser um número inteiro.")

    if not 1 <= num_results <= 10:
        raise ValueError("num_results deve estar entre 1 e 10.")

    if not gl or not gl.strip():
        raise ValueError("O país da pesquisa não pode ser vazio.")

    if not hl or not hl.strip():
        raise ValueError("O idioma da pesquisa não pode ser vazio.")

    if settings.serper_api_key is None:
        raise RuntimeError("SERPER_API_KEY não está configurada.")

    api_key = settings.serper_api_key.get_secret_value()

    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json",
    }

    payload = {
        "q": query.strip(),
        "num": num_results,
        "gl": gl.strip().lower(),
        "hl": hl.strip().lower(),
    }

    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            response = client.post(
                SERPER_SEARCH_URL,
                headers=headers,
                json=payload,
            )

            response.raise_for_status()

            data = response.json()

    except httpx.TimeoutException as exc:
        raise SerperAPIError(
            "A pesquisa excedeu o tempo limite de resposta."
        ) from exc

    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code

        raise SerperAPIError(
            f"O Serper retornou um erro HTTP: {status_code}."
        ) from exc

    except httpx.RequestError as exc:
        raise SerperAPIError(
            "Não foi possível conectar à API do Serper."
        ) from exc

    except ValueError as exc:
        raise SerperAPIError(
            "A API do Serper retornou uma resposta JSON inválida."
        ) from exc

    resultados = data.get("organic", [])

    if not isinstance(resultados, list):
        raise SerperAPIError(
            "Formato inesperado na resposta da API do Serper."
        )

    resultados_formatados = []

    for item in resultados:
        titulo = item.get("title")
        url = item.get("link")
        trecho = item.get("snippet")

        if not titulo or not url:
            continue

        dominio = urlparse(url).netloc.lower()

        if dominio.startswith("www."):
            dominio = dominio[4:]

        resultados_formatados.append(
            {
                "titulo": titulo,
                "url": url,
                "trecho": trecho or "",
                "dominio": dominio,
                "posicao": item.get(
                    "position",
                    len(resultados_formatados) + 1,
                ),
            }
        )

    return resultados_formatados
