#include "constants.h"
#include "growbies.h"
#include "lib/display.h"

#if FEATURE_LED
#include "lib/led.h"
#endif

void setup() {
    slip_buf->reset();
//
//     // 2025_04_01: Observed skipped characters at 115200 with mini pro 3v3. Suspect this is due
//     //   to the 8MHz clock providing nearest baudrates of 115942 or 114285, whereas the closest
//     //   baudrates for 8MHz for 57600 baud is 57554 or 57971.
    Serial.begin(57600);
    growbies->begin();
#if ARDUINO_ARCH_AVR
    display->begin();
#elif ARDUINO_ARCH_ESP32
    // not implemented
#endif

#if LED_INSTALLED
    pinMode(LED_PIN, OUTPUT);
#if FEATURE_LED
    led_sign_on_msg();
#else
    digitalWrite(LED_PIN, LOW);
#endif
#endif
}

void loop() {
    PacketHdr* packet_hdr;

    while (!Serial.available()){
        delay(MAIN_POLLING_LOOP_INTERVAL_MS);
        continue;
    }

    if (recv_slip(Serial.read())){
        packet_hdr = recv_packet();
        if (packet_hdr != NULL) {
            growbies->execute(packet_hdr);
        }
        slip_buf->reset();
    }
}

