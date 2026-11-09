
from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, ConfigDict, Field

from ...schemas.agent_outputs import (
    RevisoraInput,
    RevisoraOutput,
    RevisaoAtividade,
    RevisaoDiaria,
    StatusRevisaoGeral,
)
from ..models.openai import get_openai_model


# ============================================================
# SCHEMAS AUXILIARES
# ============================================================


class RevisaoDiaLLM(BaseModel):
    """Resultado da avaliação do modelo para um único dia."""

    model_config = ConfigDict(extra="forbid")

    atividades: list[RevisaoAtividade] = Field(
        min_length=1,
        max_length=3,
    )

    observacoes: list[str] = Field(
        default_factory=list,
        max_length=10,
    )


class RevisaoGeralLLM(BaseModel):
    """Avaliação geral do planejamento semanal."""

    model_config = ConfigDict(extra="forbid")

    status_geral: StatusRevisaoGeral

    parecer_geral: str = Field(
        min_length=20,
        max_length=2000,
    )

    avaliacao_pedagogica: str = Field(
        min_length=20,
        max_length=1500,
    )

    pontos_atencao: list[str] = Field(
        default_factory=list,
        max_length=15,
    )


# ============================================================
# REVISÃO INDIVIDUAL DOS DIAS
# ============================================================


def revisar_dia(
    entrada: RevisoraInput,
    dia: int,
) -> RevisaoDiaria:
    """
    Revisa as atividades de um único dia.

    Dias sem atividades são preenchidos diretamente pelo Python.
    Dias com atividades são enviados individualmente ao modelo.
    """

    if dia not in range(1, 6):
        raise ValueError("O dia deve estar entre 1 e 5.")

    pesquisa = next(
        (
            item
            for item in entrada.pesquisadora_output.pesquisas_diarias
            if item.dia == dia
        ),
        None,
    )

    estrategia = next(
        (
            item
            for item in entrada.professora_output.estrategias_diarias
            if item.dia == dia
        ),
        None,
    )

    if pesquisa is None or estrategia is None:
        raise ValueError(
            f"Não foram encontrados os dados necessários para o dia {dia}."
        )

    # Não chama o modelo quando não existem atividades.
    if not pesquisa.atividades:
        return RevisaoDiaria(
            dia=dia,
            status="sem_atividades",
            atividades=[],
            observacoes=[
                pesquisa.justificativa
                or "A pesquisa não encontrou atividades suficientes."
            ],
        )

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
                Você é a Revisora pedagógica do POMORA.

                Sua responsabilidade é avaliar criteriosamente
                as atividades pedagógicas recebidas.

                Analise cada atividade considerando:

                1. ALINHAMENTO PEDAGÓGICO
                - Relação com o objetivo específico do dia.
                - Adequação à faixa etária.
                - Coerência com a estratégia da Professora.

                2. SEGURANÇA
                - Riscos físicos, químicos e biológicos.
                - Adequação dos materiais.
                - Necessidade de supervisão adulta.
                - Cuidados necessários para a idade das crianças.

                3. VIABILIDADE
                - Disponibilidade dos materiais.
                - Clareza das etapas.
                - Compatibilidade com as restrições informadas.

                4. INCLUSÃO
                - Possibilidade de participação de todas as crianças.
                - Adequação das adaptações propostas.
                - Barreiras que possam impedir a participação.

                5. RASTREABILIDADE
                - Verifique se as evidências sustentam a atividade.
                - Não atribua às fontes informações não apresentadas.
                - Não invente fontes ou evidências.

                Utilize exclusivamente os seguintes status:

                - aprovada
                - ajustes_necessarios
                - reprovada

                Para atividades com status ajustes_necessarios,
                apresente recomendações concretas em
                ajustes_recomendados.

                Preserve os IDs originais das atividades.

                Retorne todas as atividades recebidas,
                uma única vez cada.

                Não crie atividades.
                Não invente informações.
                Não omita atividades da avaliação.
                """
            ),
            (
                "human",
                """
                SOLICITAÇÃO DO USUÁRIO:

                {user_request}

                ESTRATÉGIA PEDAGÓGICA DO DIA:

                {estrategia}

                RESULTADOS DA PESQUISA:

                {pesquisa}
                """
            ),
        ]
    )

    modelo = get_openai_model().with_structured_output(
        RevisaoDiaLLM,
        method="function_calling",
    )

    cadeia = prompt | modelo

    resultado = cadeia.invoke(
        {
            "user_request": entrada.user_request.model_dump_json(
                indent=2
            ),
            "estrategia": estrategia.model_dump_json(
                indent=2
            ),
            "pesquisa": pesquisa.model_dump_json(
                indent=2
            ),
        }
    )

    # --------------------------------------------------------
    # VALIDAÇÃO DOS IDs
    # --------------------------------------------------------

    ids_esperados = [
        atividade.id
        for atividade in pesquisa.atividades
    ]

    ids_recebidos = [
        atividade.atividade_id
        for atividade in resultado.atividades
    ]

    if (
        len(ids_esperados) != len(ids_recebidos)
        or set(ids_esperados) != set(ids_recebidos)
    ):
        raise ValueError(
            f"Dia {dia}: os IDs das atividades revisadas "
            "não correspondem exatamente aos IDs recebidos."
        )

    # --------------------------------------------------------
    # DEFINIÇÃO DO STATUS DIÁRIO
    # --------------------------------------------------------

    status_atividades = {
        atividade.status
        for atividade in resultado.atividades
    }

    if "reprovada" in status_atividades:
        status_dia = "reprovado"

    elif "ajustes_necessarios" in status_atividades:
        status_dia = "aprovado_com_ressalvas"

    else:
        status_dia = "aprovado"

    return RevisaoDiaria(
        dia=dia,
        status=status_dia,
        atividades=resultado.atividades,
        observacoes=resultado.observacoes,
    )


# ============================================================
# AVALIAÇÃO GERAL DO PLANEJAMENTO
# ============================================================


def revisar_geral(
    entrada: RevisoraInput,
    revisoes_diarias: list[RevisaoDiaria],
) -> RevisaoGeralLLM:
    """
    Avalia a coerência pedagógica e a qualidade geral
    do planejamento semanal.
    """

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
                Você é a Revisora geral do POMORA.

                Avalie o planejamento pedagógico semanal considerando:

                1. Coerência entre o objetivo geral e os objetivos
                   específicos.
                2. Adequação da progressão pedagógica dos cinco dias.
                3. Alinhamento entre as estratégias da Professora
                   e as atividades pesquisadas.
                4. Segurança e viabilidade do planejamento.
                5. Inclusão e participação das crianças.
                6. Qualidade e rastreabilidade das evidências.

                Considere também os resultados das revisões diárias.

                Utilize exclusivamente:

                - aprovado: planejamento adequado e utilizável.
                - aprovado_com_ressalvas: planejamento utilizável
                  após os ajustes necessários.
                - reprovado: existem problemas relevantes que
                  impedem a utilização do planejamento.

                Não considere um planejamento completo quando
                houver dias sem atividades suficientes.

                Não invente informações, atividades ou evidências.

                Esta avaliação é exclusivamente geral.
                Não gere revisões diárias.
                """
            ),
            (
                "human",
                """
                SOLICITAÇÃO DO USUÁRIO:

                {user_request}

                PLANEJAMENTO DA PROFESSORA:

                {professora_output}

                RESULTADOS DA PESQUISADORA:

                {pesquisadora_output}

                REVISÕES DIÁRIAS JÁ REALIZADAS:

                {revisoes_diarias}

                Gere o parecer geral do planejamento.
                """
            ),
        ]
    )

    modelo = get_openai_model().with_structured_output(
        RevisaoGeralLLM,
        method="function_calling",
    )

    cadeia = prompt | modelo

    return cadeia.invoke(
        {
            "user_request": entrada.user_request.model_dump_json(
                indent=2
            ),
            "professora_output": entrada.professora_output.model_dump_json(
                indent=2
            ),
            "pesquisadora_output": entrada.pesquisadora_output.model_dump_json(
                indent=2
            ),
            "revisoes_diarias": [
                revisao.model_dump(mode="json")
                for revisao in revisoes_diarias
            ],
        }
    )


# ============================================================
# FUNÇÃO PRINCIPAL DA REVISORA
# ============================================================


def revisar_planejamento(
    entrada: RevisoraInput,
) -> RevisoraOutput:
    """
    Executa a revisão completa do planejamento semanal.

    1. Revisa individualmente os cinco dias.
    2. Avalia o planejamento geral.
    3. Monta e valida o RevisoraOutput final.
    """

    # --------------------------------------------------------
    # 1. REVISÃO DOS CINCO DIAS
    # --------------------------------------------------------

    revisoes_diarias = [
        revisar_dia(entrada, dia)
        for dia in range(1, 6)
    ]

    # --------------------------------------------------------
    # 2. AVALIAÇÃO GERAL
    # --------------------------------------------------------

    avaliacao_geral = revisar_geral(
        entrada=entrada,
        revisoes_diarias=revisoes_diarias,
    )

    # --------------------------------------------------------
    # 3. VALIDAÇÃO DO STATUS GERAL
    # --------------------------------------------------------

    status_geral = avaliacao_geral.status_geral

    existe_dia_incompleto = any(
        revisao.status in (
            "sem_atividades",
            "reprovado",
        )
        for revisao in revisoes_diarias
    )

    # Um planejamento com dias incompletos ou reprovados
    # não pode receber aprovação integral.
    if (
        status_geral == "aprovado"
        and existe_dia_incompleto
    ):
        status_geral = "aprovado_com_ressalvas"

    # --------------------------------------------------------
    # 4. COMPOSIÇÃO DO RESULTADO FINAL
    # --------------------------------------------------------

    resultado = RevisoraOutput(
        status_geral=status_geral,
        parecer_geral=avaliacao_geral.parecer_geral,
        avaliacao_pedagogica=(
            avaliacao_geral.avaliacao_pedagogica
        ),
        pontos_atencao=avaliacao_geral.pontos_atencao,
        revisoes_diarias=revisoes_diarias,
    )

    return resultado
