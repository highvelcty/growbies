#!/bin/bash

set -ex

# Export relative paths
make export_paths -C "${REPO_ROOT}"
source "${PATH_DEBIAN_TMP_BUILD_PATHS_ENV}"

# Install the changelog and compress it, per debian requirements
dh_installchangelogs
dh_compress

# Install the copyright
dh_installdocs

# Create directories
dh_installdirs "${PATH_USR_LIB_GROWBIES}"
dh_installdirs "${PATH_VAR_LIB_GROWBIES}"
dh_installdirs "${PATH_VAR_LIB_GROWBIES_LOCK}"

# Install files
dh_install "${PATH_DIST}"/*.whl "${PATH_USR_LIB_GROWBIES}"
dh_install "${PATH_BUILD_PATHS_ENV}" "${PATH_USR_LIB_GROWBIES}"
dh_install "${PATH_PKG_BASH_SRC_GROWBIES}" "${PATH_USR_BIN}"

