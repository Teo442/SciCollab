from collections.abc import Iterator

from src.models.autor import Autor


class GrafoColaboracao:
    """Grafo não direcionado com pesos inteiros positivos de coautoria."""

    def __init__(self) -> None:
        self._autores: dict[str, Autor] = {}
        self._adjacencia: dict[str, dict[str, int]] = {}

    def adicionar_autor(self, autor: Autor) -> None:
        existente = self._autores.get(autor.id)
        if existente is not None and existente != autor:
            raise ValueError(f"Autor com dados conflitantes para o ID {autor.id!r}.")
        self._autores.setdefault(autor.id, autor)
        self._adjacencia.setdefault(autor.id, {})

    def obter_autor(self, autor_id: str) -> Autor:
        return self._autores[autor_id]

    def autores(self) -> tuple[Autor, ...]:
        """Retorna uma tupla dos autores cadastrados, na ordem de cadastro."""
        return tuple(self._autores.values())

    def registrar_coautoria(self, primeiro_id: str, segundo_id: str) -> None:
        vizinhos_primeiro = self._adjacencia[primeiro_id]
        vizinhos_segundo = self._adjacencia[segundo_id]
        if primeiro_id == segundo_id:
            raise ValueError("Uma coautoria exige dois autores distintos.")

        novo_peso = vizinhos_primeiro.get(segundo_id, 0) + 1
        vizinhos_primeiro[segundo_id] = novo_peso
        vizinhos_segundo[primeiro_id] = novo_peso

    def peso_coautoria(self, primeiro_id: str, segundo_id: str) -> int:
        self.obter_autor(segundo_id)
        return self._adjacencia[primeiro_id].get(segundo_id, 0)

    def vizinhos(self, autor_id: str) -> dict[str, int]:
        return self._adjacencia[autor_id].copy()

    def grau(self, autor_id: str) -> int:
        return len(self._adjacencia[autor_id])

    def arestas(self) -> Iterator[tuple[str, str, int]]:
        """Retorna cada par uma vez, com os IDs em ordem lexicográfica."""
        for autor_id, vizinhos in self._adjacencia.items():
            for vizinho_id, peso in vizinhos.items():
                if autor_id < vizinho_id:
                    yield autor_id, vizinho_id, peso
