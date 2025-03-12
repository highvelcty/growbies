#!/bin/bash

source debian/install_vars.sh

dh_installdirs "${PATH_OUT_LIB}";
dh_install "${PATH_IN_INSTALL_VARS_SH}" "${PATH_OUT_LIB}";
dh_install "${PATH_IN_TMP}"/*.whl "${PATH_OUT_LIB}"

