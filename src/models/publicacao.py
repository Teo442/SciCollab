from collections.abc import Sequence
from dataclasses import dataclass

from src.models._validacao import validar_areas


@dataclass(frozen=True)
class Publicacao:
    id: str
    titulo: str
    ano: int
    autor_ids: tuple[str, ...]
    areas: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id.strip():
            raise ValueError("O ID da publicação deve ser um texto não vazio.")
        if not isinstance(self.titulo, str) or not self.titulo.strip():
            raise ValueError("O título da publicação deve ser um texto não vazio.")
        if type(self.ano) is not int or self.ano <= 0:
            raise ValueError("O ano deve ser um inteiro positivo.")
        if not isinstance(self.autor_ids, Sequence) or isinstance(
            self.autor_ids, (str, bytes, bytearray)
        ):
            raise ValueError("Informe os IDs dos autores em uma sequência.")
        autor_ids = tuple(self.autor_ids)
        if not autor_ids or any(
            not isinstance(autor_id, str) or not autor_id.strip()
            for autor_id in autor_ids
        ):
            raise ValueError("A publicação deve ter pelo menos um autor com ID válido.")
        if len(autor_ids) != len(set(autor_ids)):
            raise ValueError("Os IDs dos autores da publicação devem ser distintos.")
        object.__setattr__(self, "autor_ids", autor_ids)
        object.__setattr__(self, "areas", validar_areas(self.areas))
