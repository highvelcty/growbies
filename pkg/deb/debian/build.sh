#!/bin/bash

set -ex

# Export absolute paths
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

