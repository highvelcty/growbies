#!/bin/bash

source "${PATHS_ENV}"
set -ex
cd "${PATH_SRC}"

# Create a virtual environment for building the python package to be installed
${PATH_DEBIAN_BASE_PYTHON} -m venv venv
source venv/bin/activate
pip install -e .[BUILD]
make

