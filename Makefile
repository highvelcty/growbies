.PHONY: tests
.SILENT: help

# Export relative paths. Relative to the root of the repository
REPO_ROOT := '.'
$(shell REPO_ROOT=${REPO_ROOT} python3 -m build_lib.export_paths || false)
include build/paths.env

### Interface ######################################################################################
default: package

clean:
	( \
		rm -rf $(PATH_DOT_COVERAGE).*; \
		rm -rf $(PATH_BUILD); \
		rm -rf $(PATH_DIST); \
		rm -rf $(PATH_HTMLCOV); \
		rm -rf $(PATH_VENV); \
		rm -rf *.egg-info; \
	)

coverage: $(PATH_DOT_COVERAGE)

export_paths:
	echo "Paths exported by way of Makefile execution."

package: $(PATH_DIST)

tests:
	./run_tests.sh

### Utilities ######################################################################################
$(PATH_DIST): $(PATH_GROWBIES)
	( \
		python -m build \
	)

$(PATH_DOT_COVERAGE):
	( \
		rm -f .coverage; \
		coverage combine; \
		coverage html; \
		coverage report; \
	)
