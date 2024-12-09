.SILENT: help

git_root := $(shell git rev-parse --show-toplevel)

# This will dump the paths from the package into a form that can be used by Makefile
$(shell python -m build_lib.export_paths)
# This will effectively source the paths from the package.
include build/paths.env

### Interface ######################################################################################
default: package

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
$(PATH_DIST): $(PATH_VENV_EXTRAS_BUILD) $(PATH_LLMOPS_ETL)
	( \
		. $(PATH_VENV_BIN_ACTIVATE); \
		python -m build \
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
