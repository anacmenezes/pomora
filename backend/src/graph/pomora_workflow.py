
from typing import Any

from langchain_core.messages import HumanMessage
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError

from ..api.database import SessionLocal
from ..api.routes import Solicitacao
from ..api import services

from . import workflow as intake_workflow
from .planning import planning_workflow


def inicializar_grafos(checkpointer):
    """
    Compila os dois grafos utilizando o mesmo PostgresSaver.
    Deve ser chamado durante a inicialização da API.
    """

    intake_workflow.intake_graph = (
        intake_workflow.criar_workflow_intake(checkpointer)
    )

    planning_workflow.planning_graph = (
        planning_workflow.criar_workflow_planejamento(checkpointer)
    )


def serializar_resultado(valor: Any) -> Any:
    """Converte objetos Pydantic em estruturas serializáveis."""

    if isinstance(valor, BaseModel):
        return valor.model_dump(mode="json")

    return valor


def salvar_solicitacao(
    thread_id: str,
    validated_request: dict[str, Any],
) -> int:
    """Salva a solicitação confirmada no PostgreSQL."""

    db = SessionLocal()

    try:
        registro = services.get_by_field(
            db=db,
            model=Solicitacao,
            field_name="thread_id",
            value=thread_id,
        )

        if registro is not None:
            return registro.id

        registro = services.create(
            db=db,
            model=Solicitacao,
            data={
                "thread_id": thread_id,
                "dados": validated_request,
                "status": "confirmada",
            },
        )

        return registro.id

    except IntegrityError:
        db.rollback()

        registro = services.get_by_field(
            db=db,
            model=Solicitacao,
            field_name="thread_id",
            value=thread_id,
        )

        if registro is not None:
            return registro.id

        raise

    finally:
        db.close()


def processar_mensagem_pomora(
    mensagem: str,
    thread_id: str,
) -> dict[str, Any]:
    """
    Executa o fluxo integrado do POMORA.

    1. Recebe a mensagem pela Márcia.
    2. Coleta e valida os dados.
    3. Aguarda a confirmação.
    4. Salva a solicitação no PostgreSQL.
    5. Executa Professora, Assistente e Revisora.
    6. Retorna o planejamento final.
    """

    if not mensagem or not mensagem.strip():
        raise ValueError("A mensagem do usuário não pode estar vazia.")

    if not thread_id or not thread_id.strip():
        raise ValueError("O thread_id é obrigatório.")

    if intake_workflow.intake_graph is None:
        raise RuntimeError("O grafo da Márcia não foi inicializado.")

    if planning_workflow.planning_graph is None:
        raise RuntimeError("O grafo de planejamento não foi inicializado.")

    # 1. Execução do Intake
    intake_config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    intake_resultado = intake_workflow.intake_graph.invoke(
        {
            "messages": [
                HumanMessage(content=mensagem.strip())
            ],
        },
        config=intake_config,
    )

    intake_status = intake_resultado.get("status")

    resposta_intake = {
        "status": intake_status,
        "response": intake_resultado.get("response"),
        "pending_fields": intake_resultado.get("pending_fields", []),
        "validation_errors": intake_resultado.get(
            "validation_errors",
            [],
        ),
    }

    # 2. Aguarda confirmação
    if intake_status != "confirmed":
        return {
            "intake": resposta_intake,
            "planning": None,
        }

    validated_request = intake_resultado.get("validated_request")

    if not validated_request:
        raise ValueError(
            "A solicitação foi confirmada, mas o UserRequest "
            "não foi encontrado no estado do Intake."
        )

    # 3. Salva a solicitação
    request_id = salvar_solicitacao(
        thread_id=thread_id,
        validated_request=validated_request,
    )

    intake_workflow.intake_graph.update_state(
        intake_config,
        {
            "request_id": str(request_id),
        },
    )

    resposta_intake["request_id"] = request_id

    # 4. Recupera ou executa o planejamento
    planning_thread_id = f"{thread_id}:planning"

    planning_config = {
        "configurable": {
            "thread_id": planning_thread_id,
        }
    }

    snapshot = planning_workflow.planning_graph.get_state(
        planning_config
    )

    planning_state_anterior = snapshot.values or {}

    planejamento_concluido = (
        planning_state_anterior.get("planning_status") == "completed"
    )

    if planejamento_concluido:
        planning_resultado = planning_state_anterior

    else:
        planning_resultado = (
            planning_workflow.planning_graph.invoke(
                {
                    "intake_status": intake_status,
                    "validated_request": validated_request,
                },
                config=planning_config,
            )
        )

    # 5. Extrai o resultado da Revisora
    revisora_output = planning_resultado.get("revisora_output")

    planejamento_final = serializar_resultado(revisora_output)

    return {
        "intake": resposta_intake,
        "planning": {
            "status": planning_resultado.get("planning_status"),
            "error_message": planning_resultado.get("error_message"),
            "validation_errors": planning_resultado.get(
                "validation_errors",
                [],
            ),
            "planejamento_final": planejamento_final,
        },
    }
