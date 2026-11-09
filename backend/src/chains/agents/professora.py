from langchain_core.prompts import ChatPromptTemplate
from pydantic import ValidationError

from ...schemas.agent_outputs import ProfessoraInput, ProfessoraOutput
from ..models.openai import get_openai_model
from ..prompts.professora_ppt import PROFESSORA_SYSTEM_PROMPT


def criar_cadeia_professora():
    """Cria a cadeia que elabora o planejamento pedagógico semanal completo."""

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", PROFESSORA_SYSTEM_PROMPT),
            (
                "human",
                """
                Elabore o planejamento pedagógico semanal com base na
                solicitação validada abaixo.

                SOLICITAÇÃO DO USUÁRIO:
                {user_request}

                Sua responsabilidade é criar diretamente as atividades
                pedagógicas dos cinco dias da semana. Não planeje buscas,
                pesquisas ou tarefas para outro agente.

                REQUISITOS DO PLANEJAMENTO:
                - Crie exatamente uma atividade principal para cada dia,
                  de 1 a 5, em ordem.
                - Faça todas as atividades trabalharem o tema da semana,
                  com variedade e progressão pedagógica.
                - Considere a faixa etária, a etapa escolar, o objetivo de
                  aprendizagem, a modalidade e a quantidade de crianças.
                - Considere as necessidades de adaptação informadas.
                - Priorize as preferências de materiais e respeite todas
                  as restrições de materiais.
                - Descreva atividades concretas, realizáveis e adequadas
                  ao contexto informado.
                - Para cada atividade, informe título, objetivo,
                  descrição, intenção pedagógica, duração, materiais,
                  etapas de execução, cuidados de segurança e adaptações
                  de inclusão.
                - Na Educação Infantil, informe o campo de experiência
                  da BNCC quando pertinente. Use o nome do campo e não
                  invente códigos.
                - No Ensino Fundamental, informe o componente curricular
                  ou a área quando aplicável.
                - Não invente dados sobre a turma ou necessidades que não
                  foram informadas.
                - Não inclua links, músicas, vídeos ou imagens. Esses
                  materiais serão preparados pelo agente Assistente.
                - Não apresente atividades como pesquisadas, encontradas
                  ou verificadas em fontes externas.

                Além das cinco atividades, apresente objetivo geral,
                objetivos específicos, justificativa pedagógica,
                progressão semanal, vocabulário da semana, materiais
                gerais e orientações gerais para o professor.

                INSTRUÇÃO DE CORREÇÃO:
                {correcao_validacao}
                """,
            ),
        ]
    )

    modelo = get_openai_model()
    modelo_estruturado = modelo.with_structured_output(
        ProfessoraOutput,
        method="function_calling",
    )

    return prompt | modelo_estruturado


def _montar_mensagem_correcao(erro: ValidationError) -> str:
    """Converte os erros do Pydantic em instruções para uma nova tentativa."""

    detalhes_erro = erro.errors(include_url=False)

    return (
        "A resposta anterior não cumpriu o schema ProfessoraOutput.\n\n"
        "Corrija todos os erros de validação apresentados a seguir:\n"
        f"{detalhes_erro}\n\n"
        "Gere novamente o planejamento completo e verifique especialmente:\n"
        "- Existem exatamente cinco atividades, uma para cada dia.\n"
        "- Os dias estão na ordem 1, 2, 3, 4 e 5.\n"
        "- Cada atividade contém todos os campos obrigatórios.\n"
        "- Cada atividade possui pelo menos dois passos de execução.\n"
        "- Os materiais e os cuidados de segurança são compatíveis com a atividade.\n"
        "- As atividades respeitam a faixa etária e as restrições informadas.\n"
        "- Os objetivos são coerentes com o tema e com o objetivo de aprendizagem.\n"
        "- A BNCC não contém códigos inventados.\n"
        "- Não inclua orientações de pesquisa nem referências a fontes externas.\n"
        "- Não inclua recursos de apoio; eles serão preparados pelo Assistente.\n\n"
        "Retorne todos os campos exigidos pelo schema, sem omissões."
    )


def gerar_planejamento_pedagogico(
    entrada: ProfessoraInput,
) -> ProfessoraOutput:
    """
    Recebe uma solicitação validada e produz o planejamento semanal completo.

    Faz uma única tentativa adicional quando o retorno apresenta erro
    de validação do schema ProfessoraOutput.
    """

    cadeia = criar_cadeia_professora()

    dados = {
        "user_request": entrada.user_request.model_dump_json(indent=2),
        "correcao_validacao": "Nenhuma correção necessária na primeira tentativa.",
    }

    try:
        resultado = cadeia.invoke(dados)

        if not isinstance(resultado, ProfessoraOutput):
            raise TypeError(
                "A cadeia da Professora não retornou uma instância de ProfessoraOutput."
            )

        return resultado

    except ValidationError as erro:
        print(
            "Retorno da Professora inválido. "
            "Realizando uma única tentativa de correção."
        )

        dados["correcao_validacao"] = _montar_mensagem_correcao(erro)

        resultado_corrigido = cadeia.invoke(dados)

        if not isinstance(resultado_corrigido, ProfessoraOutput):
            raise TypeError(
                "A segunda tentativa da Professora não retornou "
                "uma instância de ProfessoraOutput."
            )

        return resultado_corrigido


def gerar_estrategia_pedagogica(
    entrada: ProfessoraInput,
) -> ProfessoraOutput:
    """
    Compatibilidade temporária com o nome usado pela orquestração anterior.

    O retorno agora é o planejamento semanal completo, não apenas uma
    estratégia pedagógica para alimentar a antiga Pesquisadora.
    """

    return gerar_planejamento_pedagogico(entrada)