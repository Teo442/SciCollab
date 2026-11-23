from dataclasses import dataclass

from src.models._validacao import validar_areas


@dataclass(frozen=True)
class Autor:
    id: str
    nome: str
    areas: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id.strip():
            raise ValueError("O ID do autor deve ser um texto não vazio.")
        if not isinstance(self.nome, str) or not self.nome.strip():
            raise ValueError("O nome do autor deve ser um texto não vazio.")
        object.__setattr__(self, "areas", validar_areas(self.areas))
