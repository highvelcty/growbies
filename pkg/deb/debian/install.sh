#!/bin/bash

# Supress cannot follow non-constant source.
# shellcheck disable=SC1090
source "${PATHS_ENV}"

set -ex

# Install the changelog and compress it, per debian requirements
dh_installchangelogs
dh_compress

# Install the copyright
dh_installdocs


# Create directories
dh_installdirs "${PATH_USR_LIB_GROWBIES}"
dh_installdirs "${PATH_VAR_LIB_GROWBIES}"
dh_installdirs "${PATH_VAR_LIB_GROWBIES_LOCK}"
dh_installdirs "${PATH_VAR_LOG_GROWBIES}"
dh_installdirs "${PATH_ETC_GROWBIES}"

# Install files
dh_install "${PATH_DEBIAN_SRC}/${PATH_DIST}"/*.whl "${PATH_USR_LIB_GROWBIES}"
dh_install "${PATH_DEBIAN_SRC}/${PATH_BUILD_PATHS_ENV}" "${PATH_USR_LIB_GROWBIES}"
dh_install "${PATH_DEBIAN_SRC}/${PATH_PKG_BASH_SRC_GROWBIES}" "${PATH_USR_BIN}"

# Install systemd service
dh_installsystemd --name="${PATH_APPNAME}"-init-db-and-user
dh_installsystemd --name="${PATH_APPNAME}"-init-tables
dh_installsystemd --name="${PATH_APPNAME}"
