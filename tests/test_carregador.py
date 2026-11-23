from pathlib import Path

import pytest

from src.data.carregador import carregar_csv
from src.graph.construtor import ConstrutorGrafo


AUTORES = "id,nome,areas\nA,Ana,IA;Estatística\nB,Bruno,Biologia\n".encode()
PUBLICACOES = b'id,titulo,ano,autor_ids\nP,"Redes, grafos",2024,A;B\n'


def test_carrega_csv_com_bom_e_titulo_entre_aspas():
    autores, publicacoes = carregar_csv(b"\xef\xbb\xbf" + AUTORES, PUBLICACOES)
    assert autores[0].areas == {"IA", "Estatística"}
    assert publicacoes[0].titulo == "Redes, grafos"
    assert list(ConstrutorGrafo.construir(autores, publicacoes).arestas()) == [("A", "B", 1)]


@pytest.mark.parametrize("autores, publicacoes, mensagem", [
    (AUTORES + b"A,Outro,IA\n", PUBLICACOES, "autor duplicado"),
    (AUTORES, PUBLICACOES + b"P,Outro,2025,A\n", "ID duplicado de publicação"),
    (AUTORES, b"id,titulo,ano,autor_ids\nP,Artigo,2024,X\n", "autor não cadastrado"),
    (AUTORES, b"id,titulo,ano,autor_ids\nP,Artigo,0,A\n", "ano"),
    (AUTORES, b"id,titulo,ano,autor_ids\nP,Artigo,2024.5,A\n", "ano inválido"),
    (AUTORES, b"id,titulo,ano,autor_ids\nP,Artigo,2024,\n", "pelo menos um autor"),
    (AUTORES, b"id,titulo,ano,autor_ids\nP,Artigo,2024,A;A\n", "distintos"),
    (AUTORES, b"id,titulo,ano,autor_ids\nP,Artigo,2024\n", "quantidade incorreta"),
    (AUTORES, b'id,titulo,ano,autor_ids\nP,"Artigo,2024,A\n', "malformado"),
    (b"id,nome\nA,Ana\n", PUBLICACOES, "cabeçalho inválido"),
    (b"id,nome,areas\nA,,IA\n", PUBLICACOES, "nome do autor"),
    (b"\xff", PUBLICACOES, "UTF-8"),
])
def test_erros_de_importacao_incluem_contexto(autores, publicacoes, mensagem):
    with pytest.raises(ValueError, match=mensagem) as erro:
        carregar_csv(autores, publicacoes)
    assert ".csv" in str(erro.value)


def test_dataset_demo_forma_rede_com_autores_isolados():
    pasta = Path(__file__).resolve().parents[1] / "datasets" / "demo"
    autores, publicacoes = carregar_csv(
        (pasta / "autores.csv").read_bytes(), (pasta / "publicacoes.csv").read_bytes()
    )
    grafo = ConstrutorGrafo.construir(autores, publicacoes)
    assert 20 <= len(autores) <= 40
    assert len({publicacao.ano for publicacao in publicacoes}) >= 3
    assert list(grafo.arestas())
    assert any(grafo.grau(autor.id) == 0 for autor in autores)
