# Estudo bibliométrico (cópia em Python do que o bibliometrix faz): produção anual,
# periódicos, palavras-chave e co-ocorrência. Entrada: export do Scopus em data/raw/bibliometria.
import pandas as pd, collections as C, itertools, glob
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, networkx as nx
f = glob.glob("data/raw/bibliometria/scopus*.csv")[0]
d = pd.read_csv(f); a = d[d["Document Type"].isin(["Article", "Review"])].copy()
a = a[a.Year <= 2025]   # 2026 incompleto
kws = a["Author Keywords"].dropna().apply(lambda x: sorted({k.strip().lower() for k in x.split(";") if k.strip()}))
cnt = C.Counter(k for l in kws for k in l); top = [k for k, _ in cnt.most_common(20)]
co = C.Counter(p for l in kws for p in itertools.combinations([k for k in l if k in top], 2))
cor = "#1f4e79"
fig, ax = plt.subplots(2, 2, figsize=(11, 8.5))
y = a.Year.value_counts().sort_index(); y = y[y.index >= 1970]
ax[0, 0].bar(y.index, y.values, color=cor); ax[0, 0].set_title("A. Produção anual (artigos e revisões)", loc="left", fontsize=10)
s = a["Source title"].value_counts().head(8)[::-1]
ax[0, 1].barh(s.index.str[:34], s.values, color=cor); ax[0, 1].set_title("B. Periódicos mais produtivos", loc="left", fontsize=10)
k = pd.Series(cnt).sort_values().tail(10)
ax[1, 0].barh(k.index, k.values, color=cor); ax[1, 0].set_title("C. Palavras-chave dos autores mais frequentes", loc="left", fontsize=10)
G = nx.Graph()
for (u, v), w in co.items(): G.add_edge(u, v, weight=w)
pos = nx.spring_layout(G, seed=3, k=0.9, weight="weight")
nx.draw_networkx_edges(G, pos, ax=ax[1, 1], width=[0.3 + G[u][v]["weight"] / 8 for u, v in G.edges], alpha=.4)
nx.draw_networkx_nodes(G, pos, ax=ax[1, 1], node_size=[cnt[n] * 6 for n in G], node_color=cor, alpha=.8)
nx.draw_networkx_labels(G, pos, ax=ax[1, 1], font_size=6.5)
ax[1, 1].set_title("D. Co-ocorrência de palavras-chave", loc="left", fontsize=10); ax[1, 1].axis("off")
for x in ax.flat[:3]: x.spines[["top", "right"]].set_visible(False); x.tick_params(labelsize=7)
plt.tight_layout(); plt.savefig("output/bibliometria_painel.png", dpi=200)
res = {"documentos": len(a), "periodicos": a["Source title"].nunique(), "autores": len({x.strip() for l in a.Authors.dropna() for x in l.split(";")}),
       "ano_min": int(a.Year.min()), "ano_max": int(a.Year.max()), "citacoes_medias": round(a["Cited by"].mean(), 1)}
pd.Series(res).to_csv("output/bibliometria_resumo.csv", header=["valor"]); print(res)
