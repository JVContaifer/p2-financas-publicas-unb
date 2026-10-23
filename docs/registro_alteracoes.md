# Registro de alterações (P1 → P2)

Unidades: Tabatinga/AM (1304062), Humaitá/AM (1301704) e Malásia.
Período: 2014–2023 (dez anos mais recentes com PIB municipal divulgado).

## 1. Ponto de partida (trabalho anterior)

O repositório do trabalho anterior (`Rafaelbpin/p1financaspublicasunb`) contém um único
arquivo compactado, `FINANÇAS DO SETOR PUBLICO UNB.7z`, sem README, dados soltos ou código.
Os arquivos de dados recebidos do trabalho anterior (`dados_muni.zip`, `dados_pais.zip`)
cobrem **94 municípios do Rio de Janeiro** e o **Paraguai** (e pares). Eles **não contêm**
Tabatinga, Humaitá nem a Malásia. Conforme o enunciado, a base foi reconstruída a partir das
fontes oficiais e a limitação foi registrada aqui.

### Materiais reaproveitados do trabalho anterior

| Arquivo | Uso nesta versão |
|---|---|
| `ipeadata_ipca.csv` | Copiado sem alteração para `data/original/`. Base do deflator |
| `dados_muni.zip`, `dados_pais.zip` | Cópia **intacta** da base original do P1 (RJ e Paraguai) em `data/original/p1/`; não usados nas análises do P2 |
| `ibge_pibmunicipios_2010-2023.xlsx` | Filtrado para o Amazonas (62 municípios) → `data/raw/ibge_pib_am_2010_2023.csv` |
| `fmi_weo_dataset.csv` (WEO, FMI) | Filtrado para a Malásia (MYS) → `data/raw/weo_malasia_bruto.csv` |
| Estrutura de variáveis (receita, FPM/ICMS, transferências, despesas, IPCA, PIB) | Reaproveitada como modelo |

## 2. Dados brutos atualizados (coletados nas fontes)

| Dado | Fonte | Arquivos |
|---|---|---|
| Receitas orçamentárias (Anexo I-C) | Siconfi/Finbra, Contas Anuais, escopo "Municípios do Estado – AM" | `data/raw/siconfi/finbra_AM_<ano>_receitas_IC.csv`, 2014–2023 |
| Despesas orçamentárias (Anexo I-D) | Idem | `finbra_AM_<ano>_despesas_ID.csv`, 2014–2023 |
| Indicadores da Malásia (governo central, PIB, deflator, população) | Banco Mundial, WDI (coleta em 23/10/2026) | `data/raw/wdi_malasia.csv` |

## 3. Alterações, correções e ampliações

| # | Alteração | Motivo |
|---|---|---|
| 1 | Amostra de estimação ampliada de 2 para os **62 municípios do Amazonas**; Tabatinga e Humaitá são os casos focais (`foco = TRUE`) | Dois municípios dão menos de 20 observações. O Finbra já traz o estado inteiro |
| 2 | Valores monetários convertidos para **reais de 2023** (IPCA dez/dez acumulado) e para valores *per capita* | Exigência do enunciado |
| 3 | **Receita total definida sem intraorçamentárias** (corrente + capital) nos três planos de contas | Plano C separa as intra; planos A e B as incluem no "Total Receitas" |
| 4 | **Receita de capital = 0 apenas quando comprovada** pelo total oficial (46 observações, nenhuma de município focal); marcada em `flag_capital_zero_comprovado` | Município sem linha de capital: o zero é confirmado pela identidade contábil, não presumido |
| 5 | Conferência automática do total de receitas contra o total oficial do Finbra | 609 de 609 observações com dados fecham (|dif| < R$ 1) |
| 6 | Variáveis de detalhe (FPM, ICMS, FUNDEB, IPTU, ISS) mapeadas pelos **três planos de contas** | Códigos mudaram entre 2017/18 e 2021/22 |
| 7 | Agregados (corrente, capital, tributária, transferências, despesas por categoria) comparados por **código normalizado** | Formato dos códigos mudou (8 segmentos em 2014–17) |

## 4. Quebras de série, dados ausentes e limitações

- **Plano de contas de receitas:** A (2014–17), B (2018–21) e C (2022–23). Registrado em `regime_contas`.
- **Divisão União/Estados das transferências não é comparável** entre planos (o FUNDEB e sua complementação mudam de grupo). Por isso a análise usa o total de transferências.
- **FUNDEB:** salto entre 2021 e 2022 nos dois municípios focais coincide com a mudança de plano e com a nova complementação. Os resultados devem ser testados com e sem esta variável.
- **Tabatinga 2015 e 2016:** o município **não consta nos arquivos do Siconfi** dessas duas tabelas (os arquivos trazem 59 dos 62 municípios). Mantido como dado ausente (NaN), sem preenchimento. O PIB municipal desses anos existe no IBGE.
- **Outros municípios sem dados:** 2014 (60), 2015 (59), 2016 (59), 2017 (61), 2019 (61), 2021 (61) de 62. Ver `data/tratado/controle_cobertura.csv`. O painel de estimação é desbalanceado.
- **População:** vem do próprio Finbra e se repete em alguns pares de anos (2017/18, 2022/23). Não é uma série anual consistente do IBGE.
- **IPTU:** 89 observações com receita, mas sem a linha de IPTU, ficam NaN.
- **VAB da administração pública:** vazio no IBGE em 2022 e 2023.
- **Deflator:** IPCA dezembro a dezembro. Para fluxos anuais, um índice de média anual seria mais preciso. Não foi possível construí-lo com os dados disponíveis.
- **Malásia:** as séries `GC.*` do Banco Mundial são do **governo central**; as do WEO do FMI são do **governo geral**. A despesa em % do PIB de 2024 está ausente no Banco Mundial. Ver dicionário.

## 5. Entregas adicionais do P2 (23/10/2026)

- `data/tratado/painel_malasia.csv` (11 anos) e `docs/dicionario_malasia.csv`: Malásia em MYR de 2023 (deflator = IPC do WDI), per capita e % do PIB, separando governo central (WDI) e geral (FMI).
- `data/raw/bibliometria/scopus_export_2026-10-23.csv`: exportação original do Scopus (1.083 documentos). `docs/referencias_80.csv`: as 80 referências do artigo (todas artigos/revisões com DOI).
- `output/regressoes.csv`, `output/tabela_descritiva.csv`, `output/focais_resumo.csv`, `output/bibliometrix_*`, `output/fig_descritivas.png`: resultados.
- Regressões de painel (efeitos fixos de município e ano, EP agrupados por município) em `R/07_regressoes.py`, implementadas em numpy (statsmodels não estava disponível). Cada coeficiente do artigo vem de `output/regressoes.csv`.
- Limitações adicionais: PIB municipal é proxy fraca de renda local; transferências são endógenas (sem instrumentos); sem dados malaios de transferências subnacionais; a análise bibliométrica do artigo foi feita com o pacote bibliometrix (`R/05_bibliometrix.R`, executado no Posit Cloud em 23/10/2026; saída em `output/bibliometrix_graficos.pdf`). `R/06_bibliometria_python.py` é uma réplica complementar.
