import pytest

from src.algorithms.areas import (
    colaboracoes_entre_areas,
    distribuicao_areas,
    ranking_pontes_interdisciplinares,
)
from src.graph.construtor import ConstrutorGrafo
from src.graph.grafo import GrafoColaboracao
from src.models.autor import Autor
from src.models.publicacao import Publicacao


def criar_grafo(areas_por_autor, arestas=()):
    grafo = GrafoColaboracao()
    for autor_id, areas in areas_por_autor.items():
        grafo.adicionar_autor(Autor(autor_id, autor_id, frozenset(areas)))
    for primeiro, segundo, peso in arestas:
        for _ in range(peso):
            grafo.registrar_coautoria(primeiro, segundo)
    return grafo


def test_grafo_vazio():
    grafo = GrafoColaboracao()

    assert distribuicao_areas(grafo) == {}
    assert colaboracoes_entre_areas(grafo) == {}
    assert ranking_pontes_interdisciplinares(grafo) == []


def test_distribuicao_inclui_isolados_e_preserva_o_texto_das_areas():
    grafo = criar_grafo({"C": (), "B": ("IA", " IA "), "A": ("IA",)})

    assert list(distribuicao_areas(grafo).items()) == [(" IA ", 1), ("IA", 2)]
    assert colaboracoes_entre_areas(grafo) == {}
    assert ranking_pontes_interdisciplinares(grafo) == [("A", 0), ("B", 0), ("C", 0)]


@pytest.mark.parametrize(
    "areas_a, areas_b, peso, pares, pontuacao",
    [
        (("IA",), ("IA",), 3, {}, 0),
        (("IA",), ("Biologia",), 1, {("Biologia", "IA"): 1}, 1),
        (("IA",), ("Biologia",), 4, {("Biologia", "IA"): 4}, 4),
        ((), (), 2, {}, 0),
        ((), ("IA",), 2, {}, 0),
        (("IA",), (), 2, {}, 0),
        (("IA",), ("IA", "Biologia"), 3, {("Biologia", "IA"): 3}, 3),
        (("IA", "Biologia"), ("IA", "Biologia"), 2, {("Biologia", "IA"): 2}, 2),
    ],
)
def test_colaboracao_individual(areas_a, areas_b, peso, pares, pontuacao):
    grafo = criar_grafo({"B": areas_b, "A": areas_a}, [("B", "A", peso)])

    assert colaboracoes_entre_areas(grafo) == pares
    assert ranking_pontes_interdisciplinares(grafo) == [("A", pontuacao), ("B", pontuacao)]


def test_projecao_deduplica_pares_por_aresta_e_agrega_arestas_distintas():
    grafo = criar_grafo(
        {"D": ("Matemática",), "C": (), "B": ("IA", "Biologia", "Matemática"),
         "A": ("IA", "Biologia"), "E": ("IA",)},
        [("B", "D", 3), ("A", "B", 2), ("B", "C", 5)],
    )

    assert list(colaboracoes_entre_areas(grafo).items()) == [
        (("Biologia", "IA"), 2),
        (("Biologia", "Matemática"), 5),
        (("IA", "Matemática"), 5),
    ]
    assert ranking_pontes_interdisciplinares(grafo) == [
        ("B", 5), ("D", 3), ("A", 2), ("C", 0), ("E", 0)
    ]


def test_resultados_deterministicos_independentemente_da_ordem_de_cadastro():
    areas = {"B": ("IA", "Biologia"), "A": ("Matemática",), "C": ("IA",)}
    arestas = [("A", "C", 2), ("B", "A", 1)]
    primeiro = criar_grafo(areas, arestas)
    segundo = criar_grafo(dict(reversed(areas.items())), reversed(arestas))

    assert list(distribuicao_areas(primeiro).items()) == list(distribuicao_areas(segundo).items())
    assert list(colaboracoes_entre_areas(primeiro).items()) == list(
        colaboracoes_entre_areas(segundo).items()
    )
    assert ranking_pontes_interdisciplinares(primeiro) == ranking_pontes_interdisciplinares(
        segundo
    )


def test_analises_preservam_grafo_e_metadados():
    grafo = criar_grafo({"C": (), "A": (" IA ",), "B": ("Biologia",)}, [("B", "A", 2)])
    autores = grafo.autores()
    areas = tuple(autor.areas for autor in autores)
    arestas = list(grafo.arestas())
    vizinhancas = [list(grafo.vizinhos(autor.id).items()) for autor in autores]

    distribuicao_areas(grafo)
    colaboracoes_entre_areas(grafo)
    ranking_pontes_interdisciplinares(grafo)

    assert grafo.autores() == autores
    assert tuple(autor.areas for autor in grafo.autores()) == areas
    assert list(grafo.arestas()) == arestas
    assert [list(grafo.vizinhos(autor.id).items()) for autor in autores] == vizinhancas


def test_integracao_com_construtor_utiliza_areas_dos_autores():
    autores = [
        Autor("A", "Ana", frozenset({"IA"})),
        Autor("B", "Bruno", frozenset({"Biologia"})),
        Autor("C", "Carla"),
    ]
    publicacoes = [
        Publicacao("P1", "Artigo 1", 2024, ("A", "B", "C"), frozenset({"Física"})),
        Publicacao("P2", "Artigo 2", 2024, ("B", "A")),
    ]
    grafo = ConstrutorGrafo.construir(autores, publicacoes)

    assert distribuicao_areas(grafo) == {"Biologia": 1, "IA": 1}
    assert colaboracoes_entre_areas(grafo) == {("Biologia", "IA"): 2}
    assert ranking_pontes_interdisciplinares(grafo) == [("A", 2), ("B", 2), ("C", 0)]
