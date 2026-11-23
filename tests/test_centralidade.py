from itertools import combinations

import pytest

from src.algorithms.centralidade import (
    centralidade_grau,
    centralidade_intermediacao,
    forca_autor,
    ranking_forca,
    ranking_grau,
    ranking_intermediacao,
)
from src.graph.construtor import ConstrutorGrafo
from src.graph.grafo import GrafoColaboracao
from src.models.autor import Autor
from src.models.publicacao import Publicacao


def criar_grafo(autor_ids, coautorias=()):
    grafo = GrafoColaboracao()
    for autor_id in autor_ids:
        grafo.adicionar_autor(Autor(autor_id, autor_id))
    for primeiro_id, segundo_id in coautorias:
        grafo.registrar_coautoria(primeiro_id, segundo_id)
    return grafo


def test_rankings_em_grafo_vazio():
    grafo = GrafoColaboracao()

    assert ranking_grau(grafo) == []
    assert ranking_forca(grafo) == []


@pytest.mark.parametrize("autor_ids", ["", "A", "AB"])
@pytest.mark.parametrize("metrica", [centralidade_grau, forca_autor])
def test_metricas_rejeitam_id_inexistente(autor_ids, metrica):
    with pytest.raises(KeyError, match="X"):
        metrica(criar_grafo(autor_ids), "X")


def test_metricas_e_rankings_com_um_unico_autor():
    grafo = criar_grafo("A")

    assert centralidade_grau(grafo, "A") == 0.0
    assert forca_autor(grafo, "A") == 0
    assert ranking_grau(grafo) == [("A", 0.0)]
    assert ranking_forca(grafo) == [("A", 0)]


def test_autor_isolado_conta_na_normalizacao_e_nos_rankings():
    grafo = criar_grafo("CBA", [("B", "A")])

    assert centralidade_grau(grafo, "C") == 0.0
    assert forca_autor(grafo, "C") == 0
    assert ranking_grau(grafo) == [("A", 0.5), ("B", 0.5), ("C", 0.0)]
    assert ranking_forca(grafo) == [("A", 1), ("B", 1), ("C", 0)]


def test_metricas_em_cadeia():
    grafo = criar_grafo("DCBA", [("A", "B"), ("B", "C"), ("C", "D")])

    assert centralidade_grau(grafo, "A") == pytest.approx(1 / 3)
    assert centralidade_grau(grafo, "B") == pytest.approx(2 / 3)
    assert ranking_grau(grafo) == [("B", 2 / 3), ("C", 2 / 3), ("A", 1 / 3), ("D", 1 / 3)]
    assert ranking_forca(grafo) == [("B", 2), ("C", 2), ("A", 1), ("D", 1)]


def test_metricas_em_estrela():
    grafo = criar_grafo("DCBA", [("D", "C"), ("D", "B"), ("D", "A")])

    assert ranking_grau(grafo) == [("D", 1.0), ("A", 1 / 3), ("B", 1 / 3), ("C", 1 / 3)]
    assert ranking_forca(grafo) == [("D", 3), ("A", 1), ("B", 1), ("C", 1)]


def test_rankings_em_grafo_completo_desempatam_por_id():
    grafo = criar_grafo("CBA", combinations("CBA", 2))

    assert ranking_grau(grafo) == [("A", 1.0), ("B", 1.0), ("C", 1.0)]
    assert ranking_forca(grafo) == [("A", 2), ("B", 2), ("C", 2)]


def test_pesos_distintos_mudam_forca_e_preservam_grau():
    grafo = criar_grafo("CBA", [("B", "A"), ("B", "C"), ("B", "C")])

    assert forca_autor(grafo, "B") == 3
    assert ranking_grau(grafo) == [("B", 1.0), ("A", 0.5), ("C", 0.5)]
    assert ranking_forca(grafo) == [("B", 3), ("C", 2), ("A", 1)]


def test_metricas_preservam_o_grafo():
    grafo = criar_grafo("DCBA", [("A", "C"), ("A", "B"), ("C", "A")])
    autores = grafo.autores()
    arestas = list(grafo.arestas())
    vizinhancas = [list(grafo.vizinhos(autor.id).items()) for autor in autores]

    centralidade_grau(grafo, "A")
    forca_autor(grafo, "A")
    ranking_grau(grafo)
    ranking_forca(grafo)

    assert grafo.autores() == autores
    assert list(grafo.arestas()) == arestas
    assert [list(grafo.vizinhos(autor.id).items()) for autor in autores] == vizinhancas


def test_rankings_em_rede_construida_com_publicacoes():
    autores = [Autor(autor_id, autor_id) for autor_id in "DCBA"]
    publicacoes = [
        Publicacao("P1", "Artigo 1", 2024, ("A", "B", "C")),
        Publicacao("P2", "Artigo 2", 2024, ("B", "C")),
        Publicacao("P3", "Artigo 3", 2024, ("D",)),
    ]
    grafo = ConstrutorGrafo.construir(autores, publicacoes)

    assert ranking_grau(grafo) == [("A", 2 / 3), ("B", 2 / 3), ("C", 2 / 3), ("D", 0.0)]
    assert ranking_forca(grafo) == [("B", 3), ("C", 3), ("A", 2), ("D", 0)]


@pytest.mark.parametrize("normalizada", [False, True])
@pytest.mark.parametrize("autor_ids", ["", "A", "BA"])
def test_intermediacao_em_grafos_com_ate_dois_autores(autor_ids, normalizada):
    grafo = criar_grafo(autor_ids, combinations(autor_ids, 2))

    assert ranking_intermediacao(grafo, normalizada) == [
        (autor_id, 0.0) for autor_id in sorted(autor_ids)
    ]
    for autor_id in autor_ids:
        assert centralidade_intermediacao(grafo, autor_id, normalizada) == 0.0
    with pytest.raises(KeyError, match="X"):
        centralidade_intermediacao(grafo, "X", normalizada)


def test_intermediacao_na_cadeia_conta_pares_nao_ordenados():
    grafo = criar_grafo("DCBA", [("A", "B"), ("B", "C"), ("C", "D")])

    assert ranking_intermediacao(grafo, False) == [
        ("B", 2.0), ("C", 2.0), ("A", 0.0), ("D", 0.0)
    ]
    assert centralidade_intermediacao(grafo, "B") == pytest.approx(2 / 3)


def test_intermediacao_em_estrela_e_em_grafo_completo():
    estrela = criar_grafo("DCBA", [("D", "A"), ("D", "B"), ("D", "C")])
    completo = criar_grafo("DCBA", combinations("DCBA", 2))

    assert ranking_intermediacao(estrela) == [
        ("D", 1.0), ("A", 0.0), ("B", 0.0), ("C", 0.0)
    ]
    assert ranking_intermediacao(completo) == [
        ("A", 0.0), ("B", 0.0), ("C", 0.0), ("D", 0.0)
    ]


def test_intermediacao_divide_credito_entre_caminhos_minimos_e_ignora_pesos():
    grafo = criar_grafo("DCBA", [("A", "B"), ("B", "C"), ("C", "D"), ("D", "A")])
    grafo.registrar_coautoria("A", "B")
    arestas_originais = list(grafo.arestas())

    assert ranking_intermediacao(grafo, False) == [
        ("A", 0.5), ("B", 0.5), ("C", 0.5), ("D", 0.5)
    ]
    assert centralidade_intermediacao(grafo, "A") == pytest.approx(1 / 6)
    assert list(grafo.arestas()) == arestas_originais


def test_intermediacao_em_rede_desconexa_usa_total_de_autores_na_normalizacao():
    autores = [Autor(autor_id, autor_id) for autor_id in "FEDCBA"]
    publicacoes = [
        Publicacao("P1", "Artigo 1", 2024, ("A", "B")),
        Publicacao("P2", "Artigo 2", 2024, ("B", "C")),
        Publicacao("P3", "Artigo 3", 2024, ("D", "E")),
    ]
    grafo = ConstrutorGrafo.construir(autores, publicacoes)

    assert ranking_intermediacao(grafo) == [
        ("B", 0.1), ("A", 0.0), ("C", 0.0), ("D", 0.0), ("E", 0.0), ("F", 0.0)
    ]
