#pragma once

#include <pins_arduino.h>

#include "build_cfg.h"
#include "flags.h"
#include "types.h"

constexpr auto APPNAME = "growbies";

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

// Thermistor
#if ARDUINO_ARCH_AVR
constexpr float ADC_V_REF = 3.3; // Measured ADC reference voltage
constexpr int ADC_RESOLUTION = 1024;
#elif ARDUINO_ARCH_ESP32
constexpr int ADC_RESOLUTION = 4096;
#endif

#if THERMISTOR_HW_0
// Steinhart-hart coeffs calculated at 0*C, 25*C & 50*C
constexpr float THERMISTOR_SERIES_RESISTOR = 100000.0;
constexpr float THERMISTOR_NOMINAL_RESISTANCE = 100000.0;
constexpr float THERMISTOR_NOMINAL_TEMPERATURE = 298.15;        // kelvin
constexpr float THERMISTOR_SUPPLY_VOLTAGE = 2.7;
constexpr float THERMISTOR_BETA_COEFF = 4100.0;              // Beta coefficient for thermistor
constexpr float STEINHART_HART_A = 1.003702421E-3;
constexpr float STEINHART_HART_B = 1.811901925E-4;
constexpr float STEINHART_HART_C = 1.731869483E-7;
#endif

enum Pins : int {
#if HX711_PIN_CFG_0
    DOUT_0_PIN = 8,
    DOUT_1_PIN = 9,
    DOUT_2_PIN = 10,
    DOUT_3_PIN = 11,
    HX711_SCK_PIN = 12,
    LED_PIN = 13,
    TEMPERATURE_PIN_0 = A3,
    HW_I2C_SDA_PIN = 0xA4,
    HW_I2C_SCL_PIN = 0xA5,
#elif HX711_PIN_CFG_1
    TEMPERATURE_PIN_0 = A0,
    TEMPERATURE_PIN_1 = A1,
    TEMPERATURE_PIN_2 = A2,
    DOUT_0_PIN = D7,
    HX711_SCK_PIN = D8,
    DOUT_1_PIN = D9,
    DOUT_2_PIN = D10,
    LED_PIN = D9,
    HW_I2C_SDA_PIN = D4,
    HW_I2C_SCL_PIN = D5,
    BUTTON_0_PIN = D3,
    BUTTON_1_PIN = D6,
#endif
};

typedef enum Unit : uint16_t {
    // Bitfield
    UNIT_GRAMS          = 0x0001,
    UNIT_MASS_DAC       = 0x0002,
    UNIT_CELSIUS        = 0x0008,
} Units;

constexpr auto DEFAULT_SAMPLES_PER_DATAPOINT = 7;
constexpr auto WAIT_FOR_CMD_MILLIS = 100;
constexpr uint32_t SLEEP_MS = 1000; // 1 second
constexpr auto DELAY_INTERVAL_MS = 10;
constexpr auto DEEP_SLEEP_USECS = SLEEP_MS * 1000;
constexpr auto SMALL_DELAY_MS = 1;
constexpr int BUTTON_DEBOUNCE_MS  = 50;
constexpr int BUTTON_REREAD_COUNT =  7;

inline int get_HX711_dout_pin(const SensorIdx_t sensor){
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
#else
    assert(false && "Invalid pin configuration.");
#endif
}

inline int get_HX711_dout_port_bit(const SensorIdx_t sensor) {
#if HX711_PIN_CFG_0
    return (1 << (get_HX711_dout_pin(sensor) - DOUT_0_PIN));
#elif HX711_PIN_CFG_1
    return (1 << get_HX711_dout_pin(sensor));
#endif
}

inline int get_temperature_pin(const int mass_sensor_idx) {
    if (MASS_SENSOR_COUNT == 1) {
        return TEMPERATURE_PIN_0;
    }
#if HX711_PIN_CFG_0
    assert(false && "Unimplemented temperature pin mapping.");
#elif HX711_PIN_CFG_1
    switch (mass_sensor_idx) {
        case 0:
            return TEMPERATURE_PIN_0;
        case 1:
            return TEMPERATURE_PIN_1;
        case 2:
            return TEMPERATURE_PIN_2;
        default:
            assert(false && "Temperature pin out of range.");
    }
#endif
}