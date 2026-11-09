
import json

from pydantic import BaseModel, ConfigDict, Field
from langchain_core.tools import StructuredTool

from .web_page_reader import ler_pagina_web, PageReaderError
from .research_budget import ResearchBudget


class WebPageReaderInput(BaseModel):
    """Entrada para leitura de uma página web."""

    model_config = ConfigDict(extra="forbid")

    dia: int = Field(
        ge=1,
        le=5,
        description="Dia da semana ao qual a pesquisa pertence.",
    )

    url: str = Field(
        min_length=10,
        max_length=2000,
        description="URL HTTP ou HTTPS encontrada na pesquisa.",
    )


def criar_ferramenta_leitura_pagina(
    budget: ResearchBudget,
) -> StructuredTool:
    """Cria ferramenta de leitura vinculada ao orçamento da execução."""

    def executar_leitura_pagina(dia: int, url: str) -> str:

        permitido, motivo = budget.reservar_leitura(dia, url)

        if not permitido:
            return json.dumps(
                {
                    "status_leitura": "bloqueada",
                    "dia": dia,
                    "url": url,
                    "conteudo": None,
                    "motivo": motivo,
                    "orientacao": (
                        "Não tente novamente esta URL. "
                        "Utilize outra fonte ou registre a limitação."
                    ),
                },
                ensure_ascii=False,
                indent=2,
            )

        try:
            pagina = ler_pagina_web(url)
            conteudo = pagina.get("conteudo")

            if not isinstance(conteudo, str) or not conteudo.strip():
                raise PageReaderError(
                    "A página não retornou conteúdo textual utilizável."
                )

            resultado = {
                "status_leitura": "sucesso",
                "dia": dia,
                "url": pagina.get("url", url),
                "titulo": pagina.get("titulo"),
                "autor": pagina.get("autor"),
                "data_publicacao": pagina.get("data_publicacao"),
                "tamanho_conteudo": len(conteudo),
                "extracao_curta": len(conteudo) < 1000,
                "content": conteudo,
                "title": pagina.get("titulo"),
                "author": pagina.get("autor"),
                "date": pagina.get("data_publicacao"),
                "status_verificacao": "nao_verificado",
            }

        except PageReaderError as exc:
            resultado = {
                "status_leitura": "falha",
                "dia": dia,
                "url": url,
                "conteudo": None,
                "status_verificacao": "nao_verificado",
                "motivo": str(exc),
                "orientacao": (
                    "Descarte esta página como evidência. "
                    "Não repita a leitura."
                ),
            }

        except Exception as exc:
            resultado = {
                "status_leitura": "falha",
                "dia": dia,
                "url": url,
                "conteudo": None,
                "status_verificacao": "nao_verificado",
                "motivo": f"{type(exc).__name__}: {exc}",
                "orientacao": (
                    "Descarte esta página e prossiga sem repetir a URL."
                ),
            }

        return json.dumps(
            resultado,
            ensure_ascii=False,
            indent=2,
        )

    return StructuredTool.from_function(
        func=executar_leitura_pagina,
        name="ler_conteudo_pagina",
        description=(
            "Lê uma página pública encontrada na pesquisa. "
            "Informe obrigatoriamente o dia (1 a 5). "
            "Cada dia permite no máximo duas leituras. "
            "Uma URL só pode ser consultada uma vez por execução. "
            "Descarte páginas cuja leitura falhar."
        ),
        args_schema=WebPageReaderInput,
    )
