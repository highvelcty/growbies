#!/bin/bash

source "${PATH_REPO_ROOT}/build/paths.env"

dh_installdirs "${PATH_USR_LIB_GROWBIES}"
dh_install "${PATH_DEBIAN_TMP}"/*.* "${PATH_USR_LIB_GROWBIES}"

dh_installdirs "${PATH_VAR_LIB_GROWBIES}"
dh_installdirs "${PATH_VAR_LIB_GROWBIES_LOCK}"


