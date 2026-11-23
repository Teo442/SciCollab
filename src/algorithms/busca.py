from collections import deque

from src.graph.grafo import GrafoColaboracao


def busca_em_largura(grafo: GrafoColaboracao, autor_id: str) -> list[str]:
    """Retorna os IDs alcançáveis na ordem de descoberta, a partir de autor_id.

    Segue a ordem de inserção dos vizinhos, ignora os pesos e preserva o grafo.
    Levanta KeyError se o autor inicial não estiver cadastrado.
    """
    grafo.obter_autor(autor_id)
    fila = deque([autor_id])
    visitados = {autor_id}
    ordem = [autor_id]

    while fila:
        atual = fila.popleft()
        for vizinho in grafo.vizinhos(atual):
            if vizinho in visitados:
                continue
            visitados.add(vizinho)
            ordem.append(vizinho)
            fila.append(vizinho)

    return ordem


def componentes_conexas(grafo: GrafoColaboracao) -> list[set[str]]:
    """Agrupa os IDs do grafo não direcionado em componentes, incluindo isolados.

    A ordem segue o primeiro autor cadastrado de cada componente.
    Um grafo vazio retorna uma lista vazia. A operação preserva o grafo.
    """
    componentes: list[set[str]] = []
    visitados: set[str] = set()

    for autor in grafo.autores():
        if autor.id in visitados:
            continue
        componente = set(busca_em_largura(grafo, autor.id))
        visitados.update(componente)
        componentes.append(componente)

    return componentes
