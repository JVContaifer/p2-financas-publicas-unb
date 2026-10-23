# Tratamento da Malásia (2014-2024). Entradas: data/raw/wdi_malasia.csv (WDI, governo central) e
# data/raw/weo_malasia_bruto.csv (WEO/FMI, governo geral). Saída: data/tratado/painel_malasia.csv
# Valores reais em MYR de 2023 (deflator = IPC do WDI, FP.CPI.TOTL); per capita; % do PIB.
# Ausente = NaN (nunca zero). WEO: 2024 em diante pode ser estimativa/projeção -> flag_weo_estimado.
import pandas as pd, numpy as np
w = pd.read_csv("data/raw/wdi_malasia.csv").set_index("year")
e = pd.read_csv("data/raw/weo_malasia_bruto.csv")
anos = list(range(2014, 2025))
def weo(ind): 
    r = e[e["INDICATOR.ID"] == ind].iloc[0]; return pd.Series({a: pd.to_numeric(r[str(a)], errors="coerce") for a in anos})
t = pd.DataFrame(index=anos); t.index.name = "ano"
t["populacao"] = w.populacao
t["fator_real_2023"] = w.cpi[2023] / w.cpi
t["pib_nominal_myr"] = w.pib_nominal_myr
t["pib_real_myr_2023"] = t.pib_nominal_myr * t.fator_real_2023
t["pib_pc_real_myr_2023"] = t.pib_real_myr_2023 / t.populacao
for v in ["receita_pct_pib", "despesa_pct_pib", "tributos_pct_pib", "saldo_pct_pib", "divida_pct_pib"]: t["gc_" + v] = w[v]
t["gc_receita_real_pc"] = t.gc_receita_pct_pib / 100 * t.pib_pc_real_myr_2023
t["gc_despesa_real_pc"] = t.gc_despesa_pct_pib / 100 * t.pib_pc_real_myr_2023
t["gc_tributos_real_pc"] = t.gc_tributos_pct_pib / 100 * t.pib_pc_real_myr_2023
t["gc_receita_naotrib_pct_pib"] = t.gc_receita_pct_pib - t.gc_tributos_pct_pib
t["gg_receita_pct_pib_weo"] = weo("GGR_NGDP"); t["gg_despesa_pct_pib_weo"] = weo("GGX_NGDP")
t["gg_saldo_pct_pib_weo"] = weo("GGXCNL_NGDP"); t["gg_divida_pct_pib_weo"] = weo("GGXWDG_NGDP")
t["pib_real_cresc_pct"] = t.pib_real_myr_2023.pct_change() * 100
t["flag_weo_estimado"] = t.index >= 2025
t["flag_gc_despesa_ausente"] = t.gc_despesa_pct_pib.isna()
t.round(4).to_csv("data/tratado/painel_malasia.csv")
print(t[["pib_pc_real_myr_2023", "gc_receita_pct_pib", "gc_tributos_pct_pib", "gc_receita_naotrib_pct_pib", "gg_receita_pct_pib_weo", "gg_despesa_pct_pib_weo", "gc_divida_pct_pib"]].round(1).to_string())
