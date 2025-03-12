#!/bin/bash

set -e

source debian/install_vars.sh

# Repository paths
PATH_GIT_ROOT=$(git rev-parse --show-toplevel)
PATH_DIST="${PATH_GIT_ROOT}"/dist

mkdir -p "${PATH_IN_TMP}"
${PYTHON} -m venv "${PATH_IN_VENV}"
source "${PATH_IN_VENV_ACTIVATE}"
pip install "${PATH_GIT_ROOT}"[BUILD]
make -C "${PATH_GIT_ROOT}"
cp "${PATH_DIST}"/*.whl "${PATH_IN_TMP}"
