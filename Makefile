.PHONY: tests
.SILENT: help

default: package

build/paths.env: build_lib/export_paths.py
	PYTHONPATH=$(CURDIR) python $<

include build/paths.env

src_watch = $(shell find ${PATH_GROWBIES} -name '*' ! -path '*__pycache__*')
src_watch_ext = ${src_watch}
src_watch_ext += $(shell find ${PATH_PKG_BASH_SRC} -type f -name '*')

### Interface ######################################################################################
clean:
	 git clean -xfd --exclude ${PATH_OUTPUT} --exclude ${PATH_DOT_IDEA}

coverage: $(PATH_DOT_COVERAGE)

deb_src_copy: ${PATH_PKG_DEB_DEBIAN_SRC}

export_paths:
	@echo "Paths exported by way of Makefile execution."

package: $(PATH_DIST) $(src_watch)

tests:
	./run_tests.sh

### Utilities ######################################################################################
$(PATH_DIST): $(src_watch)
	python -m build

$(PATH_DOT_COVERAGE):
	( \
		rm -f .coverage; \
		coverage combine; \
		coverage html; \
		coverage report; \
	)

${PATH_PKG_DEB_DEBIAN_SRC}: $(src_watch_ext)
	( \
		mkdir -p ${PATH_PKG_DEB_DEBIAN_SRC}; \
		tar  --exclude=${PATH_OUTPUT} --exclude=${PATH_PKG_DEB_DEBIAN} --exclude='.[^/]*' \
		-cf - . | tar xf - -C ${PATH_PKG_DEB_DEBIAN_SRC}; \
		touch ${PATH_PKG_DEB_DEBIAN_SRC}; \
	)

