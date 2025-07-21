#ifndef constants_h
#define constants_h

#include <pins_arduino.h>
#include "flags.h"

const int MAIN_POLLING_LOOP_INTERVAL_MS = 1;
const int WAIT_READY_RETRIES = 100;
const int WAIT_READY_RETRY_DELAY_MS = 10;

const float INVALID_TEMPERATURE = 1234.5;

const uint8_t COEFFICIENT_COUNT = 2;
const uint8_t TARE_COUNT = 1;
const int MASS_SENSOR_COUNT = 3;
const int TEMPERATURE_SENSOR_COUNT = 1;


enum Pins : const int {
#if HX711_PIN_CFG_0
    DOUT_0_PIN = 8,
    DOUT_1_PIN = 9,
    DOUT_2_PIN = 10,
    DOUT_3_PIN = 11,
    HX711_SCK_PIN = 12,
    LED_PIN = 13,
    TEMPERATURE_ANALOG_PIN = 0xA3,
    HW_I2C_SDA_PIN = 0xA4,
    HW_I2C_SCL_PIN = 0xA5,
#elif HX711_PIN_CFG_1
    TEMPERATURE_ANALOG_PIN = A0,
    DOUT_0_PIN = D7,
    HX711_SCK_PIN = D8,
    DOUT_1_PIN = D9,
    DOUT_2_PIN = D10,
    LED_PIN = D9,
    HW_I2C_SDA_PIN = D4,
    HW_I2C_SCL_PIN = D5,
#endif
};

enum SensorHw : const int {
    TEMPERATURE_SENSOR = 0,
    MASS_SENSOR = 1
};

inline int get_HX711_dout_pin(int sensor){
#if HX711_PIN_CFG_0
    return DOUT_0_PIN + sensor;
#elif HX711_PIN_CFG_1
    int ret = DOUT_0_PIN;
    if (sensor == 1) {
        ret = DOUT_1_PIN;
    }
    else if (sensor == 2) {
        ret = DOUT_2_PIN;
    }
    return ret;
#endif
}

inline int get_HX711_dout_port_bit(int sensor){
#if HX711_PIN_CFG_0
    return (1 << (get_HX711_dout_pin(sensor) - DOUT_0_PIN));
#elif HX711_PIN_CFG_1
    return (1 << get_HX711_dout_pin(sensor));
#endif
}

inline int get_temperature_sensor_idx(int sensor_idx) {
    if (TEMPERATURE_SENSOR_COUNT == MASS_SENSOR_COUNT) {
        return sensor_idx;
    }
    else if (TEMPERATURE_SENSOR_COUNT == 1) {
        return 0;
    }
}

#endif /* constants_h */