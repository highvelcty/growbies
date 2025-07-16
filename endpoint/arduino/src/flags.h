#ifndef flags_h
#define flags_h

#if (!ARDUINO_ARCH_AVR && !ARDUINO_ARCH_ESP32)
    #error "Unsupported architecture."
#endif

#define TEMPERATURE_ANALOG_INPUT 1
#define POWER_CONTROL 1
#define LED_INSTALLED 1
#define FEATURE_LED (1 && LED_INSTALLED)


#endif /* flags_h */