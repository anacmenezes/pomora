from uuid import uuid4
import json

from langchain_core.messages import HumanMessage

from backend.src.graph.workflow import intake_graph


def exibir_resultado(state: dict) -> None:
    """Exibe o resultado de cada interação com a Márcia."""

    print("\n" + "=" * 60)
    print("RESPOSTA DA MÁRCIA")
    print("=" * 60)

    print(state.get("response") or "Nenhuma resposta retornada.")

    print("\nSTATUS:", state.get("status"))

    pendentes = state.get("pending_fields", [])

    if pendentes:
        print("\nCAMPOS PENDENTES:")
        for campo in pendentes:
            print(f"- {campo}")

    erros = state.get("validation_errors", [])

    if erros:
        print("\nERROS DE VALIDAÇÃO:")
        for erro in erros:
            print(f"- {erro}")

    if state.get("status") == "confirmed":
        print("\nSOLICITAÇÃO VALIDADA:")

        print(
            json.dumps(
                state.get("validated_request"),
                ensure_ascii=False,
                indent=2,
            )
        )

    print("=" * 60)


def main() -> None:
    """Executa uma conversa interativa com a agente Márcia."""

    thread_id = f"teste-marcia-{uuid4()}"

    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    print("\nPOMORA — TESTE DA AGENTE MÁRCIA")
    print("Conversa iniciada.")
    print("Digite 'sair' para encerrar.\n")

    while True:

        mensagem = input("Você: ").strip()

        if not mensagem:
            continue

        if mensagem.lower() == "sair":
            print("\nTeste encerrado.")
            break

        try:
            state = intake_graph.invoke(
                {
                    "messages": [
                        HumanMessage(content=mensagem)
                    ]
                },
                config=config,
            )

            exibir_resultado(state)

            status = state.get("status")

            if status == "confirmed":
                print("\nSolicitação confirmada com sucesso!")
                break

            if status == "cancelled":
                print("\nSolicitação cancelada.")
                break

        except Exception as erro:
            print("\nERRO DURANTE A EXECUÇÃO")
            print(f"Tipo: {type(erro).__name__}")
            print(f"Detalhes: {erro}")
            break


if __name__ == "__main__":
    main()