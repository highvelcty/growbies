#include <Arduino.h>

#include <network.h>
#include "crc.h"
#include "datalink.h"

PacketHdr* recv_packet() {
    PacketHdr* packet_hdr = nullptr;
    const uint16_t buf_len = slip_buf->buf_len();

    if (buf_len >= PACKET_MIN_BYTES) {
        uint16_t crc = 0;
        uint16_t calc_crc = 0;
        packet_hdr = (PacketHdr*)&slip_buf->buf[0];
        crc = *(uint16_t*)&slip_buf->buf[buf_len - PACKET_CRC_BYTES];
        calc_crc = crc_ccitt16(slip_buf->buf, buf_len - PACKET_CRC_BYTES);
        if (calc_crc == crc) {
            return packet_hdr;
        }
    }
    return packet_hdr;
}

void send_packet(const void* ptr, const size_t packet_size) {
    const auto byte_ptr = static_cast<const uint8_t*>(ptr);
    uint16_t crc = crc_ccitt16(byte_ptr, packet_size);
    send_slip(byte_ptr, packet_size);
    send_slip(reinterpret_cast<byte *>(&crc), sizeof(crc));
    send_slip_end();
    // This is crucial for asynchronous communication. Without this, garbage is found on the serial
    // port at host connection time.
    Serial.flush();
};
