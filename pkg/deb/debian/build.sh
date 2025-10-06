#!/bin/bash

# Supress cannot follow non-constant source.
# shellcheck disable=SC1090
source "${PATHS_ENV}"
set -ex
cd "${PATH_DEBIAN}"

# Create a virtual environment for building the python package to be installed
${PATH_DEBIAN_BASE_PYTHON} -m venv venv
source venv/bin/activate
cd "${PATH_DEBIAN_SRC}"
pip install -e .[BUILD]
make

