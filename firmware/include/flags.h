#ifndef flags_h
#define flags_h

#if (!ARDUINO_ARCH_AVR && !ARDUINO_ARCH_ESP32)
    #error "Unsupported architecture."
#endif

#define POWER_CONTROL 1
#define BATTERY_LEVEL_INDICATOR 0

#endif /* flags_h */
