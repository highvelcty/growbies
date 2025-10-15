#include "constants.h"
#include "flags.h"
#include <network.h>
#include <growbies.h>
#include <usb.h>

#if FEATURE_DISPLAY
#include <display.h>
#include <buttons.h>
#endif

#if BUTTERFLY
#if ARDUINO_ARCH_ESP32
#include "esp_sleep.h"
#endif
#include <command.h>
#endif



#if FEATURE_LED
#include "lib/led.h"
#endif

void setup() {
    slip_buf->reset();
    // 2025_04_01: Observed skipped characters at 115200 with mini pro 3v3. Suspect this is due
    //   to the 8MHz clock providing nearest baudrates of 115942 or 114285, whereas the closest
    //   baudrates for 8MHz for 57600 baud is 57554 or 57971.
    Serial.begin(57600);
    growbies.begin();
#if FEATURE_DISPLAY
    display->begin();
    display->print_mass(8.8);
    display->set_power_save(true);
#endif

#if LED_INSTALLED
    pinMode(LED_PIN, OUTPUT);
#if FEATURE_LED
    led_sign_on_msg();
#else
    digitalWrite(LED_PIN, LOW);
#endif
#endif

	enable_delay_wake();

}

#if BUTTERFLY
void loop() {
    growbies.exec_read();

    unsigned long startt = millis();
    do {
        if (!Serial.available()) {
            delay(MAIN_POLLING_LOOP_INTERVAL_MS);
        }
        else {
            // Receiving serial data resets the sleep timeout
            startt = millis();
            if (recv_slip(Serial.read())) {
                const PacketHdr *packet_hdr = recv_packet();
                if (packet_hdr != nullptr) {
                    growbies.execute(packet_hdr);
                    // Restart stay awake timer.
                    startt = millis();
                }
                slip_buf->reset();
            }
        }
    } while (millis() - startt < WAIT_FOR_CMD_MILLIS);

    delay(DEEP_SLEEP_MILLIS);
}
#else
void loop() {
    while (!Serial.available()){
        delay(MAIN_POLLING_LOOP_INTERVAL_MS);
    }

    if (recv_slip(Serial.read())) {
        const PacketHdr *packet_hdr = recv_packet();
        if (packet_hdr != nullptr) {
            growbies.execute(packet_hdr);
        }
        slip_buf->reset();
    }
}
#endif
