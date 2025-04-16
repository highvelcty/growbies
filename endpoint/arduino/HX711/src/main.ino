#include "constants.h"
#include "growbies.h"
// #include "protocol/datalink.h"
// #include "protocol/network.h"


void setup() {
    slip_buf->reset();

    // 2025_04_01: Observed skipped characters at 115200 with mini pro 3v3. Suspect this is due
    //   to the 8MHz clock providing nearest baudrates of 115942 or 114285, whereas the closest
    //   baudrates for 8MHz for 57600 baud is 57554 or 57971.
    Serial.begin(57600);
    growbies->begin();
}


void loop() {
    PacketHdr* packet_hdr;

    while (!Serial.available()){
        delay(MAIN_POLLING_LOOP_INTERVAL_MS);
    }
    if (recv_slip(Serial.read())){
        packet_hdr = recv_packet();
        if (packet_hdr != NULL) {
            growbies->execute(packet_hdr);
        }
        slip_buf->reset();
    }
}

