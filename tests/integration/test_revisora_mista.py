
from backend.src.schemas.agent_outputs import (
    RevisoraInput,
    RevisoraOutput,
    PesquisadoraOutput,
    PesquisaDiaria,
    FontePesquisa,
    AtividadePesquisada,
    EvidenciaPesquisa,
)

from backend.src.chains.agents.revisora import (
    revisar_planejamento,
)

from test_pesquisadora_manual import (
    preparar_entrada_pesquisadora,
)


def criar_fonte(id, titulo, url, dominio, resumo):
    return FontePesquisa(
        id=id,
        titulo=titulo,
        url=url,
        dominio=dominio,
        idioma="pt-BR",
        tipo_fonte="institucional",
        status_extracao="completa",
        resumo_conteudo=resumo,
    )


def criar_atividade(
    id,
    titulo,
    descricao,
    objetivo,
    materiais,
    etapas,
    cuidados,
    adaptacoes,
    fonte_id,
    evidencia,
):
    return AtividadePesquisada(
        id=id,
        titulo=titulo,
        descricao=descricao,
        objetivo_aprendizagem=objetivo,
        faixa_etaria_indicada="Educação Infantil - 4 anos",
        duracao_estimada_minutos=20,
        materiais=materiais,
        etapas_execucao=etapas,
        cuidados_seguranca=cuidados,
        adaptacoes_inclusao=adaptacoes,
        origem="encontrada",
        fontes_ids=[fonte_id],
        evidencias=[
            EvidenciaPesquisa(
                fonte_id=fonte_id,
                trecho=evidencia,
                contribuicao=(
                    "Evidência utilizada para fundamentar "
                    "a proposta da atividade."
                ),
            )
        ],
    )


def preparar_resultado_pesquisadora():
    fontes = [
        criar_fonte(
            "d1_f1",
            "Brincadeiras de imitação de animais",
            "https://exemplo.org/animais",
            "exemplo.org",
            "Atividades de imitação de movimentos de animais.",
        ),
        criar_fonte(
            "d2_f1",
            "Atividades de artes com materiais recicláveis",
            "https://exemplo.org/artes",
            "exemplo.org",
            "Propostas de construção artística com materiais recicláveis.",
        ),
        criar_fonte(
            "d3_f1",
            "Atividades de movimento corporal",
            "https://exemplo.org/movimento",
            "exemplo.org",
            "Propostas de atividades corporais para crianças.",
        ),
    ]

    atividade_aprovavel = criar_atividade(
        id="d1_a1",
        titulo="Imitando os movimentos dos animais",
        descricao=(
            "As crianças observam imagens de animais e "
            "imitam seus movimentos em um espaço livre."
        ),
        objetivo="Explorar movimentos corporais e coordenação motora.",
        materiais=["Imagens de animais"],
        etapas=[
            "Apresentar imagens de diferentes animais.",
            "Convidar as crianças a imitar seus movimentos.",
            "Conversar sobre os movimentos realizados.",
        ],
        cuidados=[
            "Manter o espaço livre de obstáculos.",
            "Supervisionar a movimentação das crianças.",
        ],
        adaptacoes=[
            "Permitir movimentos simplificados ou imitação dos sons.",
        ],
        fonte_id="d1_f1",
        evidencia=(
            "As crianças observam imagens de animais e imitam "
            "seus movimentos corporais em atividades lúdicas."
        ),
    )

    atividade_com_ajustes = criar_atividade(
        id="d2_a1",
        titulo="Construção de animais com recicláveis",
        descricao=(
            "As crianças constroem representações de animais "
            "utilizando embalagens e materiais recicláveis."
        ),
        objetivo="Estimular criatividade e coordenação motora fina.",
        materiais=[
            "Caixas de papelão",
            "Tampinhas",
            "Cola",
            "Tesouras",
        ],
        etapas=[
            "Selecionar materiais recicláveis.",
            "Montar representações de animais.",
            "Apresentar as produções aos colegas.",
        ],
        cuidados=[
            "Supervisionar o uso de tesouras.",
        ],
        adaptacoes=[
            "Oferecer materiais pré-cortados.",
        ],
        fonte_id="d2_f1",
        evidencia=(
            "As crianças podem criar representações de animais "
            "utilizando papelão, embalagens e materiais recicláveis."
        ),
    )

    atividade_sem_sustentacao = criar_atividade(
        id="d3_a1",
        titulo="Corrida competitiva de obstáculos",
        descricao=(
            "As crianças participam de uma corrida competitiva "
            "com obstáculos elevados e saltos entre plataformas."
        ),
        objetivo="Desenvolver velocidade e coordenação motora.",
        materiais=[
            "Plataformas elevadas",
            "Obstáculos",
        ],
        etapas=[
            "Organizar plataformas elevadas.",
            "Solicitar que as crianças saltem entre as plataformas.",
            "Comparar os tempos de conclusão da corrida.",
        ],
        cuidados=[
            "Supervisionar a atividade.",
        ],
        adaptacoes=[
            "Permitir que as crianças observem a atividade.",
        ],
        fonte_id="d3_f1",
        evidencia=(
            "A fonte apresenta atividades de movimento corporal "
            "e exploração de movimentos pelas crianças."
        ),
    )

    pesquisas_diarias = [
        PesquisaDiaria(
            dia=1,
            status_pesquisa="resultados_encontrados",
            atividades=[atividade_aprovavel],
        ),
        PesquisaDiaria(
            dia=2,
            status_pesquisa="resultados_encontrados",
            atividades=[atividade_com_ajustes],
        ),
        PesquisaDiaria(
            dia=3,
            status_pesquisa="resultados_encontrados",
            atividades=[atividade_sem_sustentacao],
        ),
        PesquisaDiaria(
            dia=4,
            status_pesquisa="sem_resultados_suficientes",
            atividades=[],
            justificativa="Não foram encontradas atividades suficientes.",
        ),
        PesquisaDiaria(
            dia=5,
            status_pesquisa="sem_resultados_suficientes",
            atividades=[],
            justificativa="Não foram encontradas atividades suficientes.",
        ),
    ]

    return PesquisadoraOutput(
        fontes=fontes,
        pesquisas_diarias=pesquisas_diarias,
    )


def main():
    print("\nPREPARANDO ENTRADA DA PROFESSORA")

    entrada_pesquisadora = preparar_entrada_pesquisadora()

    print("\nPREPARANDO RESULTADO MISTO DA PESQUISADORA")

    pesquisadora_output = preparar_resultado_pesquisadora()

    entrada_revisora = RevisoraInput(
        user_request=entrada_pesquisadora.user_request,
        professora_output=entrada_pesquisadora.professora_output,
        pesquisadora_output=pesquisadora_output,
    )

    print("Entrada da Revisora validada.")

    print("\nEXECUTANDO REVISORA")

    resultado: RevisoraOutput = revisar_planejamento(
        entrada_revisora
    )

    print("\nRESULTADO FINAL")
    print(resultado.model_dump_json(indent=2))

    print("\nRESUMO DA REVISÃO")
    print("Status geral:", resultado.status_geral)

    for dia in resultado.revisoes_diarias:
        print(
            f"\nDia {dia.dia} | Status: {dia.status}"
        )

        for atividade in dia.atividades:
            print(
                f"  Atividade: {atividade.atividade_id}"
                f"\n  Decisão: {atividade.status}"
                f"\n  Justificativa: {atividade.justificativa}"
            )

            for ajuste in atividade.ajustes_recomendados:
                print("  Ajuste:", ajuste)

    print("\nTESTE MISTO FINALIZADO")


if __name__ == "__main__":
    main()
