#!/bin/bash

set -ex

make --environment-overrides export_paths -C "${REPO_ROOT}"
source "${PATHS_ENV}"

# Copy the repository, excluding the directory tree containing this file, into a directory within
# the debian directory.
mkdir -p "${PATH_DEBIAN_TMP}"
pushd "${REPO_ROOT}"
tar cf - --exclude="$(basename "${PATH_PKG_DEB}")" . | (cd "${PATH_DEBIAN_TMP}" && tar xf -)
popd

# Create a virtual environment for building the python package to be installed
${PATH_DEBIAN_BASE_PYTHON} -m venv "${PATH_DEBIAN_VENV}"
source "${PATH_DEBIAN_VENV_ACTIVATE}"
pip install "${PATH_DEBIAN_TMP}"[BUILD]
make -C "${PATH_DEBIAN_TMP}"

#mkdir -p "${PATH_DEBIAN_TMP_USR_LIB_GROWBIES}"~
#cp "${PATH_DIST}"/*.whl "${PATH_DEBIAN_TMP_USR_LIB_GROWBIES}"
#cp "${PATH_BUILD_PATHS_ENV}" "${PATH_DEBIAN_TMP_USR_LIB_GROWBIES}"
#
#mkdir -p "${PATH_DEBIAN_TMP_USR_BIN_GROWBIES}"
#cp "${PATH_PKG_BASH_SRC_GROWBIES}" "${PATH_DEBIAN_TMP_USR_BIN_GROWBIES}"

