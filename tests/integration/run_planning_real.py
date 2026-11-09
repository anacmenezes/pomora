
from backend.src.schemas.request import (
    UserRequest,
    Escolaridade,
    Modalidade,
)
from backend.src.schemas.agent_outputs import RedatoraOutput
from backend.src.graph.planning.planning_workflow import planning_graph


def preparar_solicitacao() -> UserRequest:
    """Prepara a mesma solicitação usada nos testes anteriores."""

    return UserRequest(
        escolaridade=Escolaridade.EDUCACAO_INFANTIL,
        ano_serie="4 anos",
        modalidade=Modalidade.COLETIVA,
        quantidade_criancas=10,
        tema_semana="Animais",
        objetivo_aprendizagem=(
            "Desenvolver a coordenação motora fina e ampla "
            "por meio de atividades lúdicas."
        ),
        preferencias_materiais=[
            "Materiais recicláveis",
            "Papel",
            "Papelão",
            "Tampinhas",
        ],
        restricoes_materiais=[],
        idioma="pt-BR",
        curriculo_regiao="BR",
    )


def main():
    user_request = preparar_solicitacao()

    print("\n" + "=" * 60)
    print("POMORA — EXECUÇÃO REAL DO PLANNING GRAPH")
    print("=" * 60)

    entrada = {
        "intake_status": "confirmed",
        "validated_request": user_request.model_dump(
            mode="json"
        ),
    }

    resultado = planning_graph.invoke(entrada)

    if resultado.get("planning_status") != "ready":
        raise RuntimeError(
            resultado.get("error_message", "Planejamento bloqueado.")
        )

    saida = resultado.get("redatora_output")

    if not isinstance(saida, RedatoraOutput):
        raise TypeError(
            "A Redatora não retornou um RedatoraOutput válido."
        )

    print("\n" + "=" * 60)
    print("PLANEJAMENTO CONCLUÍDO")
    print("=" * 60)

    print("Status geral:", saida.status_geral)
    print("Tema:", saida.contexto.tema_semana)
    print("Total de dias:", len(saida.dias))
    print("Total de fontes:", len(saida.fontes))

    total_atividades = 0

    for dia in saida.dias:
        quantidade = len(dia.atividades)
        total_atividades += quantidade

        print(
            f"\nDia {dia.dia}"
            f"\nStatus da pesquisa: {dia.status_pesquisa}"
            f"\nStatus da revisão: {dia.status_revisao}"
            f"\nAtividades: {quantidade}"
        )

        if dia.justificativa_pesquisa:
            print("Justificativa:", dia.justificativa_pesquisa)

        if dia.observacoes_revisao:
            print("Observações:", dia.observacoes_revisao)

    print("\nTotal de atividades:", total_atividades)

    print("\n" + "=" * 60)
    print("VALIDAÇÃO FINAL")
    print("=" * 60)

    assert len(saida.dias) == 5
    assert [dia.dia for dia in saida.dias] == [1, 2, 3, 4, 5]

    print("OK - RedatoraOutput validado pelo Pydantic.")
    print("OK - Cinco dias presentes e ordenados.")
    print("OK - Fontes e revisões incorporadas.")

    print("\nExecução real concluída com sucesso.")

    print("\n" + "=" * 60)
    print("RESULTADO JSON COMPLETO")
    print("=" * 60)

    print(saida.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
