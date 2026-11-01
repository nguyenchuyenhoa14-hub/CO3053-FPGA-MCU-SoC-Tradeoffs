# Bien dich bao cao va slide (XeLaTeX). "make" = cap nhat so lieu tu experiments/ roi build ca hai.
all: data report.pdf slides.pdf

data:
	$(MAKE) -C ../experiments collect

%.pdf: %.tex shared.tex $(wildcard ../experiments/results/numbers.tex)
	xelatex -interaction=nonstopmode -halt-on-error $< > /dev/null || { tail -20 $*.log; exit 1; }
	xelatex -interaction=nonstopmode -halt-on-error $< > /dev/null

clean:
	rm -f *.aux *.log *.nav *.out *.snm *.toc *.vrb

.PHONY: all data clean
