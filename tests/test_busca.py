import pytest

from src.algorithms.busca import busca_em_largura, componentes_conexas
from src.graph.construtor import ConstrutorGrafo
from src.graph.grafo import GrafoColaboracao
from src.models.autor import Autor
from src.models.publicacao import Publicacao


def criar_grafo(autor_ids, arestas=()):
    grafo = GrafoColaboracao()
    for autor_id in autor_ids:
        grafo.adicionar_autor(Autor(autor_id, autor_id))
    for primeiro_id, segundo_id in arestas:
        grafo.registrar_coautoria(primeiro_id, segundo_id)
    return grafo


@pytest.mark.parametrize("autor_ids", [(), ("A",)])
def test_busca_em_largura_rejeita_autor_inexistente(autor_ids):
    with pytest.raises(KeyError, match="X"):
        busca_em_largura(criar_grafo(autor_ids), "X")


def test_busca_em_largura_em_autor_isolado():
    grafo = criar_grafo("ABC", [("A", "B")])
    assert busca_em_largura(grafo, "C") == ["C"]


def test_busca_em_largura_em_cadeia():
    grafo = criar_grafo("ABCD", [("A", "B"), ("B", "C"), ("C", "D")])
    assert busca_em_largura(grafo, "D") == ["D", "C", "B", "A"]


def test_busca_em_largura_em_ciclo():
    grafo = criar_grafo("ABCD", [("A", "B"), ("B", "C"), ("C", "D"), ("D", "A")])
    assert busca_em_largura(grafo, "A") == ["A", "B", "D", "C"]


def test_busca_em_largura_em_ramificacoes_respeita_ordem_de_insercao():
    grafo = criar_grafo("ABCDE", [("A", "C"), ("A", "B"), ("C", "E"), ("B", "D")])
    assert busca_em_largura(grafo, "A") == ["A", "C", "B", "E", "D"]


def test_busca_em_largura_em_grafo_desconexo():
    grafo = criar_grafo("ABCD", [("A", "B"), ("C", "D")])
    assert busca_em_largura(grafo, "C") == ["C", "D"]


def test_busca_em_largura_ignora_pesos():
    grafo = criar_grafo("ABCD", [("A", "B"), ("A", "C"), ("A", "C"), ("B", "D")])
    assert busca_em_largura(grafo, "A") == ["A", "B", "C", "D"]


@pytest.mark.parametrize("algoritmo", [busca_em_largura, componentes_conexas])
def test_consulta_cada_vertice_uma_so_vez(algoritmo, monkeypatch):
    grafo = criar_grafo("ABCD", [("A", "B"), ("A", "C"), ("B", "D"), ("C", "D")])
    consultar_vizinhos = grafo.vizinhos
    consultas = []

    def contar_consulta(autor_id):
        consultas.append(autor_id)
        return consultar_vizinhos(autor_id)

    monkeypatch.setattr(grafo, "vizinhos", contar_consulta)
    if algoritmo is busca_em_largura:
        assert algoritmo(grafo, "A") == ["A", "B", "C", "D"]
    else:
        assert algoritmo(grafo) == [{"A", "B", "C", "D"}]

    assert consultas == ["A", "B", "C", "D"]


def test_componentes_em_grafo_vazio():
    assert componentes_conexas(GrafoColaboracao()) == []


def test_componentes_com_um_autor():
    assert componentes_conexas(criar_grafo("A")) == [{"A"}]


def test_componentes_em_grafo_totalmente_conectado():
    grafo = criar_grafo("ABC", [("A", "B"), ("A", "C"), ("B", "C")])
    assert componentes_conexas(grafo) == [{"A", "B", "C"}]


def test_componentes_em_grafo_desconexo_seguem_a_ordem_de_cadastro():
    grafo = criar_grafo("CADB", [("A", "B"), ("C", "D")])
    assert componentes_conexas(grafo) == [{"C", "D"}, {"A", "B"}]


def test_componentes_com_multiplos_isolados():
    grafo = criar_grafo("ACBD", [("A", "B")])
    assert componentes_conexas(grafo) == [{"A", "B"}, {"C"}, {"D"}]


def test_buscas_preservam_autores_arestas_e_ordem_dos_vizinhos():
    grafo = criar_grafo("ABCD", [("A", "C"), ("A", "B"), ("A", "C")])
    autores = grafo.autores()
    arestas = list(grafo.arestas())
    vizinhancas = [list(grafo.vizinhos(autor.id).items()) for autor in autores]

    busca_em_largura(grafo, "A")
    componentes_conexas(grafo)

    assert grafo.autores() == autores
    assert list(grafo.arestas()) == arestas
    assert [list(grafo.vizinhos(autor.id).items()) for autor in autores] == vizinhancas


def test_componentes_da_rede_construida_com_publicacoes():
    autores = [Autor(autor_id, autor_id) for autor_id in "ABCDEFG"]
    publicacoes = [
        Publicacao("P1", "Artigo 1", 2024, ("A", "B")),
        Publicacao("P2", "Artigo 2", 2024, ("B", "C")),
        Publicacao("P3", "Artigo 3", 2024, ("D", "E")),
        Publicacao("P4", "Artigo 4", 2024, ("F",)),
    ]

    grafo = ConstrutorGrafo.construir(autores, publicacoes)

    assert componentes_conexas(grafo) == [{"A", "B", "C"}, {"D", "E"}, {"F"}, {"G"}]
