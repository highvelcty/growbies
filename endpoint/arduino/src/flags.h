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

#define TEMPERATURE_LOAD_CELL 1
#define POWER_CONTROL 1
#define LED_INSTALLED 1
#define FEATURE_LED (1 && LED_INSTALLED)

#endif /* flags_h */