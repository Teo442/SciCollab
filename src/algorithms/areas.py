from collections import Counter

from src.graph.grafo import GrafoColaboracao


def distribuicao_areas(grafo: GrafoColaboracao) -> dict[str, int]:
    """Conta os autores por área, incluindo isolados, com as chaves ordenadas."""
    contagens = Counter(area for autor in grafo.autores() for area in autor.areas)
    return dict(sorted(contagens.items()))


def colaboracoes_entre_areas(grafo: GrafoColaboracao) -> dict[tuple[str, str], int]:
    """Retorna a projeção agregada das coautorias em pares ordenados de áreas.

    Autores com múltiplas áreas podem fazer uma coautoria contribuir para
    vários pares. Cada par distinto recebe o peso da aresta uma única vez.
    """
    pesos: Counter[tuple[str, str]] = Counter()
    for primeiro, segundo, peso in grafo.arestas():
        areas_a = grafo.obter_autor(primeiro).areas
        areas_b = grafo.obter_autor(segundo).areas
        if not areas_a or not areas_b:
            continue
        pares = {
            (area_a, area_b) if area_a < area_b else (area_b, area_a)
            for area_a in areas_a
            for area_b in areas_b
            if area_a != area_b
        }
        for par in pares:
            pesos[par] += peso
    return dict(sorted(pesos.items()))


def ranking_pontes_interdisciplinares(
    grafo: GrafoColaboracao,
) -> list[tuple[str, int]]:
    """Ordena a força das coautorias interdisciplinares, com desempate por ID.

    A pontuação soma pesos incidentes quando existe um par de áreas distintas
    entre os autores da aresta. A intermediação de Brandes mede a participação
    em caminhos mínimos e é calculada separadamente.
    """
    pontuacoes = dict.fromkeys((autor.id for autor in grafo.autores()), 0)
    for primeiro, segundo, peso in grafo.arestas():
        areas_a = grafo.obter_autor(primeiro).areas
        areas_b = grafo.obter_autor(segundo).areas
        if not areas_a or not areas_b:
            continue
        # Com áreas nas duas pontas, só dois conjuntos unitários iguais
        # impedem a formação de um par de áreas distintas.
        if len(areas_a) == len(areas_b) == 1 and areas_a == areas_b:
            continue
        pontuacoes[primeiro] += peso
        pontuacoes[segundo] += peso
    return sorted(pontuacoes.items(), key=lambda item: (-item[1], item[0]))
