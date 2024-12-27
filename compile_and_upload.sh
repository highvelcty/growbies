#!/bin/bash

set -e

arduino-cli compile -b arduino:avr:uno arduino/arduino.ino
arduino-cli upload arduino/arduino.ino -p /dev/ttyACM0 -b arduino:avr:uno


