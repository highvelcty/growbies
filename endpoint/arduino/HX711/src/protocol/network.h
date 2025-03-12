#ifndef network_h
#define network_h

#include <Arduino.h>
#include "datalink.h"

#define PACKET_CHECKSUM_BYTES 2
#define PACKET_MIN_BYTES sizeof(PacketHdr) + PACKET_CHECKSUM_BYTES

struct PacketHdr {
    uint16_t type;

    PacketHdr(uint16_t type_){
        this->type = type_;
    };
};

PacketHdr* recv_packet();


template <typename T>
void send_packet(T& structure) {
    byte* ptr = (byte*)&structure;
    uint16_t checksum = 0;

    for (uint16_t byte_idx = 0; byte_idx < sizeof(T); ++byte_idx){
        checksum += ptr[byte_idx];
    }

    send_slip(ptr, sizeof(structure));
    send_slip((byte*)&checksum, sizeof(checksum));
    send_slip_end();
};

#endif /* network_h */