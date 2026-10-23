# ==========================================================
# 05_bibliometrix.R
# Estudo bibliométrico com o pacote bibliometrix
# Base: exportação do Scopus (CSV), busca em 23/10/2026
#   TITLE-ABS-KEY ( {flypaper effect} OR {fiscal illusion} OR
#     {intergovernmental transfers} OR {intergovernmental grants} )
#   filtros: Article, English
#
# Como rodar (Posit Cloud / RStudio):
#   1. Suba o CSV do Scopus para a pasta do projeto.
#   2. No Console:  source("05_bibliometrix.R")   (ajuste o nome se necessário)
# A instalação do pacote pode levar de 10 a 20 minutos na primeira vez.
# Cada bloco roda isolado: se um falhar, os outros continuam.
# Saídas: output/bibliometrix_*.csv, output/bibliometrix_graficos.pdf
# ==========================================================
if (!requireNamespace("bibliometrix", quietly = TRUE)) install.packages("bibliometrix")
library(bibliometrix)
dir.create("output", showWarnings = FALSE)

# ---------- 1. Localiza o arquivo do Scopus ----------
arq <- list.files(pattern = "scopus.*\\.csv$", recursive = TRUE, ignore.case = TRUE)[1]
if (is.na(arq)) stop("Não achei o CSV do Scopus. Suba o arquivo e tente de novo.")
message("Arquivo: ", arq)

# ---------- 2. Importa e converte ----------
M <- convert2df(file = arq, dbsource = "scopus", format = "csv")
message("Documentos importados: ", nrow(M))
# Mantém só artigos e revisões de periódico (o export traz capítulos, notas etc.)
M <- M[M$DT %in% c("ARTICLE", "REVIEW", "ARTICLE; ARTICLE IN PRESS"), ]
message("Após filtro ARTICLE/REVIEW: ", nrow(M))
write.csv(M[, intersect(c("AU", "TI", "SO", "PY", "TC", "DI", "DE", "AB"), names(M))],
          "output/bibliometrix_base_resumida.csv", row.names = FALSE)

# ---------- 3. Análise descritiva ----------
res <- biblioAnalysis(M, sep = ";")
S <- summary(res, k = 15, pause = FALSE)
capture.output(S, file = "output/bibliometrix_resumo.txt")

tabelas <- c("MainInformationDF", "AnnualProduction", "MostProdAuthors", "MostCitedPapers",
             "MostProdCountries", "TCperCountries", "MostRelSources", "MostRelKeywords")
for (nm in tabelas) {
  tryCatch({
    if (!is.null(S[[nm]])) write.csv(S[[nm]], paste0("output/bibliometrix_", nm, ".csv"),
                                     row.names = FALSE)
  }, error = function(e) message("Tabela ", nm, ": ", conditionMessage(e)))
}

# ---------- 4. Gráficos (todos no mesmo PDF) ----------
pdf("output/bibliometrix_graficos.pdf", width = 10, height = 7)

tryCatch(plot(x = res, k = 15, pause = FALSE),
         error = function(e) message("Gráficos descritivos: ", conditionMessage(e)))

tryCatch({   # Co-ocorrência de palavras-chave dos autores
  NM <- biblioNetwork(M, analysis = "co-occurrences", network = "author_keywords", sep = ";")
  networkPlot(NM, normalize = "association", n = 30, Title = "Co-ocorrência de palavras-chave",
              type = "fruchterman", size = TRUE, remove.multiple = FALSE, labelsize = 0.8)
}, error = function(e) message("Rede de palavras-chave: ", conditionMessage(e)))

tryCatch({   # Co-citação de referências
  NM <- biblioNetwork(M, analysis = "co-citation", network = "references", sep = ";")
  networkPlot(NM, n = 30, Title = "Co-citação", type = "fruchterman",
              size = TRUE, remove.multiple = FALSE, labelsize = 0.7)
}, error = function(e) message("Co-citação: ", conditionMessage(e)))

tryCatch({   # Colaboração entre países
  M2 <- metaTagExtraction(M, Field = "AU_CO", sep = ";")
  NM <- biblioNetwork(M2, analysis = "collaboration", network = "countries", sep = ";")
  networkPlot(NM, n = 20, Title = "Colaboração entre países", type = "circle",
              size = TRUE, remove.multiple = FALSE, labelsize = 0.8)
}, error = function(e) message("Colaboração entre países: ", conditionMessage(e)))

tryCatch({   # Mapa temático
  Map <- thematicMap(M, field = "DE", n = 250, minfreq = 5, stemming = FALSE,
                     size = 0.5, n.labels = 3, repel = TRUE)
  plot(Map$map)
}, error = function(e) message("Mapa temático: ", conditionMessage(e)))

dev.off()
message("Pronto. Veja a pasta output/ (exporte bibliometrix_graficos.pdf e os CSV).")
