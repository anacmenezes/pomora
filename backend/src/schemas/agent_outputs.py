from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    model_validator,
)

from .request import Idioma, UserRequest


# ============================================================
# MARCIA — COLETA E CONFIRMACAO DA SOLICITACAO
# ============================================================

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
    """Contexto enviado pela aplicacao para a agente Marcia."""

    model_config = ConfigDict(extra="forbid")

    user_message: str = Field(min_length=1)
    current_data: dict[str, Any] = Field(default_factory=dict)
    pending_fields: list[str] = Field(default_factory=list)
    conversation_stage: ConversationStage
    language: Idioma = Idioma.PORTUGUES_BR


class MarciaOutput(BaseModel):
    """Resposta estruturada produzida pela agente Marcia."""

    model_config = ConfigDict(extra="forbid")

    updates: dict[str, Any] = Field(
        default_factory=dict,
        description="Valores novos ou corrigidos para os campos da solicitacao.",
    )
    updated_fields: list[IntakeField] = Field(
        default_factory=list,
        description=(
            "Lista exata dos campos que devem ser atualizados. "
            "Permite distinguir ausencia de alteracao de um valor nulo."
        ),
    )
    confirmation_decision: ConfirmationDecision | None = Field(
        default=None,
        description=(
            "Decisao identificada quando a aplicacao estiver "
            "aguardando confirmacao."
        ),
    )
    clarification_question: str | None = Field(
        default=None,
        description="Pergunta para esclarecer uma informacao ambigua.",
    )
    next_question: str | None = Field(
        default=None,
        description=(
            "Proxima pergunta para coletar o primeiro campo obrigatorio "
            "ainda nao preenchido."
        ),
    )

    @model_validator(mode="after")
    def validar_campos_atualizados(self):
        campos_declarados = set(self.updated_fields)
        campos_recebidos = set(self.updates)

        if len(self.updated_fields) != len(campos_declarados):
            raise ValueError("Nao e permitido repetir campos em updated_fields.")

        if campos_declarados != campos_recebidos:
            raise ValueError(
                "updated_fields deve corresponder exatamente "
                "as chaves presentes em updates."
            )

        return self


# ============================================================
# PROFESSORA — PLANEJAMENTO PEDAGOGICO
# ============================================================


class ProfessoraInput(BaseModel):
    """Solicitacao validada recebida pela agente Professora."""

    model_config = ConfigDict(extra="forbid")

    user_request: UserRequest = Field(
        description="Solicitacao completa e validada pela Marcia."
    )


class AtividadeDiaria(BaseModel):
    """Atividade completa planejada para um dia da semana."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    dia: int = Field(ge=1, le=5, description="Dia do planejamento: 1 a 5.")
    titulo: str = Field(min_length=3, max_length=150)
    objetivo: str = Field(min_length=10, max_length=500)
    descricao: str = Field(
        min_length=20,
        max_length=2000,
        description="Descricao clara da proposta e de como ela acontece.",
    )
    intencao_pedagogica: str = Field(min_length=10, max_length=700)
    campo_experiencia_bncc: str | None = Field(
        default=None,
        max_length=200,
        description=(
            "Campo de experiencia da BNCC, quando se tratar da Educacao Infantil. "
            "Informar o nome, sem inventar codigos."
        ),
    )
    componente_curricular: str | None = Field(
        default=None,
        max_length=200,
        description=(
            "Componente curricular ou area, quando aplicavel ao Ensino Fundamental."
        ),
    )
    duracao_minutos: int = Field(ge=1, le=240)
    materiais: list[str] = Field(min_length=1, max_length=30)
    etapas_execucao: list[str] = Field(
        min_length=2,
        max_length=12,
        description="Passo a passo pratico para o professor executar a atividade.",
    )
    cuidados_seguranca: list[str] = Field(
        min_length=1,
        max_length=10,
        description="Cuidados concretos para executar a atividade com seguranca.",
    )
    adaptacoes_inclusao: list[str] = Field(
        default_factory=list,
        max_length=10,
        description="Alternativas para diferentes ritmos e necessidades de participacao.",
    )


class ProfessoraOutput(BaseModel):
    """Planejamento pedagogico semanal produzido pela Professora."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    objetivo_geral: str = Field(min_length=10, max_length=500)
    objetivos_especificos: list[str] = Field(min_length=2, max_length=10)
    justificativa_pedagogica: str = Field(min_length=20, max_length=1200)
    progressao_semanal: str = Field(min_length=20, max_length=1200)
    atividades_diarias: list[AtividadeDiaria] = Field(
        min_length=5,
        max_length=5,
        description="Uma atividade principal completa para cada dia, de 1 a 5.",
    )
    vocabulario_semana: list[str] = Field(
        min_length=1,
        max_length=30,
        description="Palavras e conceitos que podem ser explorados durante a semana.",
    )
    materiais_gerais: list[str] = Field(
        default_factory=list,
        max_length=40,
        description="Materiais que podem ser separados para mais de um dia.",
    )
    orientacoes_gerais: list[str] = Field(
        default_factory=list,
        max_length=12,
        description="Orientacoes gerais para o professor conduzir a semana.",
    )

    @model_validator(mode="after")
    def validar_sequencia_dias(self):
        dias = [atividade.dia for atividade in self.atividades_diarias]
        if dias != [1, 2, 3, 4, 5]:
            raise ValueError(
                "O planejamento deve conter exatamente uma atividade para "
                "cada dia, em ordem de 1 a 5."
            )
        return self


# ============================================================
# ASSISTENTE — MATERIAIS DE APOIO
# ============================================================


class AssistenteInput(BaseModel):
    """Dados recebidos pelo Assistente para preparar recursos de apoio."""

    model_config = ConfigDict(extra="forbid")

    user_request: UserRequest
    professora_output: ProfessoraOutput


class ImagemApoio(BaseModel):
    """Descricao para gerar ou localizar uma ilustracao de apoio."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    descricao: str = Field(
        min_length=10,
        max_length=500,
        description="O que a ilustracao deve mostrar e seu estilo visual.",
    )
    prompt_geracao: str = Field(
        min_length=10,
        max_length=1200,
        description="Instrucao detalhada para gerar a ilustracao com IA.",
    )
    texto_alternativo: str = Field(
        min_length=5,
        max_length=300,
        description="Descricao acessivel da imagem.",
    )
    legenda: str | None = Field(default=None, max_length=300)
    imagem_url: str | None = Field(
        default=None,
        max_length=2000,
        description="URL ou caminho preenchido apos a geracao da imagem.",
    )


class MusicaApoio(BaseModel):
    """Musica sugerida para apoiar uma atividade."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    titulo: str = Field(min_length=2, max_length=200)
    descricao: str = Field(min_length=10, max_length=700)
    finalidade_pedagogica: str = Field(min_length=10, max_length=500)
    url: HttpUrl | None = Field(
        default=None,
        description="Link da musica, somente quando conhecido e verificado.",
    )


class VideoApoio(BaseModel):
    """Video sugerido para apoiar uma atividade."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    titulo: str = Field(min_length=2, max_length=200)
    descricao: str = Field(min_length=10, max_length=700)
    finalidade_pedagogica: str = Field(min_length=10, max_length=500)
    duracao_minutos: int | None = Field(default=None, ge=1, le=240)
    url: HttpUrl | None = Field(
        default=None,
        description="Link do video, somente quando conhecido e verificado.",
    )


class RecursosDia(BaseModel):
    """Materiais complementares associados a um dia do planejamento."""

    model_config = ConfigDict(extra="forbid")

    dia: int = Field(ge=1, le=5)
    imagens: list[ImagemApoio] = Field(default_factory=list, max_length=8)
    musicas: list[MusicaApoio] = Field(default_factory=list, max_length=5)
    videos: list[VideoApoio] = Field(default_factory=list, max_length=5)
    orientacoes_uso: list[str] = Field(
        default_factory=list,
        max_length=8,
        description="Como utilizar os recursos durante a atividade.",
    )


class AssistenteOutput(BaseModel):
    """Recursos de apoio organizados para os cinco dias da semana."""

    model_config = ConfigDict(extra="forbid")

    recursos_diarios: list[RecursosDia] = Field(min_length=5, max_length=5)
    observacoes: list[str] = Field(default_factory=list, max_length=10)

    @model_validator(mode="after")
    def validar_sequencia_dias(self):
        dias = [recursos.dia for recursos in self.recursos_diarios]
        if dias != [1, 2, 3, 4, 5]:
            raise ValueError(
                "Os recursos devem apresentar exatamente os cinco dias, "
                "em ordem de 1 a 5."
            )
        return self


# ============================================================
# REVISORA — VALIDACAO E ORGANIZACAO DO PLANO FINAL
# ============================================================


StatusRevisaoGeral = Literal[
    "aprovado",
    "aprovado_com_ressalvas",
    "reprovado",
]


class RevisoraInput(BaseModel):
    """Dados recebidos pela Revisora para consolidar o planejamento."""

    model_config = ConfigDict(extra="forbid")

    user_request: UserRequest
    professora_output: ProfessoraOutput
    assistente_output: AssistenteOutput


class DiaPlanejamentoFinal(BaseModel):
    """Atividade e recursos de apoio consolidados para um dia."""

    model_config = ConfigDict(extra="forbid")

    dia: int = Field(ge=1, le=5)
    atividade: AtividadeDiaria
    recursos: RecursosDia
    observacoes_revisao: list[str] = Field(default_factory=list, max_length=10)

    @model_validator(mode="after")
    def validar_correspondencia_dia(self):
        if self.atividade.dia != self.dia:
            raise ValueError("O dia da atividade deve corresponder ao dia do plano.")
        if self.recursos.dia != self.dia:
            raise ValueError("O dia dos recursos deve corresponder ao dia do plano.")
        return self


class PlanoSemanalFinal(BaseModel):
    """Documento semanal consolidado e revisado, pronto para apresentacao."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    contexto: UserRequest
    apresentacao: str = Field(min_length=20, max_length=1000)
    objetivo_geral: str = Field(min_length=10, max_length=500)
    objetivos_especificos: list[str] = Field(min_length=2, max_length=10)
    justificativa_pedagogica: str = Field(min_length=20, max_length=1200)
    progressao_semanal: str = Field(min_length=20, max_length=1200)
    vocabulario_semana: list[str] = Field(min_length=1, max_length=30)
    materiais_gerais: list[str] = Field(default_factory=list, max_length=40)
    orientacoes_gerais: list[str] = Field(default_factory=list, max_length=15)
    status_revisao: StatusRevisaoGeral
    parecer_geral: str = Field(min_length=20, max_length=2000)
    avaliacao_pedagogica: str = Field(min_length=20, max_length=1500)
    pontos_atencao: list[str] = Field(default_factory=list, max_length=15)
    dias: list[DiaPlanejamentoFinal] = Field(min_length=5, max_length=5)

    @model_validator(mode="after")
    def validar_planejamento_final(self):
        dias = [item.dia for item in self.dias]
        if dias != [1, 2, 3, 4, 5]:
            raise ValueError(
                "O planejamento final deve conter exatamente os cinco dias, "
                "em ordem de 1 a 5."
            )
        return self


class RevisoraOutput(PlanoSemanalFinal):
    """Saida final da Revisora, pronta para exibicao ou persistencia."""

    pass
