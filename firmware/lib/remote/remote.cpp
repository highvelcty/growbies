#include "constants.h"
#include <nvm.h>
#include "remote.h"

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
}

void Remote::begin() {
    // Configure wake pin and attach ISR
    pinMode(BUTTON_0_PIN, INPUT);
    pinMode(BUTTON_1_PIN, INPUT);
    attachInterrupt(digitalPinToInterrupt(BUTTON_0_PIN), Remote::wakeISR0, RISING);
    attachInterrupt(digitalPinToInterrupt(BUTTON_1_PIN), Remote::wakeISR1, RISING);


    // Initialize display
    display.begin();
    display.setFont(u8x8_font_chroma48medium8_r);
    display.setFlipMode(identify_store->payload()->flip);
    display.draw1x2String(0, 0, "Growbies");
}

void Remote::print_mass(const float mass) {
    char buf[8];
    dtostrf(mass, 6, 1, buf);
    this->display.setFont(u8x8_font_px437wyse700a_2x2_r);
    this->display.draw1x2String(0, 0, buf);
    this->display.setFont(u8x8_font_chroma48medium8_r);
    this->display.draw1x2String(15, 2, "g");
}

bool Remote::service() {
    bool button_pressed = false;
    if (last_button_pressed != EVENT::NONE) {
        const unsigned long now = millis();

        if (now - debounce_time >= BUTTON_DEBOUNCE_MS) {
            button_pressed = true;
            display.clearDisplay();
            if (last_button_pressed == EVENT::SELECT) {
                display.draw1x2String(0, 0, "Select");
            }
            else if (last_button_pressed == EVENT::DIRECTION_0) {
                display.draw1x2String(0, 0, "Direction 0");
            }
            else if (last_button_pressed == EVENT::DIRECTION_1) {
                display.draw1x2String(0, 0, "Direction 1");
            }
        }
        last_button_pressed = EVENT::NONE;
    }
    return button_pressed;
}

void Remote::set_flip(const bool flip) {
    display.setFlipMode(flip);
}

void IRAM_ATTR Remote::wakeISR0() {
    instance->last_button_pressed = EVENT::SELECT;
    for (auto ii = 0; ii < BUTTON_READ_COUNT; ++ii) {
        if (digitalRead(BUTTON_1_PIN)) {
            instance->last_button_pressed = EVENT::DIRECTION_1;
            break;
        }
        delayMicroseconds(SMALL_DELAY_MS);
    }
}

void IRAM_ATTR Remote::wakeISR1() {
    instance->last_button_pressed = EVENT::DIRECTION_0;
    for (auto ii = 0; ii < BUTTON_READ_COUNT; ++ii) {
        if (digitalRead(BUTTON_0_PIN)) {
            instance->last_button_pressed = EVENT::DIRECTION_1;
            break;
        }
        delayMicroseconds(SMALL_DELAY_MS);
    }
}