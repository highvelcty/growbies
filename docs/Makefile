SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = source/
BUILDDIR      = build/

default: html

builddir:
	( \
	    mkdir -p ${BUILDDIR}; \
	)

clean:
	( \
	    rm -rf ${BUILDDIR}*; \
	)

html: builddir
	( \
		$(SPHINXBUILD) -b html $(SOURCEDIR) $(BUILDDIR) $(SPHINXOPTS) $(O); \
	)
