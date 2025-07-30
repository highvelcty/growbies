#ifndef flags_h
#define flags_h

#if (!ARDUINO_ARCH_AVR && !ARDUINO_ARCH_ESP32)
    #error "Unsupported architecture."
#endif

#define HX711_PIN_CFG_0 ARDUINO_ARCH_AVR
#define HX711_PIN_CFG_1 ARDUINO_ARCH_ESP32
#if !(HX711_PIN_CFG_0 ^ HX711_PIN_CFG_1)
    #error "One and only one HX711 pin configuration must be selected."
#endif

#define POWER_CONTROL 0
#define LED_INSTALLED 0
#define FEATURE_LED (1 && LED_INSTALLED)
#define FEATURE_DISPLAY 1 && (ARDUINO_ARCH_AVR)

#define MASS_SENSOR_COUNT 3
#define TEMPERATURE_SENSOR_COUNT 3

#if TEMPERATURE_SENSOR_COUNT > 0
// Maps to Eaton NRNE105H4100B1H
#define THERMISTOR_HW_0 true
#define THERMISTOR_HW_1 false
static_assert(!THERMISTOR_HW_0 != !THERMISTOR_HW_1);
#endif

#define BUTTERFLY true && (ARDUINO_ARCH_ESP32)

#endif /* flags_h */
