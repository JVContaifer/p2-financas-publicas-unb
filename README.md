# P2 – Finanças do Setor Público (UnB, CCA0169, Turma 01, 2026.2)

**Matrícula:** 211014396
**Unidades:** Tabatinga/AM, Humaitá/AM e Malásia. Período: 2014–2023.

## Estrutura do repositório

```
data/
  original/    material reaproveitado do trabalho anterior, sem alteração (IPCA; p1/ = cópia da base original do P1: dados_muni.zip e dados_pais.zip)
  raw/         dados brutos atualizados, coletados nas fontes
    siconfi/   Finbra I-C (receitas) e I-D (despesas), AM, 2014-2023
  tratado/     dados usados nas análises (painel_am.csv, painel_focais.csv, controle_cobertura.csv)
R/             scripts
docs/
  dicionario_variaveis.csv     definição, unidade, fonte, cobertura, tratamento, fórmula
  registro_alteracoes.md       o que mudou em relação ao trabalho anterior
output/        tabelas e gráficos gerados
artigo/        artigo (artigo.tex, refs.bib, 211014396.pdf)
data/raw/bibliometria/  exportação original do Scopus
```

## Reprodução

1. Python 3.10+ com `pandas` e `numpy`.
2. Na raiz do repositório: `python3 R/03_tratamento.py`
   Lê `data/raw` e `data/original` e grava em `data/tratado/`. O script confere o total de
   receitas contra o total oficial do Finbra e interrompe se algum município focal não fechar.
3. `R/02_coleta_malasia.R` (R) coleta os indicadores da Malásia no Banco Mundial (WDI); `python3 R/04_tratamento_malasia.py` gera `data/tratado/painel_malasia.csv`.
4. `python3 R/07_regressoes.py` (regressões, `output/regressoes.csv`) e `python3 R/08_descritivas_figuras.py` (tabela e figura descritivas). Requer `matplotlib`.
5. Bibliometria (obrigatória, com bibliometrix): no R/RStudio, `setwd()` para a pasta com o CSV do Scopus (`data/raw/bibliometria/`) e `source("R/05_bibliometrix.R")`. Gera `output/bibliometrix_graficos.pdf` (executado no Posit Cloud, R 4.6.1, em 23/10/2026); `output/bibliometrix_painel.png` é a composição dos painéis A–D usada no artigo. `R/06_bibliometria_python.py` é uma réplica complementar em Python, não usada no artigo.
6. Artigo: `cd artigo && sh build.sh` (pdflatex + bibtex). O PDF entregue é `artigo/211014396.pdf`; `artigo/refs.bib` traz as referências.

### Origem dos dados brutos

- **Finbra (Siconfi):** `https://siconfi.tesouro.gov.br/siconfi/pages/public/consulta_finbra/finbra_list.jsf`
  → *Contas Anuais* → escopo *Municípios do Estado* → Amazonas → tabelas *Receitas Orçamentárias (Anexo I-C)*
  e *Despesas Orçamentárias (Anexo I-D)*, um exercício por vez (arquivos baixados em 23/10/2026).
- **PIB municipal:** IBGE, *Produto Interno Bruto dos Municípios* (arquivo do trabalho anterior, filtrado para o AM).
- **IPCA:** Ipeadata (arquivo do trabalho anterior).
- **Malásia:** Banco Mundial (WDI) e FMI (WEO), este último a partir do arquivo do trabalho anterior.

## Trabalho anterior

`https://github.com/Rafaelbpin/p1financaspublicasunb` (arquivo `FINANÇAS DO SETOR PUBLICO UNB.7z`).
Os dados recebidos dele cobrem municípios do RJ e o Paraguai, e não as unidades desta atribuição.
Materiais reaproveitados e justificativa: ver `docs/registro_alteracoes.md`.

## Limitações principais

Ver `docs/registro_alteracoes.md`, seção 4: três planos de contas de receitas (A/B/C), Tabatinga
sem dados em 2015 e 2016, quebra do FUNDEB em 2021/22, população repetida em alguns anos e
diferença de cobertura entre o governo central (Banco Mundial) e o governo geral (FMI) na Malásia.
