#include "menu.h"
#include <nvm.h>
#include "remote.h"
#include "utils.h"


// Define static instance pointer
Remote* Remote::instance = nullptr;

// Application-wide singleton accessor
Remote& Remote::get() {
    static Remote singleton;
    return singleton;
}

Remote::Remote()
    : display(U8X8_PIN_NONE, HW_I2C_SCL_PIN, HW_I2C_SDA_PIN)
{
    // Makes member data accessible via ISR
    instance = this;

    menu = std::make_unique<Menu>(*this);
}

void Remote::begin() {
    // Order is important, the display must be initialized before attaching interrupts.
    display.begin();
    flip(identify_store->payload()->flip);
    contrast(identify_store->payload()->contrast);
    menu->render();

    // Configure wake pin and attach ISR
    pinMode(BUTTON_0_PIN, INPUT);
    pinMode(BUTTON_1_PIN, INPUT);
    attachInterrupt(digitalPinToInterrupt(BUTTON_0_PIN), Remote::wakeISR0, RISING);
    attachInterrupt(digitalPinToInterrupt(BUTTON_1_PIN), Remote::wakeISR1, RISING);
}

bool Remote::service() {
    bool button_pressed = false;
    if (last_button_pressed != EVENT::NONE) {
        const unsigned long now = millis();

        if (static_cast<long>(now - debounce_time) >= BUTTON_DEBOUNCE_MS) {
            display.clearDisplay();
            if (last_button_pressed == EVENT::SELECT) {
                menu->select();
            }
            else if (last_button_pressed == EVENT::DIRECTION_0) {
                if (identify_store->payload()->flip) {
                    menu->down();
                }
                else {
                    menu->up();
                }
            }
            else if (last_button_pressed == EVENT::DIRECTION_1) {
                if (identify_store->payload()->flip) {
                    menu->up();
                }
                else {
                    menu->down();
                }
            }
            button_pressed = true;
            debounce_time = now;
        }
        last_button_pressed = EVENT::NONE;
    }

    if (!digitalRead(BUTTON_0_PIN) and !digitalRead(BUTTON_1_PIN)) {
        arm_isr = true;
    }
    else {
        arm_isr = false;
    }

    return button_pressed;
}

void IRAM_ATTR Remote::wakeISR0() {
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

void IRAM_ATTR Remote::wakeISR1() {
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

void Remote::contrast(const uint8_t contrast) {
    identify_store->edit().payload.contrast = contrast;
    identify_store->commit();
    display.setContrast(contrast);
}

void Remote::flip(const bool flip) {
    display.setFlipMode(flip);
    menu->render();
}

void Remote::set_temperature_units(TemperatureUnits units) {
    menu->render();
}
