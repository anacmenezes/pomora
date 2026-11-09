
from backend.src.schemas.request import (
    UserRequest,
    Escolaridade,
    Modalidade,
)

from backend.src.schemas.agent_outputs import (
    ProfessoraInput,
    PesquisadoraInput,
)

from backend.src.chains.agents.professora import (
    gerar_estrategia_pedagogica,
)

from backend.src.chains.agents.pesquisadora import (
    pesquisar_atividades_pedagogicas,
)


def preparar_entrada_pesquisadora() -> PesquisadoraInput:
    """
    Prepara a solicitação do usuário, gera a estratégia pedagógica
    e retorna a entrada validada para a Pesquisadora.
    """

    user_request = UserRequest(
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

    print("\n" + "=" * 60)
    print("ETAPA 1 — PROFESSORA")
    print("=" * 60)

    professora_input = ProfessoraInput(
        user_request=user_request
    )

    professora_output = gerar_estrategia_pedagogica(
        professora_input
    )

    print("\nEstratégia pedagógica gerada:")
    print(professora_output.model_dump_json(indent=2))

    print("\n" + "=" * 60)
    print("ETAPA 2 — PREPARAÇÃO DA PESQUISADORA")
    print("=" * 60)

    entrada = PesquisadoraInput(
        user_request=user_request,
        professora_output=professora_output,
    )

    print("Entrada da Pesquisadora validada.")

    return entrada


def main():
    entrada = preparar_entrada_pesquisadora()

    print("\n" + "=" * 60)
    print("ETAPA 3 — PESQUISADORA")
    print("=" * 60)

    resultado = pesquisar_atividades_pedagogicas(
        entrada
    )

    print("\n" + "=" * 60)
    print("PESQUISA PEDAGÓGICA CONCLUÍDA")
    print("=" * 60)

    print(resultado.model_dump_json(indent=2))

    print("\n" + "=" * 60)
    print("RESUMO DOS RESULTADOS")
    print("=" * 60)

    print("Total de fontes:", len(resultado.fontes))

    for pesquisa in resultado.pesquisas_diarias:
        print(
            f"\nDia {pesquisa.dia}"
            f"\nStatus: {pesquisa.status_pesquisa}"
            f"\nAtividades: {len(pesquisa.atividades)}"
        )

        if pesquisa.justificativa:
            print("Justificativa:", pesquisa.justificativa)

    print("\nTeste integrado finalizado.")


if __name__ == "__main__":
    main()
