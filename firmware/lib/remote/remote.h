#pragma once

#include <U8x8lib.h>

enum class EVENT: int8_t {
    NONE = -1,
    SELECT = 0,
    DIRECTION_0 = 1,
    DIRECTION_1 = 2,
};

enum class BUTTON : uint8_t {
    NONE = 0,
    UP = 1,
    DOWN = 2,
    SELECT = 3
};

class Remote {
public:
    Remote();

    static void begin();

    BUTTON service();


private:
    // Pointer used by ISR to touch the singleton
    static Remote* instance;

    unsigned long debounce_time = 0;
    unsigned long hold_start_time = 0;
    unsigned long hold_delay = BUTTON_DEBOUNCE_MS * 10;

    // volatile make this ISR-safe
    volatile EVENT last_button_pressed = EVENT::NONE;
    volatile EVENT hold_button = EVENT::NONE;
    volatile bool arm_isr = true;

    static void wakeISR0();
    static void wakeISR1();
};
