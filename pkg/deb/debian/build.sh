#!/bin/bash

set -ex

source "${PATH_REPO_ROOT}/build/paths.env"

# Stage/copy supporting files into the debian directory for inclusion by the "install"
# rule; i.e. only files found in the debian directory can be included by the "install" rule.
mkdir -p "${PATH_DEBIAN_TMP}"
${PATH_DEBIAN_BASE_PYTHON} -m venv "${PATH_DEBIAN_VENV}"
source "${PATH_DEBIAN_VENV_ACTIVATE}"
pip install "${PATH_REPO_ROOT}"[BUILD]
make -C "${PATH_REPO_ROOT}"
cp "${PATH_DIST}"/*.whl "${PATH_DEBIAN_TMP}"
cp "${PATH_BUILD_PATHS_ENV}" "${PATH_DEBIAN_TMP}"

# Install the changelog and compress it, per DEBIANian requirements
dh_installchangelogs
dh_compress

# Install the copyright
dh_installdocs
