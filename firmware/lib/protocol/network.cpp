#include "network.h"

PacketHdr* recv_packet() {
    PacketHdr* packet_hdr = nullptr;
    uint16_t buf_len = slip_buf->buf_len();
    uint16_t calc_crc = 0;
    uint16_t crc = 0;


    if (buf_len >= PACKET_MIN_BYTES) {
        packet_hdr = (PacketHdr*)&slip_buf->buf[0];
        crc = *(uint16_t*)&slip_buf->buf[buf_len - PACKET_CRC_BYTES];
        calc_crc = crc_ccitt16(slip_buf->buf, buf_len - PACKET_CRC_BYTES);
        if (calc_crc == crc) {
            return packet_hdr;
        }
        else {
            return nullptr;
        }
    }
    else {
        return nullptr;
    }
}
