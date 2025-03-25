.PHONY: tests
.SILENT: help

default: package

# Export relative paths. Relative to the root of the repository
REPO_ROOT := '.'
build/paths.env: build_lib/export_paths.py
	REPO_ROOT=${REPO_ROOT} python $<

include build/paths.env

### Interface ######################################################################################

clean: clean_pkg
	 git clean -xfd --exclude ${PATH_OUTPUT} --exclude ${PATH_DOT_IDEA}

clean_pkg:
	git clean -xfd -f ${PATH_PKG}

coverage: $(PATH_DOT_COVERAGE)

deb_src_copy: ${PATH_DEBIAN_TMP}

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

${PATH_DEBIAN_TMP}: $(PATH_GROWBIES)
	( \
		mkdir -p ${PATH_DEBIAN_TMP}; \
		tar  --exclude=${PATH_OUTPUT} --exclude=${PATH_DEBIAN_TMP} --exclude='.[^/]*' \
		-cf ${PATH_DEBIAN_TMP_SOURCE_TAR} .; \
		touch ${PATH_DEBIAN_TMP}; \
	)



#tar cf - --exclude="${PATH_PKG_DEB_DEBIAN}" . | \
#(pushd "${PATH_DEBIAN_TMP}" &&	tar xf - && popd); \