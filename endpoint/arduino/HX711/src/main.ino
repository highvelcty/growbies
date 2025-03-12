#include "constants.h"
#include "growbies.h"
#include "protocol/datalink.h"
#include "protocol/network.h"


void setup() {
    slip_buf->reset();
    Serial.begin(115200);
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


