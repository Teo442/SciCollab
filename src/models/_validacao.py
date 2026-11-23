from collections.abc import Collection


def validar_areas(areas: Collection[str]) -> frozenset[str]:
    if not isinstance(areas, Collection) or isinstance(areas, (str, bytes, bytearray)):
        raise ValueError("Informe as áreas em uma coleção de textos.")

    valores = tuple(areas)
    if any(not isinstance(area, str) or not area.strip() for area in valores):
        raise ValueError("Cada área deve ser um texto não vazio.")
    return frozenset(valores)
