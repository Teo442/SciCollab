from pathlib import Path

from streamlit.testing.v1 import AppTest


APP = Path(__file__).resolve().parents[1] / "app" / "main.py"


def test_demo_e_filtro_anual_no_streamlit():
    app = AppTest.from_file(str(APP), default_timeout=30).run()

    assert not app.exception
    assert [aba.label for aba in app.tabs] == [
        "Rede", "Autores", "Comunidades", "Áreas", "Evolução"
    ]
    assert {metrica.label: metrica.value for metrica in app.metric} == {
        "Autores": "28",
        "Publicações": "45",
        "Arestas": "51",
        "Componentes": "5",
        "Densidade": "13.5%",
        "Agrupamento médio": "51.4%",
    }
    assert app.get("plotly_chart")
    app.radio[1].set_value("Anual").run()
    app.slider[1].set_value(2020).run()
    assert not app.exception
    assert next(metrica.value for metrica in app.metric if metrica.label == "Publicações") == "8"
    assert app.tabs[-1].dataframe[0].value["publicacoes"].tolist() == [8, 8, 9, 10, 10]


def test_upload_valido_e_erro_de_referencia_no_streamlit():
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    app.radio[0].set_value("Importar CSV").run()
    assert any("Selecione os dois arquivos" in item.value for item in app.info)

    app.file_uploader[0].upload("autores.csv", b"id,nome,areas\nA,Ana,IA\nB,Bruno,Biologia\n")
    app.file_uploader[1].upload(
        "publicacoes.csv", b"id,titulo,ano,autor_ids\nP,Artigo,2024,A;B\n"
    ).run()
    assert not app.exception
    assert not app.error
    assert next(metrica.value for metrica in app.metric if metrica.label == "Arestas") == "1"

    app.file_uploader[1].clear().upload(
        "publicacoes.csv", b"id,titulo,ano,autor_ids\nP,Artigo,2024,X\n"
    ).run()
    assert not app.exception
    assert any("autor não cadastrado" in erro.value for erro in app.error)
