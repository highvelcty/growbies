#!/bin/bash

set -e

rm .coverage > /dev/null 2>&1 || true
COVERAGE_PROCESS_START=.coveragerc coverage run -m unittest -k tests "$@"
