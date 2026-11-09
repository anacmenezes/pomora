
import pytest
from pydantic import ValidationError

from backend.src.schemas.agent_outputs import (
    RevisaoAtividade,
    RevisaoDiaria,
    RevisoraOutput,
)


def test_atividade_aprovada():
    atividade = RevisaoAtividade(
        atividade_id="d1_a1",
        status="aprovada",
        justificativa="A atividade está adequada aos objetivos pedagógicos.",
    )

    assert atividade.status == "aprovada"


def test_atividade_com_ajustes_exige_recomendacoes():
    with pytest.raises(ValidationError):
        RevisaoAtividade(
            atividade_id="d1_a1",
            status="ajustes_necessarios",
            justificativa="A atividade precisa de pequenas correções.",
        )


def test_atividade_com_ajustes_validos():
    atividade = RevisaoAtividade(
        atividade_id="d1_a1",
        status="ajustes_necessarios",
        justificativa="A atividade precisa de pequenas correções.",
        ajustes_recomendados=[
            "Adaptar os materiais para a faixa etária."
        ],
    )

    assert len(atividade.ajustes_recomendados) == 1


def test_dia_sem_atividades():
    dia = RevisaoDiaria(
        dia=1,
        status="sem_atividades",
        observacoes=["A pesquisa não encontrou atividades suficientes."],
    )

    assert dia.atividades == []


def test_dia_sem_atividades_nao_pode_conter_revisoes():
    with pytest.raises(ValidationError):
        RevisaoDiaria(
            dia=1,
            status="sem_atividades",
            atividades=[
                RevisaoAtividade(
                    atividade_id="d1_a1",
                    status="aprovada",
                    justificativa="A atividade está adequada.",
                )
            ],
        )


def test_revisora_exige_cinco_dias():
    with pytest.raises(ValidationError):
        RevisoraOutput(
            status_geral="aprovado",
            parecer_geral="O planejamento apresenta boa organização pedagógica.",
            avaliacao_pedagogica="Os objetivos estão alinhados às estratégias propostas.",
            revisoes_diarias=[
                RevisaoDiaria(
                    dia=1,
                    status="sem_atividades",
                )
            ],
        )


def test_dia_aprovado():
    dia = RevisaoDiaria(
        dia=1,
        status="aprovado",
        atividades=[
            RevisaoAtividade(
                atividade_id="d1_a1",
                status="aprovada",
                justificativa="A atividade atende aos critérios definidos.",
            )
        ],
    )

    assert dia.status == "aprovado"


def test_dia_deve_respeitar_status_permitidos():
    with pytest.raises(ValidationError):
        RevisaoDiaria(
            dia=1,
            status="pendente",
        )


def test_revisora_deve_conter_cinco_dias_em_ordem():
    dias = [
        RevisaoDiaria(dia=dia, status="sem_atividades")
        for dia in [1, 2, 4, 3, 5]
    ]

    with pytest.raises(ValidationError):
        RevisoraOutput(
            status_geral="aprovado_com_ressalvas",
            parecer_geral="O planejamento apresenta pontos que precisam de atenção.",
            avaliacao_pedagogica="A proposta apresenta coerência entre tema e objetivos.",
            revisoes_diarias=dias,
        )


def test_revisao_geral_com_status_invalido():
    with pytest.raises(ValidationError):
        RevisoraOutput(
            status_geral="pendente",
            parecer_geral="O planejamento apresenta pontos que precisam de atenção.",
            avaliacao_pedagogica="A proposta apresenta coerência entre tema e objetivos.",
            revisoes_diarias=[
                RevisaoDiaria(
                    dia=dia,
                    status="sem_atividades",
                )
                for dia in range(1, 6)
            ],
        )
