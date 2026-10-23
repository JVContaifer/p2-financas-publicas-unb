#!/usr/bin/env python3
"""
03_tratamento.py
Tratamento dos dados municipais: 62 municípios do Amazonas (amostra de estimação),
com Tabatinga (1304062) e Humaitá (1301704) como casos focais.

Entradas (a partir da raiz do repositório):
  data/raw/siconfi/finbra_AM_<ano>_receitas_IC.csv   Finbra, Anexo I-C (receitas)
  data/raw/siconfi/finbra_AM_<ano>_despesas_ID.csv   Finbra, Anexo I-D (despesas)
  data/raw/ibge_pib_am_2010_2023.csv                 IBGE, PIB dos Municípios (AM)
  data/original/ipeadata_ipca.csv                    IPCA 12 meses (trabalho anterior)

Saídas (data/tratado/):
  painel_am.csv           painel município-ano, 62 municípios
  painel_focais.csv       subconjunto: Tabatinga e Humaitá
  controle_cobertura.csv  o que existe e o que falta, por município-ano
  log_tratamento.txt      conferências e avisos

Regras (enunciado da P2):
  * Dado ausente => NaN, nunca zero.
  * Valores reais em reais de 2023 (IPCA acumulado, dezembro a dezembro).
  * O plano de contas de receitas mudou duas vezes (A: 2014-17, B: 2018-21, C: 2022-23).
    Agregados são comparados por código normalizado; detalhes (FPM, ICMS, FUNDEB, IPTU,
    ISS) por código exato de cada plano. A coluna `regime_contas` registra o plano usado.
Uso:  python3 R/03_tratamento.py
"""
import glob, io, os, re, sys
import numpy as np
import pandas as pd

BASE_YEAR = 2023
FOCAIS = {"1304062": "Tabatinga", "1301704": "Humaitá"}
RAW, OUT = "data/raw/siconfi", "data/tratado"
os.makedirs(OUT, exist_ok=True)
log = []


def say(msg):
    print(msg)
    log.append(msg)


# ------------------------------------------------------------------ leitura Finbra
def norm_cod(c):
    """Remove grupos finais zerados: 1.7.0.0.00.00.00 e 1.7.0.0.00.0.0 -> '1.7'."""
    if not isinstance(c, str):
        return np.nan
    g = c.split(".")
    while len(g) > 1 and set(g[-1]) == {"0"}:
        g.pop()
    return ".".join(g)


def le_finbra(path):
    txt = open(path, "rb").read().decode("latin-1").split("\n")
    ano = int(re.search(r"(\d{4})", txt[0]).group(1))
    h = next(i for i, l in enumerate(txt[:12]) if l.startswith("Institui"))
    df = pd.read_csv(io.StringIO("\n".join(txt[h:])), sep=";", dtype=str)
    df["valor"] = (df["Valor"].str.replace(".", "", regex=False)
                   .str.replace(",", ".", regex=False).astype(float))
    df["pop"] = pd.to_numeric(df["População"], errors="coerce")
    df["cod"] = df["Conta"].str.extract(r"^(\d[\d\.]*\d)")[0]
    df["cod_n"] = df["cod"].map(norm_cod)  # código normalizado (ver norm_cod)
    df["municipio"] = df["Instituição"].str.extract(r"^(?:Prefeitura Municipal de |Prefeitura de )?(.*?)\s*-\s*AM$")[0]
    df["ano"] = ano
    return df.rename(columns={"Cod.IBGE": "cod_ibge", "Coluna": "coluna"})


def carrega(sufixo):
    fr = [le_finbra(p) for p in sorted(glob.glob(f"{RAW}/finbra_AM_*_{sufixo}.csv"))]
    if not fr:
        sys.exit(f"Nenhum arquivo *_{sufixo}.csv em {RAW}")
    return pd.concat(fr, ignore_index=True)


TAB = {"rec": carrega("receitas_IC"), "dsp": carrega("despesas_ID")}
IDX = {k: {g: d for g, d in v.groupby(["ano", "cod_ibge", "coluna"], sort=False)} for k, v in TAB.items()}
VAZIO = TAB["rec"].iloc[0:0]


def sub(tab, ano, mun, coluna):
    return IDX[tab].get((ano, mun, coluna), VAZIO)


def pega(tab, ano, mun, coluna, codigos, soma=False, chave="cod"):
    """Valor de uma conta. O primeiro candidato encontrado vence.
    Candidato em lista = somar as linhas; com soma=True a PRIMEIRA é obrigatória e as
    demais são somadas se existirem (ex.: cotas de 1% do FPM, criadas ao longo do tempo).
    Ausente => (NaN, None), nunca zero."""
    d = sub(tab, ano, mun, coluna)
    for cand in codigos:
        lista = cand if isinstance(cand, (list, tuple)) else [cand]
        s = d[d[chave].isin(lista)]
        if len(s) == 0:
            continue
        if soma and lista[0] not in set(s[chave]):
            continue
        if s.duplicated(chave).any():
            say(f"ATENÇÃO duplicidade {ano} {mun} {lista}")
        return s.groupby(chave).valor.first().sum(), str(lista)
    return np.nan, None


def pega_texto(tab, ano, mun, coluna, regex):
    d = sub(tab, ano, mun, coluna)
    d = d[d.Conta.str.contains(regex, regex=True, na=False)]
    return d.valor.iloc[0] if len(d) else np.nan


RB = "Receitas Brutas Realizadas"
AGREGADOS = {  # códigos normalizados (cod_n)
    "receita_corrente": ["1"], "receita_capital": ["2"],
    "receita_tributaria": ["1.1"],      # impostos, taxas e contribuições de melhoria
    "impostos": ["1.1.1"], "contribuicoes": ["1.2"],
    "transf_correntes": ["1.7"], "transf_capital": ["2.4"],
}
# Detalhes (código exato). Planos: C = 2022-23 | B = 2018-21 | A = 2014-17.
DETALHES = {
    "fpm": [("C", ["1.7.1.1.51.0.0"]),
            ("B", [["1.7.1.8.01.2.0", "1.7.1.8.01.3.0", "1.7.1.8.01.4.0"]]),
            ("A", [["1.7.2.1.01.02.00", "1.7.2.1.01.03.00", "1.7.2.1.01.04.00"]])],
    "icms_cota_parte": [("C", ["1.7.2.1.50.0.0"]), ("B", ["1.7.2.8.01.1.0"]), ("A", ["1.7.2.2.01.01.00"])],
    "fundeb_recebido": [("C", [["1.7.5.1.00.0.0", "1.7.1.5.00.0.0"]]), ("B", ["1.7.5.8.01.0.0"]),
                        ("A", ["1.7.2.4.01.00.00"])],
    "iptu": [("C", ["1.1.1.2.50.0.0"]), ("B", ["1.1.1.8.01.1.0"]), ("A", ["1.1.1.2.02.00.00"])],
    "iss": [("C", ["1.1.1.4.51.1.0"]), ("B", ["1.1.1.8.02.3.0"]), ("A", ["1.1.1.3.05.00.00"])],
}
DESPESAS = {"desp_pessoal": "3.1", "desp_outras_corr": "3.3", "desp_investimento": "4.4",
            "desp_corrente": "3", "desp_capital": "4"}

# ------------------------------------------------------------------ painel
anos = sorted(set(TAB["rec"].ano) | set(TAB["dsp"].ano))
nomes = {**{r.cod_ibge: r.municipio for r in TAB["dsp"].drop_duplicates("cod_ibge").itertuples()},
         **{r.cod_ibge: r.municipio for r in TAB["rec"].drop_duplicates("cod_ibge").itertuples()}}
for c, n in FOCAIS.items():
    nomes.setdefault(c, n)
codigos = sorted(nomes)
say(f"Municípios: {len(codigos)} | anos: {anos[0]}-{anos[-1]}")

linhas = []
for ano in anos:
    for mun in codigos:
        r = {"ano": ano, "cod_ibge": mun, "municipio": nomes[mun], "foco": mun in FOCAIS}
        tem_rec = (ano, mun, RB) in IDX["rec"]
        tem_dsp = (ano, mun, "Despesas Empenhadas") in IDX["dsp"]
        r["sem_dados_receitas"], r["sem_dados_despesas"] = (not tem_rec), (not tem_dsp)
        pop = sub("rec", ano, mun, RB)["pop"] if tem_rec else sub("dsp", ano, mun, "Despesas Empenhadas")["pop"]
        r["populacao"] = pop.iloc[0] if len(pop) else np.nan
        if tem_rec:
            for k, cods in AGREGADOS.items():
                r[k], _ = pega("rec", ano, mun, RB, cods, chave="cod_n")
            rc, rk = r["receita_corrente"], r["receita_capital"]
            intra = pega_texto("rec", ano, mun, RB, r"^RECEITAS \(INTRA")
            if np.isnan(intra):  # planos A e B: códigos 7.* e 8.*
                v7, _ = pega("rec", ano, mun, RB, ["7"], chave="cod_n")
                v8, _ = pega("rec", ano, mun, RB, ["8"], chave="cod_n")
                intra = np.nansum([v7, v8]) if not (np.isnan(v7) and np.isnan(v8)) else np.nan
            r["receita_intra"] = intra  # NaN = nenhuma linha intra informada
            tot = pega_texto("rec", ano, mun, RB, r"^(?:Total Receitas|TOTAL DAS RECEITAS)")
            # Município sem linha de "Receitas de Capital": o zero só é assumido quando o total
            # oficial da tabela comprova (total - intra == receita corrente). Fica sinalizado.
            r["flag_capital_zero_comprovado"] = False
            if np.isnan(rk) and not np.isnan(rc) and not np.isnan(tot) \
                    and abs(tot - rc - np.nan_to_num(intra)) < 1:
                rk = r["receita_capital"] = 0.0
                r["flag_capital_zero_comprovado"] = True
            # Receita total EXCLUI intraorçamentárias nos três planos (comparabilidade)
            r["receita_total"] = rc + rk if not np.isnan(rc + rk) else np.nan
            r["dif_conferencia_total"] = tot - (r["receita_total"] + np.nan_to_num(intra))
            ct, ck = r["transf_correntes"], r["transf_capital"]
            r["transf_totais"] = ct + (0 if np.isnan(ck) else ck) if not np.isnan(ct) else np.nan
            r["flag_transf_capital_ausente"] = bool(np.isnan(ck))
            r["receita_propria_corrente"] = rc - ct
            reg = set()
            for k, planos in DETALHES.items():
                v, usado = np.nan, None
                for plano, cods in planos:
                    v, usado = pega("rec", ano, mun, RB, cods, soma=True)
                    if usado:
                        reg.add(plano)
                        break
                r[k] = v
            r["regime_contas"] = "/".join(sorted(reg)) if reg else "indeterminado"
            for col, nm in [("Deduções - FUNDEB", "ded_fundeb"),
                            ("Deduções - Transferências Constitucionais", "ded_transf_const"),
                            ("Outras Deduções da Receita", "ded_outras")]:
                r[nm] = pega_texto("rec", ano, mun, col, r"^(?:Total Receitas|RECEITAS \(EXCETO INTRA)")
        if tem_dsp:
            r["desp_empenhada_total"] = pega_texto("dsp", ano, mun, "Despesas Empenhadas", r"^Total Geral da Despesa")
            r["desp_liquidada_total"] = pega_texto("dsp", ano, mun, "Despesas Liquidadas", r"^Total Geral da Despesa")
            for k, c in DESPESAS.items():
                r[k], _ = pega("dsp", ano, mun, "Despesas Empenhadas", [c], chave="cod_n")
        linhas.append(r)
pn = pd.DataFrame(linhas)

# ------------------------------------------------------------------ PIB (IBGE)
pib = pd.read_csv("data/raw/ibge_pib_am_2010_2023.csv", dtype={"cod_ibge": str})
pib["pib_nominal"] = pib["pib_mil_rs"] * 1000
pib["vab_adm"] = pib["vab_adm"] * 1000  # vazio em 2022-23 no IBGE
pn = pn.merge(pib[["ano", "cod_ibge", "pib_nominal", "vab_adm"]], on=["ano", "cod_ibge"], how="left")

# ------------------------------------------------------------------ deflator (IPCA dez/dez)
ip = open("data/original/ipeadata_ipca.csv", "rb").read().decode("utf-8-sig").split("\n")
anual = {}
for l in ip[1:]:
    p = l.strip().split(";")
    if len(p) >= 2 and p[0].endswith(".12"):
        anual[int(p[0][:4])] = float(p[1].replace(",", "."))
fator = {}
for a in range(2010, BASE_YEAR + 1):
    f = 1.0
    for s in range(a + 1, BASE_YEAR + 1):
        f *= 1 + anual[s] / 100
    fator[a] = f
pn["deflator_para_2023"] = pn["ano"].map(fator)

MONET = ["receita_total", "receita_corrente", "receita_capital", "receita_tributaria", "impostos",
         "contribuicoes", "transf_correntes", "transf_capital", "transf_totais", "receita_propria_corrente",
         "fpm", "icms_cota_parte", "fundeb_recebido", "iptu", "iss", "receita_intra",
         "ded_fundeb", "ded_transf_const", "ded_outras", "desp_empenhada_total", "desp_liquidada_total",
         "desp_pessoal", "desp_outras_corr", "desp_investimento", "desp_corrente", "desp_capital", "pib_nominal"]
novas = {}
for c in MONET:
    if c in pn:
        novas[c + "_real"] = pn[c] * pn["deflator_para_2023"]
        if c != "pib_nominal":
            novas[c + "_pc_real"] = novas[c + "_real"] / pn["populacao"]
pn = pd.concat([pn, pd.DataFrame(novas)], axis=1)
pn["dependencia_transf"] = pn["transf_totais"] / pn["receita_total"]
pn["participacao_tributaria"] = pn["receita_tributaria"] / pn["receita_total"]
pn["transf_sobre_pib"] = pn["transf_totais"] / pn["pib_nominal"]
pn["tributaria_sobre_pib"] = pn["receita_tributaria"] / pn["pib_nominal"]
pn["resultado_orcamentario_real"] = pn["receita_total_real"] - pn["desp_empenhada_total_real"]
pn = pn.sort_values(["cod_ibge", "ano"]).reset_index(drop=True)

pn.to_csv(f"{OUT}/painel_am.csv", index=False)
pn[pn.foco].to_csv(f"{OUT}/painel_focais.csv", index=False)
pn[["ano", "cod_ibge", "municipio", "foco", "sem_dados_receitas", "sem_dados_despesas", "regime_contas"]] \
    .to_csv(f"{OUT}/controle_cobertura.csv", index=False)

# ------------------------------------------------------------------ conferências
say("\nCobertura (municípios com dados de receitas / despesas por ano):")
cv = pn.groupby("ano").agg(receitas=("sem_dados_receitas", lambda s: int((~s).sum())),
                           despesas=("sem_dados_despesas", lambda s: int((~s).sum())))
say(cv.to_string())
dados = pn[pn.dif_conferencia_total.notna()]
falha = dados[dados.dif_conferencia_total.abs() >= 1]
say(f"\nConferência do total de receitas: {len(dados) - len(falha)} de {len(dados)} observações fecham (|dif| < R$ 1).")
if len(falha):
    say("Não fecham: " + "; ".join(f"{r.municipio} {r.ano} (dif {r.dif_conferencia_total:,.0f})" for r in falha.itertuples()))
assert not falha[falha.foco].shape[0], "Total não fecha para um município focal!"
for k in ["fpm", "icms_cota_parte", "fundeb_recebido", "iptu", "iss"]:
    n = int(pn.loc[~pn.sem_dados_receitas, k].isna().sum())
    say(f"{k}: {n} observações com dados de receita mas sem a linha de detalhe (ficam NaN)")
say("\nFocais sem dados na fonte: " + "; ".join(
    f"{r.municipio} {r.ano}" for r in pn[pn.foco & pn.sem_dados_receitas].itertuples()))
open(f"{OUT}/log_tratamento.txt", "w", encoding="utf-8").write("\n".join(log))
