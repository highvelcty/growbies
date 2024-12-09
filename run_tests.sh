#!/bin/bash

set -e

make venv/extras/TESTS
source venv/bin/activate
rm .coverage > /dev/null 2>&1 || true
COVERAGE_PROCESS_START=.coveragerc coverage run -m pytest -k tests "$@"
