import csv
from collections.abc import Iterator
from io import StringIO

from src.models.autor import Autor
from src.models.publicacao import Publicacao


def _registros(
    conteudo: bytes, arquivo: str, obrigatorios: set[str], opcionais: set[str]
) -> Iterator[tuple[str, dict[str, str]]]:
    try:
        texto = conteudo.decode("utf-8-sig")
    except UnicodeDecodeError as erro:
        raise ValueError(f"{arquivo}: salve o arquivo em UTF-8.") from erro

    leitor = csv.reader(StringIO(texto, newline=""), strict=True)
    try:
        colunas = [coluna.strip() for coluna in next(leitor, [])]
        if (
            not obrigatorios.issubset(colunas)
            or set(colunas) - obrigatorios - opcionais
            or len(colunas) != len(set(colunas))
        ):
            esperadas = ", ".join(sorted(obrigatorios))
            extras = f" Opcionais: {', '.join(sorted(opcionais))}." if opcionais else ""
            raise ValueError(f"{arquivo}: cabeçalho inválido. Esperado: {esperadas}.{extras}")
        for valores in leitor:
            if not valores:
                continue
            local = f"{arquivo}, linha {leitor.line_num}"
            if len(valores) != len(colunas):
                raise ValueError(f"{local}: quantidade incorreta de campos.")
            yield local, dict(zip(colunas, valores))
    except csv.Error as erro:
        raise ValueError(f"{arquivo}, linha {leitor.line_num}: CSV malformado ({erro}).") from erro


def carregar_csv(
    autores_csv: bytes, publicacoes_csv: bytes
) -> tuple[tuple[Autor, ...], tuple[Publicacao, ...]]:
    """Importa dois CSVs UTF-8 separados por vírgula, com listas separadas por ';'.

    Remove espaços externos dos campos e itens. IDs repetidos são erros.
    O CSV de publicações pode incluir a coluna opcional areas.
    """
    autores: dict[str, Autor] = {}
    for local, linha in _registros(autores_csv, "autores.csv", {"id", "nome", "areas"}, set()):
        autor_id = linha["id"].strip()
        if autor_id in autores:
            raise ValueError(f"{local}: ID de autor duplicado {autor_id!r}.")
        try:
            areas = [valor.strip() for valor in linha["areas"].split(";")] if linha["areas"].strip() else []
            autores[autor_id] = Autor(autor_id, linha["nome"].strip(), areas)
        except ValueError as erro:
            raise ValueError(f"{local}: {erro}") from erro

    publicacoes: dict[str, Publicacao] = {}
    for local, linha in _registros(
        publicacoes_csv, "publicacoes.csv", {"id", "titulo", "ano", "autor_ids"}, {"areas"}
    ):
        publicacao_id = linha["id"].strip()
        if publicacao_id in publicacoes:
            raise ValueError(f"{local}: ID duplicado de publicação {publicacao_id!r}.")
        ano = linha["ano"].strip()
        if not ano.isascii() or not ano.isdecimal():
            raise ValueError(f"{local}: ano inválido. Informe um inteiro positivo.")
        autor_ids = [valor.strip() for valor in linha["autor_ids"].split(";")]
        areas_csv = linha.get("areas", "").strip()
        areas = [valor.strip() for valor in areas_csv.split(";")] if areas_csv else []
        try:
            publicacao = Publicacao(publicacao_id, linha["titulo"].strip(), int(ano), autor_ids, areas)
        except ValueError as erro:
            raise ValueError(f"{local}: {erro}") from erro
        for autor_id in publicacao.autor_ids:
            if autor_id not in autores:
                raise ValueError(f"{local}: autor não cadastrado {autor_id!r}.")
        publicacoes[publicacao_id] = publicacao

    return tuple(autores.values()), tuple(publicacoes.values())
