# Bien dich bao cao va slide (XeLaTeX). "make" = cap nhat so lieu tu experiments/ roi build ca hai.
all: data figs report.pdf slides.pdf slides_hcmut.pdf slides_en.pdf slides_hcmut_en.pdf

slides.pdf slides_hcmut.pdf: slides_body.tex slides_common.tex
slides_en.pdf slides_hcmut_en.pdf: slides_body_en.tex slides_common.tex $(wildcard figs/plots_en/*.png)
slides_hcmut.pdf slides_hcmut_en.pdf: $(wildcard hcmut/*)

figs: figs/credits.tex figs/plots/lit_coremark.png

figs/credits.tex: figs/img/credits.json figs/make_credits.py
	/usr/bin/python3 figs/make_credits.py

figs/plots/lit_coremark.png: figs/make_lit_plots.py
	/usr/bin/python3 figs/make_lit_plots.py
	/usr/bin/python3 figs/make_lit_plots.py --lang en

data:
	$(MAKE) -C ../experiments collect

%.pdf: %.tex shared.tex figs/credits.tex $(wildcard figs/plots/*.png) $(wildcard ../experiments/results/numbers.tex)
	xelatex -interaction=nonstopmode -halt-on-error $< > /dev/null || { tail -20 $*.log; exit 1; }
	xelatex -interaction=nonstopmode -halt-on-error $< > /dev/null

clean:
	rm -f *.aux *.log *.nav *.out *.snm *.toc *.vrb

.PHONY: all data figs clean
