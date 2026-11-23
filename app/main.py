
from math import cos, sin, tau
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.algorithms.areas import colaboracoes_entre_areas, distribuicao_areas
from src.algorithms.busca import componentes_conexas
from src.algorithms.centralidade import ranking_forca, ranking_grau, ranking_intermediacao
from src.algorithms.comunidades import detectar_comunidades
from src.algorithms.metricas import coeficiente_agrupamento_global
from src.algorithms.temporal import evolucao_temporal
from src.data.carregador import carregar_csv
from src.graph.construtor import ConstrutorGrafo


DEMO = Path(__file__).resolve().parents[1] / "datasets" / "demo"
OPENALEX = DEMO.with_name("openalex")
LIMITE_VISUAL = 80


@st.cache_data(max_entries=16)
def carregar(autores_csv, publicacoes_csv):
    return carregar_csv(autores_csv, publicacoes_csv)


@st.cache_data(max_entries=16)
def analisar(autores, publicacoes, inicio, fim):
    janela = tuple(
        p for p in publicacoes
        if (inicio is None or p.ano >= inicio) and (fim is None or p.ano <= fim)
    )
    grafo = ConstrutorGrafo.construir(autores, janela)
    arestas = list(grafo.arestas())
    comunidades = detectar_comunidades(grafo)
    quantidade = len(autores)
    densidade = 2 * len(arestas) / (quantidade * (quantidade - 1)) if quantidade > 1 else 0.0
    indicadores = {
        "Autores": quantidade,
        "Publicações": len(janela),
        "Arestas": len(arestas),
        "Componentes": len(componentes_conexas(grafo)),
        "Densidade": f"{densidade:.1%}",
        "Agrupamento médio": f"{coeficiente_agrupamento_global(grafo):.1%}",
    }
    return grafo, arestas, comunidades, indicadores


@st.cache_data(max_entries=16)
def serie_anual(autores, publicacoes, inicio, fim, acumulado):
    return evolucao_temporal(autores, publicacoes, inicio, fim, acumulado)


@st.cache_data(max_entries=16)
def rankings(autores, publicacoes, inicio, fim, calcular_intermediacao):
    grafo, _, _, _ = analisar(autores, publicacoes, inicio, fim)
    return (
        ranking_grau(grafo),
        ranking_forca(grafo),
        ranking_intermediacao(grafo) if calcular_intermediacao else [],
    )


def figura_rede(autores, arestas, comunidade_por_id):
    ids = sorted(autores)
    posicoes = {
        autor_id: (cos(tau * i / len(ids)), sin(tau * i / len(ids)))
        for i, autor_id in enumerate(ids)
    }
    x_arestas, y_arestas = [], []
    for primeiro, segundo, _ in arestas:
        if primeiro in posicoes and segundo in posicoes:
            x_a, y_a = posicoes[primeiro]
            x_b, y_b = posicoes[segundo]
            x_arestas.extend((x_a, x_b, None))
            y_arestas.extend((y_a, y_b, None))

    figura = go.Figure([
        go.Scatter(
            x=x_arestas, y=y_arestas, mode="lines", hoverinfo="skip",
            line={"color": "rgba(100,116,139,0.50)", "width": 1},
        ),
        go.Scatter(
            x=[posicoes[autor_id][0] for autor_id in ids],
            y=[posicoes[autor_id][1] for autor_id in ids],
            mode="markers",
            customdata=[[autores[autor_id].nome, autor_id, comunidade_por_id[autor_id]]
                        for autor_id in ids],
            hovertemplate="%{customdata[0]} (%{customdata[1]})<br>"
                          "Comunidade %{customdata[2]}<extra></extra>",
            marker={
                "size": 12, "color": [comunidade_por_id[autor_id] for autor_id in ids],
                "colorscale": "Turbo",
            },
        ),
    ])
    figura.update_layout(
        showlegend=False, margin={"l": 15, "r": 15, "t": 15, "b": 15},
        xaxis={"visible": False}, yaxis={"visible": False, "scaleanchor": "x"},
        height=500,
    )
    return figura


def main():
    st.set_page_config(page_title="SciCollab", layout="wide")
    st.title("SciCollab")
    st.caption("Análise de redes de colaboração científica")

    with st.sidebar:
        fontes = ["Demonstração", "Importar CSV"]
        if all((OPENALEX / nome).is_file() for nome in ("autores.csv", "publicacoes.csv")):
            fontes.append("OpenAlex local")
        fonte = st.radio("Fonte de dados", fontes)
        try:
            if fonte == "Importar CSV":
                arquivo_autores = st.file_uploader("CSV de autores", type="csv")
                arquivo_publicacoes = st.file_uploader("CSV de publicações", type="csv")
                if arquivo_autores is None or arquivo_publicacoes is None:
                    st.info("Selecione os dois arquivos CSV.")
                    return
                autores, publicacoes = carregar(
                    arquivo_autores.getvalue(), arquivo_publicacoes.getvalue()
                )
            else:
                pasta = OPENALEX if fonte == "OpenAlex local" else DEMO
                if pasta == OPENALEX:
                    st.caption("Amostra OpenAlex da PUC Minas, 2020–2024.")
                else:
                    st.caption("Dataset sintético de demonstração.")
                autores, publicacoes = carregar(
                    (pasta / "autores.csv").read_bytes(), (pasta / "publicacoes.csv").read_bytes()
                )
        except (ValueError, OSError) as erro:
            st.error(f"Falha ao carregar os dados: {erro}")
            return

        anos = sorted({publicacao.ano for publicacao in publicacoes})
        acumulado = st.radio("Modo da rede", ["Acumulada", "Anual"]) == "Acumulada"
        if len(anos) > 1:
            inicio, fim = st.slider(
                "Intervalo de anos", anos[0], anos[-1], (anos[0], anos[-1])
            )
        else:
            inicio = fim = anos[0] if anos else None
        inicio_rede, fim_rede = inicio, fim
        if acumulado:
            st.caption("Rede com todas as publicações do intervalo, inclusive seus limites.")
        else:
            st.caption("Rede com as publicações do ano selecionado. A série mostra cada ano separadamente.")
            if inicio is not None and fim > inicio:
                inicio_rede = fim_rede = st.slider("Ano da rede", inicio, fim, fim)

    grafo, arestas, comunidades, indicadores = analisar(
        autores, publicacoes, inicio_rede, fim_rede
    )
    for coluna, (nome, valor) in zip(st.columns(len(indicadores)), indicadores.items()):
        coluna.metric(nome, valor)
    st.caption("A rede inclui todo o cadastro. A evolução anual considera apenas autores ativos.")
    rede, pessoas, grupos, areas, evolucao = st.tabs(
        ["Rede", "Autores", "Comunidades", "Áreas", "Evolução"]
    )
    por_id = {autor.id: autor for autor in autores}
    comunidade_por_id = {
        autor_id: numero
        for numero, grupo in enumerate(comunidades, start=1)
        for autor_id in grupo
    }

    with rede:
        visiveis = sorted(autores, key=lambda autor: (-grafo.grau(autor.id), autor.id))[:LIMITE_VISUAL]
        if len(visiveis) < len(autores):
            st.info(f"Exibindo {len(visiveis)} de {len(autores)} autores, priorizando os de maior grau.")
        if visiveis:
            figura = figura_rede({autor.id: autor for autor in visiveis}, arestas, comunidade_por_id)
            st.plotly_chart(figura, width="stretch")
        else:
            st.info("Nenhum autor disponível.")

    with pessoas:
        if por_id:
            autor_id = st.selectbox(
                "Consultar autor", sorted(por_id),
                format_func=lambda identificador: f"{por_id[identificador].nome} ({identificador})",
            )
            vizinhos = sorted(grafo.vizinhos(autor_id).items(), key=lambda par: (-par[1], par[0]))
            if vizinhos:
                st.dataframe(pd.DataFrame([
                    (vizinho, por_id[vizinho].nome, peso) for vizinho, peso in vizinhos
                ], columns=["ID", "Colaborador", "Publicações conjuntas"]), hide_index=True)
            else:
                st.info("Este autor não tem colaboradores no recorte.")

            calcular = len(autores) <= 300 or st.checkbox(
                "Calcular intermediação para esta rede", help="O cálculo pode ser demorado em redes grandes."
            )
            valores = rankings(autores, publicacoes, inicio_rede, fim_rede, calcular)
            for coluna, titulo, ranking in zip(
                st.columns(3), ["Grau", "Força", "Intermediação"], valores
            ):
                coluna.subheader(titulo)
                if ranking:
                    coluna.dataframe(pd.DataFrame([
                        (identificador, por_id[identificador].nome, valor)
                        for identificador, valor in ranking
                    ], columns=["ID", "Autor", titulo]), hide_index=True)

    with grupos:
        st.write(f"{len(comunidades)} comunidades identificadas.")
        st.dataframe(pd.DataFrame([
            (numero, len(grupo), ", ".join(sorted(grupo)))
            for numero, grupo in enumerate(comunidades, start=1)
        ], columns=["Comunidade", "Autores", "IDs"]), hide_index=True)

    with areas:
        esquerda, direita = st.columns(2)
        esquerda.subheader("Autores por área")
        esquerda.dataframe(
            pd.DataFrame(distribuicao_areas(grafo).items(), columns=["Área", "Autores"]),
            hide_index=True,
        )
        direita.subheader("Conexões interdisciplinares")
        direita.dataframe(pd.DataFrame([
            (area_a, area_b, peso) for (area_a, area_b), peso in colaboracoes_entre_areas(grafo).items()
        ], columns=["Área A", "Área B", "Peso"]), hide_index=True)

    with evolucao:
        if inicio is None:
            st.info("Nenhuma publicação com ano disponível para a série temporal.")
        else:
            tabela = pd.DataFrame(serie_anual(autores, publicacoes, inicio, fim, acumulado))
            st.line_chart(tabela, x="ano", y=["autores_ativos", "publicacoes", "arestas", "peso_total"])
            st.line_chart(tabela, x="ano", y=["componentes", "maior_componente"])
            st.line_chart(tabela, x="ano", y="densidade")
            st.dataframe(tabela, hide_index=True)


if __name__ == "__main__":
    main()
