
from typing import Any

from langchain_core.messages import HumanMessage
from pydantic import ValidationError

from ..chains.agents.marcia import interpretar_mensagem
from ..schemas.agent_outputs import MarciaInput
from ..schemas.intake import IntakeDraft
from ..schemas.request import Idioma, UserRequest
from .state import IntakeGraphState


ESCOLARIDADE_LABELS = {
    "educacao_infantil": "Educação Infantil",
    "ensino_fundamental_i": "Ensino Fundamental I",
    "ensino_fundamental_ii": "Ensino Fundamental II",
}

MODALIDADE_LABELS = {
    "individual": "Individual",
    "coletiva": "Coletiva",
}


def obter_intake_draft(state: IntakeGraphState) -> IntakeDraft:
    """
    Recupera e valida os dados parciais da conversa.
    """

    intake_data = state.get("intake_data") or {}

    return IntakeDraft.model_validate(intake_data)


def processar_mensagem_usuario(
    state: IntakeGraphState,
) -> dict[str, Any]:
    """
    Interpreta a última mensagem do usuário com a Márcia,
    aplica as atualizações e valida o rascunho.
    """

    messages = state.get("messages", [])

    ultima_mensagem = next(
        (
            mensagem
            for mensagem in reversed(messages)
            if isinstance(mensagem, HumanMessage)
        ),
        None,
    )

    if ultima_mensagem is None or not isinstance(
        ultima_mensagem.content, str
    ):
        return {
            "status": "needs_clarification",
            "response": (
                "Não consegui identificar sua mensagem. "
                "Pode enviá-la novamente?"
            ),
        }

    status_atual = state.get("status", "collecting")

    if status_atual in ("confirmed", "cancelled"):
        return {
            "response": (
                "Esta solicitação já foi finalizada. "
                "Inicie ou retome uma solicitação para continuar."
            ),
        }

    etapa = (
        "awaiting_confirmation"
        if status_atual == "awaiting_confirmation"
        else "collecting"
    )

    draft = obter_intake_draft(state)

    entrada = MarciaInput(
        user_message=ultima_mensagem.content,
        current_data=draft.model_dump(
            mode="json",
            exclude_none=True,
        ),
        pending_fields=draft.campos_pendentes,
        conversation_stage=etapa,
        language=draft.idioma or Idioma.PORTUGUES_BR,
    )

    resultado = interpretar_mensagem(entrada)

    novos_dados = draft.model_dump(
        mode="json",
        exclude_none=True,
    )

    for campo in resultado.updated_fields:
        novos_dados[campo] = resultado.updates[campo]

    try:
        draft_atualizado = IntakeDraft.model_validate(novos_dados)

    except ValidationError as exc:
        return {
            "status": "needs_clarification",
            "validation_errors": [
                formatar_erros_validacao(exc)
            ],
            "response": (
                "Não consegui validar algumas informações. "
                "Pode esclarecer sua resposta?"
            ),
        }

    resposta = (
        resultado.clarification_question
        or resultado.next_question
        or ""
    )

    atualizacao = {
        "intake_data": draft_atualizado.model_dump(
            mode="json",
            exclude_none=True,
        ),
        "pending_fields": draft_atualizado.campos_pendentes,
        "validation_errors": [],
        "response": resposta,
    }

    # Tratamento das mensagens durante a confirmação.
    if etapa == "awaiting_confirmation":

        decisao = resultado.confirmation_decision

        if decisao == "cancel":
            atualizacao["status"] = "awaiting_confirmation"
            atualizacao["confirmation_decision"] = "cancel"

        elif decisao == "confirm":

            if resultado.updated_fields:
                atualizacao["status"] = "awaiting_confirmation"
                atualizacao["confirmation_decision"] = None
                atualizacao["response"] = (
                    "Identifiquei alterações junto com sua confirmação. "
                    "Você deseja corrigir ou confirmar os dados atuais?"
                )

            else:
                atualizacao["status"] = "awaiting_confirmation"
                atualizacao["confirmation_decision"] = "confirm"

        elif decisao == "correct":

            atualizacao["confirmation_decision"] = None

            if resultado.updated_fields:
                atualizacao["status"] = "collecting"

            else:
                atualizacao["status"] = "awaiting_confirmation"
                atualizacao["response"] = (
                    resultado.clarification_question
                    or "Qual informação você deseja corrigir?"
                )

        else:
            # Mantém a etapa de confirmação para que a próxima
            # resposta seja interpretada no contexto correto.
            atualizacao["status"] = "awaiting_confirmation"
            atualizacao["confirmation_decision"] = None
            atualizacao["response"] = (
                resultado.clarification_question
                or "Você deseja confirmar, corrigir ou cancelar?"
            )

    else:
        # Tratamento das mensagens durante a coleta.
        atualizacao["status"] = (
            "needs_clarification"
            if resultado.clarification_question
            else "collecting"
        )

        atualizacao["confirmation_decision"] = None

    return atualizacao


def verificar_completude(state: IntakeGraphState) -> dict[str, Any]:
    if state.get("status") == "needs_clarification":
        return {
            "status": "needs_clarification",
            "pending_fields": state.get("pending_fields", []),
        }

    draft = obter_intake_draft(state)
    campos_pendentes = draft.campos_pendentes

    if campos_pendentes:
        return {
            "status": "collecting",
            "pending_fields": campos_pendentes,
            "validated_request": None,
        }

    try:
        UserRequest.model_validate(
            draft.model_dump(exclude_none=True)
        )

    except ValidationError as exc:
        erros = [
            error["msg"]
            for error in exc.errors(include_input=False)
        ]

        return {
            "status": "needs_clarification",
            "pending_fields": [],
            "validated_request": None,
            "validation_errors": erros,
            "response": (
                "Encontrei uma inconsistência nas informações: "
                f"{'; '.join(erros)} "
                "Pode corrigir os dados para continuarmos?"
            ),
        }

    return {
        "status": "awaiting_confirmation",
        "pending_fields": [],
        "validation_errors": [],
    }


def preparar_confirmacao(
    state: IntakeGraphState,
) -> dict[str, Any]:
    """
    Prepara um resumo dos dados para revisão do usuário.
    """

    draft = obter_intake_draft(state)

    if not draft.esta_completo:
        return verificar_completude(state)

    dados = draft.model_dump(mode="json", exclude_none=True)

    escolaridade = ESCOLARIDADE_LABELS.get(
        dados["escolaridade"],
        dados["escolaridade"],
    )

    modalidade = MODALIDADE_LABELS.get(
        dados["modalidade"],
        dados["modalidade"],
    )

    preferencias = dados.get("preferencias_materiais") or []
    restricoes = dados.get("restricoes_materiais") or []

    resumo = [
        "Confira as informações do seu planejamento:",
        "",
        f"Escolaridade: {escolaridade}",
        f"Ano/turma: {dados['ano_serie']}",
        f"Modalidade: {modalidade}",
        f"Quantidade de crianças: {dados['quantidade_criancas']}",
        f"Tema da semana: {dados['tema_semana']}",
        f"Objetivo: {dados['objetivo_aprendizagem']}",
        (
            "Adaptações: "
            f"{dados.get('necessidades_adaptacoes') or 'Não informadas'}"
        ),
        (
            "Preferências de materiais: "
            f"{', '.join(preferencias) if preferencias else 'Não informadas'}"
        ),
        (
            "Restrições de materiais: "
            f"{', '.join(restricoes) if restricoes else 'Não informadas'}"
        ),
        f"Idioma: {dados.get('idioma', 'pt-BR')}",
        f"Referência curricular: {dados.get('curriculo_regiao', 'BR')}",
        "",
        "As informações estão corretas? Posso gerar seu planejamento?",
    ]

    return {
        "status": "awaiting_confirmation",
        "response": "\n".join(resumo),
        "pending_fields": [],
        "validation_errors": [],
    }


def validar_confirmacao(
    state: IntakeGraphState,
) -> dict[str, Any]:
    """
    Aplica as regras determinísticas de confirmação.

    A classificação da resposta vem da agente Márcia.
    A validação final é realizada pelo Pydantic.
    """

    decision = state.get("confirmation_decision")

    if decision is None:
        return {
            "status": "needs_clarification",
            "response": (
                "Não consegui identificar sua decisão. "
                "Você confirma as informações?"
            ),
            "validated_request": None,
        }

    if decision == "cancel":
        return {
            "status": "cancelled",
            "validated_request": None,
            "response": (
                "A solicitação foi cancelada. "
                "Os dados foram preservados para uma possível retomada."
            ),
        }

    if decision == "unclear":
        return {
            "status": "needs_clarification",
            "validated_request": None,
            "response": (
                "Não consegui identificar se você deseja confirmar "
                "ou corrigir as informações. Pode esclarecer?"
            ),
        }

    if decision == "correct":
        return {
            "status": "collecting",
            "confirmation_decision": None,
            "validated_request": None,
            "response": "Vamos atualizar as informações.",
        }

    if decision == "confirm":

        if state.get("status") != "awaiting_confirmation":
            return {
                "status": "needs_clarification",
                "validated_request": None,
                "response": (
                    "A solicitação ainda não está pronta para confirmação."
                ),
            }

        try:
            draft = obter_intake_draft(state)

            if not draft.esta_completo:
                return verificar_completude(state)

            request = UserRequest.model_validate(
                draft.model_dump(exclude_none=True)
            )

        except ValidationError as exc:
            return {
                "status": "needs_clarification",
                "validated_request": None,
                "validation_errors": [
                    error["msg"]
                    for error in exc.errors(include_input=False)
                ],
                "response": (
                    "Encontrei uma inconsistência nas informações. "
                    "Precisamos revisá-las antes de continuar."
                ),
            }

        return {
            "status": "confirmed",
            "validated_request": request.model_dump(mode="json"),
            "validation_errors": [],
            "response": (
                "Solicitação confirmada. "
                "O planejamento pedagógico está liberado."
            ),
        }

    return {
        "status": "needs_clarification",
        "validated_request": None,
        "response": "Não foi possível processar sua resposta.",
    }


def formatar_erros_validacao(exc: ValidationError) -> list[str]:
    return [
        error["msg"].removeprefix("Value error, ")
        for error in exc.errors(include_input=False)
    ]