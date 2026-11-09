from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, ConfigDict, Field, model_validator

from ...schemas.agent_outputs import (
    DiaPlanejamentoFinal,
    RevisoraInput,
    RevisoraOutput,
    StatusRevisaoGeral,
)
from ..models.openai import get_openai_model
from ..prompts.revisora_ppt import REVISORA_SYSTEM_PROMPT


# ============================================================
# SCHEMAS AUXILIARES DA REVISAO
# ============================================================


class RevisaoDiaLLM(BaseModel):
    """
    Observacoes produzidas pela Revisora para um dia
    do planejamento pedagogico.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    dia: int = Field(
        ge=1,
        le=5,
        description="Numero do dia revisado, de 1 a 5.",
    )

    observacoes_revisao: list[str] = Field(
        default_factory=list,
        max_length=10,
        description=(
            "Problemas encontrados, ajustes recomendados ou "
            "observacoes uteis para a execucao da atividade "
            "e dos recursos de apoio."
        ),
    )


class RevisaoGeralLLM(BaseModel):
    """
    Resultado estruturado da revisao pedagogica semanal.

    Este schema representa exclusivamente a avaliacao
    produzida pelo modelo. A composicao do plano final
    e realizada pelo Python.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    apresentacao: str = Field(
        min_length=20,
        max_length=1000,
        description="Apresentacao do planejamento semanal.",
    )

    status_revisao: StatusRevisaoGeral

    parecer_geral: str = Field(
        min_length=20,
        max_length=2000,
        description="Parecer geral sobre o planejamento.",
    )

    avaliacao_pedagogica: str = Field(
        min_length=20,
        max_length=1500,
        description="Avaliacao da coerencia pedagogica semanal.",
    )

    pontos_atencao: list[str] = Field(
        default_factory=list,
        max_length=15,
        description="Pontos que merecem atencao antes da aplicacao.",
    )

    revisoes_diarias: list[RevisaoDiaLLM] = Field(
        min_length=5,
        max_length=5,
        description="Observacoes especificas para cada um dos cinco dias.",
    )

    @model_validator(mode="after")
    def validar_sequencia_dias(self):
        dias = [
            revisao.dia
            for revisao in self.revisoes_diarias
        ]

        if dias != [1, 2, 3, 4, 5]:
            raise ValueError(
                "A revisao deve apresentar exatamente os cinco dias, "
                "em ordem de 1 a 5."
            )

        return self


# ============================================================
# VALIDACAO DOS DADOS DE ENTRADA
# ============================================================


def _validar_dados_entrada(
    entrada: RevisoraInput,
) -> None:
    """
    Verifica se o planejamento da Professora e os recursos
    do Assistente apresentam os mesmos cinco dias.
    """

    dias_planejamento = [
        atividade.dia
        for atividade in entrada.professora_output.atividades_diarias
    ]

    dias_recursos = [
        recursos.dia
        for recursos in entrada.assistente_output.recursos_diarios
    ]

    if dias_planejamento != [1, 2, 3, 4, 5]:
        raise ValueError(
            "O planejamento da Professora deve conter "
            "exatamente os dias 1 a 5, em ordem."
        )

    if dias_recursos != [1, 2, 3, 4, 5]:
        raise ValueError(
            "Os recursos do Assistente devem conter "
            "exatamente os dias 1 a 5, em ordem."
        )


# ============================================================
# CONSTRUCAO DOS DIAS DO PLANEJAMENTO FINAL
# ============================================================


def _construir_dias_finais(
    entrada: RevisoraInput,
    revisao_llm: RevisaoGeralLLM,
) -> list[DiaPlanejamentoFinal]:
    """
    Combina as atividades da Professora, os recursos do Assistente
    e as observacoes produzidas pela Revisora.

    Os dados originais dos agentes sao preservados.
    A Revisora nao reescreve nem inventa atividades ou recursos.
    """

    recursos_por_dia = {
        recursos.dia: recursos
        for recursos in entrada.assistente_output.recursos_diarios
    }

    observacoes_por_dia = {
        revisao.dia: revisao.observacoes_revisao
        for revisao in revisao_llm.revisoes_diarias
    }

    dias_finais: list[DiaPlanejamentoFinal] = []

    for atividade in entrada.professora_output.atividades_diarias:

        dia = atividade.dia

        recursos = recursos_por_dia.get(dia)

        if recursos is None:
            raise ValueError(
                f"Nao foram encontrados recursos do Assistente "
                f"para o dia {dia}."
            )

        observacoes = observacoes_por_dia.get(dia)

        if observacoes is None:
            raise ValueError(
                f"Nao foram encontradas observacoes da Revisora "
                f"para o dia {dia}."
            )

        dia_final = DiaPlanejamentoFinal(
            dia=dia,
            atividade=atividade,
            recursos=recursos,
            observacoes_revisao=observacoes,
        )

        dias_finais.append(dia_final)

    if len(dias_finais) != 5:
        raise ValueError(
            "O planejamento final deve conter exatamente cinco dias."
        )

    return dias_finais


# ============================================================
# CADEIA DE REVISAO
# ============================================================


def criar_cadeia_revisora():
    """
    Cria a cadeia responsavel por revisar o planejamento
    pedagogico e os materiais de apoio.
    """

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                REVISORA_SYSTEM_PROMPT,
            ),
            (
                "human",
                """
                SOLICITACAO VALIDADA DO USUARIO:

                {user_request}

                PLANEJAMENTO PEDAGOGICO DA PROFESSORA:

                {professora_output}

                MATERIAIS DE APOIO DO ASSISTENTE:

                {assistente_output}

                Revise o planejamento e os recursos como um conjunto.

                Considere a coerencia pedagogica, a adequacao a faixa
                etaria, a seguranca, a inclusao e a viabilidade.

                Avalie tambem a relacao entre cada atividade e seus
                respectivos materiais de apoio.

                Preserve os dados originais produzidos pela Professora
                e pelo Assistente.

                Produza:

                - Apresentacao do planejamento.
                - Status geral da revisao.
                - Parecer geral.
                - Avaliacao pedagogica.
                - Pontos de atencao.
                - Observacoes especificas para os cinco dias.

                Retorne exatamente cinco revisoes diarias,
                na ordem de 1 a 5.

                Quando um dia nao apresentar problemas relevantes,
                utilize uma lista vazia em observacoes_revisao.

                Nao crie atividades nem recursos.
                Nao invente informacoes.
                """
            ),
        ]
    )

    modelo = get_openai_model().with_structured_output(
        RevisaoGeralLLM,
        method="function_calling",
    )

    return prompt | modelo


# ============================================================
# FUNCAO PRINCIPAL DA REVISO RA
# ============================================================


def revisar_planejamento(
    entrada: RevisoraInput,
) -> RevisoraOutput:
    """
    Executa a revisao e a consolidacao do planejamento semanal.

    Etapas:

    1. Valida os dados recebidos.
    2. Revisa o planejamento da Professora.
    3. Revisa os recursos do Assistente.
    4. Combina atividades, recursos e observacoes.
    5. Retorna o planejamento final validado pelo Pydantic.
    """

    # --------------------------------------------------------
    # 1. VALIDACAO DOS DADOS DE ENTRADA
    # --------------------------------------------------------

    _validar_dados_entrada(entrada)

    # --------------------------------------------------------
    # 2. CRIACAO DA CADEIA
    # --------------------------------------------------------

    cadeia = criar_cadeia_revisora()

    # --------------------------------------------------------
    # 3. EXECUCAO DA REVISAO
    # --------------------------------------------------------

    resultado = cadeia.invoke(
        {
            "user_request": (
                entrada.user_request.model_dump_json(
                    indent=2,
                )
            ),

            "professora_output": (
                entrada.professora_output.model_dump_json(
                    indent=2,
                )
            ),

            "assistente_output": (
                entrada.assistente_output.model_dump_json(
                    indent=2,
                )
            ),
        }
    )

    # --------------------------------------------------------
    # 4. VALIDACAO DO RETORNO DO MODELO
    # --------------------------------------------------------

    if not isinstance(resultado, RevisaoGeralLLM):
        resultado = RevisaoGeralLLM.model_validate(resultado)

    # --------------------------------------------------------
    # 5. CONSTRUCAO DOS CINCO DIAS
    # --------------------------------------------------------

    dias_finais = _construir_dias_finais(
        entrada=entrada,
        revisao_llm=resultado,
    )

    # --------------------------------------------------------
    # 6. COMPOSICAO DO PLANEJAMENTO FINAL
    # --------------------------------------------------------

    plano_final = RevisoraOutput(
        contexto=entrada.user_request,

        apresentacao=resultado.apresentacao,

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

        vocabulario_semana=(
            entrada.professora_output.vocabulario_semana
        ),

        materiais_gerais=(
            entrada.professora_output.materiais_gerais
        ),

        orientacoes_gerais=(
            entrada.professora_output.orientacoes_gerais
        ),

        status_revisao=resultado.status_revisao,

        parecer_geral=resultado.parecer_geral,

        avaliacao_pedagogica=(
            resultado.avaliacao_pedagogica
        ),

        pontos_atencao=resultado.pontos_atencao,

        dias=dias_finais,
    )

    return plano_final