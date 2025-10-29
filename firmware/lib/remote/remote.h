#pragma once

#include <memory>

#include <U8x8lib.h>

// Forward Declarations
class Menu;

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
    bool service();


    void contrast(uint8_t contrast);
    void flip(bool flip);

    U8X8_SSD1306_128X32_UNIVISION_HW_I2C display;
    std::unique_ptr<Menu> menu;

private:
    // Pointer used by ISR to touch the singleton
    static Remote* instance;

    unsigned long debounce_time = 0;

    // volatile make this ISR-safe
    volatile EVENT last_button_pressed = EVENT::NONE;
    volatile bool arm_isr = true;

    static void wakeISR0();
    static void wakeISR1();
};
