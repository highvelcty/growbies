#pragma once

#include <pins_arduino.h>

#include "build_cfg.h"
#include "types.h"

constexpr auto APPNAME = "growbies";

constexpr int DEFAULT_BAUD_RATE = 57600;
constexpr int MAIN_POLLING_LOOP_INTERVAL_MS = 1;
constexpr int WAIT_READY_RETRIES = 100;
constexpr int WAIT_READY_RETRY_DELAY_MS = 10;

constexpr int SLIP_IN_BUF_ALLOC_BYTES = 256;
constexpr int SLIP_OUT_BUF_ALLOC_BYTES = 512;
// The worst case slip packet encoding
constexpr int MAX_SLIP_UNENCODED_PACKET_BYTES = (SLIP_OUT_BUF_ALLOC_BYTES / 2) - 2;
constexpr float INVALID_TEMPERATURE = 1234.5;
constexpr float INVALID_MASS_SAMPLE_THRESHOLD_DAC = 10000;
constexpr float INVALID_TEMPERATURE_SAMPLE_THRESHOLD_DAC = 50;
constexpr auto SMALL_DELAY_MS = 1;

constexpr int ADC_RESOLUTION = 4096;

#if PIN_CFG == 1
enum Pins : int {
    THERMISTOR_PIN_0 = A0,
    THERMISTOR_PIN_1 = A1,
    THERMISTOR_PIN_2 = A2,
    BATTERY_SENSE_PIN = A3,
    BUTTON_0_PIN = D1,
    BUTTON_1_PIN = D2,
    HW_I2C_SDA_PIN = D4,
    HW_I2C_SCL_PIN = D5,
    HX711_SCK_PIN = D6,
    HX711_VCC_PIN = D7,
    DOUT_2_PIN = D8,
    DOUT_1_PIN = D9,
    DOUT_0_PIN = D10,
};
#elif PIN_CFG == 2
enum Pins : int {
    THERMISTOR_PIN_0 = A0,
    THERMISTOR_PIN_1 = A1,
    THERMISTOR_PIN_2 = A2,
    BATTERY_SENSE_PIN = A3,
    BUTTON_0_PIN = D1,
    BUTTON_1_PIN = D2,
    HW_I2C_SDA_PIN = D4,
    HW_I2C_SCL_PIN = D5,
    HX711_VCC_PIN = D6,
    HX711_SCK_PIN = D10,
    DOUT_2_PIN = D7,
    DOUT_1_PIN = D8,
    DOUT_0_PIN = D9,
};
#elif PIN_CFG == 3
enum Pins : int {
    HEATER_ACTIVE = D6,
    FAN_ACTIVE = D5,
    ACTIVATE_BUTTON = D4,
    GROUNDED_PIN = D3,
    THERMISTOR_PIN_0 = A2,
};
#else
static_assert(always_false<int>::value, "Invalid PIN_CFG value");
#endif

typedef enum Unit : uint16_t {
    // Bitfield
    UNIT_GRAMS          = 0x0001,
    UNIT_MASS_DAC       = 0x0002,
    UNIT_CELSIUS        = 0x0008,
} Units;


inline int get_HX711_dout_pin(const SensorIdx_t sensor){
#if PIN_CFG == 3
    assert(false && "Invalid for pin configuration.");
#else
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

inline int get_HX711_dout_port_bit(const SensorIdx_t sensor) {
    return (1 << get_HX711_dout_pin(sensor));
}

inline int get_temperature_pin(const int mass_sensor_idx) {
    if (MASS_SENSOR_COUNT <= 1) {
        return THERMISTOR_PIN_0;
    }
#if PIN_CFG == 3
    return THERMISTOR_PIN_0;
#else
    switch (mass_sensor_idx) {
        case 0:
            return THERMISTOR_PIN_0;
        case 1:
            return THERMISTOR_PIN_1;
        case 2:
            return THERMISTOR_PIN_2;
        default:
            assert(false && "Temperature pin out of range.");
    }
#endif
}
