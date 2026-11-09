from langchain_core.prompts import ChatPromptTemplate
from pydantic import ValidationError

from ...schemas.agent_outputs import (
    AssistenteInput,
    AssistenteOutput,
)
from ..models.openai import get_openai_model
from ..prompts.assistente_ppt import ASSISTENTE_SYSTEM_PROMPT


# ============================================================
# VALIDACAO DOS DADOS DE ENTRADA
# ============================================================


def _validar_entrada(entrada: AssistenteInput) -> None:
    """Confere se a Professora entregou exatamente cinco atividades."""

    dias = [
        atividade.dia
        for atividade in entrada.professora_output.atividades_diarias
    ]

    if dias != [1, 2, 3, 4, 5]:
        raise ValueError(
            "O Assistente precisa receber exatamente uma atividade "
            "para cada dia, de 1 a 5, em ordem."
        )


# ============================================================
# CADEIA DO ASSISTENTE
# ============================================================


def criar_cadeia_assistente():
    """Cria a cadeia responsavel por preparar os materiais de apoio."""

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", ASSISTENTE_SYSTEM_PROMPT),
            (
                "human",
                """
                Prepare os materiais de apoio para o planejamento semanal abaixo.

                SOLICITACAO VALIDADA DO USUARIO:

                {user_request}

                PLANEJAMENTO PEDAGOGICO DA PROFESSORA:

                {professora_output}

                Gere recursos organizados para os cinco dias, respeitando
                o tema, a atividade, a faixa etaria, a escolaridade,
                as preferencias e as restricoes de materiais.

                Para cada dia, prepare pelo menos uma ilustracao de apoio,
                com descricao, prompt detalhado para geracao por IA,
                texto alternativo e legenda quando pertinente.

                Inclua sugestoes de musicas e videos ao longo da semana,
                somente quando tiverem finalidade pedagogica clara.

                As sugestoes devem estar relacionadas ao tema e as atividades.

                Nao altere, reescreva ou substitua as atividades da Professora.

                Nao invente links ou alegue que um recurso foi encontrado
                ou verificado externamente.

                INSTRUCAO DE CORRECAO:

                {correcao_validacao}
                """,
            ),
        ]
    )

    modelo = get_openai_model().with_structured_output(
        AssistenteOutput,
        method="function_calling",
    )

    return prompt | modelo


# ============================================================
# VALIDACAO DO RETORNO
# ============================================================


def _validar_recursos(resultado: AssistenteOutput) -> None:
    """Valida a presenca e a organizacao dos recursos da semana."""

    dias = [
        recurso.dia
        for recurso in resultado.recursos_diarios
    ]

    if dias != [1, 2, 3, 4, 5]:
        raise ValueError(
            "Os recursos devem conter exatamente os dias 1 a 5, em ordem."
        )

    for recursos_dia in resultado.recursos_diarios:

        if not recursos_dia.imagens:
            raise ValueError(
                f"O dia {recursos_dia.dia} precisa de pelo menos "
                "uma ilustracao de apoio."
            )

        if not recursos_dia.orientacoes_uso:
            raise ValueError(
                f"O dia {recursos_dia.dia} precisa apresentar pelo menos "
                "uma orientacao de uso dos recursos."
            )

    if not any(
        recursos.musicas
        for recursos in resultado.recursos_diarios
    ):
        raise ValueError(
            "Inclua pelo menos uma sugestao musical pertinente ao longo da semana."
        )

    if not any(
        recursos.videos
        for recursos in resultado.recursos_diarios
    ):
        raise ValueError(
            "Inclua pelo menos uma sugestao de video pertinente ao longo da semana."
        )


# ============================================================
# CORRECAO DE RESPOSTA INVALIDA
# ============================================================


def _montar_mensagem_correcao(erro: Exception) -> str:
    """Gera instrucoes para uma unica tentativa adicional."""

    if isinstance(erro, ValidationError):
        detalhes = erro.errors(include_url=False)
    else:
        detalhes = str(erro)

    return (
        "A resposta anterior nao cumpriu os requisitos do Assistente.\n\n"
        "Corrija os problemas abaixo e gere novamente a estrutura completa:\n"
        f"{detalhes}\n\n"
        "Confira especialmente:\n"
        "- Existem exatamente cinco objetos em recursos_diarios, na ordem 1 a 5.\n"
        "- Cada dia possui pelo menos uma imagem de apoio.\n"
        "- Cada imagem possui descricao, prompt_geracao e texto_alternativo.\n"
        "- Cada dia possui pelo menos uma orientacao_uso.\n"
        "- A semana possui pelo menos uma sugestao de musica e uma de video.\n"
        "- Todos os recursos estao relacionados ao tema e a atividade do dia.\n"
        "- Os recursos sao adequados a faixa etaria e a etapa escolar.\n"
        "- Nao altere nem invente atividades pedagogicas.\n"
        "- Nao invente URLs. Deixe imagem_url e url como null.\n"
        "- Preencha todos os campos obrigatorios definidos no AssistenteOutput.\n"
    )


# ============================================================
# NORMALIZACAO DOS RECURSOS
# ============================================================


def _remover_urls_nao_verificadas(
    resultado: AssistenteOutput,
) -> AssistenteOutput:
    """
    Remove URLs que o modelo possa ter produzido sem verificacao externa.

    Nesta etapa, o Assistente nao possui ferramenta de navegacao nem de
    geracao de imagens. Portanto, mantem os prompts de ilustracao e as
    sugestoes de musica/video, mas deixa os campos de URL vazios.
    """

    recursos_normalizados = []
    encontrou_url = False

    for recursos_dia in resultado.recursos_diarios:

        imagens = []

        for imagem in recursos_dia.imagens:

            if imagem.imagem_url is not None:
                encontrou_url = True

            imagens.append(
                imagem.model_copy(
                    update={"imagem_url": None}
                )
            )

        musicas = []

        for musica in recursos_dia.musicas:

            if musica.url is not None:
                encontrou_url = True

            musicas.append(
                musica.model_copy(
                    update={"url": None}
                )
            )

        videos = []

        for video in recursos_dia.videos:

            if video.url is not None:
                encontrou_url = True

            videos.append(
                video.model_copy(
                    update={"url": None}
                )
            )

        recursos_normalizados.append(
            recursos_dia.model_copy(
                update={
                    "imagens": imagens,
                    "musicas": musicas,
                    "videos": videos,
                }
            )
        )

    observacoes = list(resultado.observacoes)

    nota_recursos = (
        "As ilustracoes possuem prompts de geracao, mas ainda precisam "
        "ser geradas por um servico de imagens. As sugestoes de musicas "
        "e videos estao descritas, mas nao possuem links verificados."
    )

    if nota_recursos not in observacoes:
        observacoes.append(nota_recursos)

    if encontrou_url:
        observacoes.append(
            "URLs produzidas sem verificacao foram removidas para evitar "
            "a apresentacao de links incorretos."
        )

    return resultado.model_copy(
        update={
            "recursos_diarios": recursos_normalizados,
            "observacoes": observacoes[:10],
        }
    )


# ============================================================
# FUNCAO PRINCIPAL DO ASSISTENTE
# ============================================================


def gerar_recursos_apoio(
    entrada: AssistenteInput,
) -> AssistenteOutput:
    """
    Recebe o planejamento semanal e prepara os materiais de apoio.

    1. Valida a entrada da Professora.
    2. Gera recursos para os cinco dias.
    3. Valida a estrutura e a cobertura dos recursos.
    4. Remove URLs nao verificadas.
    5. Retorna AssistenteOutput.

    A geracao efetiva das imagens e a verificacao de links de musicas
    e videos dependem de integracoes externas, ainda nao executadas
    por esta cadeia.
    """

    # --------------------------------------------------------
    # 1. VALIDACAO DA ENTRADA
    # --------------------------------------------------------

    _validar_entrada(entrada)

    # --------------------------------------------------------
    # 2. CRIACAO DA CADEIA
    # --------------------------------------------------------

    cadeia = criar_cadeia_assistente()

    dados = {
        "user_request": entrada.user_request.model_dump_json(
            indent=2
        ),
        "professora_output": entrada.professora_output.model_dump_json(
            indent=2
        ),
        "correcao_validacao": (
            "Nenhuma correcao necessaria na primeira tentativa."
        ),
    }

    # --------------------------------------------------------
    # 3. EXECUCAO E VALIDACAO
    # --------------------------------------------------------

    try:

        resultado = cadeia.invoke(dados)

        if not isinstance(resultado, AssistenteOutput):
            resultado = AssistenteOutput.model_validate(resultado)

        _validar_recursos(resultado)

    except (ValidationError, ValueError) as erro:

        print(
            "Retorno do Assistente invalido. "
            "Realizando uma unica tentativa de correcao."
        )

        dados["correcao_validacao"] = (
            _montar_mensagem_correcao(erro)
        )

        resultado = cadeia.invoke(dados)

        if not isinstance(resultado, AssistenteOutput):
            resultado = AssistenteOutput.model_validate(resultado)

        _validar_recursos(resultado)

    # --------------------------------------------------------
    # 4. NORMALIZACAO DOS RECURSOS
    # --------------------------------------------------------

    resultado = _remover_urls_nao_verificadas(resultado)

    return resultado


# ============================================================
# FUNCAO ALTERNATIVA PARA A ORQUESTRACAO
# ============================================================


def preparar_materiais_apoio(
    entrada: AssistenteInput,
) -> AssistenteOutput:
    """Alias para facilitar a integracao do Assistente ao grafo."""

    return gerar_recursos_apoio(entrada)