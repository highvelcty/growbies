#!/bin/bash

set -e

arduino-cli compile -b arduino:avr:uno velostat.ino
arduino-cli upload velostat.ino -p /dev/ttyACM1 -b arduino:avr:uno


