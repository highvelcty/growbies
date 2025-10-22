#include <Arduino.h>      // for pinMode, attachInterrupt, detachInterrupt, digitalPinToInterrupt
#include "esp_sleep.h"    // for esp_sleep_enable_ext0_wakeup(), esp_deep_sleep_start()

#include "buttons.h"
#include "constants.h"
#include <display.h>

void enable_deep_sleep_wake() {
    // See https://forum.seeedstudio.com/t/external-wakeup-from-deep-sleep-on-xiao-esp32c3/267532/6
    detachInterrupt(digitalPinToInterrupt(BUTTON_0_PIN)); // disable digital domain
    pinMode(BUTTON_0_PIN, INPUT_PULLDOWN);
    esp_deep_sleep_enable_gpio_wakeup(1ull << WAKE_GPIO, ESP_GPIO_WAKEUP_GPIO_HIGH);
}


void enable_light_sleep_wake() {
    detachInterrupt(digitalPinToInterrupt(BUTTON_0_PIN)); // ensure clean state
    pinMode(BUTTON_0_PIN, INPUT_PULLDOWN);
    attachInterrupt(digitalPinToInterrupt(BUTTON_0_PIN), on_wake_line, RISING);
}

void on_wake_line() {
    display->print_mass(3.14);
}