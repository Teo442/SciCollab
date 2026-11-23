from itertools import combinations

import pytest

from src.algorithms.comunidades import detectar_comunidades
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


@pytest.mark.parametrize(
    "autor_ids, esperado",
    [("", []), ("A", [{"A"}]), ("CBA", [{"A"}, {"B"}, {"C"}])],
)
def test_comunidades_sem_arestas(autor_ids, esperado):
    assert detectar_comunidades(criar_grafo(autor_ids)) == esperado


@pytest.mark.parametrize("autor_ids", ["AB", "BA"])
def test_dois_autores_conectados_formam_uma_comunidade(autor_ids):
    grafo = criar_grafo(autor_ids, [("A", "B")])

    assert detectar_comunidades(grafo, max_iteracoes=1) == [{"A", "B"}]


def test_cadeia_linear_converge_para_uma_comunidade():
    grafo = criar_grafo("ABCD", [("A", "B"), ("B", "C"), ("C", "D")])

    assert detectar_comunidades(grafo) == [{"A", "B", "C", "D"}]


def test_ciclo_de_quatro_vertices():
    grafo = criar_grafo("ABCD", [("A", "B"), ("B", "C"), ("C", "D"), ("D", "A")])

    assert detectar_comunidades(grafo) == [{"A", "B", "C", "D"}]


def test_grafo_completo_converge_para_uma_comunidade():
    grafo = criar_grafo("DCBA", combinations("ABCD", 2))

    assert detectar_comunidades(grafo) == [{"A", "B", "C", "D"}]


def test_grupos_densos_com_ligacao_fraca_e_autor_isolado():
    internas = [*combinations("ABC", 2), *combinations("DEF", 2)]
    grafo = criar_grafo("GFEDCBA", [*internas, *internas, ("C", "D")])

    assert detectar_comunidades(grafo) == [{"A", "B", "C"}, {"D", "E", "F"}, {"G"}]


def test_peso_prevalece_sobre_desempate_lexicografico():
    grafo = criar_grafo("ABCD", [("A", "B"), ("A", "D"), ("B", "C")])
    assert detectar_comunidades(grafo) == [{"A", "B", "C", "D"}]

    grafo.registrar_coautoria("A", "D")
    assert detectar_comunidades(grafo) == [{"A", "D"}, {"B", "C"}]


def test_pontuacao_soma_pesos_de_vizinhos_com_mesmo_rotulo():
    arestas = [("A", "B"), ("A", "D"), ("B", "C"), ("B", "D")]
    grafo = criar_grafo("ABCD", [*arestas, ("A", "D")])

    # B recebe o mesmo rótulo de A e D, somando dois pesos unitários.
    assert detectar_comunidades(grafo, max_iteracoes=1) == [{"A", "B", "C", "D"}]


def test_empate_usa_menor_rotulo_independentemente_da_ordem_das_arestas():
    grafo = criar_grafo("ABCD", [("A", "D"), ("A", "B"), ("B", "C")])

    assert detectar_comunidades(grafo, max_iteracoes=1) == [{"A", "B", "C", "D"}]


def test_empate_preserva_rotulo_atual_mesmo_se_houver_rotulo_menor():
    grafo = criar_grafo("ABCD", [("A", "C"), ("A", "D"), ("B", "D")])

    assert detectar_comunidades(grafo) == [{"A", "C"}, {"B", "D"}]


@pytest.mark.parametrize(
    "autor_ids, esperado", [("ABC", [{"A"}, {"B", "C"}]), ("CBA", [{"A", "B", "C"}])]
)
def test_primeira_passagem_segue_ordem_de_cadastro(autor_ids, esperado):
    grafo = criar_grafo(autor_ids, [("A", "B"), ("B", "C"), ("B", "C")])

    assert detectar_comunidades(grafo, max_iteracoes=1) == esperado


def test_limite_de_passagens_retorna_ultimo_estado_calculado():
    grafo = criar_grafo("ABC", [("A", "B"), ("B", "C"), ("B", "C")])

    assert detectar_comunidades(grafo, max_iteracoes=1) == [{"A"}, {"B", "C"}]
    assert detectar_comunidades(grafo, max_iteracoes=2) == [{"A", "B", "C"}]


@pytest.mark.parametrize("limite", [0, -1, False, True, 1.5, "2", None])
def test_rejeita_limite_invalido(limite):
    with pytest.raises(ValueError, match="max_iteracoes"):
        detectar_comunidades(GrafoColaboracao(), limite)


def test_execucoes_repetidas_preservam_particao_e_grafo():
    grafo = criar_grafo("DCBA", [("A", "C"), ("A", "B"), ("A", "C")])
    autores = grafo.autores()
    arestas = list(grafo.arestas())
    vizinhancas = [list(grafo.vizinhos(autor.id).items()) for autor in autores]

    primeira = detectar_comunidades(grafo)
    assert detectar_comunidades(grafo) == primeira
    assert sum(map(len, primeira)) == len(autores)
    assert set().union(*primeira) == {autor.id for autor in autores}
    assert grafo.autores() == autores
    assert list(grafo.arestas()) == arestas
    assert [list(grafo.vizinhos(autor.id).items()) for autor in autores] == vizinhancas


def test_integracao_com_construtor_grafo():
    autores = [Autor(autor_id, autor_id) for autor_id in "FEDCBA"]
    publicacoes = [
        Publicacao("P1", "Artigo 1", 2024, ("A", "B", "C")),
        Publicacao("P2", "Artigo 2", 2024, ("D", "E", "F")),
    ]
    grafo = ConstrutorGrafo.construir(autores, publicacoes)

    assert detectar_comunidades(grafo) == [{"A", "B", "C"}, {"D", "E", "F"}]
