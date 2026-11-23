import pytest

from src.algorithms.temporal import evolucao_temporal
from src.models.autor import Autor
from src.models.publicacao import Publicacao


@pytest.fixture
def base():
    autores = [Autor(identificador, identificador) for identificador in "ABCD"]
    publicacoes = [
        Publicacao("1", "Dupla", 2020, ("A", "B")),
        Publicacao("2", "Dupla novamente", 2022, ("A", "B")),
        Publicacao("3", "Individual", 2022, ("C",)),
    ]
    return autores, publicacoes


def test_acumulado_inclui_lacuna_e_autor_individual(base):
    primeiro, lacuna, ultimo = evolucao_temporal(*base)
    assert primeiro == {
        "ano": 2020, "autores_ativos": 2, "publicacoes": 1, "arestas": 1,
        "peso_total": 1, "componentes": 1, "maior_componente": 2, "densidade": 1.0,
    }
    assert lacuna == {**primeiro, "ano": 2021}
    assert ultimo == {
        "ano": 2022, "autores_ativos": 3, "publicacoes": 3, "arestas": 1,
        "peso_total": 2, "componentes": 2, "maior_componente": 2, "densidade": 1 / 3,
    }


def test_anual_e_acumulado_respeitam_janelas(base):
    anual = evolucao_temporal(*base, acumulado=False)
    assert anual[1]["autores_ativos"] == anual[1]["componentes"] == 0
    assert anual[2]["peso_total"] == 1
    assert anual[2]["publicacoes"] == 2
    acumulado = evolucao_temporal(*base, ano_inicial=2021, ano_final=2023)
    assert acumulado[0]["publicacoes"] == 0
    assert acumulado[1] == anual[2]
    assert acumulado[2] == {**anual[2], "ano": 2023}


def test_sem_publicacoes():
    assert evolucao_temporal([], []) == []
    assert evolucao_temporal([], [], 2020, 2020)[0]["densidade"] == 0.0


@pytest.mark.parametrize("filtros", [
    {"ano_inicial": False}, {"ano_final": 0}, {"acumulado": 1},
    {"ano_inicial": 2022, "ano_final": 2020},
])
def test_rejeita_filtros_invalidos(base, filtros):
    with pytest.raises(ValueError):
        evolucao_temporal(*base, **filtros)


def test_deduplica_e_valida_inclusive_fora_da_janela(base):
    autores, publicacoes = base
    assert evolucao_temporal(autores, [*publicacoes, publicacoes[0]]) == evolucao_temporal(*base)
    with pytest.raises(ValueError, match="conflitantes"):
        evolucao_temporal(autores, [*publicacoes, Publicacao("1", "Outra", 2024, ("A",))])
    with pytest.raises(ValueError, match="não cadastrado"):
        evolucao_temporal(autores, [*publicacoes, Publicacao("4", "Outra", 2024, ("X",))], ano_final=2022)
