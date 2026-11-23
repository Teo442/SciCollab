from itertools import combinations

from src.graph.grafo import GrafoColaboracao


def coeficiente_agrupamento_local(grafo: GrafoColaboracao, autor_id: str) -> float:
    """Retorna a fração de pares de vizinhos conectados, ignorando os pesos.

    Autores com menos de dois vizinhos têm coeficiente zero.
    Levanta KeyError se o autor não estiver cadastrado.
    """
    vizinhos = grafo.vizinhos(autor_id)
    grau = len(vizinhos)
    if grau < 2:
        return 0.0

    conexoes = sum(
        grafo.peso_coautoria(primeiro, segundo) > 0
        for primeiro, segundo in combinations(vizinhos, 2)
    )
    return 2 * conexoes / (grau * (grau - 1))


def coeficiente_agrupamento_global(grafo: GrafoColaboracao) -> float:
    """Calcula a média dos coeficientes locais, incluindo graus zero e um.

    Uma rede vazia tem média zero. A transitividade global é uma métrica
    distinta, definida pela razão entre triplas fechadas e triplas conectadas.
    """
    autores = grafo.autores()
    if not autores:
        return 0.0

    return sum(
        coeficiente_agrupamento_local(grafo, autor.id) for autor in autores
    ) / len(autores)


def ranking_agrupamento(grafo: GrafoColaboracao) -> list[tuple[str, float]]:
    """Retorna pares (ID, coeficiente), por valor decrescente e ID crescente."""
    return sorted(
        (
            (autor.id, coeficiente_agrupamento_local(grafo, autor.id))
            for autor in grafo.autores()
        ),
        key=lambda item: (-item[1], item[0]),
    )
