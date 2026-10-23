#!/bin/sh
# Compila o artigo (pdflatex + bibtex). Executar dentro de artigo/.
pdflatex -interaction=nonstopmode artigo.tex && bibtex artigo && pdflatex -interaction=nonstopmode artigo.tex && pdflatex -interaction=nonstopmode artigo.tex
