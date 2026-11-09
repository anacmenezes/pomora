import json
import traceback
from pathlib import Path
from uuid import uuid4

from backend.src.graph.pomora_workflow import (
    processar_mensagem_pomora,
)


def exibir_resposta(resultado: dict) -> None:
    """Exibe o resultado do atendimento e do planejamento."""

    intake = resultado.get("intake") or {}
    planning = resultado.get("planning")

    print("\n" + "=" * 65)
    print("POMORA - RESULTADO DO ATENDIMENTO")
    print("=" * 65)

    print("Status:", intake.get("status"))
    print("\nResposta:")
    print(intake.get("response"))

    pendentes = intake.get("pending_fields", [])

    if pendentes:
        print("\nCampos pendentes:", pendentes)

    erros = intake.get("validation_errors", [])

    if erros:
        print("\nErros:", erros)

    if planning is None:
        print("\nAguardando conclusão do atendimento da Márcia.")
        return

    print("\n" + "=" * 65)
    print("RESULTADO DO PLANEJAMENTO")
    print("=" * 65)

    print("Status:", planning.get("status"))

    if planning.get("error_message"):
        print("Erro:", planning["error_message"])

    if planning.get("validation_errors"):
        print("Validações:", planning["validation_errors"])

    plano = planning.get("planejamento_final")

    if plano:
        print("\nPLANEJAMENTO FINAL GERADO")

        print("Tema:", plano["contexto"]["tema_semana"])
        print("Objetivo:", plano["objetivo_geral"])
        print("Status da revisão:", plano["status_revisao"])

        print("\nATIVIDADES DA SEMANA:")

        for dia in plano["dias"]:
            atividade = dia["atividade"]
            recursos = dia["recursos"]

            print(f"\nDia {dia['dia']}: {atividade['titulo']}")
            print("Objetivo:", atividade["objetivo"])
            print("Imagens:", len(recursos["imagens"]))
            print("Músicas:", len(recursos["musicas"]))
            print("Vídeos:", len(recursos["videos"]))

            if dia["observacoes_revisao"]:
                print("Observações:", dia["observacoes_revisao"])

        # Salva o documento completo em JSON.
        pasta_saida = Path("outputs")
        pasta_saida.mkdir(exist_ok=True)

        arquivo = pasta_saida / "planejamento_integrado.json"

        arquivo.write_text(
            json.dumps(
                plano,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        print("\nPlanejamento completo salvo em:")
        print(arquivo.resolve())


def main() -> None:
    """Executa os dois grafos em uma única conversa."""

    thread_id = f"pomora-integrado-{uuid4()}"

    print("\nPOMORA - TESTE INTEGRADO")
    print("Márcia → Professora → Assistente → Revisora")
    print("\nConversa iniciada.")
    print("Digite 'sair' para encerrar.\n")

    while True:

        mensagem = input("Você: ").strip()

        if not mensagem:
            continue

        if mensagem.lower() == "sair":
            print("\nTeste encerrado.")
            break

        try:
            resultado = processar_mensagem_pomora(
                mensagem=mensagem,
                thread_id=thread_id,
            )

            exibir_resposta(resultado)

            intake_status = (
                resultado.get("intake") or {}
            ).get("status")

            planning = resultado.get("planning")

            if intake_status == "cancelled":
                print("\nSolicitação cancelada.")
                break

            if (
                planning
                and planning.get("status") == "completed"
            ):
                print("\nFLUXO INTEGRADO CONCLUÍDO!")
                break

            if (
                planning
                and planning.get("status") == "blocked"
            ):
                print("\nPlanejamento bloqueado.")
                break

        except Exception as erro:
            print("\nERRO DURANTE O FLUXO INTEGRADO")
            print(f"Tipo: {type(erro).__name__}")
            print(f"Detalhes: {erro}")
            traceback.print_exc()
            break


if __name__ == "__main__":
    main()