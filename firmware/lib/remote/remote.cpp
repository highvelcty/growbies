#include "constants.h"
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
    pinMode(WAKE_PIN, INPUT);
    attachInterrupt(digitalPinToInterrupt(WAKE_PIN), Remote::wakeISR, RISING);
    pinMode(BUTTON_PIN, INPUT);


    // Initialize display
    display.begin();
    print_mass(8.8);
    // display.setFont(u8x8_font_chroma48medium8_r);
    // display.clearDisplay();
    // display.draw1x2String(0, 0, "Growbies");
}

bool Remote::handleButtons() {
    bool button_pressed = false;
    if (wake_flag) {
        button1_pressed = false;
        button2_pressed = false;
        button3_pressed = false;
        const unsigned long now = millis();
        if (now - last_button_time >= BUTTON_DEBOUNCE_MS) {
            button_pressed = true;
            last_button_time = now;
            const int adc_val = analogRead(BUTTON_PIN);
            if (adc_val < BUTTON_1_THRESHOLD) {
                button1_pressed = true;
            } else if (adc_val < BUTTON_2_THRESHOLD) {
                button2_pressed = true;
            } else {
                button3_pressed = true;
            }
        }
        // Clear the wake flag regardless, so we only process once per edge
        wake_flag = false;
    }
    return button_pressed;
}

void Remote::print_mass(const float mass) {
    char buf[8];
    dtostrf(mass, 6, 1, buf);
    this->display.setFont(u8x8_font_px437wyse700a_2x2_r);
    this->display.draw1x2String(0, 0, buf);
    this->display.setFont(u8x8_font_chroma48medium8_r);
    this->display.draw1x2String(15, 2, "g");
}

void Remote::service() {
    if (handleButtons()) {
        update_display();
    }
}

void Remote::update_display() {
    print_mass(3.3);

    // if (button1_pressed) {
    //     display.draw1x2String(0, 0, "Button 1");
    // }
    // else if (button2_pressed) {
    //     display.draw1x2String(0, 0, "Button 2");
    // }
    // else if (button3_pressed) {
    //     display.draw1x2String(0, 0, "Button 3");
    // }
}

// Lightweight ISR: set a flag and handle the rest in the main loop
void IRAM_ATTR Remote::wakeISR() {
    if (instance) {
        instance->wake_flag = true;
    }
}
