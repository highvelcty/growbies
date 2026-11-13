
SPHINXOPTS    ?=
SPHINXMULTIVERSION ?= sphinx-multiversion
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
		$(SPHINXMULTIVERSION) $(SOURCEDIR) $(BUILDDIR) $(SPHINXOPTS) $(O); \
	)
