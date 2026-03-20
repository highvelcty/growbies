#include "nvm/nvm.h"
#include "remote_in.h"

static RemoteIn remote_in_singleton;
RemoteIn* RemoteIn::instance = &remote_in_singleton;

void RemoteIn::begin() {
    // configure button pins for floating input
    pinMode(BUTTON_0_PIN, INPUT);
    pinMode(BUTTON_1_PIN, INPUT);
    // configure button pins for interrupt during runtime
    attachInterrupt(digitalPinToInterrupt(BUTTON_0_PIN), RemoteIn::wakeISR0, HIGH);
    attachInterrupt(digitalPinToInterrupt(BUTTON_1_PIN), RemoteIn::wakeISR1, HIGH);
    esp_sleep_disable_wakeup_source(ESP_SLEEP_WAKEUP_TIMER);
    // configure button pins to wake from deep sleep
    esp_deep_sleep_enable_gpio_wakeup(1ULL << digitalPinToGPIONumber(BUTTON_0_PIN) |
                                      1ULL << digitalPinToGPIONumber(BUTTON_1_PIN),
                                      ESP_GPIO_WAKEUP_GPIO_HIGH);
    // to filter spurious noise during boot.
    instance->power_on_debounce_ms = millis() + POWER_ON_DEBOUNCE_MS;
}

// This is not const because it modifies the static member variables shared by the ISRs.
// ReSharper disable once CppMemberFunctionMayBeConst
BUTTON RemoteIn::service() { // NOLINT(*-make-member-function-const)
    auto button = BUTTON::NONE;
    const auto now = millis();

    // A button event has been detected
    if (instance->button_event_bits != EVENT::NONE) {
        if (now - power_on_debounce_ms <= POWER_ON_DEBOUNCE_MS) {
            // No button servicing until the MCU has settled.
            instance->button_event_bits = EVENT::NONE;
            return button;
        }
    }

    // Service the button event
    if ((digitalRead(BUTTON_0_PIN) != HIGH) and (digitalRead(BUTTON_1_PIN) != HIGH)) {
        if (instance->button_event_bits == EVENT::SELECT) {
            button = BUTTON::SELECT;
        }
        if (instance->button_event_bits == EVENT::DIRECTION_0) {
            if (identify_store->payload()->flip) {
                button = BUTTON::DOWN;
            }
            else {
                button = BUTTON::UP;
            }
        }
        if (instance->button_event_bits == EVENT::DIRECTION_1) {
            if (identify_store->payload()->flip) {
                button = BUTTON::UP;
            }
            else {
                button = BUTTON::DOWN;
            }
        }

        instance->button_event_bits = EVENT::NONE;
    }

    return button;
}

void IRAM_ATTR RemoteIn::wakeISR0() {
    instance->button_event_bits = instance->button_event_bits | EVENT::SELECT;
}

void IRAM_ATTR RemoteIn::wakeISR1() {
    instance->button_event_bits = instance->button_event_bits | EVENT::DIRECTION_0;
}
