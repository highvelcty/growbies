#!/bin/bash

set -e

python -m unittest -k ftests.* "$@"
