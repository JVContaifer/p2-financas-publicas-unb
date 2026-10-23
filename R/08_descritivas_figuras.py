import pandas as pd, numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
d = pd.read_csv("data/tratado/painel_am.csv"); m = pd.read_csv("data/tratado/painel_malasia.csv")
nome = {1304062: "Tabatinga", 1301704: "Humaitá"}
d["mun"] = d.cod_ibge.map(nome)
c = ["transf_totais_pc_real", "receita_propria_corrente_pc_real", "dependencia_transf", "desp_corrente_pc_real", "desp_pessoal_pc_real", "desp_investimento_pc_real", "fpm_pc_real", "fundeb_recebido_pc_real", "participacao_tributaria"]
rows = []
for a in (2014, 2018, 2023):
    x = d[d.ano == a]
    for lab, s in [("Tabatinga", x[x.cod_ibge == 1304062]), ("Humaitá", x[x.cod_ibge == 1301704]), ("Mediana AM (62)", x)]:
        r = {"ano": a, "unidade": lab}; r.update({k: (s[k].median() if len(s) else np.nan) for k in c}); rows.append(r)
T = pd.DataFrame(rows); T.round(3).to_csv("output/tabela_descritiva.csv", index=False); print(T.round(2).to_string())
print(d.groupby("ano").size().to_dict())
# Figura: dependência e transferências pc reais
fig, ax = plt.subplots(1, 3, figsize=(12, 3.6)); cor = {"Tabatinga": "#1f4e79", "Humaitá": "#c0504d"}
for k, g in d[d.foco].groupby("mun"): ax[0].plot(g.ano, g.dependencia_transf * 100, marker="o", ms=3, label=k, color=cor[k]); ax[1].plot(g.ano, g.transf_totais_pc_real / 1000, marker="o", ms=3, label=k, color=cor[k])
q = d.groupby("ano").dependencia_transf.quantile([.1, .5, .9]).unstack() * 100
ax[0].fill_between(q.index, q[.1], q[.9], color="grey", alpha=.2, label="P10-P90 AM"); ax[0].plot(q.index, q[.5], color="grey", ls="--", label="Mediana AM")
q2 = d.groupby("ano").transf_totais_pc_real.quantile([.1, .5, .9]).unstack() / 1000
ax[1].fill_between(q2.index, q2[.1], q2[.9], color="grey", alpha=.2); ax[1].plot(q2.index, q2[.5], color="grey", ls="--")
ax[0].set_title("Dependência de transferências (% receita total)", fontsize=9, loc="left"); ax[1].set_title("Transferências per capita (mil R$ de 2023)", fontsize=9, loc="left")
ax[2].plot(m.ano, m.gc_tributos_pct_pib, color="#2e7d32", marker="o", ms=3, label="Tributos (gov. central)"); ax[2].plot(m.ano, m.gc_receita_pct_pib, color="#7f7f7f", marker="o", ms=3, label="Receita total (gov. central)")
ax[2].set_title("Malásia: receita do governo central (% PIB)", fontsize=9, loc="left")
for x in ax: x.spines[["top", "right"]].set_visible(False); x.tick_params(labelsize=7); x.legend(fontsize=6.5, frameon=False)
plt.tight_layout(); plt.savefig("output/fig_descritivas.png", dpi=200)
