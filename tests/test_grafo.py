import pytest

from src.graph.grafo import GrafoColaboracao
from src.models.autor import Autor


@pytest.fixture
def grafo():
    rede = GrafoColaboracao()
    rede.adicionar_autor(Autor("A", "Ana"))
    rede.adicionar_autor(Autor("B", "Bruno"))
    rede.adicionar_autor(Autor("C", "Carla"))
    return rede


def test_cadastra_autor_isolado(grafo):
    autor = Autor("D", "Ana", frozenset({"Computação"}))
    grafo.adicionar_autor(autor)

    assert grafo.obter_autor("D") is autor
    assert grafo.obter_autor("A").nome == autor.nome
    assert grafo.grau("D") == 0
    assert grafo.vizinhos("D") == {}
    assert grafo.peso_coautoria("A", "D") == 0
    assert list(grafo.arestas()) == []


def test_registra_coautoria_simetrica(grafo):
    grafo.registrar_coautoria("B", "A")

    assert grafo.peso_coautoria("A", "B") == 1
    assert grafo.peso_coautoria("B", "A") == 1
    assert list(grafo.arestas()) == [("A", "B", 1)]


def test_incrementa_peso_sem_aumentar_grau(grafo):
    grafo.registrar_coautoria("A", "B")
    grafo.registrar_coautoria("B", "A")
    grafo.adicionar_autor(Autor("A", "Ana"))

    assert grafo.vizinhos("A") == {"B": 2}
    assert grafo.vizinhos("B") == {"A": 2}
    assert grafo.grau("A") == 1


def test_rejeita_cadastro_conflitante(grafo):
    with pytest.raises(ValueError):
        grafo.adicionar_autor(Autor("A", "Outro nome"))

    assert grafo.obter_autor("A").nome == "Ana"


def test_rejeita_laco(grafo):
    with pytest.raises(ValueError):
        grafo.registrar_coautoria("A", "A")

    assert grafo.vizinhos("A") == {}


@pytest.mark.parametrize("primeiro_id, segundo_id", [("A", "X"), ("X", "A")])
def test_rejeita_coautoria_com_autor_inexistente(grafo, primeiro_id, segundo_id):
    with pytest.raises(KeyError, match="X"):
        grafo.registrar_coautoria(primeiro_id, segundo_id)

    assert grafo.vizinhos("A") == {}
    assert list(grafo.arestas()) == []


def test_consulta_grau_e_vizinhos_sem_expor_adjacencia(grafo):
    grafo.registrar_coautoria("A", "B")
    grafo.registrar_coautoria("A", "C")

    vizinhos = grafo.vizinhos("A")
    assert vizinhos == {"B": 1, "C": 1}
    vizinhos.clear()
    assert grafo.grau("A") == 2
    assert grafo.vizinhos("A") == {"B": 1, "C": 1}


@pytest.mark.parametrize(
    "metodo, argumentos",
    [
        ("obter_autor", ("X",)),
        ("grau", ("X",)),
        ("vizinhos", ("X",)),
        ("peso_coautoria", ("X", "A")),
        ("peso_coautoria", ("A", "X")),
    ],
)
def test_consultas_rejeitam_autor_inexistente(grafo, metodo, argumentos):
    with pytest.raises(KeyError, match="X"):
        getattr(grafo, metodo)(*argumentos)


def test_enumera_autores_incluindo_isolados(grafo):
    grafo.registrar_coautoria("A", "B")
    autores = grafo.autores()

    assert autores == (Autor("A", "Ana"), Autor("B", "Bruno"), Autor("C", "Carla"))
    assert grafo.grau("C") == 0

    novo_autor = Autor("D", "Daniel")
    grafo.adicionar_autor(novo_autor)
    assert grafo.autores() == (*autores, novo_autor)


def test_enumera_multiplas_arestas_com_pesos_distintos(grafo):
    grafo.registrar_coautoria("B", "A")
    grafo.registrar_coautoria("C", "B")
    grafo.registrar_coautoria("A", "B")

    assert sorted(grafo.arestas()) == [("A", "B", 2), ("B", "C", 1)]


def test_preserva_arestas_apos_operacoes_invalidas(grafo):
    grafo.registrar_coautoria("A", "B")
    grafo.registrar_coautoria("A", "B")
    grafo.registrar_coautoria("B", "C")

    with pytest.raises(ValueError):
        grafo.adicionar_autor(Autor("B", "Outro nome"))
    with pytest.raises(ValueError):
        grafo.registrar_coautoria("B", "B")
    with pytest.raises(KeyError):
        grafo.registrar_coautoria("B", "X")

    assert grafo.vizinhos("A") == {"B": 2}
    assert grafo.vizinhos("B") == {"A": 2, "C": 1}
    assert grafo.vizinhos("C") == {"B": 1}
    assert sorted(grafo.arestas()) == [("A", "B", 2), ("B", "C", 1)]
