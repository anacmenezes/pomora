
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from ...schemas.agent_outputs import (
    RedatoraInput,
    RedatoraOutput,
    DiaPlanejamentoRedigido,
    AtividadeRedigida,
)
from ..models.openai import get_openai_model
from ..prompts.redatora_ppt import REDATORA_SYSTEM_PROMPT


# ============================================================
# SCHEMA INTERNO PARA A NARRATIVA
# ============================================================


class RedatoraNarrativaLLM(BaseModel):
    """Campos textuais produzidos pelo modelo."""

    model_config = ConfigDict(extra="forbid")

    apresentacao: str = Field(
        min_length=20,
        max_length=1000,
    )

    orientacoes_gerais: list[str] = Field(
        min_length=3,
        max_length=10,
    )


# ============================================================
# CADEIA DA REDATORA
# ============================================================


def criar_cadeia_redatora():
    """Cria a cadeia responsável pela apresentação textual."""

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", REDATORA_SYSTEM_PROMPT),
            (
                "human",
                """
                SOLICITAÇÃO DO USUÁRIO:

                {user_request}

                PLANEJAMENTO DA PROFESSORA:

                {professora_output}

                RESULTADOS DA PESQUISADORA:

                {pesquisadora_output}

                RESULTADO DA REVISORA:

                {revisora_output}

                PLANEJAMENTO ESTRUTURADO JÁ ORGANIZADO:

                {dias_planejamento}

                INSTRUÇÃO DE CORREÇÃO:

                {correcao_validacao}

                Gere somente a apresentação e as orientações gerais.
                Respeite todos os dados e decisões recebidos.
                """,
            ),
        ]
    )

    modelo = get_openai_model()

    modelo_estruturado = modelo.with_structured_output(
        RedatoraNarrativaLLM,
        method="function_calling",
    )

    return prompt | modelo_estruturado


# ============================================================
# COMPOSIÇÃO DOS CINCO DIAS
# ============================================================


def montar_planejamento_diario(
    entrada: RedatoraInput,
) -> list[DiaPlanejamentoRedigido]:
    """
    Associa estratégias, atividades pesquisadas e revisões.

    A composição é determinística: nenhum dado de atividade
    ou de revisão é criado pelo modelo.
    """

    estrategias = {
        item.dia: item
        for item in entrada.professora_output.estrategias_diarias
    }

    pesquisas = {
        item.dia: item
        for item in entrada.pesquisadora_output.pesquisas_diarias
    }

    revisoes = {
        item.dia: item
        for item in entrada.revisora_output.revisoes_diarias
    }

    dias = []

    for numero_dia in range(1, 6):
        estrategia = estrategias[numero_dia]
        pesquisa = pesquisas[numero_dia]
        revisao = revisoes[numero_dia]

        revisoes_por_id = {
            item.atividade_id: item
            for item in revisao.atividades
        }

        atividades_redigidas = []

        for atividade in pesquisa.atividades:
            revisao_atividade = revisoes_por_id.get(atividade.id)

            if revisao_atividade is None:
                raise ValueError(
                    f"A atividade {atividade.id} do dia {numero_dia} "
                    "não possui uma revisão correspondente."
                )

            atividades_redigidas.append(
                AtividadeRedigida(
                    atividade=atividade,
                    revisao=revisao_atividade,
                )
            )

        dias.append(
            DiaPlanejamentoRedigido(
                dia=numero_dia,
                estrategia=estrategia,
                status_pesquisa=pesquisa.status_pesquisa,
                status_revisao=revisao.status,
                atividades=atividades_redigidas,
                justificativa_pesquisa=pesquisa.justificativa,
                observacoes_revisao=revisao.observacoes,
            )
        )

    return dias


# ============================================================
# GERAÇÃO DA NARRATIVA
# ============================================================


def gerar_narrativa(
    entrada: RedatoraInput,
    dias: list[DiaPlanejamentoRedigido],
) -> RedatoraNarrativaLLM:
    """Gera a apresentação e as orientações gerais."""

    cadeia = criar_cadeia_redatora()

    dados = {
        "user_request": entrada.user_request.model_dump_json(
            indent=2
        ),
        "professora_output": (
            entrada.professora_output.model_dump_json(indent=2)
        ),
        "pesquisadora_output": (
            entrada.pesquisadora_output.model_dump_json(indent=2)
        ),
        "revisora_output": (
            entrada.revisora_output.model_dump_json(indent=2)
        ),
        "dias_planejamento": [
            dia.model_dump(mode="json")
            for dia in dias
        ],
        "correcao_validacao": "",
    }

    try:
        return cadeia.invoke(dados)

    except ValidationError as erro:
        print(
            "Retorno narrativo inválido. "
            "Realizando uma tentativa de correção."
        )

        dados["correcao_validacao"] = (
            "A resposta anterior não cumpriu o schema "
            "RedatoraNarrativaLLM.\n"
            f"Erros encontrados:\n{erro}\n\n"
            "Gere novamente os campos apresentacao e "
            "orientacoes_gerais completos. "
            "Respeite os limites e os tipos definidos no schema. "
            "Não invente informações."
        )

        return cadeia.invoke(dados)


# ============================================================
# FUNÇÃO PRINCIPAL DA REDATORA
# ============================================================


def redigir_planejamento(
    entrada: RedatoraInput,
) -> RedatoraOutput:
    """
    Produz o planejamento pedagógico semanal estruturado.

    1. Organiza os cinco dias.
    2. Preserva as atividades e suas revisões.
    3. Gera a apresentação e as orientações gerais.
    4. Incorpora os dados pedagógicos e as fontes.
    5. Valida o resultado final.
    """

    # 1. Monta os cinco dias de forma determinística.
    dias = montar_planejamento_diario(entrada)

    # 2. Gera somente os campos narrativos.
    narrativa = gerar_narrativa(
        entrada=entrada,
        dias=dias,
    )

    # 3. Monta o resultado final.
    resultado = RedatoraOutput(
        contexto=entrada.user_request,
        apresentacao=narrativa.apresentacao,
        objetivo_geral=(
            entrada.professora_output.objetivo_geral
        ),
        objetivos_especificos=(
            entrada.professora_output.objetivos_especificos
        ),
        justificativa_pedagogica=(
            entrada.professora_output.justificativa_pedagogica
        ),
        progressao_semanal=(
            entrada.professora_output.progressao_semanal
        ),
        criterios_selecao_atividades=(
            entrada.professora_output.criterios_selecao_atividades
        ),
        orientacoes_gerais=narrativa.orientacoes_gerais,
        status_geral=(
            entrada.revisora_output.status_geral
        ),
        parecer_geral=(
            entrada.revisora_output.parecer_geral
        ),
        avaliacao_pedagogica=(
            entrada.revisora_output.avaliacao_pedagogica
        ),
        pontos_atencao=(
            entrada.revisora_output.pontos_atencao
        ),
        dias=dias,
        fontes=entrada.pesquisadora_output.fontes,
    )

    return resultado
