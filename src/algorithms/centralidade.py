from collections import deque

from src.graph.grafo import GrafoColaboracao


def centralidade_grau(grafo: GrafoColaboracao, autor_id: str) -> float:
    """Retorna o grau normalizado, ou 0.0 para um grafo com um único autor.

    Levanta KeyError se o autor não estiver cadastrado.
    """
    grau = grafo.grau(autor_id)
    return grau / max(1, len(grafo.autores()) - 1)


def forca_autor(grafo: GrafoColaboracao, autor_id: str) -> int:
    """Soma os pesos incidentes ao autor. Levanta KeyError para ID desconhecido."""
    return sum(grafo.vizinhos(autor_id).values())


def ranking_grau(grafo: GrafoColaboracao) -> list[tuple[str, float]]:
    """Retorna pares (ID, centralidade), por valor decrescente e ID crescente."""
    autores = grafo.autores()
    denominador = max(1, len(autores) - 1)
    return sorted(
        ((autor.id, grafo.grau(autor.id) / denominador) for autor in autores),
        key=lambda item: (-item[1], item[0]),
    )


def ranking_forca(grafo: GrafoColaboracao) -> list[tuple[str, int]]:
    """Retorna pares (ID, força), por valor decrescente e ID crescente."""
    return sorted(
        ((autor.id, forca_autor(grafo, autor.id)) for autor in grafo.autores()),
        key=lambda item: (-item[1], item[0]),
    )


def _intermediacoes(
    grafo: GrafoColaboracao, normalizada: bool
) -> dict[str, float]:
    pontuacoes = dict.fromkeys((autor.id for autor in grafo.autores()), 0.0)
    total = len(pontuacoes)
    if total <= 2:
        return pontuacoes

    adjacencia = {autor_id: tuple(grafo.vizinhos(autor_id)) for autor_id in pontuacoes}
    for origem in adjacencia:
        fila = deque([origem])
        ordem = []
        distancias = {origem: 0}
        caminhos = {origem: 1}
        predecessores: dict[str, list[str]] = {origem: []}

        while fila:
            atual = fila.popleft()
            ordem.append(atual)
            proxima_distancia = distancias[atual] + 1
            for vizinho in adjacencia[atual]:
                if vizinho not in distancias:
                    distancias[vizinho] = proxima_distancia
                    caminhos[vizinho] = 0
                    predecessores[vizinho] = []
                    fila.append(vizinho)
                if distancias[vizinho] == proxima_distancia:
                    caminhos[vizinho] += caminhos[atual]
                    predecessores[vizinho].append(atual)

        dependencias = dict.fromkeys(ordem, 0.0)
        for atual in reversed(ordem):
            for predecessor in predecessores[atual]:
                fracao = caminhos[predecessor] / caminhos[atual]
                dependencias[predecessor] += fracao * (1.0 + dependencias[atual])
            if atual != origem:
                pontuacoes[atual] += dependencias[atual]

    # Cada par é contado em duas direções. A normalização usa pares não ordenados.
    divisor = (total - 1) * (total - 2) if normalizada else 2
    return {autor_id: valor / divisor for autor_id, valor in pontuacoes.items()}


def centralidade_intermediacao(
    grafo: GrafoColaboracao, autor_id: str, normalizada: bool = True
) -> float:
    """Retorna a intermediação de um autor com comprimentos unitários.

    Por padrão, normaliza pelo total de pares possíveis entre os demais autores.
    Levanta KeyError se o ID não estiver cadastrado.
    """
    grafo.obter_autor(autor_id)
    return _intermediacoes(grafo, normalizada)[autor_id]


def ranking_intermediacao(
    grafo: GrafoColaboracao, normalizada: bool = True
) -> list[tuple[str, float]]:
    """Retorna pares (ID, intermediação), por valor decrescente e ID crescente."""
    return sorted(
        _intermediacoes(grafo, normalizada).items(),
        key=lambda item: (-item[1], item[0]),
    )
