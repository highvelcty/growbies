#include "constants.h"
#include "growbies.h"

#include <U8x8lib.h>

U8X8_SSD1306_128X32_UNIVISION_HW_I2C u8x8(U8X8_PIN_NONE, A5_HW_I2C_SCL, A4_HW_I2C_SDA);

void setup() {
    slip_buf->reset();

    // 2025_04_01: Observed skipped characters at 115200 with mini pro 3v3. Suspect this is due
    //   to the 8MHz clock providing nearest baudrates of 115942 or 114285, whereas the closest
    //   baudrates for 8MHz for 57600 baud is 57554 or 57971.
    Serial.begin(57600);
    u8x8.begin();
    growbies->begin();
}


void loop() {

    u8x8.setContrast(16);
    u8x8.setFont(u8x8_font_px437wyse700a_2x2_r);
    u8x8.draw1x2String(0,0,"1234.5 ");
    u8x8.setFont(u8x8_font_chroma48medium8_r);
    u8x8.draw1x2String(13,2, "g");

    PacketHdr* packet_hdr;

    while (!Serial.available()){
        delay(MAIN_POLLING_LOOP_INTERVAL_MS);
        continue;
    }

    if (recv_slip(Serial.read())){
        packet_hdr = recv_packet();
        if (packet_hdr != NULL) {
            digitalWrite(LED_BUILTIN, HIGH);
            growbies->execute(packet_hdr);
        }
        slip_buf->reset();
    }
}

