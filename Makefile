.PHONY: tests
.SILENT: help

default: package

build/paths.env: build_lib/export_paths.py
	PYTHONPATH=$(CURDIR) python $<

include build/paths.env

src_watch := $(shell find ${PATH_APPNAME} -type f)

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
	GIT_HASH=$(git rev-parse --short HEAD) python -m build

$(PATH_DOT_COVERAGE):
	( \
		rm -f .coverage; \
		coverage combine; \
		coverage html; \
		coverage report; \
	)

${PATH_PKG_DEB_DEBIAN_SRC}: $(src_watch)
	( \
		rm -rf ${PATH_PKG_DEB_DEBIAN_SRC}; \
		mkdir -p ${PATH_PKG_DEB_DEBIAN_SRC}; \
		tar --exclude=${PATH_ARCHIVE} \
			--exclude=${PATH_DOCS} \
			--exclude=${PATH_OUTPUT} \
			--exclude=${PATH_PKG_DEB} \
		    --exclude=${PATH_TESTS} \
		    --exclude-from=.gitignore \
			--exclude='.[^/]*' \
			--exclude='*__pycache__' \
		-cf - . | tar xf - -C ${PATH_PKG_DEB_DEBIAN_SRC}; \
		python -m build_lib.build_cfg gateway; \
		touch ${PATH_PKG_DEB_DEBIAN_SRC}; \
	)
