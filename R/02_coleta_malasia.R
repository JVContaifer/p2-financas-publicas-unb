# ==========================================================
# 02_coleta_malasia.R
# Coleta de dados brutos: Malásia
# Fontes: Banco Mundial (WDI) e FMI (WEO, arquivo já enviado)
# Saída: data/raw/*.csv
# ==========================================================
pkgs <- c("WDI", "data.table", "dplyr", "readr", "tidyr")
new  <- pkgs[!pkgs %in% rownames(installed.packages())]
if (length(new)) install.packages(new)
invisible(lapply(pkgs, library, character.only = TRUE))

dir.create("data/raw", recursive = TRUE, showWarnings = FALSE)
anos <- 2014:2024

# ---------- 1. Banco Mundial (WDI) ----------
# Códigos a CONFERIR no portal: algumas séries fiscais (GC.*) podem ter
# lacunas para a Malásia. Lacuna = NA, nunca zero.
ind <- c(
  pib_nominal_myr   = "NY.GDP.MKTP.CN",
  pib_real_myr      = "NY.GDP.MKTP.KN",
  deflator_pib      = "NY.GDP.DEFL.ZS",
  cpi               = "FP.CPI.TOTL",
  populacao         = "SP.POP.TOTL",
  receita_pct_pib   = "GC.REV.XGRT.GD.ZS",
  despesa_pct_pib   = "GC.XPN.TOTL.GD.ZS",
  tributos_pct_pib  = "GC.TAX.TOTL.GD.ZS",
  saldo_pct_pib     = "GC.NLD.TOTL.GD.ZS",
  divida_pct_pib    = "GC.DOD.TOTL.GD.ZS"
)
wdi <- WDI(country = "MYS", indicator = ind,
           start = min(anos), end = max(anos), extra = TRUE)
write_csv(wdi, "data/raw/wdi_malasia.csv")

# ---------- 2. FMI WEO (arquivo enviado: fmi_weo_dataset.csv) ----------
# Colocar o arquivo em data/original/ antes de rodar.
weo <- fread("data/original/fmi_weo_dataset.csv", encoding = "UTF-8")
setnames(weo, make.names(names(weo)))
mys <- weo[COUNTRY.ID == "MYS"]
cat("Linhas Malásia no WEO:", nrow(mys), "\n")
cat("Indicadores disponíveis:\n")
print(unique(mys[, .(INDICATOR.ID, INDICATOR)]))
fwrite(mys, "data/raw/weo_malasia_bruto.csv")
# Obs.: verifique a versão (WEO 9.0.0 no arquivo) e quais anos são
# estimativas/projeções antes de usar 2024+ nas análises.

# ---------- 3. Dados que NÃO vêm de API (coleta manual documentada) ----------
# Transferências federais aos estados da Malásia (statutory grants, capitation
# grant, state road grant) e receitas próprias estaduais:
#   - Ministry of Finance Malaysia: Fiscal Outlook and Federal Government
#     Revenue Estimates (tabelas anuais)
#   - Department of Statistics Malaysia (DOSM): Finance Statistics
#     (State Government) / OpenDOSM
#   - Bank Negara Malaysia: Annual Report
# Registre cada tabela baixada em docs/registro_fontes.md com URL, data
# de acesso e versão. Sem dado disponível => NA, nunca zero.
