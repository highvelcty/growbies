SPHINXOPTS ?=
SPHINXBUILD ?= sphinx-build
SPHINXMULTIVERSION ?= sphinx-multiversion

SOURCEDIR = source/
BUILDDIR ?= build/
DOCSDIR ?= $(BUILDDIR)docs/

default: html

.PHONY: default builddir clean html multihtml

builddir:
	mkdir -p $(DOCSDIR)

clean:
	rm -rf $(BUILDDIR)

html: builddir
	$(SPHINXBUILD) -b html "$(SOURCEDIR)" "$(DOCSDIR)" $(SPHINXOPTS) $(O)

multihtml: builddir
	git --no-pager -C .. fetch origin '+refs/heads/*:refs/remotes/origin/*' --tags --prune
	$(SPHINXMULTIVERSION) -c "$(SOURCEDIR)" \
		-D 'smv_branch_whitelist=^docs/firmware-.*$$' \
		"$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	$(SPHINXMULTIVERSION) -c "$(SOURCEDIR)" \
		-D 'smv_branch_whitelist=^docs/gateway-.*$$' \
		"$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	$(SPHINXMULTIVERSION) -c "$(SOURCEDIR)" \
		-D 'smv_branch_whitelist=^docs/manual-.*$$' \
		"$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	./source/_scripts/make_top_level_index.py "$(BUILDDIR)"
	$(MAKE) html

