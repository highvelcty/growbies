#!/bin/bash

set -e

arduino-cli compile -b arduino:avr:uno velostat.ino
arduino-cli upload velostat.ino -p /dev/ttyACM0 -b arduino:avr:uno


