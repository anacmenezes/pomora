
from unittest.mock import patch

import pytest

from backend.src.graph.planning import planning_nodes
from backend.src.graph.planning.planning_nodes import (
    validar_solicitacao_confirmada,
)
from backend.src.graph.planning.planning_workflow import (
    criar_workflow_planejamento,
)
from backend.src.schemas.agent_outputs import (
    ProfessoraInput,
    PesquisadoraInput,
    RevisoraInput,
    RedatoraInput,
)
from backend.src.schemas.request import UserRequest


@pytest.fixture
def entrada():
    """
    Reutiliza os dados sintéticos já utilizados
    nos testes de schemas da Redatora.
    """
    from tests.unit.test_redatora_schemas import criar_entrada

    return criar_entrada()


@pytest.fixture
def solicitacao_confirmada(entrada):
    return {
        "intake_status": "confirmed",
        "validated_request": entrada.user_request.model_dump(
            mode="json"
        ),
    }


def test_bloqueia_solicitacao_nao_confirmada():
    resultado = validar_solicitacao_confirmada({
        "intake_status": "collecting",
        "validated_request": None,
    })

    assert resultado["planning_status"] == "blocked"


def test_bloqueia_solicitacao_sem_dados():
    resultado = validar_solicitacao_confirmada({
        "intake_status": "confirmed",
        "validated_request": None,
    })

    assert resultado["planning_status"] == "blocked"


def test_valida_e_converte_user_request(entrada):
    dados = entrada.user_request.model_dump(mode="json")

    resultado = validar_solicitacao_confirmada({
        "intake_status": "confirmed",
        "validated_request": dados,
    })

    assert resultado["planning_status"] == "ready"
    assert isinstance(resultado["user_request"], UserRequest)


def test_bloqueia_dados_invalidos():
    resultado = validar_solicitacao_confirmada({
        "intake_status": "confirmed",
        "validated_request": {
            "escolaridade": "invalida",
        },
    })

    assert resultado["planning_status"] == "blocked"
    assert resultado["validation_errors"]


def test_executa_agentes_na_ordem_correta(
    entrada,
    solicitacao_confirmada,
):
    chamadas = []

    def mock_professora(dados):
        assert isinstance(dados, ProfessoraInput)
        chamadas.append("professora")
        return entrada.professora_output

    def mock_pesquisadora(dados):
        assert isinstance(dados, PesquisadoraInput)
        chamadas.append("pesquisadora")
        return entrada.pesquisadora_output

    def mock_revisora(dados):
        assert isinstance(dados, RevisoraInput)
        chamadas.append("revisora")
        return entrada.revisora_output

    def mock_redatora(dados):
        assert isinstance(dados, RedatoraInput)
        chamadas.append("redatora")
        return entrada.revisora_output

    workflow = criar_workflow_planejamento()

    with (
        patch.object(
            planning_nodes,
            "gerar_estrategia_pedagogica",
            side_effect=mock_professora,
        ),
        patch.object(
            planning_nodes,
            "pesquisar_atividades_pedagogicas",
            side_effect=mock_pesquisadora,
        ),
        patch.object(
            planning_nodes,
            "revisar_planejamento",
            side_effect=mock_revisora,
        ),
        patch.object(
            planning_nodes,
            "redigir_planejamento",
            side_effect=mock_redatora,
        ),
    ):
        resultado = workflow.invoke(solicitacao_confirmada)

    assert chamadas == [
        "professora",
        "pesquisadora",
        "revisora",
        "redatora",
    ]

    assert resultado["planning_status"] == "ready"


def test_redatora_executa_com_revisao_reprovada(
    entrada,
    solicitacao_confirmada,
):
    chamadas = []

    revisao_reprovada = entrada.revisora_output.model_copy(
        update={"status_geral": "reprovado"}
    )

    def mock_professora(dados):
        return entrada.professora_output

    def mock_pesquisadora(dados):
        return entrada.pesquisadora_output

    def mock_revisora(dados):
        return revisao_reprovada

    def mock_redatora(dados):
        chamadas.append("redatora")
        assert dados.revisora_output.status_geral == "reprovado"
        return entrada.revisora_output

    workflow = criar_workflow_planejamento()

    with (
        patch.object(
            planning_nodes,
            "gerar_estrategia_pedagogica",
            side_effect=mock_professora,
        ),
        patch.object(
            planning_nodes,
            "pesquisar_atividades_pedagogicas",
            side_effect=mock_pesquisadora,
        ),
        patch.object(
            planning_nodes,
            "revisar_planejamento",
            side_effect=mock_revisora,
        ),
        patch.object(
            planning_nodes,
            "redigir_planejamento",
            side_effect=mock_redatora,
        ),
    ):
        workflow.invoke(solicitacao_confirmada)

    assert chamadas == ["redatora"]
