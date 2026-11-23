from pathlib import Path

from streamlit.testing.v1 import AppTest

from scripts import importar_openalex as openalex
from src.data.carregador import carregar_csv


RAIZ = Path(__file__).resolve().parents[1]


def trabalho(codigo, ano, autores, area=None):
    return {
        "id": f"https://openalex.org/{codigo}",
        "display_name": codigo,
        "publication_year": ano,
        "authorships": [
            {"author": {"id": f"https://openalex.org/{autor}", "display_name": autor}}
            for autor in autores
        ],
        "primary_topic": {"field": {"display_name": area}},
    }


def test_coleta_respeita_cotas_ordem_e_areas(monkeypatch):
    def consultar(ano, pagina, tamanho):
        assert pagina == 1 and tamanho == 100
        return [
            trabalho(f"W{ano}3", ano, ["A1", "A3"], "Física"),
            trabalho(f"W{ano}1", ano, ["A1"]),
            trabalho(f"W{ano}2", ano, ["A1", "A1", "A2"], "Matemática"),
            trabalho(f"W{ano}2", ano, ["A1", "A2"], "Matemática"),
        ]

    monkeypatch.setattr(openalex, "consultar", consultar)
    monkeypatch.setattr(openalex, "sleep", lambda _: None)
    nomes, areas, publicacoes, contagens = openalex.coletar(6)
    assert contagens == {2020: (4, 2), **{ano: (4, 1) for ano in range(2021, 2025)}}
    assert len(publicacoes) == 6
    assert publicacoes["W20202"][2] == "A1;A2"
    assert nomes == {"A1": "A1", "A2": "A2", "A3": "A3"}
    assert areas["A1"] == {"Física", "Matemática"}


def test_exclui_trabalhos_com_muitas_assinaturas():
    registro = trabalho("W1", 2020, [f"A{i}" for i in range(1, 22)])
    assert openalex.interpretar(registro, 2020) is None


def test_amostra_real_passa_pelo_carregador_e_pela_validacao():
    pasta = RAIZ / "datasets" / "openalex"
    csvs = [(pasta / nome).read_bytes() for nome in ("autores.csv", "publicacoes.csv")]
    autores, publicacoes = carregar_csv(*csvs)
    assert len(publicacoes) == 150
    assert len(autores) == 664
    assert {p.ano for p in publicacoes} == set(openalex.ANOS)
    assert all(2 <= len(p.autor_ids) <= openalex.LIMITE_AUTORES for p in publicacoes)
    relatorio = openalex.gerar_relatorio(*csvs, {}, "data de teste", 150)
    assert "| Arestas | 2021 |" in relatorio
    assert "| Soma dos pesos | 2074 |" in relatorio


def test_amostra_local_no_streamlit():
    app = AppTest.from_file(str(RAIZ / "app" / "main.py"), default_timeout=30).run()
    assert app.radio[0].value == "Demonstração"
    app.radio[0].set_value("OpenAlex local").run()
    assert not app.exception
    assert not app.error
    metricas = {item.label: item.value for item in app.metric}
    assert metricas["Autores"] == "664"
    assert metricas["Publicações"] == "150"
    assert metricas["Arestas"] == "2021"
