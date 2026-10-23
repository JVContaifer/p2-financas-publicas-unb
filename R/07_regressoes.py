# Regressões de painel (efeitos fixos de município e ano, EP clusterizado por município), numpy puro.
# Y e X em log(per capita real, R$ 2023). Estimação em dados com todas as variáveis disponíveis.
import numpy as np, pandas as pd
from math import erf, sqrt
d = pd.read_csv("data/tratado/painel_am.csv").sort_values(["cod_ibge", "ano"])
d["pib_pc"] = d.pib_nominal_real / d.populacao
L = lambda c: np.log(d[c].where(d[c] > 0))
d["l_desp"] = L("desp_corrente_pc_real"); d["l_transf"] = L("transf_totais_pc_real")
d["l_prop"] = L("receita_propria_corrente_pc_real"); d["l_pib"] = np.log(d.pib_pc.where(d.pib_pc > 0))
d["l_transf_sfund"] = np.log((d.transf_totais_pc_real - d.fundeb_recebido_pc_real.fillna(0)).where(lambda x: x > 0))
d["l_pessoal"] = L("desp_pessoal_pc_real"); d["l_inv"] = L("desp_investimento_pc_real"); d["l_trib"] = L("receita_tributaria_pc_real")
g = d.groupby("cod_ibge")
d["dl_transf"] = g.l_transf.diff(); d["dpos"] = d.dl_transf.clip(lower=0); d["dneg"] = d.dl_transf.clip(upper=0)
d["dl_prop"] = g.l_prop.diff(); d["dl_desp"] = g.l_desp.diff(); d["dl_pib"] = g.l_pib.diff()
def pval(t): return 2 * (1 - 0.5 * (1 + erf(abs(t) / sqrt(2))))
def fe(y, xs, df, tfe=True, nome=""):
    z = df[[y] + xs + ["cod_ibge", "ano"]].dropna(); Y = z[y].values; X = z[xs].values.astype(float)
    if tfe:
        D = pd.get_dummies(z.ano, drop_first=True).values.astype(float); X = np.c_[X, D]
    X = np.c_[X] ; ids = z.cod_ibge.values
    # within transformation por município
    def dm(A):
        A = pd.DataFrame(A); return (A - A.groupby(ids).transform("mean")).values
    Yw, Xw = dm(Y.reshape(-1, 1)).ravel(), dm(X)
    b = np.linalg.lstsq(Xw, Yw, rcond=None)[0]; e = Yw - Xw @ b
    XtXi = np.linalg.pinv(Xw.T @ Xw); M = np.zeros_like(XtXi); G = np.unique(ids)
    for k in G:
        s = Xw[ids == k].T @ e[ids == k]; M += np.outer(s, s)
    n, K = len(z), Xw.shape[1]; c = len(G) / (len(G) - 1) * (n - 1) / (n - K - len(G))
    V = c * XtXi @ M @ XtXi; se = np.sqrt(np.diag(V))
    r2w = 1 - (e @ e) / (Yw @ Yw)
    fe.V = V[:len(xs), :len(xs)]; fe.b = b[:len(xs)]
    out = pd.DataFrame({"coef": b[:len(xs)], "ep": se[:len(xs)], "p": [pval(b[i] / se[i]) for i in range(len(xs))]}, index=xs)
    out["modelo"] = nome; out["N"] = n; out["municipios"] = len(G); out["R2_within"] = round(r2w, 3)
    return out
R = []
R.append(fe("l_desp", ["l_transf", "l_prop"], d, nome="M1 FE: gasto corrente ~ transf + receita própria"))
R.append(fe("l_desp", ["l_transf", "l_pib"], d, nome="M2 FE: gasto corrente ~ transf + PIB pc (renda)"))
R.append(fe("l_desp", ["l_transf_sfund", "l_pib"], d, nome="M3 FE: M2 sem FUNDEB nas transferências"))
R.append(fe("l_prop", ["l_transf", "l_pib"], d, nome="M4 FE: receita própria ~ transf + PIB pc"))
R.append(fe("l_trib", ["l_transf", "l_pib"], d, nome="M5 FE: receita tributária ~ transf + PIB pc"))
R.append(fe("l_pessoal", ["l_transf", "l_pib"], d, nome="M6 FE: despesa pessoal"))
R.append(fe("l_inv", ["l_transf", "l_pib"], d, nome="M7 FE: investimento"))
R.append(fe("dl_desp", ["dpos", "dneg", "dl_pib"], d, tfe=True, nome="M8 FD+FE ano: Δgasto ~ Δtransf+ , Δtransf- , Δpib (assimetria)"))
R.append(fe("dl_prop", ["dpos", "dneg", "dl_pib"], d, tfe=True, nome="M9 FD+FE ano: Δreceita própria ~ Δtransf+ , Δtransf- (substituição fiscal)"))
d2 = d[d.ano <= 2021]
R.append(fe("l_desp", ["l_transf", "l_pib"], d2, nome="M10 FE: M2 só 2014-2021 (plano A/B)"))
q99 = d.transf_totais_pc_real.quantile(.99)
R.append(fe("l_desp", ["l_transf", "l_pib"], d[d.transf_totais_pc_real <= q99], nome="M11 FE: M2 sem 1% maiores transferências pc (robustez a outliers)"))
R.append(fe("l_desp", ["l_transf", "l_pib"], d[~d.foco], nome="M12 FE: M2 sem Tabatinga e Humaitá"))
fe("dl_desp", ["dpos", "dneg", "dl_pib"], d, nome="")
z = (fe.b[0] - fe.b[1]) / np.sqrt(fe.V[0, 0] + fe.V[1, 1] - 2 * fe.V[0, 1]); print("Teste dpos=dneg (M8): z=%.2f p=%.3f" % (z, pval(z)))
res = pd.concat(R); res.round(4).to_csv("output/regressoes.csv", index_label="variavel")
pd.set_option("display.width", 200); print(res.round(3).drop(columns=["municipios"]).to_string())
# Teste de assimetria: dpos = dneg
print("\nDiagnósticos: correlação l_transf x l_pib", round(d[["l_transf", "l_pib"]].corr().iloc[0, 1], 3))
# casos focais vs distribuição
f = d[d.foco][["ano", "cod_ibge", "dependencia_transf", "transf_totais_pc_real", "receita_propria_corrente_pc_real", "desp_corrente_pc_real"]]
f.to_csv("output/focais_resumo.csv", index=False)
p = d.groupby("ano").dependencia_transf.median().round(3); print("mediana dependência AM:", p.to_dict())
