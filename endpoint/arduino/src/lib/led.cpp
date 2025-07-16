#include "led.h"
#if FEATURE_LED
#include <Arduino.h>
#include "constants.h"

void led_sign_on_msg() {
    for(uint8_t ii = 0; ii < 6; ++ii){
        digitalWrite(LED_PIN, !(ii % 2));
        delay(33);
    }
}

#endif /* LED */