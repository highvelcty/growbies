#!/bin/sh

set -e

# Build paths
export PATH_IN_INSTALL_VARS_SH=debian/install_vars.sh
INSTALL_VARS_FILENAME=$(basename ${PATH_IN_INSTALL_VARS_SH})
export PATH_IN_TMP=debian/tmp
export PYTHON=python3.11
export PATH_IN_VENV="${PATH_IN_TMP}"/venv
export PATH_IN_VENV_ACTIVATE="${PATH_IN_VENV}"/bin/activate

# Install paths
export PATH_OUT_LIB="${DESTDIR}/usr/lib/growbies-gateway"
export PATH_OUT_INSTALL_VARS_SH="${PATH_OUT_LIB}"/"${INSTALL_VARS_FILENAME}"
export PATH_OUT_VENV="${PATH_OUT_LIB}"/venv
export PATH_OUT_VENV_ACTIVATE="${PATH_OUT_VENV}"/bin/activate

