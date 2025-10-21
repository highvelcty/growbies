#pragma once

#include <Arduino.h>
#include <U8x8lib.h>

constexpr int BUTTON_DEBOUNCE_MS  = 50;
constexpr int DEFAULT_CONTRAST = 16;
constexpr int BUTTON_1_THRESHOLD = 400;
constexpr int BUTTON_2_THRESHOLD = 800;

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
    void print_mass(float mass);
    bool service();


private:
    // Pointer used by ISR to touch the singleton
    static Remote* instance;

    U8X8_SSD1306_128X32_UNIVISION_HW_I2C display;

    bool button1_pressed = false;
    bool button2_pressed = false;
    bool button3_pressed = false;
    unsigned long last_button_time = 0;

    // volatile make this ISR-safe
    volatile bool wake_flag = false;

    bool handleButtons();
    void update_display();
    static void wakeISR();
};
