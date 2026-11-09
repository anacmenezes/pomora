
import pytest
from pydantic import ValidationError

from backend.src.schemas.request import (
    Escolaridade,
    Idioma,
    Modalidade,
    UserRequest,
)
from backend.src.schemas.agent_outputs import (
    AtividadePesquisada,
    AtividadeRedigida,
    DiaPlanejamentoRedigido,
    EvidenciaPesquisa,
    EstrategiaDiaria,
    FontePesquisa,
    PesquisaDiaria,
    PesquisadoraOutput,
    ProfessoraOutput,
    RedatoraInput,
    RedatoraOutput,
    RevisaoAtividade,
    RevisaoDiaria,
    RevisoraOutput,
)
from backend.src.chains.agents.redatora import montar_planejamento_diario


def criar_solicitacao():
    return UserRequest(
        escolaridade=Escolaridade.EDUCACAO_INFANTIL,
        ano_serie="Pré-escola",
        modalidade=Modalidade.COLETIVA,
        quantidade_criancas=10,
        tema_semana="Natureza e meio ambiente",
        objetivo_aprendizagem=(
            "Reconhecer elementos da natureza por meio de experiências."
        ),
    )


def criar_estrategia(dia):
    return EstrategiaDiaria(
        dia=dia,
        foco=f"Exploração da natureza no dia {dia}",
        objetivo_especifico="Identificar elementos naturais do ambiente.",
        intencao_pedagogica="Estimular a observação e a curiosidade.",
        estrategia_aprendizagem="Aprendizagem por investigação e exploração.",
        orientacoes_pesquisa=["Atividades práticas e adequadas à faixa etária."],
        cuidados_seguranca=["Supervisão constante de um adulto."],
        adaptacoes_inclusao=["Permitir diferentes formas de participação."],
    )


def criar_atividade(dia):
    atividade_id = f"atividade_dia_{dia}"

    return AtividadePesquisada(
        id=atividade_id,
        titulo=f"Exploração da natureza {dia}",
        descricao=(
            "As crianças irão observar elementos naturais e conversar "
            "sobre suas características."
        ),
        objetivo_aprendizagem="Reconhecer elementos naturais.",
        materiais=["Folhas", "Pedras grandes"],
        etapas_execucao=[
            "Apresentar os materiais às crianças.",
            "Convidar as crianças a observar e comparar os elementos.",
        ],
        cuidados_seguranca=["Utilizar materiais limpos e seguros."],
        adaptacoes_inclusao=["Oferecer apoio individual quando necessário."],
        origem="encontrada",
        fontes_ids=["fonte_1"],
        evidencias=[
            EvidenciaPesquisa(
                fonte_id="fonte_1",
                trecho=(
                    "A exploração de elementos naturais permite observar "
                    "características e diferenças entre materiais."
                ),
                contribuicao=(
                    "Fundamenta a proposta de observação dos elementos."
                ),
            )
        ],
    )


def criar_fonte():
    return FontePesquisa(
        id="fonte_1",
        titulo="Educação ambiental na educação infantil",
        url="https://example.org/educacao-ambiental",
        dominio="example.org",
        idioma=Idioma.PORTUGUES_BR,
        tipo_fonte="institucional",
        status_extracao="completa",
    )


def criar_entrada():
    estrategias = [criar_estrategia(dia) for dia in range(1, 6)]

    professora = ProfessoraOutput(
        objetivo_geral="Desenvolver a percepção sobre a natureza.",
        objetivos_especificos=[
            "Observar elementos naturais.",
            "Comparar características dos elementos.",
        ],
        justificativa_pedagogica=(
            "A proposta favorece a aprendizagem por exploração."
        ),
        progressao_semanal=(
            "As experiências avançam da observação para a comparação."
        ),
        estrategias_diarias=estrategias,
        criterios_selecao_atividades=[
            "Adequação à faixa etária.",
            "Segurança dos materiais.",
            "Alinhamento aos objetivos.",
        ],
    )

    pesquisas = []
    revisoes = []

    for dia in range(1, 6):
        if dia < 5:
            atividade = criar_atividade(dia)

            pesquisas.append(
                PesquisaDiaria(
                    dia=dia,
                    status_pesquisa="resultados_encontrados",
                    atividades=[atividade],
                )
            )

            revisoes.append(
                RevisaoDiaria(
                    dia=dia,
                    status="aprovado",
                    atividades=[
                        RevisaoAtividade(
                            atividade_id=atividade.id,
                            status="aprovada",
                            justificativa="A atividade atende aos critérios.",
                        )
                    ],
                )
            )
        else:
            pesquisas.append(
                PesquisaDiaria(
                    dia=dia,
                    status_pesquisa="sem_resultados_suficientes",
                    atividades=[],
                    justificativa="Não foram encontrados resultados suficientes.",
                )
            )

            revisoes.append(
                RevisaoDiaria(
                    dia=dia,
                    status="sem_atividades",
                    atividades=[],
                    observacoes=["Não há atividades para avaliar."],
                )
            )

    pesquisadora = PesquisadoraOutput(
        fontes=[criar_fonte()],
        pesquisas_diarias=pesquisas,
    )

    revisora = RevisoraOutput(
        status_geral="aprovado_com_ressalvas",
        parecer_geral="Quatro dias possuem atividades aprovadas.",
        avaliacao_pedagogica="As propostas estão alinhadas aos objetivos.",
        pontos_atencao=["O quinto dia precisa de novas atividades."],
        revisoes_diarias= revisoes,
    )

    return RedatoraInput(
        user_request=criar_solicitacao(),
        professora_output=professora,
        pesquisadora_output=pesquisadora,
        revisora_output=revisora,
    )


def test_redatora_monta_exatamente_cinco_dias():
    entrada = criar_entrada()

    dias = montar_planejamento_diario(entrada)

    assert len(dias) == 5
    assert [dia.dia for dia in dias] == [1, 2, 3, 4, 5]


def test_redatora_preserva_estrategias_diarias():
    entrada = criar_entrada()

    dias = montar_planejamento_diario(entrada)

    for dia in dias:
        estrategia_original = entrada.professora_output.estrategias_diarias[
            dia.dia - 1
        ]

        assert dia.estrategia == estrategia_original


def test_redatora_associa_atividade_a_revisao_corretamente():
    entrada = criar_entrada()

    dias = montar_planejamento_diario(entrada)

    for dia in dias[:4]:
        assert len(dia.atividades) == 1

        atividade_redigida = dia.atividades[0]

        assert (
            atividade_redigida.atividade.id
            == atividade_redigida.revisao.atividade_id
        )


def test_redatora_preserva_dia_sem_atividades():
    entrada = criar_entrada()

    dias = montar_planejamento_diario(entrada)

    quinto_dia = dias[4]

    assert quinto_dia.dia == 5
    assert quinto_dia.atividades == []
    assert quinto_dia.status_pesquisa == "sem_resultados_suficientes"
    assert quinto_dia.status_revisao == "sem_atividades"
    assert quinto_dia.justificativa_pesquisa is not None


def test_redatora_input_rejeita_ids_de_revisao_incompativeis():
    entrada = criar_entrada()

    dados = entrada.model_dump()
    dados["revisora_output"]["revisoes_diarias"][0]["atividades"][0][
        "atividade_id"
    ] = "id_inexistente"

    with pytest.raises(ValidationError):
        RedatoraInput.model_validate(dados)


def test_atividade_redigida_rejeita_revisao_de_outro_id():
    atividade = criar_atividade(1)

    revisao = RevisaoAtividade(
        atividade_id="outro_id",
        status="aprovada",
        justificativa="A atividade atende aos critérios.",
    )

    with pytest.raises(ValidationError):
        AtividadeRedigida(
            atividade=atividade,
            revisao=revisao,
        )


def test_dia_redigido_rejeita_dia_sem_atividades_inconsistente():
    entrada = criar_entrada()
    estrategia = entrada.professora_output.estrategias_diarias[4]

    with pytest.raises(ValidationError):
        DiaPlanejamentoRedigido(
            dia=5,
            estrategia=estrategia,
            status_pesquisa="sem_resultados_suficientes",
            status_revisao="aprovado",
            atividades=[],
            justificativa_pesquisa="Não foram encontrados resultados.",
        )


def test_redatora_preserva_fontes():
    entrada = criar_entrada()

    dias = montar_planejamento_diario(entrada)

    ids_fontes = {
        fonte.id for fonte in entrada.pesquisadora_output.fontes
    }

    for dia in dias:
        for item in dia.atividades:
            assert set(item.atividade.fontes_ids).issubset(ids_fontes)


def test_redatora_output_rejeita_dias_fora_de_ordem():
    entrada = criar_entrada()
    dias = montar_planejamento_diario(entrada)

    with pytest.raises(ValidationError):
        RedatoraOutput(
            contexto=entrada.user_request,
            apresentacao="Este é um planejamento pedagógico semanal.",
            objetivo_geral=entrada.professora_output.objetivo_geral,
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
            orientacoes_gerais=[
                "Organizar os materiais.",
                "Supervisionar as atividades.",
                "Respeitar o ritmo das crianças.",
            ],
            status_geral=entrada.revisora_output.status_geral,
            parecer_geral=entrada.revisora_output.parecer_geral,
            avaliacao_pedagogica=(
                entrada.revisora_output.avaliacao_pedagogica
            ),
            pontos_atencao=entrada.revisora_output.pontos_atencao,
            dias=list(reversed(dias)),
            fontes=entrada.pesquisadora_output.fontes,
        )
