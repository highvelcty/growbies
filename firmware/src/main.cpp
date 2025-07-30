#include "constants.h"
#include "flags.h"
#include <growbies.h>

#if FEATURE_DISPLAY
#include <display.h>
#endif

#if BUTTERFLY
#include "esp_sleep.h"
#include <command.h>
#endif



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
    growbies.begin();
#if FEATURE_DISPLAY
    display->begin();
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

#if BUTTERFLY
void loop() {
    // Read data
    // Send data
    // Wait for response
    // Sleep
}
#else
void loop() {
    while (!Serial.available()){
        delay(MAIN_POLLING_LOOP_INTERVAL_MS);
    }

    if (recv_slip(Serial.read())){
        const PacketHdr *packet_hdr = recv_packet();
        if (packet_hdr != nullptr) {
            growbies.execute(packet_hdr);
        }
        slip_buf->reset();
    }
}
#endif
