#include "nvm/nvm.h"
#include "remote_low.h"

// Define the static member
RemoteLow* RemoteLow::instance = nullptr;

RemoteLow::RemoteLow()
{
    // Makes member data accessible via ISR
    instance = this;
}

void RemoteLow::begin() {
    // configure button pins for floating input
    pinMode(BUTTON_0_PIN, INPUT);
    pinMode(BUTTON_1_PIN, INPUT);
    // configure button pins for interrupt during runtime
    attachInterrupt(digitalPinToInterrupt(BUTTON_0_PIN), RemoteLow::wakeISR0, RISING);
    attachInterrupt(digitalPinToInterrupt(BUTTON_1_PIN), RemoteLow::wakeISR1, RISING);
    // configure button pins to wake from deep sleep
    esp_deep_sleep_enable_gpio_wakeup(1ULL << digitalPinToGPIONumber(BUTTON_0_PIN) |
                                      1ULL << digitalPinToGPIONumber(BUTTON_1_PIN),
                                      ESP_GPIO_WAKEUP_GPIO_HIGH);
    // to filter spurious noise during boot.
    instance->debounce_time = millis() + BUTTON_DEBOUNCE_MS;
}

BUTTON RemoteLow::service() {
    auto button_pressed = BUTTON::NONE;
    const unsigned long now = millis();

    if (last_button_pressed != EVENT::NONE) {
        if (static_cast<long>(now - debounce_time) >= BUTTON_DEBOUNCE_MS) {
            if (last_button_pressed == EVENT::SELECT) {
                button_pressed = BUTTON::SELECT;
            }
            else if (last_button_pressed == EVENT::DIRECTION_0) {
                if (identify_store->payload()->flip) {
                    button_pressed = BUTTON::DOWN;
                }
                else {
                    button_pressed = BUTTON::UP;
                }
            }
            else if (last_button_pressed == EVENT::DIRECTION_1) {
                if (identify_store->payload()->flip) {
                    button_pressed = BUTTON::UP;
                }
                else {
                    button_pressed = BUTTON::DOWN;
                }
            }
            debounce_time = now;
            hold_start_time = now;
            hold_button = last_button_pressed;
            // last_button_pressed = EVENT::NONE;
        }
        last_button_pressed = EVENT::NONE;
    }

    if (!digitalRead(BUTTON_0_PIN) and !digitalRead(BUTTON_1_PIN)) {
        arm_isr = true;
        hold_delay = BUTTON_DEBOUNCE_MS * 10;
    }
    else {
        arm_isr = false;
        if (now - hold_start_time >= hold_delay && hold_button != EVENT::SELECT) {
            last_button_pressed = hold_button;
            hold_delay = 0;
        }
    }

    return button_pressed;
}

void IRAM_ATTR RemoteLow::wakeISR0() {
    if (instance->arm_isr) {
        if (digitalRead(BUTTON_1_PIN)) {
            instance->last_button_pressed = EVENT::DIRECTION_1;
            return;
        }
        // This loop ensures a mechanical button impulse length and quality, preventing
        // misregistration.
        for (int ii = 0; ii < BUTTON_REREAD_COUNT; ++ii) {
            if (!digitalRead(BUTTON_0_PIN)) {
                return;
            }
        }
        instance->last_button_pressed = EVENT::SELECT;
    }
}

void IRAM_ATTR RemoteLow::wakeISR1() {
    if (instance->arm_isr) {
        if (digitalRead(BUTTON_0_PIN)) {
            instance->last_button_pressed = EVENT::DIRECTION_1;
            return;
        }
        // This loop ensures a mechanical button impulse length and quality, preventing
        // misregistration.
        for (int ii = 0; ii < BUTTON_REREAD_COUNT; ++ii) {
            if (!digitalRead(BUTTON_1_PIN)) {
                return;
            }
        }
        instance->last_button_pressed = EVENT::DIRECTION_0;
    }
}
