
from backend.src.schemas.agent_outputs import (
    RevisoraInput,
    RevisoraOutput,
    PesquisadoraOutput,
    PesquisaDiaria,
)

from backend.src.chains.agents.revisora import (
    revisar_planejamento,
)

from test_pesquisadora_manual import (
    preparar_entrada_pesquisadora,
)


def main():
    print("\n" + "=" * 60)
    print("ETAPA 1 — PREPARAÇÃO DA PROFESSORA")
    print("=" * 60)

    entrada_pesquisadora = preparar_entrada_pesquisadora()

    print("\n" + "=" * 60)
    print("ETAPA 2 — SIMULAÇÃO DO RESULTADO DA PESQUISADORA")
    print("=" * 60)

    pesquisadora_output = PesquisadoraOutput(
        fontes=[],
        pesquisas_diarias=[
            PesquisaDiaria(
                dia=dia,
                status_pesquisa="sem_resultados_suficientes",
                atividades=[],
                justificativa=(
                    "Não foram encontradas atividades "
                    "com evidências suficientes."
                ),
            )
            for dia in range(1, 6)
        ],
    )

    print("Resultado da Pesquisadora preparado.")
    print("Cinco dias sem atividades.")

    print("\n" + "=" * 60)
    print("ETAPA 3 — PREPARAÇÃO DA REVISORA")
    print("=" * 60)

    entrada_revisora = RevisoraInput(
        user_request=entrada_pesquisadora.user_request,
        professora_output=entrada_pesquisadora.professora_output,
        pesquisadora_output=pesquisadora_output,
    )

    print("Entrada da Revisora validada.")

    print("\n" + "=" * 60)
    print("ETAPA 4 — EXECUÇÃO DA REVISORA")
    print("=" * 60)

    resultado = revisar_planejamento(entrada_revisora)

    print("\nRESULTADO FINAL")
    print(resultado.model_dump_json(indent=2))

    print("\n" + "=" * 60)
    print("RESUMO DA REVISÃO")
    print("=" * 60)

    print("Status geral:", resultado.status_geral)

    for revisao in resultado.revisoes_diarias:
        print(
            f"Dia {revisao.dia} | "
            f"Status: {revisao.status} | "
            f"Atividades revisadas: {len(revisao.atividades)}"
        )

    print("\nTESTE DA REVISORA FINALIZADO")


if __name__ == "__main__":
    main()
