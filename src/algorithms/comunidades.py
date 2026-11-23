from src.graph.grafo import GrafoColaboracao


def detectar_comunidades(
    grafo: GrafoColaboracao, max_iteracoes: int = 100
) -> list[set[str]]:
    """Agrupa autores por rótulo com propagação ponderada assíncrona.

    Cada passagem atualiza os rótulos imediatamente na ordem de cadastro.
    Em empate, preserva o rótulo atual se ele tiver pontuação máxima.
    Uma passagem sem mudanças encerra o cálculo. max_iteracoes limita
    a quantidade de passagens completas pelos vértices.
    Em um ciclo, escolhe o estado com menos rótulos distintos entre os
    estados do próprio ciclo. Empates usam a ordem lexicográfica dos
    rótulos na ordem de cadastro dos autores. Se o limite for atingido
    antes de detectar um ciclo ou estabilizar, usa o último estado.
    As comunidades são ordenadas pelo menor ID de cada uma.
    """
    if type(max_iteracoes) is not int or max_iteracoes <= 0:
        raise ValueError("max_iteracoes deve ser um inteiro positivo.")

    autores = tuple(autor.id for autor in grafo.autores())
    vizinhancas = {autor_id: grafo.vizinhos(autor_id) for autor_id in autores}
    estado = autores
    rotulos = dict(zip(autores, estado))
    historico = [estado]
    indices = {estado: 0}

    for _ in range(max_iteracoes):
        for autor_id in autores:
            pontuacoes: dict[str, int] = {}
            for vizinho, peso in vizinhancas[autor_id].items():
                rotulo = rotulos[vizinho]
                pontuacoes[rotulo] = pontuacoes.get(rotulo, 0) + peso
            if not pontuacoes:
                continue
            melhor_rotulo = min(
                pontuacoes, key=lambda rotulo: (-pontuacoes[rotulo], rotulo)
            )
            if pontuacoes.get(rotulos[autor_id], 0) < pontuacoes[melhor_rotulo]:
                rotulos[autor_id] = melhor_rotulo

        novo_estado = tuple(rotulos[autor_id] for autor_id in autores)
        if novo_estado == estado:
            break
        if novo_estado in indices:
            inicio = indices[novo_estado]
            estado = min(
                historico[inicio:],
                key=lambda candidato: (len(set(candidato)), candidato),
            )
            break

        estado = novo_estado
        indices[estado] = len(historico)
        historico.append(estado)

    comunidades: dict[str, set[str]] = {}
    for autor_id, rotulo in zip(autores, estado):
        comunidades.setdefault(rotulo, set()).add(autor_id)
    return sorted(comunidades.values(), key=min)
