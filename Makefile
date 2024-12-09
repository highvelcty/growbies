.PHONY: tests
.SILENT: help

git_root := $(shell git rev-parse --show-toplevel)

# This will dump the paths from the package into a form that can be used by Makefile
$(shell python -m build_lib.export_paths)
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

venv:
	( \
		python -m venv $(PATH_VENV) --clear $(VENV); \
		mkdir $(PATH_VENV_EXTRAS); \
		. $(PATH_VENV_BIN_ACTIVATE); \
		pip install -e . \
	)


### Utilities ######################################################################################
$(PATH_DIST): $(PATH_VENV_EXTRAS_BUILD) $(PATH_PRECISION_FARMING)
	( \
		. $(PATH_VENV_BIN_ACTIVATE); \
		python -m build \
	)

$(PATH_DOT_COVERAGE): $(PATH_VENV_EXTRAS_TESTS)

.coverage:
	( \
		. $(PATH_VENV_BIN_ACTIVATE); \
		rm -f .coverage; \
		coverage combine; \
		coverage html; \
		coverage report; \
	)

$(PATH_VENV_EXTRAS_BUILD): venv
	( \
		. $(PATH_VENV_BIN_ACTIVATE); \
		pip install .[BUILD]; \
		touch $(PATH_VENV_EXTRAS_BUILD) \
	)

$(PATH_VENV_EXTRAS_TESTS): venv
	( \
		. $(PATH_VENV_BIN_ACTIVATE); \
		pip install .[TESTS]; \
		touch $(PATH_VENV_EXTRAS_TESTS) \
	)
