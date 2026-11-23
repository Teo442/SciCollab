"""Coleta artigos da PUC Minas e valida os CSVs com o próprio SciCollab."""

import argparse
import csv
import json
import math
import os
import re
from collections import defaultdict
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from io import StringIO
from pathlib import Path
from time import sleep
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from src.algorithms.areas import (
    colaboracoes_entre_areas,
    distribuicao_areas,
    ranking_pontes_interdisciplinares,
)
from src.algorithms.busca import busca_em_largura, componentes_conexas
from src.algorithms.centralidade import ranking_forca, ranking_grau, ranking_intermediacao
from src.algorithms.comunidades import detectar_comunidades
from src.algorithms.metricas import coeficiente_agrupamento_global, ranking_agrupamento
from src.algorithms.temporal import evolucao_temporal
from src.data.carregador import carregar_csv
from src.graph.construtor import ConstrutorGrafo


RAIZ = Path(__file__).resolve().parents[1]
API = "https://api.openalex.org"
INSTITUICAO = "I170935008"
ANOS = range(2020, 2025)
SEMENTE = 42
LIMITE_AUTORES = 20
FILTRO = f"institutions.id:{INSTITUICAO},type:article,publication_year:"


def consultar(ano, pagina, tamanho_amostra):
    parametros = {
        "filter": FILTRO + str(ano),
        "sample": tamanho_amostra,
        "seed": SEMENTE,
        "per_page": 100,
        "page": pagina,
        "select": "id,display_name,publication_year,authorships,primary_topic",
    }
    cabecalhos = {"User-Agent": "SciCollab/1.0"}
    chave = os.getenv("OPENALEX_API_KEY")
    if chave:
        cabecalhos["Authorization"] = f"Bearer {chave}"
    pedido = Request(f"{API}/works?{urlencode(parametros)}", headers=cabecalhos)

    for tentativa in range(3):
        try:
            with urlopen(pedido, timeout=35) as resposta:
                dados = json.load(resposta)
            if not isinstance(dados, dict) or not isinstance(dados.get("results"), list):
                raise RuntimeError("Resposta do OpenAlex sem uma lista de resultados.")
            return dados["results"]
        except HTTPError as erro:
            motivo = erro.read()
            if erro.code == 429 and b"daily_budget" in motivo:
                raise RuntimeError("Orçamento diário da API do OpenAlex esgotado.") from None
            if erro.code not in {429, 500, 502, 503, 504} or tentativa == 2:
                raise RuntimeError(f"OpenAlex retornou HTTP {erro.code} para {ano}, página {pagina}.") from None
            espera = erro.headers.get("Retry-After")
            segundos = 2 ** tentativa
            if espera:
                if espera.isdecimal():
                    segundos = int(espera)
                else:
                    try:
                        segundos = max(0, (parsedate_to_datetime(espera) - datetime.now(timezone.utc)).total_seconds())
                    except (TypeError, ValueError):
                        pass
            if segundos > 60:
                raise RuntimeError(f"OpenAlex pediu espera de {segundos:.0f} s. Execute novamente depois.") from None
            sleep(segundos)
        except (URLError, TimeoutError):
            if tentativa == 2:
                raise RuntimeError(f"Falha de conexão com o OpenAlex para {ano}, página {pagina}.") from None
            sleep(2 ** tentativa)


def identificar(valor, prefixo):
    if isinstance(valor, str):
        codigo = valor.removeprefix("https://openalex.org/")
        if re.fullmatch(rf"{prefixo}[1-9][0-9]*", codigo):
            return codigo
    return None


def interpretar(registro, ano):
    codigo = identificar(registro.get("id"), "W")
    titulo = (registro.get("display_name") or "").strip()
    assinaturas = registro.get("authorships") or []
    if not codigo or not titulo or registro.get("publication_year") != ano:
        return None
    if not 2 <= len(assinaturas) <= LIMITE_AUTORES:
        return None

    autores = {}
    for assinatura in assinaturas:
        autor = assinatura.get("author") or {}
        autor_id = identificar(autor.get("id"), "A")
        nome = (autor.get("display_name") or "").strip()
        if autor_id and nome:
            autores.setdefault(autor_id, nome)
    if len(autores) < 2:
        return None

    campo = (registro.get("primary_topic") or {}).get("field") or {}
    area = (campo.get("display_name") or "").strip()
    return codigo, titulo, autores, area


def coletar(limite):
    nomes = {}
    areas = defaultdict(set)
    publicacoes = {}
    contagens = {}
    por_ano, resto = divmod(limite, len(ANOS))
    for posicao, ano in enumerate(ANOS):
        cota = por_ano + (posicao < resto)
        if not cota:
            continue
        tamanho_amostra = min(10_000, max(100, 3 * cota))
        registros = []
        for pagina in range(1, (tamanho_amostra + 99) // 100 + 1):
            lote = consultar(ano, pagina, tamanho_amostra)
            registros.extend(lote)
            sleep(0.25)
            if len(lote) < 100:
                break
        aceitos = 0
        for registro in sorted(registros, key=lambda item: item.get("id") or ""):
            trabalho = interpretar(registro, ano)
            if trabalho is None:
                continue
            codigo, titulo, autores, area = trabalho
            if codigo in publicacoes:
                continue
            publicacoes[codigo] = (titulo, ano, ";".join(autores), area)
            for autor_id, nome in autores.items():
                nomes.setdefault(autor_id, nome)
                if area:
                    areas[autor_id].add(area)
            aceitos += 1
            if aceitos == cota:
                break
        contagens[ano] = (len(registros), aceitos)
    return nomes, areas, publicacoes, contagens


def csv_bytes(cabecalho, linhas):
    saida = StringIO(newline="")
    escritor = csv.writer(saida, lineterminator="\r\n")
    escritor.writerow(cabecalho)
    escritor.writerows(linhas)
    return saida.getvalue().encode("utf-8")


def gerar_relatorio(autores_csv, publicacoes_csv, contagens, data, limite):
    autores, publicacoes = carregar_csv(autores_csv, publicacoes_csv)
    grafo = ConstrutorGrafo.construir(autores, publicacoes)
    arestas = list(grafo.arestas())
    if not arestas or any(p.ano not in ANOS for p in publicacoes):
        raise ValueError("A amostra precisa ter arestas e anos entre 2020 e 2024.")
    componentes = componentes_conexas(grafo)
    maior = max(componentes, key=len)
    if set(busca_em_largura(grafo, min(maior))) != maior:
        raise ValueError("Inconsistência entre BFS e maior componente.")
    rankings = {
        "Grau normalizado": ranking_grau(grafo),
        "Força": ranking_forca(grafo),
        "Intermediação normalizada": ranking_intermediacao(grafo),
    }
    agrupamento = coeficiente_agrupamento_global(grafo)
    comunidades = detectar_comunidades(grafo)
    distribuicao = distribuicao_areas(grafo)
    conexoes = colaboracoes_entre_areas(grafo)
    anual = evolucao_temporal(autores, publicacoes, ANOS.start, ANOS.stop - 1, acumulado=False)
    ids = {autor.id for autor in autores}
    if set().union(*comunidades) != ids or sum(map(len, comunidades)) != len(ids):
        raise ValueError("A partição de comunidades é inválida.")
    agrupamentos = ranking_agrupamento(grafo)
    for ranking in (*rankings.values(), agrupamentos, ranking_pontes_interdisciplinares(grafo)):
        if len(ranking) != len(ids) or {autor for autor, _ in ranking} != ids or any(
            not math.isfinite(valor) or valor < 0 for _, valor in ranking
        ):
            raise ValueError("Ranking incompleto ou com valores inválidos.")
    densidade = 2 * len(arestas) / (len(autores) * (len(autores) - 1))
    valores_normalizados = (
        densidade, agrupamento, *(linha["densidade"] for linha in anual),
        *(valor for _, valor in rankings["Grau normalizado"]),
        *(valor for _, valor in rankings["Intermediação normalizada"]),
        *(valor for _, valor in agrupamentos),
    )
    if any(not 0 <= valor <= 1 for valor in valores_normalizados):
        raise ValueError("Métrica normalizada fora do intervalo de zero a um.")

    linhas = [
        "# Resultados experimentais com OpenAlex", "",
        f"- Fonte [OpenAlex](https://openalex.org/) e [API REST]({API}/).",
        f"- Instituição Pontifícia Universidade Católica de Minas Gerais "
        f"([OpenAlex {INSTITUICAO}](https://openalex.org/{INSTITUICAO}), [ROR 03j1rr444](https://ror.org/03j1rr444)).",
        f"- Coleta em {data} UTC. Metadados OpenAlex sob [CC0](https://help.openalex.org/data/how-its-built/).",
        f"- Filtro por ano `{FILTRO}AAAA`, de 2020 a 2024.",
        f"- Amostra por ano com semente {SEMENTE}, até {limite} publicações no total. "
        "As cotas são divididas entre os anos, com o resto atribuído aos primeiros, sem redistribuição.",
        "- Por ano, foram solicitados três candidatos por vaga ou 100, o que for maior, "
        "com limite de 10.000. Seleção em ordem lexicográfica do ID retornado.",
        f"- Exclusão de trabalhos sem ID, título ou ano válido, com mais de {LIMITE_AUTORES} assinaturas "
        "ou com menos de dois autores distintos identificados por ID e nome. "
        "Assinaturas sem identificação são omitidas. Publicações e autores são deduplicados pelo ID OpenAlex.",
        "- São incluídos coautores externos. O filtro institucional exige ao menos uma afiliação vinculada ao trabalho.",
        "- As áreas dos autores são inferidas dos campos do tópico principal das publicações selecionadas, "
        "quando presentes. Elas descrevem a amostra e cobrem apenas parte da atuação de cada pesquisador.",
        "",
        "| Ano | Registros recebidos | Publicações aceitas |", "|---|---:|---:|",
    ]
    linhas.extend(f"| {ano} | {recebidos} | {aceitos} |" for ano, (recebidos, aceitos) in contagens.items())
    linhas += [
        "", f"Total recebido da API de trabalhos: {sum(valor[0] for valor in contagens.values())}.",
        "", "## Rede completa da amostra", "",
        "| Métrica | Valor |", "|---|---:|",
        f"| Publicações | {len(publicacoes)} |", f"| Autores | {len(autores)} |",
        f"| Arestas | {len(arestas)} |", f"| Soma dos pesos | {sum(peso for _, _, peso in arestas)} |",
        f"| Componentes conexas | {len(componentes)} |", f"| Maior componente | {len(maior)} |",
        f"| Densidade | {densidade:.8f} |", f"| Agrupamento médio | {agrupamento:.8f} |",
        f"| Comunidades | {len(comunidades)} |", f"| Pares de áreas conectadas | {len(conexoes)} |",
    ]
    for titulo, ranking in rankings.items():
        linhas += ["", f"## Cinco primeiros por {titulo.lower()}", "", "| ID | Autor | Valor |", "|---|---|---:|"]
        for autor_id, valor in ranking[:5]:
            nome = grafo.obter_autor(autor_id).nome.replace("|", r"\|").replace("\n", " ").replace("\r", " ")
            linhas.append(f"| {autor_id} | {nome} | {valor:.8g} |")
    linhas += ["", "## Distribuição de áreas", "", "| Campo OpenAlex | Autores |", "|---|---:|"]
    linhas.extend(f"| {area.replace('|', '&#124;')} | {quantidade} |" for area, quantidade in distribuicao.items())
    linhas += [
        "", f"Autores sem área na amostra: {sum(not autor.areas for autor in autores)}.",
        "", "## Evolução anual", "", "Cada linha considera apenas as publicações e os autores ativos daquele ano.", "",
        "| Ano | Autores ativos | Publicações | Arestas | Peso total | Componentes | Maior componente | Densidade |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for linha in anual:
        valores = [str(linha[chave]) for chave in (
            "ano", "autores_ativos", "publicacoes", "arestas", "peso_total", "componentes", "maior_componente"
        )]
        linhas.append(f"| {' | '.join(valores)} | {linha['densidade']:.8f} |")
    linhas += [
        "", "## Limitações", "",
        "- Cotas anuais, cobertura do índice e exclusão de artigos com muitas assinaturas limitam a representatividade.",
        "- Afiliações e identidades dependem da desambiguação do OpenAlex e podem mudar em novas consultas.",
        "- A semente permite repetir a consulta, mas alterações no índice podem mudar as amostras. "
        "Os CSVs preservam a amostra usada neste relatório.",
        "- Coautoria é uma aproximação de colaboração. Artigos com mais autores geram mais pares, "
        "e a projeção interdisciplinar pode atribuir uma aresta a vários pares de campos.",
        "- A propagação de rótulos depende da ordem de cadastro. Os autores foram cadastrados em ordem de ID.",
        "",
    ]
    return "\n".join(linhas)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-publicacoes", type=int, default=150, help="limite total (padrão: 150)")
    args = parser.parse_args()
    if not 1 <= args.max_publicacoes <= 16_665:
        parser.error("--max-publicacoes deve estar entre 1 e 16665.")
    try:
        nomes, areas, publicacoes, contagens = coletar(args.max_publicacoes)
        autores_csv = csv_bytes(
            ("id", "nome", "areas"),
            ((codigo, nomes[codigo], ";".join(sorted(areas[codigo]))) for codigo in sorted(nomes)),
        )
        publicacoes_csv = csv_bytes(
            ("id", "titulo", "ano", "autor_ids", "areas"),
            ((codigo, *dados) for codigo, dados in sorted(publicacoes.items(), key=lambda item: (item[1][1], item[0]))),
        )
        data = datetime.now(timezone.utc).isoformat(timespec="seconds").removesuffix("+00:00")
        relatorio = gerar_relatorio(autores_csv, publicacoes_csv, contagens, data, args.max_publicacoes)
        pasta = RAIZ / "datasets" / "openalex"
        pasta.mkdir(parents=True, exist_ok=True)
        arquivo_relatorio = RAIZ / "docs" / "resultados_openalex.md"
        arquivo_relatorio.parent.mkdir(parents=True, exist_ok=True)
        (pasta / "autores.csv").write_bytes(autores_csv)
        (pasta / "publicacoes.csv").write_bytes(publicacoes_csv)
        arquivo_relatorio.write_text(relatorio, encoding="utf-8")
        print(f"{len(publicacoes)} publicações e {len(nomes)} autores. Registros por ano: {contagens}")
    except (OSError, ValueError, RuntimeError) as erro:
        parser.exit(1, f"Falha na importação: {erro}\n")


if __name__ == "__main__":
    main()
