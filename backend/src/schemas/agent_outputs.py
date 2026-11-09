
from typing import Any, Literal

from pydantic import (
    BaseModel, 
    ConfigDict, 
    Field, 
    model_validator,
    HttpUrl,
)

from .request import Idioma, UserRequest


IntakeField = Literal[
    "escolaridade",
    "ano_serie",
    "modalidade",
    "quantidade_criancas",
    "necessidades_adaptacoes",
    "tema_semana",
    "objetivo_aprendizagem",
    "preferencias_materiais",
    "restricoes_materiais",
    "idioma",
    "curriculo_regiao",
]

ConfirmationDecision = Literal[
    "confirm",
    "correct",
    "cancel",
    "unclear",
]

ConversationStage = Literal[
    "collecting",
    "awaiting_confirmation",
]


class MarciaInput(BaseModel):
    """Contexto enviado pela aplicação para a agente Márcia."""

    model_config = ConfigDict(extra="forbid")

    user_message: str = Field(min_length=1)

    current_data: dict[str, Any] = Field(
        default_factory=dict,
    )

    pending_fields: list[str] = Field(
        default_factory=list,
    )

    conversation_stage: ConversationStage

    language: Idioma = Idioma.PORTUGUES_BR


class MarciaOutput(BaseModel):
    """Resposta estruturada produzida pela agente Márcia."""

    model_config = ConfigDict(extra="forbid")

    updates: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Valores novos ou corrigidos para os campos da solicitação."
        ),
    )

    updated_fields: list[IntakeField] = Field(
        default_factory=list,
        description=(
            "Lista exata dos campos que devem ser atualizados. "
            "Permite distinguir ausência de alteração de um valor nulo."
        ),
    )

    confirmation_decision: ConfirmationDecision | None = Field(
        default=None,
        description=(
            "Decisão identificada quando a aplicação estiver "
            "aguardando confirmação."
        ),
    )

    clarification_question: str | None = Field(
        default=None,
        description=(
            "Pergunta para esclarecer uma informação ambígua, "
            "quando necessário."
        ),
    )
    
    next_question: str | None = Field(
        default=None,
        description=(
            "Próxima pergunta para coletar o primeiro campo "
            "obrigatório ainda não preenchido."
        ),
    )

    @model_validator(mode="after")
    def validar_campos_atualizados(self):
        campos_declarados = set(self.updated_fields)
        campos_recebidos = set(self.updates)

        if len(self.updated_fields) != len(campos_declarados):
            raise ValueError(
                "Não é permitido repetir campos em updated_fields."
            )

        if campos_declarados != campos_recebidos:
            raise ValueError(
                "updated_fields deve corresponder exatamente "
                "às chaves presentes em updates."
            )

        return self



class ProfessoraInput(BaseModel):
    """Solicitação validada recebida pela agente Professora."""

    model_config = ConfigDict(extra="forbid")

    user_request: UserRequest = Field(
        description="Solicitação completa e validada pela Márcia."
    )


class EstrategiaDiaria(BaseModel):
    """Estratégia pedagógica definida para um dia da semana."""

    model_config = ConfigDict(extra="forbid")

    dia: int = Field(
        ge=1,
        le=5,
        description="Número do dia no planejamento, de 1 a 5.",
    )

    foco: str = Field(
        min_length=3,
        max_length=150,
        description="Foco pedagógico do dia.",
    )

    objetivo_especifico: str = Field(
        min_length=10,
        max_length=300,
        description="Aprendizagem específica esperada para o dia.",
    )

    intencao_pedagogica: str = Field(
        min_length=10,
        max_length=500,
        description="O que se pretende desenvolver pedagogicamente.",
    )

    estrategia_aprendizagem: str = Field(
        min_length=10,
        max_length=500,
        description=(
            "Abordagem de aprendizagem que deverá orientar "
            "a seleção das atividades."
        ),
    )

    orientacoes_pesquisa: list[str] = Field(
        min_length=1,
        max_length=10,
        description=(
            "Orientações para a Pesquisadora encontrar "
            "atividades adequadas ao foco do dia."
        ),
    )
    
    cuidados_seguranca: list[str] = Field(
        min_length=1,
        max_length=8,
        description=(
            "Cuidados concretos de segurança para executar "
            "as experiências propostas neste dia."
        ),
    )

    adaptacoes_inclusao: list[str] = Field(
        min_length=1,
        max_length=8,
        description=(
            "Alternativas para permitir a participação de "
            "crianças com diferentes ritmos e habilidades."
        ),
    )


class ProfessoraOutput(BaseModel):
    """Plano pedagógico estratégico produzido pela Professora."""

    model_config = ConfigDict(extra="forbid")

    objetivo_geral: str = Field(
        min_length=10,
        max_length=500,
        description="Objetivo pedagógico central da semana.",
    )

    objetivos_especificos: list[str] = Field(
        min_length=2,
        max_length=8,
        description="Aprendizagens específicas esperadas ao longo da semana.",
    )

    justificativa_pedagogica: str = Field(
        min_length=20,
        max_length=1000,
        description=(
            "Justificativa da organização pedagógica proposta, "
            "considerando o contexto da solicitação."
        ),
    )

    progressao_semanal: str = Field(
        min_length=20,
        max_length=1000,
        description=(
            "Explicação de como as aprendizagens evoluem "
            "ao longo dos cinco dias."
        ),
    )

    estrategias_diarias: list[EstrategiaDiaria] = Field(
        min_length=5,
        max_length=5,
        description=(
            "Estratégia pedagógica para cada um dos cinco dias."
        ),
    )

    criterios_selecao_atividades: list[str] = Field(
        min_length=3,
        max_length=10,
        description=(
            "Critérios que a Pesquisadora deverá utilizar "
            "para selecionar as atividades."
        ),
    )

    @model_validator(mode="after")
    def validar_sequencia_dias(self):
        dias = [estrategia.dia for estrategia in self.estrategias_diarias]

        if dias != [1, 2, 3, 4, 5]:
            raise ValueError(
                "As estratégias devem conter exatamente os dias "
                "1, 2, 3, 4 e 5, nessa ordem."
            )

        return self


class PesquisadoraInput(BaseModel):
    """Dados de entrada para a pesquisa pedagógica."""

    model_config = ConfigDict(extra="forbid")

    user_request: UserRequest
    professora_output: ProfessoraOutput


class FontePesquisa(BaseModel):
    """Identificação e metadados de uma fonte consultada."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str = Field(min_length=1, max_length=50)
    titulo: str = Field(min_length=3, max_length=300)
    url: HttpUrl
    dominio: str = Field(min_length=3, max_length=200)

    autor: str | None = Field(default=None, max_length=200)
    data_publicacao: str | None = Field(default=None, max_length=30)

    idioma: Idioma

    tipo_fonte: Literal[
        "institucional",
        "artigo",
        "blog",
        "video",
        "rede_social",
        "outro",
    ]

    status_extracao: Literal[
        "completa",
        "parcial",
        "somente_metadados",
        "falha",
    ]

    resumo_conteudo: str | None = Field(default=None, max_length=2000)

    limitacoes: list[str] = Field(
        default_factory=list,
        max_length=10,
    )


class EvidenciaPesquisa(BaseModel):
    """Trecho efetivamente recuperado de uma fonte."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    fonte_id: str = Field(min_length=1, max_length=50)

    trecho: str = Field(
        min_length=20,
        max_length=1500,
        description="Trecho encontrado no conteúdo da fonte.",
    )

    contribuicao: str = Field(
        min_length=10,
        max_length=500,
        description="O que esse trecho sustenta na atividade proposta.",
    )


class AtividadePesquisada(BaseModel):
    """Atividade encontrada ou adaptada com base em uma fonte."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str = Field(min_length=1, max_length=50)

    titulo: str = Field(min_length=3, max_length=200)

    descricao: str = Field(min_length=20, max_length=2000)

    objetivo_aprendizagem: str = Field(
        min_length=10,
        max_length=500,
    )

    faixa_etaria_indicada: str | None = Field(
        default=None,
        max_length=200,
    )

    duracao_estimada_minutos: int | None = Field(
        default=None,
        ge=1,
        le=180,
    )

    materiais: list[str] = Field(
        min_length=1,
        max_length=30,
    )

    etapas_execucao: list[str] = Field(
        min_length=2,
        max_length=12,
    )

    cuidados_seguranca: list[str] = Field(
        min_length=1,
        max_length=10,
    )

    adaptacoes_inclusao: list[str] = Field(
        min_length=1,
        max_length=10,
    )

    origem: Literal["encontrada", "adaptada"]

    descricao_adaptacao: str | None = Field(
        default=None,
        max_length=1000,
    )

    fontes_ids: list[str] = Field(
        min_length=1,
        max_length=10,
    )

    evidencias: list[EvidenciaPesquisa] = Field(
        min_length=1,
        max_length=10,
    )

    @model_validator(mode="after")
    def validar_rastreabilidade(self):
        fontes_referenciadas = set(self.fontes_ids)
        fontes_das_evidencias = {
            evidencia.fonte_id for evidencia in self.evidencias
        }

        if not fontes_das_evidencias.issubset(fontes_referenciadas):
            raise ValueError(
                "Toda evidência deve pertencer a uma fonte "
                "informada em fontes_ids."
            )

        if self.origem == "adaptada" and not self.descricao_adaptacao:
            raise ValueError(
                "Atividades adaptadas devem explicar "
                "quais modificações foram realizadas."
            )

        return self


class PesquisaDiaria(BaseModel):
    """Resultados da pesquisa referentes a um dia da semana."""

    model_config = ConfigDict(extra="forbid")

    dia: int = Field(ge=1, le=5)

    status_pesquisa: Literal[
        "resultados_encontrados",
        "sem_resultados_suficientes",
    ]

    atividades: list[AtividadePesquisada] = Field(
        default_factory=list,
        max_length=3,
    )

    justificativa: str | None = Field(
        default=None,
        max_length=1000,
    )

    @model_validator(mode="after")
    def validar_resultados(self):
        if (
            self.status_pesquisa == "resultados_encontrados"
            and not self.atividades
        ):
            raise ValueError(
                "É necessário apresentar pelo menos uma atividade."
            )

        if (
            self.status_pesquisa == "sem_resultados_suficientes"
            and self.atividades
        ):
            raise ValueError(
                "Não devem existir atividades quando "
                "a pesquisa não encontrou resultados suficientes."
            )

        if (
            self.status_pesquisa == "sem_resultados_suficientes"
            and not self.justificativa
        ):
            raise ValueError(
                "Informe por que não foram encontrados "
                "resultados suficientes."
            )

        return self

class PesquisadoraDiaOutput(BaseModel):
    """Resultado da pesquisa pedagógica de um único dia."""

    fontes: list[FontePesquisa] = Field(default_factory=list)

    pesquisa_diaria: PesquisaDiaria

    @model_validator(mode="after")
    def validar_referencias_das_fontes(self):
        ids_fontes = {fonte.id for fonte in self.fontes}

        ids_utilizados = {
            fonte_id
            for atividade in self.pesquisa_diaria.atividades
            for fonte_id in atividade.fontes_ids
        }

        if not ids_utilizados.issubset(ids_fontes):
            raise ValueError(
                "Uma ou mais atividades utilizam fontes "
                "que não foram declaradas no resultado diário."
            )

        return self

class PesquisadoraOutput(BaseModel):
    """Resultado estruturado da pesquisa pedagógica semanal."""

    model_config = ConfigDict(extra="forbid")

    fontes: list[FontePesquisa] = Field(
        default_factory=list,
        max_length=50,
    )

    pesquisas_diarias: list[PesquisaDiaria] = Field(
        min_length=5,
        max_length=5,
    )

    @model_validator(mode="after")
    def validar_pesquisa_semanal(self):
        dias = [pesquisa.dia for pesquisa in self.pesquisas_diarias]

        if dias != [1, 2, 3, 4, 5]:
            raise ValueError(
                "A pesquisa deve apresentar os cinco dias "
                "em ordem, de 1 a 5."
            )

        ids_fontes = [fonte.id for fonte in self.fontes]

        if len(ids_fontes) != len(set(ids_fontes)):
            raise ValueError("Os IDs das fontes devem ser únicos.")

        fontes_disponiveis = set(ids_fontes)

        for pesquisa in self.pesquisas_diarias:
            for atividade in pesquisa.atividades:
                fontes_utilizadas = set(atividade.fontes_ids)

                if not fontes_utilizadas.issubset(fontes_disponiveis):
                    raise ValueError(
                        f"A atividade {atividade.id} utiliza "
                        "uma fonte que não está cadastrada na pesquisa."
                    )

        return self


# ============================================================
# REVISORA
# ============================================================

StatusAtividade = Literal[
    "aprovada",
    "ajustes_necessarios",
    "reprovada",
]

StatusDia = Literal[
    "aprovado",
    "aprovado_com_ressalvas",
    "reprovado",
    "sem_atividades",
]

StatusRevisaoGeral = Literal[
    "aprovado",
    "aprovado_com_ressalvas",
    "reprovado",
]


class RevisoraInput(BaseModel):
    """Dados recebidos pela agente Revisora."""

    model_config = ConfigDict(extra="forbid")

    user_request: UserRequest
    professora_output: ProfessoraOutput
    pesquisadora_output: PesquisadoraOutput


class RevisaoAtividade(BaseModel):
    """Parecer da Revisora sobre uma atividade pesquisada."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    atividade_id: str = Field(
        min_length=1,
        max_length=50,
    )

    status: StatusAtividade

    justificativa: str = Field(
        min_length=10,
        max_length=1000,
        description="Justificativa da decisão tomada.",
    )

    ajustes_recomendados: list[str] = Field(
        default_factory=list,
        max_length=10,
        description="Ajustes necessários antes de utilizar a atividade.",
    )

    @model_validator(mode="after")
    def validar_ajustes(self):
        if (
            self.status == "ajustes_necessarios"
            and not self.ajustes_recomendados
        ):
            raise ValueError(
                "Atividades que precisam de ajustes devem "
                "apresentar recomendações."
            )

        return self


class RevisaoDiaria(BaseModel):
    """Resultado da revisão das atividades de um dia."""

    model_config = ConfigDict(extra="forbid")

    dia: int = Field(ge=1, le=5)

    status: StatusDia

    atividades: list[RevisaoAtividade] = Field(
        default_factory=list,
        max_length=3,
    )

    observacoes: list[str] = Field(
        default_factory=list,
        max_length=10,
    )

    @model_validator(mode="after")
    def validar_atividades(self):
        if self.status == "sem_atividades" and self.atividades:
            raise ValueError(
                "Um dia sem atividades não pode apresentar revisões."
            )

        if self.status != "sem_atividades" and not self.atividades:
            raise ValueError(
                "Dias com outro status devem apresentar "
                "pelo menos uma atividade revisada."
            )

        ids = [atividade.atividade_id for atividade in self.atividades]

        if len(ids) != len(set(ids)):
            raise ValueError(
                "Não é permitido repetir atividades na revisão diária."
            )

        return self


class RevisoraOutput(BaseModel):
    """Parecer final da Revisora sobre o planejamento semanal."""

    model_config = ConfigDict(extra="forbid")

    status_geral: StatusRevisaoGeral

    parecer_geral: str = Field(
        min_length=20,
        max_length=2000,
    )

    avaliacao_pedagogica: str = Field(
        min_length=20,
        max_length=1500,
        description=(
            "Avaliação da coerência pedagógica e da adequação "
            "do planejamento semanal."
        ),
    )

    pontos_atencao: list[str] = Field(
        default_factory=list,
        max_length=15,
    )

    revisoes_diarias: list[RevisaoDiaria] = Field(
        min_length=5,
        max_length=5,
    )

    @model_validator(mode="after")
    def validar_sequencia_dias(self):
        dias = [
            revisao.dia
            for revisao in self.revisoes_diarias
        ]

        if dias != [1, 2, 3, 4, 5]:
            raise ValueError(
                "A revisão deve apresentar exatamente os cinco dias, "
                "em ordem de 1 a 5."
            )

        return self


# ============================================================
# REDATORA
# ============================================================

StatusPesquisaRedatora = Literal[
    "resultados_encontrados",
    "sem_resultados_suficientes",
]


class RedatoraInput(BaseModel):
    """Dados completos recebidos pela agente Redatora."""

    model_config = ConfigDict(extra="forbid")

    user_request: UserRequest
    professora_output: ProfessoraOutput
    pesquisadora_output: PesquisadoraOutput
    revisora_output: RevisoraOutput

    @model_validator(mode="after")
    def validar_consistencia_dos_resultados(self):
        pesquisas = {
            item.dia: item
            for item in self.pesquisadora_output.pesquisas_diarias
        }
        revisoes = {
            item.dia: item
            for item in self.revisora_output.revisoes_diarias
        }

        if set(pesquisas) != {1, 2, 3, 4, 5}:
            raise ValueError(
                "A pesquisa deve conter os cinco dias."
            )

        if set(revisoes) != {1, 2, 3, 4, 5}:
            raise ValueError(
                "A revisão deve conter os cinco dias."
            )

        for dia in range(1, 6):
            ids_pesquisa = {
                atividade.id
                for atividade in pesquisas[dia].atividades
            }

            ids_revisao = {
                atividade.atividade_id
                for atividade in revisoes[dia].atividades
            }

            if ids_pesquisa != ids_revisao:
                raise ValueError(
                    f"Dia {dia}: os IDs das atividades pesquisadas "
                    "não correspondem aos IDs revisados."
                )

        return self


class AtividadeRedigida(BaseModel):
    """Atividade original associada à sua avaliação."""

    model_config = ConfigDict(extra="forbid")

    atividade: AtividadePesquisada
    revisao: RevisaoAtividade

    @model_validator(mode="after")
    def validar_identidade_da_atividade(self):
        if self.atividade.id != self.revisao.atividade_id:
            raise ValueError(
                "A atividade e sua revisão devem possuir o mesmo ID."
            )

        return self


class DiaPlanejamentoRedigido(BaseModel):
    """Planejamento estruturado de um dia da semana."""

    model_config = ConfigDict(extra="forbid")

    dia: int = Field(ge=1, le=5)

    estrategia: EstrategiaDiaria

    status_pesquisa: StatusPesquisaRedatora

    status_revisao: StatusDia

    atividades: list[AtividadeRedigida] = Field(
        default_factory=list,
        max_length=3,
    )

    justificativa_pesquisa: str | None = Field(
        default=None,
        max_length=1000,
    )

    observacoes_revisao: list[str] = Field(
        default_factory=list,
        max_length=10,
    )

    @model_validator(mode="after")
    def validar_dia(self):
        if self.estrategia.dia != self.dia:
            raise ValueError(
                "O dia da estratégia deve corresponder ao dia do planejamento."
            )

        if self.status_pesquisa == "sem_resultados_suficientes":
            if self.atividades:
                raise ValueError(
                    "Um dia sem resultados suficientes não pode "
                    "apresentar atividades."
                )

            if self.status_revisao != "sem_atividades":
                raise ValueError(
                    "Um dia sem atividades deve possuir status "
                    "sem_atividades na revisão."
                )

            if not self.justificativa_pesquisa:
                raise ValueError(
                    "Informe a justificativa para a ausência de atividades."
                )

        if self.status_pesquisa == "resultados_encontrados":
            if not self.atividades:
                raise ValueError(
                    "Resultados encontrados devem apresentar atividades."
                )

            if self.status_revisao == "sem_atividades":
                raise ValueError(
                    "Um dia com atividades não pode ter status sem_atividades."
                )

        ids = [
            item.atividade.id
            for item in self.atividades
        ]

        if len(ids) != len(set(ids)):
            raise ValueError(
                "Não é permitido repetir atividades no mesmo dia."
            )

        return self


class RedatoraOutput(BaseModel):
    """Planejamento pedagógico semanal final do POMORA."""

    model_config = ConfigDict(extra="forbid")

    contexto: UserRequest

    apresentacao: str = Field(
        min_length=20,
        max_length=1000,
    )

    objetivo_geral: str = Field(
        min_length=10,
        max_length=500,
    )

    objetivos_especificos: list[str] = Field(
        min_length=2,
        max_length=8,
    )

    justificativa_pedagogica: str = Field(
        min_length=20,
        max_length=1000,
    )

    progressao_semanal: str = Field(
        min_length=20,
        max_length=1000,
    )

    criterios_selecao_atividades: list[str] = Field(
        min_length=3,
        max_length=10,
    )

    orientacoes_gerais: list[str] = Field(
        min_length=3,
        max_length=10,
    )

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

    dias: list[DiaPlanejamentoRedigido] = Field(
        min_length=5,
        max_length=5,
    )

    fontes: list[FontePesquisa] = Field(
        default_factory=list,
        max_length=50,
    )

    @model_validator(mode="after")
    def validar_planejamento_final(self):
        dias = [item.dia for item in self.dias]

        if dias != [1, 2, 3, 4, 5]:
            raise ValueError(
                "O planejamento deve conter exatamente os dias "
                "1, 2, 3, 4 e 5, nessa ordem."
            )

        ids_atividades = [
            item.atividade.id
            for dia in self.dias
            for item in dia.atividades
        ]

        if len(ids_atividades) != len(set(ids_atividades)):
            raise ValueError(
                "Os IDs das atividades devem ser únicos no planejamento."
            )

        ids_fontes = [fonte.id for fonte in self.fontes]

        if len(ids_fontes) != len(set(ids_fontes)):
            raise ValueError(
                "Os IDs das fontes devem ser únicos."
            )

        fontes_disponiveis = set(ids_fontes)

        for dia in self.dias:
            for item in dia.atividades:
                fontes_utilizadas = set(item.atividade.fontes_ids)

                if not fontes_utilizadas.issubset(fontes_disponiveis):
                    raise ValueError(
                        f"A atividade {item.atividade.id} utiliza "
                        "fontes que não estão no planejamento final."
                    )

        return self
