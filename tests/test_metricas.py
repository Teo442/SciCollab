from itertools import combinations

import pytest

from src.algorithms.metricas import (
    coeficiente_agrupamento_global,
    coeficiente_agrupamento_local,
    ranking_agrupamento,
)
from src.graph.construtor import ConstrutorGrafo
from src.graph.grafo import GrafoColaboracao
from src.models.autor import Autor
from src.models.publicacao import Publicacao


def criar_grafo(autor_ids, arestas=()):
    grafo = GrafoColaboracao()
    for autor_id in autor_ids:
        grafo.adicionar_autor(Autor(autor_id, autor_id))
    for primeiro, segundo in arestas:
        grafo.registrar_coautoria(primeiro, segundo)
    return grafo


def test_grafo_vazio():
    grafo = GrafoColaboracao()
    assert coeficiente_agrupamento_global(grafo) == 0.0
    assert ranking_agrupamento(grafo) == []


@pytest.mark.parametrize("autor_ids", ["", "ABC"])
def test_autor_inexistente(autor_ids):
    with pytest.raises(KeyError, match="X"):
        coeficiente_agrupamento_local(criar_grafo(autor_ids), "X")


@pytest.mark.parametrize(
    "autor_ids, arestas",
    [
        pytest.param("A", [], id="isolado"),
        pytest.param("AB", [("A", "B")], id="um-vizinho"),
        pytest.param("ABCD", [("A", "B"), ("B", "C"), ("C", "D")], id="cadeia"),
        pytest.param("ABCD", [("A", "B"), ("A", "C"), ("A", "D")], id="estrela"),
        pytest.param(
            "ABCD", [("A", "B"), ("B", "C"), ("C", "D"), ("D", "A")], id="ciclo"
        ),
    ],
)
def test_coeficientes_zero_em_grafos_sem_triangulos(autor_ids, arestas):
    grafo = criar_grafo(autor_ids, arestas)
    for autor_id in autor_ids:
        valor = coeficiente_agrupamento_local(grafo, autor_id)
        assert isinstance(valor, float)
        assert valor == 0.0
    assert coeficiente_agrupamento_global(grafo) == 0.0


@pytest.mark.parametrize("autor_ids", ["ABC", "ABCD"])
def test_grafo_completo(autor_ids):
    grafo = criar_grafo(autor_ids, combinations(autor_ids, 2))
    assert ranking_agrupamento(grafo) == [(autor_id, 1.0) for autor_id in autor_ids]
    assert coeficiente_agrupamento_global(grafo) == 1.0


def test_triangulo_com_ligacao_adicional_e_empates_no_ranking():
    grafo = criar_grafo("DCBA", [*combinations("ABC", 2), ("A", "D")])

    assert coeficiente_agrupamento_local(grafo, "A") == pytest.approx(1 / 3)
    assert coeficiente_agrupamento_global(grafo) == pytest.approx(7 / 12)
    assert ranking_agrupamento(grafo) == [
        ("B", 1.0), ("C", 1.0), ("A", 1 / 3), ("D", 0.0)
    ]


def test_grafo_desconexo_inclui_isolados_e_grau_um_na_media():
    grafo = criar_grafo("FEDCBA", [*combinations("ABC", 2), ("D", "E")])

    assert coeficiente_agrupamento_global(grafo) == 0.5
    assert ranking_agrupamento(grafo) == [
        ("A", 1.0), ("B", 1.0), ("C", 1.0), ("D", 0.0), ("E", 0.0), ("F", 0.0)
    ]


def test_pesos_distintos_sao_ignorados():
    grafo = criar_grafo("ABCD", [*combinations("ABC", 2), ("A", "D")])
    grafo.registrar_coautoria("B", "C")
    grafo.registrar_coautoria("A", "D")
    grafo.registrar_coautoria("A", "D")

    assert coeficiente_agrupamento_local(grafo, "A") == pytest.approx(1 / 3)
    assert coeficiente_agrupamento_global(grafo) == pytest.approx(7 / 12)


def test_metricas_preservam_o_grafo():
    grafo = criar_grafo("DCBA", [*combinations("ABC", 2), ("B", "A")])
    autores = grafo.autores()
    arestas = list(grafo.arestas())
    vizinhancas = [list(grafo.vizinhos(autor.id).items()) for autor in autores]

    coeficiente_agrupamento_local(grafo, "A")
    coeficiente_agrupamento_global(grafo)
    ranking_agrupamento(grafo)

    assert grafo.autores() == autores
    assert list(grafo.arestas()) == arestas
    assert [list(grafo.vizinhos(autor.id).items()) for autor in autores] == vizinhancas


def test_integracao_com_construtor_grafo():
    autores = [Autor(autor_id, autor_id) for autor_id in "EDCBA"]
    publicacoes = [
        Publicacao("P1", "Artigo 1", 2024, ("A", "B", "C")),
        Publicacao("P2", "Artigo 2", 2024, ("A", "D")),
        Publicacao("P3", "Artigo 3", 2024, ("E",)),
    ]
    grafo = ConstrutorGrafo.construir(autores, publicacoes)

    assert coeficiente_agrupamento_global(grafo) == pytest.approx(7 / 15)
    assert ranking_agrupamento(grafo) == [
        ("B", 1.0), ("C", 1.0), ("A", 1 / 3), ("D", 0.0), ("E", 0.0)
    ]
