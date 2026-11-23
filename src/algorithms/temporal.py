from collections import defaultdict
from collections.abc import Iterable

from src.algorithms.busca import componentes_conexas
from src.graph.construtor import ConstrutorGrafo
from src.models.autor import Autor
from src.models.publicacao import Publicacao


def evolucao_temporal(
    autores: Iterable[Autor],
    publicacoes: Iterable[Publicacao],
    ano_inicial: int | None = None,
    ano_final: int | None = None,
    acumulado: bool = True,
) -> list[dict[str, int | float]]:
    """Retorna uma linha por ano, inclusive nos anos sem publicações.

    Limites omitidos vêm da base. Sem publicações, ambos os limites devem
    ser explícitos para produzir linhas. No modo acumulado, cada janela
    começa no limite inferior. Só autores da janela entram no grafo.
    """
    for ano in (ano_inicial, ano_final):
        if ano is not None and (type(ano) is not int or ano <= 0):
            raise ValueError("Os limites devem ser anos inteiros positivos.")
    if type(acumulado) is not bool:
        raise ValueError("acumulado deve ser booleano.")
    if ano_inicial is not None and ano_final is not None and ano_inicial > ano_final:
        raise ValueError("O ano inicial deve ser menor ou igual ao ano final.")

    cadastro = ConstrutorGrafo.construir(autores, []).autores()
    ids_cadastrados = {autor.id for autor in cadastro}
    unicas: dict[str, Publicacao] = {}
    por_ano: dict[int, list[Publicacao]] = defaultdict(list)
    for publicacao in publicacoes:
        if publicacao.id in unicas:
            if unicas[publicacao.id] != publicacao:
                raise ValueError(f"Publicação {publicacao.id!r} com dados conflitantes.")
            continue
        for autor_id in publicacao.autor_ids:
            if autor_id not in ids_cadastrados:
                raise ValueError(f"Publicação {publicacao.id!r}: autor {autor_id!r} não cadastrado.")
        unicas[publicacao.id] = publicacao
        por_ano[publicacao.ano].append(publicacao)

    inicio = ano_inicial if ano_inicial is not None else min(por_ano, default=None)
    fim = ano_final if ano_final is not None else max(por_ano, default=None)
    if inicio is None or fim is None:
        return []

    registros = []
    janela: list[Publicacao] = []
    ativos: set[str] = set()
    resumo: dict[str, int | float] = {}
    for ano in range(inicio, fim + 1):
        novas = por_ano.get(ano, [])
        if not acumulado:
            janela = []
            ativos = set()
        janela.extend(novas)
        for publicacao in novas:
            ativos.update(publicacao.autor_ids)

        if novas or not resumo or not acumulado:
            grafo = ConstrutorGrafo.construir(
                (autor for autor in cadastro if autor.id in ativos), janela
            )
            componentes = componentes_conexas(grafo)
            arestas = peso_total = 0
            for _, _, peso in grafo.arestas():
                arestas += 1
                peso_total += peso
            total = len(ativos)
            resumo = {
                "autores_ativos": total,
                "publicacoes": len(janela),
                "arestas": arestas,
                "peso_total": peso_total,
                "componentes": len(componentes),
                "maior_componente": max(map(len, componentes), default=0),
                "densidade": 2 * arestas / (total * (total - 1)) if total > 1 else 0.0,
            }
        registros.append({"ano": ano, **resumo})
    return registros
