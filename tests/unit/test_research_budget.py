
from backend.src.chains.tools.research_budget import ResearchBudget


def test_limita_duas_buscas_por_dia():
    budget = ResearchBudget()

    assert budget.reservar_busca(1, "atividade animais")[0] is True
    assert budget.reservar_busca(1, "coordenação motora")[0] is True

    permitido, motivo = budget.reservar_busca(1, "circuito motor")

    assert permitido is False
    assert "Limite" in motivo


def test_bloqueia_consulta_repetida():
    budget = ResearchBudget()

    assert budget.reservar_busca(1, "atividade animais")[0] is True

    permitido, motivo = budget.reservar_busca(2, " ATIVIDADE   ANIMAIS ")

    assert permitido is False
    assert "já foi realizada" in motivo


def test_bloqueia_url_repetida():
    budget = ResearchBudget()

    url = "https://exemplo.com/atividade/"

    assert budget.reservar_leitura(1, url)[0] is True

    permitido, motivo = budget.reservar_leitura(
        2,
        "https://EXEMPLO.com/atividade/#secao",
    )

    assert permitido is False
    assert "já foi consultada" in motivo


def test_limite_de_leitura_independente_por_dia():
    budget = ResearchBudget()

    assert budget.reservar_leitura(1, "https://site.com/a")[0] is True
    assert budget.reservar_leitura(1, "https://site.com/b")[0] is True

    permitido, _ = budget.reservar_leitura(1, "https://site.com/c")

    assert permitido is False

    # Outro dia possui orçamento próprio.
    assert budget.reservar_leitura(2, "https://site.com/c")[0] is True
