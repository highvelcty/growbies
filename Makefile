.PHONY: tests
.SILENT: help

git_root := $(shell git rev-parse --show-toplevel)

# This will dump the paths from the package into a form that can be used by Makefile
# and then source the output, sharing the path definitions
$(shell python3 -m build_lib.export_paths || false)

# This will effectively source the paths from the package.
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

package: $(PATH_DIST)

tests:
	./run_tests.sh

### Utilities ######################################################################################
#$(PATH_DIST): $(PATH_GROWBIES)
$(PATH_DIST):
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
