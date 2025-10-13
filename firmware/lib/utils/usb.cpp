#include "usb.h"

#if ARDUINO_ARCH_AVR
bool is_usb_plugged_in() {
    return true;
}
#elif ARDUINO_ARCH_ESP32
#include <esp32-hal-gpio.h>

bool is_usb_plugged_in() {
    return digitalRead(USB_VBUS_PIN) == HIGH;
}
#endif
