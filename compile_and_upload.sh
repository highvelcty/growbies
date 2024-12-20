#!/bin/bash

set -e

arduino-cli compile -b arduino:avr:uno arduino/arduino.ino
arduino-cli upload arduino/arduino.ino -p /dev/ttyACM2 -b arduino:avr:uno


