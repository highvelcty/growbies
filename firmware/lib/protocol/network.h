#ifndef network_h
#define network_h

#include <Arduino.h>
#include "command.h"
#include "crc.h"
#include "datalink.h"

#define PACKET_CRC_BYTES 2
#define PACKET_MIN_BYTES sizeof(PacketHdr) + PACKET_CRC_BYTES

PacketHdr* recv_packet();


template <typename PacketType>
void send_packet(PacketType& structure, size_t packet_size = 0) {
    byte* ptr = (byte*)&structure;
    uint16_t crc = crc_ccitt16(ptr, packet_size);
    send_slip(ptr, packet_size);
    send_slip((byte*)&crc, sizeof(crc));
    send_slip_end();
    // This is crucial for asynchronous communication. Without this, garbage is found on the serial
    // port at host connection time.
    Serial.flush();
};

#endif /* network_h */