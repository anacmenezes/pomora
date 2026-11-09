
import ipaddress
import socket
from urllib.parse import urlparse

import httpx
import trafilatura
from trafilatura import extract_metadata


DEFAULT_TIMEOUT = 20.0
MAX_PAGE_SIZE = 1_000_000  # 1 MB
USER_AGENT = "POMORA-EducationalResearch/1.0"


class PageReaderError(RuntimeError):
    """Erro durante o acesso ou a extração de uma página."""


def validar_url_publica(url: str) -> None:
    """Valida o endereço e evita acesso a destinos locais ou privados."""

    try:
        parsed = urlparse(url)
    except ValueError as exc:
        raise ValueError("URL inválida.") from exc

    if parsed.scheme not in {"http", "https"}:
        raise ValueError("A URL deve utilizar HTTP ou HTTPS.")

    if not parsed.hostname:
        raise ValueError("A URL não possui um domínio válido.")

    if parsed.username or parsed.password:
        raise ValueError("URLs com credenciais não são permitidas.")

    hostname = parsed.hostname

    try:
        enderecos = socket.getaddrinfo(
            hostname,
            parsed.port or (443 if parsed.scheme == "https" else 80),
            type=socket.SOCK_STREAM,
        )
    except (socket.gaierror, OSError) as exc:
        raise PageReaderError(
            "Não foi possível resolver o domínio da página."
        ) from exc

    if not enderecos:
        raise PageReaderError("O domínio não retornou endereços IP.")

    for endereco in enderecos:
        ip = ipaddress.ip_address(endereco[4][0].split("%")[0])

        if not ip.is_global:
            raise ValueError(
                "A URL aponta para um endereço não público."
            )


def ler_pagina_web(url: str) -> dict[str, str | None]:
    """
    Acessa uma página pública e extrai seu conteúdo principal.

    O conteúdo retornado é material externo não verificado.
    """

    if not url or not url.strip():
        raise ValueError("A URL não pode ser vazia.")

    url = url.strip()
    validar_url_publica(url)

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml",
    }

    try:
        with httpx.Client(
            timeout=DEFAULT_TIMEOUT,
            follow_redirects=False,
            headers=headers,
        ) as client:
            with client.stream("GET", url) as response:

                if 300 <= response.status_code < 400:
                    raise PageReaderError(
                        "A página solicitou um redirecionamento. "
                        "O leitor não segue redirecionamentos automaticamente."
                    )

                response.raise_for_status()

                content_type = response.headers.get(
                    "content-type", ""
                ).lower()

                if (
                    "text/html" not in content_type
                    and "application/xhtml+xml" not in content_type
                ):
                    raise PageReaderError(
                        "A URL não retornou um documento HTML."
                    )

                content_length = response.headers.get("content-length")

                if content_length:
                    try:
                        if int(content_length) > MAX_PAGE_SIZE:
                            raise PageReaderError(
                                "A página ultrapassa o limite de tamanho permitido."
                            )
                    except ValueError as exc:
                        raise PageReaderError(
                            "A página informou um tamanho inválido."
                        ) from exc

                partes = []
                tamanho_total = 0

                for parte in response.iter_bytes():
                    tamanho_total += len(parte)

                    if tamanho_total > MAX_PAGE_SIZE:
                        raise PageReaderError(
                            "O conteúdo ultrapassa o limite de 1 MB."
                        )

                    partes.append(parte)

                encoding = response.encoding or "utf-8"
                html = b"".join(partes).decode(
                    encoding,
                    errors="replace",
                )

                url_final = str(response.url)

    except PageReaderError:
        raise

    except httpx.TimeoutException as exc:
        raise PageReaderError(
            "O acesso à página excedeu o tempo limite."
        ) from exc

    except httpx.HTTPStatusError as exc:
        raise PageReaderError(
            f"A página retornou erro HTTP {exc.response.status_code}."
        ) from exc

    except httpx.RequestError as exc:
        raise PageReaderError(
            "Não foi possível acessar a página."
        ) from exc

    except (UnicodeError, ValueError) as exc:
        raise PageReaderError(
            "Não foi possível interpretar o conteúdo da página."
        ) from exc

    conteudo = trafilatura.extract(
        html,
        output_format="txt",
        include_comments=False,
        include_tables=True,
        favor_precision=True,
    )

    if not conteudo or not conteudo.strip():
        raise PageReaderError(
            "Não foi possível extrair o conteúdo principal da página."
        )

    metadata = extract_metadata(html)

    return {
        "url": url_final,
        "titulo": metadata.title if metadata else None,
        "autor": metadata.author if metadata else None,
        "data_publicacao": metadata.date if metadata else None,
        "conteudo": conteudo.strip(),
    }
