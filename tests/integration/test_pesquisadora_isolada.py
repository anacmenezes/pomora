
from test_pesquisadora_manual import (
    preparar_entrada_pesquisadora,
)

from backend.src.chains.agents.pesquisadora import (
    pesquisar_atividades_pedagogicas,
)


def main():
    print("\nINICIANDO PREPARAÇÃO DA ENTRADA")

    entrada = preparar_entrada_pesquisadora()

    print("\nINICIANDO PESQUISADORA ISOLADAMENTE")

    resultado = pesquisar_atividades_pedagogicas(
        entrada
    )

    print("\nRESULTADO FINAL")
    print(resultado.model_dump_json(indent=2))

    print("\nRESUMO")
    print("Total de fontes:", len(resultado.fontes))

    for pesquisa in resultado.pesquisas_diarias:
        print(
            f"Dia {pesquisa.dia} | "
            f"Status: {pesquisa.status_pesquisa} | "
            f"Atividades: {len(pesquisa.atividades)}"
        )

        if pesquisa.justificativa:
            print("Justificativa:", pesquisa.justificativa)

    print("\nTESTE FINALIZADO")


if __name__ == "__main__":
    main()
