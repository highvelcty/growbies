#ifndef constants_h
#define constants_h

#include <pins_arduino.h>
#include "flags.h"

const int MAIN_POLLING_LOOP_INTERVAL_MS = 1;
const int WAIT_READY_RETRIES = 100;
const int WAIT_READY_RETRY_DELAY_MS = 10;

const uint8_t COEFFICIENT_COUNT = 2;
const uint8_t TARE_COUNT = 1;
const int MASS_SENSOR_COUNT = 1;
const int TEMPERATURE_SENSOR_COUNT = 1;

// Uno and mini pro are 1024 bytes.
// ESP32C3 is 512 bytes.
//
// Selected here is least common denominator.
const int EEPROM_BYTES = 512;

#if TEMPERATURE_ANALOG_INPUT
const int TEMPERATURE_ANALOG_PIN = A3;
#endif

enum ArduinoDigitalPins : const int {
#if ARDUINO_ARCH_AVR
    STARTING_DOUT_PIN = 8,
    HX711_SCK_PIN = 12,
    LED_PIN = 13,
#elif ARDUINO_ARCH_ESP32
    STARTING_DOUT_PIN = D7,
    HX711_SCK_PIN = D8,
    LED_PIN = D9,
#endif
};

enum ArduinoAnalogPins : const int {
    A4_HW_I2C_SDA = 0xA4,
    A5_HW_I2C_SCL = 0xA5,
};

enum SensorHw : const int {
    TEMPERATURE_SENSOR = 0,
    MASS_SENSOR = 1
};

inline int get_HX711_dout_pin(int sensor){
    return STARTING_DOUT_PIN + sensor;
}

inline int get_HX711_dout_port_bit(int sensor){
    return (1 << (get_HX711_dout_pin(sensor) - STARTING_DOUT_PIN));
}

#endif /* constants_h */