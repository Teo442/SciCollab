# SciCollab

O SciCollab é um projeto universitário de análise de redes de colaboração
científica. Cada autor é um vértice. A rede é não direcionada, e o peso de
uma aresta é o número de publicações conjuntas no recorte analisado.

O grafo e os algoritmos são implementados em Python. A interface usa
Streamlit, Pandas e Plotly, e os testes usam Pytest.

## Executar no Windows

No PowerShell, abra a raiz do projeto. Se o ambiente virtual ainda não existir,
crie-o com Python 3.12 e instale as dependências.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Para iniciar a aplicação com o ambiente já preparado:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app/main.py
```

Para executar os testes:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

## Dados

A aplicação abre com a base **sintética** de `datasets/demo/`, composta
por 28 autores e 45 publicações fictícias de 2020 a 2024. Os dois CSVs
versionáveis reproduzem a mesma rede em cada execução e funcionam offline.

Para usar outra base, selecione **Importar CSV** e envie os dois arquivos.
Use UTF-8 (com ou sem BOM), cabeçalho na primeira linha, vírgula entre
colunas e ponto e vírgula dentro dos campos multivalorados. Use aspas
duplas para campos que contenham vírgulas.

`autores.csv`

```csv
id,nome,areas
A01,Ana,Computação;Estatística
A02,Bruno,Biologia
A03,Carla,
```

`publicacoes.csv`

```csv
id,titulo,ano,autor_ids
P01,"Redes, dados e biologia",2024,A01;A02
P02,Estudo individual,2025,A03
```

Os IDs devem ser únicos dentro de cada arquivo. Uma publicação exige
ano inteiro positivo e pelo menos um ID de autor cadastrado, sem repetição.
A coluna `areas` dos autores pode conter células vazias. O arquivo de
publicações aceita também uma coluna opcional `areas`, com o mesmo separador.
O importador remove espaços externos e indica o arquivo e a linha quando
identifica registros inválidos.

### OpenAlex

Selecione **OpenAlex local** para usar a amostra da PUC Minas, ou envie
os dois CSVs de `datasets/openalex/` pelo upload. A coleta, os critérios e
as métricas estão em [resultados_openalex.md](docs/resultados_openalex.md).

Para repetir a coleta a partir da raiz do projeto:

```powershell
.\.venv\Scripts\python.exe -m scripts.importar_openalex --max-publicacoes 150
```

O script usa `OPENALEX_API_KEY` se a variável estiver definida. Sem chave,
a API aplica o orçamento compartilhado do endereço IP. Uma nova coleta
substitui os dois CSVs e o relatório após a validação. Alterações no índice
do OpenAlex podem mudar a amostra em consultas futuras.

## Análises

- **Rede** mostra o grafo com cores por comunidade e indicadores de autores,
  publicações, arestas, componentes, densidade e agrupamento médio. O desenho
  circular prioriza até 80 autores por grau e mantém as arestas entre os
  autores exibidos. Os indicadores usam a rede inteira do recorte.
- **Autores** permite consultar colaboradores e comparar rankings de grau
  normalizado, força e intermediação. A intermediação usa Brandes com
  comprimentos unitários.
- **Comunidades** apresenta os grupos encontrados por propagação de rótulos
  ponderada e assíncrona.
- **Áreas** mostra a distribuição dos autores e a projeção das coautorias
  em pares de áreas diferentes.
- **Evolução** acompanha autores ativos, publicações, arestas, peso total,
  componentes, tamanho da maior componente e densidade.

Em **Acumulada**, a rede principal usa todo o intervalo selecionado.
Cada ponto anual da série usa as publicações desde o início do intervalo
até o ano do ponto, inclusive. Em **Anual**, a rede principal usa um ano
selecionado dentro do intervalo e cada ponto da série usa apenas seu próprio
ano. A rede principal inclui todos os autores cadastrados. Cada ponto da
série inclui somente autores com publicação na respectiva janela, inclusive
quem publicou individualmente.

## Estrutura

| Caminho | Conteúdo |
|---|---|
| `app/` | Interface Streamlit |
| `src/models/` | Modelos de autores e publicações |
| `src/graph/` | Grafo de adjacência e construtor |
| `src/algorithms/` | Buscas, métricas, comunidades, áreas e análise temporal |
| `src/data/` | Importador CSV |
| `datasets/demo/` | Base sintética de demonstração |
| `datasets/openalex/` | Amostra pública da PUC Minas |
| `scripts/importar_openalex.py` | Coleta e validação da amostra OpenAlex |
| `tests/` | Testes unitários e de integração |

## Limitações conhecidas

- Cada publicação com `k` autores gera `k(k − 1)/2` pares. Publicações
  com muitos autores e redes densas encarecem a construção e as métricas.
  A série temporal reconstrói o grafo de cada janela com novos artigos no
  modo acumulado. A intermediação é opcional na interface acima de 300 autores.
- A ordem de cadastro pode influenciar os resultados da propagação de rótulos.
  As análises de áreas dependem da classificação dos autores, e uma coautoria
  pode contribuir para vários pares de áreas.
- Bases externas adicionais precisam ser preparadas no formato CSV
  documentado, com IDs resolvidos e campos de área revisados.
