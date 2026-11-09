
import json

from pydantic import BaseModel, ConfigDict, Field
from langchain_core.tools import StructuredTool

from .web_search import buscar_na_web
from .research_budget import ResearchBudget


class WebSearchInput(BaseModel):
    """Parâmetros de entrada para pesquisa na web."""

    model_config = ConfigDict(extra="forbid")

    dia: int = Field(ge=1, le=5, description="Dia da semana, de 1 a 5.")

    query: str = Field(
        min_length=5,
        max_length=500,
        description="Consulta objetiva sobre atividades pedagógicas.",
    )

    num_results: int = Field(default=5, ge=1, le=10)
    gl: str = Field(default="br", min_length=2, max_length=2)
    hl: str = Field(default="pt-br", min_length=2, max_length=10)


def criar_ferramenta_busca_web(
    budget: ResearchBudget,
) -> StructuredTool:
    """Cria ferramenta de busca vinculada ao orçamento da execução."""

    def executar_busca_web(
        dia: int,
        query: str,
        num_results: int = 5,
        gl: str = "br",
        hl: str = "pt-br",
    ) -> str:

        permitido, motivo = budget.reservar_busca(dia, query)

        if not permitido:
            return json.dumps(
                {
                    "status_busca": "bloqueada",
                    "dia": dia,
                    "consulta": query,
                    "motivo": motivo,
                    "orientacao": (
                        "Não tente repetir esta busca. "
                        "Continue com as evidências disponíveis."
                    ),
                },
                ensure_ascii=False,
                indent=2,
            )

        try:
            resultados = buscar_na_web(
                query=query,
                num_results=num_results,
                gl=gl,
                hl=hl,
            )

            return json.dumps(
                {
                    "status_busca": "sucesso",
                    "dia": dia,
                    "consulta": query,
                    "total_resultados": len(resultados),
                    "resultados": resultados,
                    "observacao": (
                        "Resultados candidatos. "
                        "As fontes ainda precisam ser verificadas."
                    ),
                },
                ensure_ascii=False,
                indent=2,
            )

        except Exception as exc:
            return json.dumps(
                {
                    "status_busca": "falha",
                    "dia": dia,
                    "consulta": query,
                    "motivo": f"{type(exc).__name__}: {exc}",
                    "orientacao": (
                        "Descarte esta tentativa e prossiga "
                        "sem repetir a consulta."
                    ),
                },
                ensure_ascii=False,
                indent=2,
            )

    return StructuredTool.from_function(
        func=executar_busca_web,
        name="buscar_atividades_web",
        description=(
            "Pesquisa atividades pedagógicas e referências educacionais. "
            "Informe obrigatoriamente o dia da semana (1 a 5). "
            "Cada dia permite no máximo duas buscas. "
            "Não repita consultas."
        ),
        args_schema=WebSearchInput,
    )
