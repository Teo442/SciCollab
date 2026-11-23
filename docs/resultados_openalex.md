# Resultados experimentais com OpenAlex

- Fonte [OpenAlex](https://openalex.org/) e [API REST](https://api.openalex.org/).
- Instituição Pontifícia Universidade Católica de Minas Gerais ([OpenAlex I170935008](https://openalex.org/I170935008), [ROR 03j1rr444](https://ror.org/03j1rr444)).
- Coleta em 2026-11-22T18:32:50 UTC. Metadados OpenAlex sob [CC0](https://help.openalex.org/data/how-its-built/).
- Filtro por ano `institutions.id:I170935008,type:article,publication_year:AAAA`, de 2020 a 2024.
- Amostra por ano com semente 42, até 150 publicações no total. As cotas são divididas entre os anos, com o resto atribuído aos primeiros, sem redistribuição.
- Por ano, foram solicitados três candidatos por vaga ou 100, o que for maior, com limite de 10.000. Seleção em ordem lexicográfica do ID retornado.
- Exclusão de trabalhos sem ID, título ou ano válido, com mais de 20 assinaturas ou com menos de dois autores distintos identificados por ID e nome. Assinaturas sem identificação são omitidas. Publicações e autores são deduplicados pelo ID OpenAlex.
- São incluídos coautores externos. O filtro institucional exige ao menos uma afiliação vinculada ao trabalho.
- As áreas dos autores são inferidas dos campos do tópico principal das publicações selecionadas, quando presentes. Elas descrevem a amostra e cobrem apenas parte da atuação de cada pesquisador.

| Ano | Registros recebidos | Publicações aceitas |
|---|---:|---:|
| 2020 | 100 | 30 |
| 2021 | 100 | 30 |
| 2022 | 100 | 30 |
| 2023 | 100 | 30 |
| 2024 | 100 | 30 |

Total recebido da API de trabalhos: 500.

## Rede completa da amostra

| Métrica | Valor |
|---|---:|
| Publicações | 150 |
| Autores | 664 |
| Arestas | 2021 |
| Soma dos pesos | 2074 |
| Componentes conexas | 122 |
| Maior componente | 20 |
| Densidade | 0.00918152 |
| Agrupamento médio | 0.87409832 |
| Comunidades | 126 |
| Pares de áreas conectadas | 9 |

## Cinco primeiros por grau normalizado

| ID | Autor | Valor |
|---|---|---:|
| A5000564533 | Patrick J. Bourdeau | 0.028657617 |
| A5002191079 | Gætano Oliva | 0.028657617 |
| A5002950248 | Jivanildo Pinheiro Miranda | 0.028657617 |
| A5005551001 | Jane C. F. Oliveira | 0.028657617 |
| A5010282388 | Eduardo José dos Reis Dias | 0.028657617 |

## Cinco primeiros por força

| ID | Autor | Valor |
|---|---|---:|
| A5007265087 | José Rubens Gonçalves Carneiro | 20 |
| A5071481232 | Lucilaine Valéria de Souza Santos | 20 |
| A5000564533 | Patrick J. Bourdeau | 19 |
| A5002191079 | Gætano Oliva | 19 |
| A5002950248 | Jivanildo Pinheiro Miranda | 19 |

## Cinco primeiros por intermediação normalizada

| ID | Autor | Valor |
|---|---|---:|
| A5064811540 | Luís Cândido Pinto da Silva | 0.00025517992 |
| A5084072659 | Gisele Pires de Mendonça Dantas | 0.0002050553 |
| A5054950181 | Flávio Ricardo Manzi | 0.00020049851 |
| A5108608121 | Paulo Franco Taitson | 0.00020049851 |
| A5071481232 | Lucilaine Valéria de Souza Santos | 0.00018075245 |

## Distribuição de áreas

| Campo OpenAlex | Autores |
|---|---:|
| Agricultural and Biological Sciences | 54 |
| Arts and Humanities | 26 |
| Biochemistry, Genetics and Molecular Biology | 20 |
| Business, Management and Accounting | 17 |
| Computer Science | 4 |
| Decision Sciences | 8 |
| Dentistry | 57 |
| Economics, Econometrics and Finance | 2 |
| Energy | 4 |
| Engineering | 44 |
| Environmental Science | 21 |
| Health Professions | 20 |
| Immunology and Microbiology | 4 |
| Mathematics | 3 |
| Medicine | 211 |
| Neuroscience | 4 |
| Nursing | 8 |
| Physics and Astronomy | 9 |
| Psychology | 19 |
| Social Sciences | 136 |
| Veterinary | 3 |

Autores sem área na amostra: 0.

## Evolução anual

Cada linha considera apenas as publicações e os autores ativos daquele ano.

| Ano | Autores ativos | Publicações | Arestas | Peso total | Componentes | Maior componente | Densidade |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2020 | 149 | 30 | 487 | 487 | 28 | 20 | 0.04416833 |
| 2021 | 136 | 30 | 463 | 463 | 28 | 20 | 0.05043573 |
| 2022 | 136 | 30 | 358 | 371 | 27 | 11 | 0.03899782 |
| 2023 | 116 | 30 | 272 | 282 | 26 | 11 | 0.04077961 |
| 2024 | 157 | 30 | 471 | 471 | 30 | 14 | 0.03846154 |

## Limitações

- Cotas anuais, cobertura do índice e exclusão de artigos com muitas assinaturas limitam a representatividade.
- Afiliações e identidades dependem da desambiguação do OpenAlex e podem mudar em novas consultas.
- A semente permite repetir a consulta, mas alterações no índice podem mudar as amostras. Os CSVs preservam a amostra usada neste relatório.
- Coautoria é uma aproximação de colaboração. Artigos com mais autores geram mais pares, e a projeção interdisciplinar pode atribuir uma aresta a vários pares de campos.
- A propagação de rótulos depende da ordem de cadastro. Os autores foram cadastrados em ordem de ID.
