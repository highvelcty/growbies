.PHONY: tests
.SILENT: help

default: package

build/paths.env: build_lib/export_paths.py
	python $<

include build/paths.env

### Interface ######################################################################################

clean: clean_pkg
	 git clean -xfd --exclude ${PATH_OUTPUT} --exclude ${PATH_DOT_IDEA}

clean_pkg:
	git clean -xfd -f ${PATH_PKG}

coverage: $(PATH_DOT_COVERAGE)

deb_src_copy: ${PATH_PKG_DEB_DEBIAN_SRC}

export_paths:
	echo "Paths exported by way of Makefile execution."

package: $(PATH_DIST)

tests:
	./run_tests.sh

### Utilities ######################################################################################
$(PATH_DIST): $(PATH_GROWBIES)
	python -m build


$(PATH_DOT_COVERAGE):
	( \
		rm -f .coverage; \
		coverage combine; \
		coverage html; \
		coverage report; \
	)

${PATH_PKG_DEB_DEBIAN_SRC}: $(PATH_GROWBIES)
	( \
		mkdir -p ${PATH_PKG_DEB_DEBIAN_SRC}; \
		tar  --exclude=${PATH_OUTPUT} --exclude=${PATH_PKG_DEB_DEBIAN} --exclude='.[^/]*' \
		-cf - . | tar xf - -C ${PATH_PKG_DEB_DEBIAN_SRC}; \
		touch ${PATH_PKG_DEB_DEBIAN_SRC}; \
	)

