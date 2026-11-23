from dataclasses import replace

import pytest

from src.graph.construtor import ConstrutorGrafo
from src.graph.grafo import GrafoColaboracao
from src.models.autor import Autor
from src.models.publicacao import Publicacao


@pytest.fixture
def autores():
    return [
        Autor("A", "Ana", frozenset({" Computação "})),
        Autor("B", "Bruno"),
        Autor("C", "Carla"),
    ]


def test_constroi_coautoria_de_dois_autores_e_preserva_isolado(autores):
    publicacao = Publicacao("P1", "Artigo", 2024, ("B", "A"))
    grafo = ConstrutorGrafo.construir(autores, [publicacao])

    assert list(grafo.arestas()) == [("A", "B", 1)]
    assert grafo.vizinhos("A") == {"B": 1}
    assert grafo.vizinhos("B") == {"A": 1}
    assert grafo.autores() == tuple(autores)
    assert grafo.vizinhos("C") == {}


def test_constroi_todos_os_pares_de_uma_publicacao(autores):
    publicacao = Publicacao("P1", "Artigo", 2024, ("C", "A", "B"))
    grafo = ConstrutorGrafo.construir(autores, [publicacao])

    assert sorted(grafo.arestas()) == [("A", "B", 1), ("A", "C", 1), ("B", "C", 1)]


def test_soma_publicacoes_distintas_e_ignora_duplicatas_identicas(autores):
    primeira = Publicacao("P1", "Artigo", 2023, ("A", "B", "C"))
    segunda = Publicacao("P2", "Outro artigo", 2024, ("B", "A"))
    grafo = ConstrutorGrafo.construir(autores, [primeira, segunda, replace(primeira)])

    assert sorted(grafo.arestas()) == [("A", "B", 2), ("A", "C", 1), ("B", "C", 1)]


@pytest.mark.parametrize("publicacoes", [[], [Publicacao("P1", "Solo", 2024, ("A",))]])
def test_preserva_vertices_sem_coautoria(autores, publicacoes):
    grafo = ConstrutorGrafo.construir(autores, publicacoes)

    assert grafo.autores() == tuple(autores)
    assert list(grafo.arestas()) == []


def test_rejeita_publicacao_conflitante_mesmo_fora_do_recorte(autores):
    publicacao = Publicacao("P1", "Artigo", 2024, ("A", "B"))
    conflitante = replace(publicacao, ano=2025)

    with pytest.raises(ValueError, match="Publicação.*conflitantes.*P1"):
        ConstrutorGrafo.construir(autores, [publicacao, conflitante], ano_final=2024)


def test_valida_referencias_antes_de_registrar_arestas(autores, monkeypatch):
    def falhar_se_registrar(*args):
        pytest.fail("Uma aresta foi registrada antes de validar todas as publicações.")

    monkeypatch.setattr(GrafoColaboracao, "registrar_coautoria", falhar_se_registrar)
    valida = Publicacao("P1", "Artigo", 2024, ("A", "B"))
    invalida = Publicacao("P2", "Solo", 2025, ("X",))

    with pytest.raises(ValueError, match="P2.*não cadastrado.*X"):
        ConstrutorGrafo.construir(autores, [valida, invalida], ano_final=2024)


def test_aceita_autores_duplicados_identicos(autores):
    grafo = ConstrutorGrafo.construir([*autores, replace(autores[0])], [])

    assert grafo.autores() == tuple(autores)


def test_rejeita_autores_duplicados_conflitantes(autores):
    conflitante = replace(autores[0], nome="Outro nome")

    with pytest.raises(ValueError, match="Autor.*conflitantes.*'A'"):
        ConstrutorGrafo.construir([*autores, conflitante], [])


@pytest.mark.parametrize(
    "filtros, arestas",
    [
        ({}, [("A", "B", 3), ("A", "C", 1), ("B", "C", 1)]),
        ({"ano_inicial": 2021, "ano_final": 2022}, [("A", "B", 2)]),
        ({"ano_inicial": 2022}, [("A", "B", 1), ("B", "C", 1)]),
        ({"ano_final": 2021}, [("A", "B", 2), ("A", "C", 1)]),
        ({"ano_final": 2022, "acumulado": True}, [("A", "B", 3), ("A", "C", 1)]),
        ({"ano_inicial": 2021, "ano_final": 2021}, [("A", "B", 1)]),
        ({"ano_inicial": 2024}, []),
    ],
)
def test_filtra_publicacoes_por_ano_e_preserva_autores(autores, filtros, arestas):
    publicacoes = [
        Publicacao("P1", "Artigo 1", 2020, ("A", "B")),
        Publicacao("P2", "Artigo 2", 2020, ("A", "C")),
        Publicacao("P3", "Artigo 3", 2021, ("A", "B")),
        Publicacao("P4", "Artigo 4", 2022, ("A", "B")),
        Publicacao("P5", "Artigo 5", 2023, ("B", "C")),
    ]
    grafo = ConstrutorGrafo.construir(autores, publicacoes, **filtros)

    assert sorted(grafo.arestas()) == arestas
    assert grafo.autores() == tuple(autores)


@pytest.mark.parametrize(
    "filtros",
    [
        {"ano_inicial": 0},
        {"ano_final": -1},
        {"ano_inicial": True},
        {"ano_final": "2024"},
        {"ano_final": 2024.0},
        {"ano_inicial": 2025, "ano_final": 2024},
        {"acumulado": True},
        {"ano_inicial": 2020, "ano_final": 2024, "acumulado": True},
        {"ano_final": 2024, "acumulado": 1},
    ],
)
def test_rejeita_parametros_temporais_invalidos(filtros):
    with pytest.raises(ValueError):
        ConstrutorGrafo.construir([], [], **filtros)


def test_preserva_os_dados_de_entrada_e_aceita_iteradores(autores):
    publicacoes = [Publicacao("P1", "Artigo", 2024, ("B", "A"), frozenset({"IA"}))]
    autores_originais = [replace(autor) for autor in autores]
    publicacoes_originais = [replace(publicacao) for publicacao in publicacoes]

    grafo = ConstrutorGrafo.construir(iter(autores), iter(publicacoes))

    assert autores == autores_originais
    assert publicacoes == publicacoes_originais
    assert grafo.obter_autor("A") is autores[0]
    assert grafo.obter_autor("A").areas == frozenset({" Computação "})
    assert list(grafo.arestas()) == [("A", "B", 1)]
