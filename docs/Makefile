SPHINXOPTS ?=
SPHINXBUILD ?= sphinx-build
SPHINXMULTIVERSION ?= sphinx-multiversion

SOURCEDIR = source/
BUILDDIR = build/
DOCSDIR = build/docs/

default: html

builddir:
	mkdir -p $(DOCSDIR)

clean:
	rm -rf $(BUILDDIR)

html: builddir
	$(SPHINXBUILD) -b html "$(SOURCEDIR)" "$(BUILDDIR)html" $(SPHINXOPTS) $(O)

multihtml: builddir
	$(SPHINXMULTIVERSION) -c "$(SOURCEDIR)firmware" "$(SOURCEDIR)" "$(DOCSDIR)" $(SPHINXOPTS) $(O)
	$(SPHINXMULTIVERSION) -c "$(SOURCEDIR)gateway" "$(SOURCEDIR)" "$(DOCSDIR)" $(SPHINXOPTS) $(O)
	$(SPHINXMULTIVERSION) -c "$(SOURCEDIR)manual" "$(SOURCEDIR)" "$(DOCSDIR)" $(SPHINXOPTS) $(O)