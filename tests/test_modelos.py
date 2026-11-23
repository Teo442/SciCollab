from dataclasses import FrozenInstanceError

import pytest

from src.models.autor import Autor
from src.models.publicacao import Publicacao


def test_autor_preserva_areas_em_objeto_imutavel():
    areas = {"Computação", "Matemática"}
    autor = Autor("A", "Ana", areas)
    areas.clear()

    assert autor.areas == frozenset({"Computação", "Matemática"})
    with pytest.raises(FrozenInstanceError):
        autor.nome = "Outro nome"


@pytest.mark.parametrize("autor_id, nome", [("", "Ana"), ("A", " ")])
def test_autor_rejeita_campos_vazios(autor_id, nome):
    with pytest.raises(ValueError):
        Autor(autor_id, nome)


def test_publicacao_preserva_ordem_e_areas_em_objeto_imutavel():
    autor_ids = ["B", "A"]
    areas = {"Computação"}
    publicacao = Publicacao("P1", "Artigo", 2024, autor_ids, areas)
    autor_ids.clear()
    areas.clear()

    assert publicacao.autor_ids == ("B", "A")
    assert publicacao.areas == frozenset({"Computação"})
    with pytest.raises(FrozenInstanceError):
        publicacao.ano = 2025


@pytest.mark.parametrize(
    "publicacao_id, titulo, ano, autor_ids",
    [
        ("", "Artigo", 2024, ("A",)),
        ("P1", " ", 2024, ("A",)),
        ("P1", "Artigo", 0, ("A",)),
        ("P1", "Artigo", True, ("A",)),
        ("P1", "Artigo", 2024, ()),
        ("P1", "Artigo", 2024, ("",)),
        ("P1", "Artigo", 2024, (" ",)),
        ("P1", "Artigo", 2024, (42,)),
        ("P1", "Artigo", 2024, ("A", "A")),
        ("P1", "Artigo", 2024, "AB"),
        ("P1", "Artigo", 2024, {"A", "B"}),
        ("P1", "Artigo", 2024, {"A": "Ana"}),
        ("P1", "Artigo", 2024, None),
    ],
)
def test_publicacao_rejeita_dados_invalidos(publicacao_id, titulo, ano, autor_ids):
    with pytest.raises(ValueError):
        Publicacao(publicacao_id, titulo, ano, autor_ids)


@pytest.mark.parametrize(
    "classe, argumentos",
    [(Autor, ("A", "Ana")), (Publicacao, ("P1", "Artigo", 2024, ("A",)))],
)
class TestAreas:
    @pytest.mark.parametrize("areas", ["IA", ["IA", 42], [[]], [""], [" \t"]])
    def test_rejeita_areas_invalidas(self, classe, argumentos, areas):
        with pytest.raises(ValueError):
            classe(*argumentos, areas=areas)

    def test_aceita_colecao_vazia(self, classe, argumentos):
        assert classe(*argumentos, areas=[]).areas == frozenset()

    def test_preserva_textos_originais(self, classe, argumentos):
        modelo = classe(*argumentos, areas=(" IA ", "IA", " IA "))

        assert modelo.areas == frozenset({" IA ", "IA"})


def test_publicacao_aceita_um_unico_autor():
    publicacao = Publicacao("P1", "Artigo", 2024, [" A "])

    assert publicacao.autor_ids == (" A ",)
