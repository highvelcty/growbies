#pragma once

constexpr int POWER_ON_DEBOUNCE_MS  = 50;
constexpr int BUTTON_PRESS_POLL_COUNT = 5;
constexpr int BUTTON_PRESS_PULL_INTERVAL_MS = 1;

// bitfield
enum class EVENT: uint8_t {
    NONE        = 0x00,
    SELECT      = 0x01,
    DIRECTION_0 = 0x02,
    DIRECTION_1 = 0x03,
};

enum class BUTTON : uint8_t {
    NONE = 0,
    UP = 1,
    DOWN = 2,
    SELECT = 3
};
// Allow bitwise OR for your enum class
inline EVENT operator|(EVENT a, EVENT b) {
    return static_cast<EVENT>(static_cast<uint8_t>(a) | static_cast<uint8_t>(b));
}

class RemoteIn {
public:
    static RemoteIn& get() { return *instance; }
    static void begin();

    BUTTON service();


private:
    // Pointer used by ISR to touch the singleton
    static RemoteIn* instance;

    unsigned long power_on_debounce_ms = 0;
    unsigned long hold_time_ms = 0;
    unsigned long hold_interval_ms = 0;

    // volatile make this ISR-safe
    volatile EVENT button_event_bits = EVENT::NONE;

    static void wakeISR0();
    static void wakeISR1();
};
