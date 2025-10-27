#pragma once

#include <Arduino.h>
#include <U8x8lib.h>

#include "drawing.h"


constexpr int DEFAULT_CONTRAST = 16;

enum class EVENT: int8_t {
    NONE = -1,
    SELECT = 0,
    DIRECTION_0 = 1,
    DIRECTION_1 = 2,
};

class Remote {
public:
    // Enforce singleton
    Remote();
    Remote(const Remote&) = delete;
    Remote& operator=(const Remote&) = delete;
    Remote(Remote&&) = delete;
    Remote& operator=(Remote&&) = delete;

    // Access the application-wide singleton instance
    static Remote& get();

    // Initialize wake-on-interrupt configuration previously done by enable_delay_wake
    void begin();
    void draw(const Drawing& drawing);
    void print_mass(float mass);
    void draw_mass(float grams, TareIdx tare_idx);
    bool service();
    void set_flip(bool flip);


private:
    // Pointer used by ISR to touch the singleton
    static Remote* instance;

    U8X8_SSD1306_128X32_UNIVISION_HW_I2C display;

    unsigned long debounce_time = 0;

    // volatile make this ISR-safe
    volatile EVENT last_button_pressed = EVENT::NONE;
    volatile bool arm_isr = true;

    static void wakeISR0();
    static void wakeISR1();
};
