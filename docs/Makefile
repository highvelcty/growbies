
SPHINXOPTS ?=
SPHINXBUILD ?= sphinx-build
SPHINXMULTIVERSION ?= sphinx-multiversion
SOURCEDIR = source/
BUILDDIR = build/
OUTPUTDIR = build/docs/this_branch

default: html

builddir:
	( \
	    mkdir -p ${BUILDDIR}; \
	)

clean:
	( \
	    rm -rf ${BUILDDIR}*; \
	)

multihtml: builddir
	( \
		$(SPHINXMULTIVERSION) $(SOURCEDIR) $(BUILDDIR) $(SPHINXOPTS) $(O); \
	)


html: builddir
	( \
	$(SPHINXBUILD) -b html "$(SOURCEDIR)" "$(OUTPUTDIR)" $(SPHINXOPTS) $(O) \
	)
