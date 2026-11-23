from collections.abc import Iterable
from itertools import combinations

from src.graph.grafo import GrafoColaboracao
from src.models.autor import Autor
from src.models.publicacao import Publicacao


class ConstrutorGrafo:
    """Constrói grafos sem manter estado entre chamadas."""

    @staticmethod
    def construir(
        autores: Iterable[Autor],
        publicacoes: Iterable[Publicacao],
        ano_inicial: int | None = None,
        ano_final: int | None = None,
        acumulado: bool = False,
    ) -> GrafoColaboracao:
        """Valida todas as publicações e registra os pares do recorte inclusivo."""
        for nome, ano in (("ano_inicial", ano_inicial), ("ano_final", ano_final)):
            if ano is not None and (type(ano) is not int or ano <= 0):
                raise ValueError(f"{nome} deve ser um inteiro positivo.")
        if not isinstance(acumulado, bool):
            raise ValueError("acumulado deve ser um booleano.")
        if acumulado and (ano_final is None or ano_inicial is not None):
            raise ValueError("O modo acumulado exige ano_final e proíbe ano_inicial.")
        if ano_inicial is not None and ano_final is not None and ano_inicial > ano_final:
            raise ValueError("ano_inicial deve ser menor ou igual a ano_final.")

        grafo = GrafoColaboracao()
        for autor in autores:
            grafo.adicionar_autor(autor)

        publicacoes_por_id: dict[str, Publicacao] = {}
        for publicacao in publicacoes:
            existente = publicacoes_por_id.get(publicacao.id)
            if existente is not None:
                if existente != publicacao:
                    raise ValueError(
                        f"Publicação com dados conflitantes para o ID {publicacao.id!r}."
                    )
                continue

            for autor_id in publicacao.autor_ids:
                try:
                    grafo.obter_autor(autor_id)
                except KeyError as erro:
                    raise ValueError(
                        f"A publicação {publicacao.id!r} referencia o autor "
                        f"não cadastrado {autor_id!r}."
                    ) from erro
            publicacoes_por_id[publicacao.id] = publicacao

        for publicacao in publicacoes_por_id.values():
            if ano_inicial is not None and publicacao.ano < ano_inicial:
                continue
            if ano_final is not None and publicacao.ano > ano_final:
                continue

            for primeiro_id, segundo_id in combinations(publicacao.autor_ids, 2):
                grafo.registrar_coautoria(primeiro_id, segundo_id)

        return grafo
