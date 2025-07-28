#include "network.h"

PacketHdr* recv_packet() {
    PacketHdr* packet_hdr = NULL;
    uint16_t buf_len = slip_buf->buf_len();
    uint16_t calc_checksum = 0;
    uint16_t checksum = 0;

    if (buf_len >= PACKET_MIN_BYTES) {
        packet_hdr = (PacketHdr*)&slip_buf->buf[0];
        checksum = *(uint16_t*)&slip_buf->buf[buf_len - PACKET_CHECKSUM_BYTES];
        for (uint16_t byte_idx = 0; byte_idx < buf_len - PACKET_CHECKSUM_BYTES; ++byte_idx){
            calc_checksum += slip_buf->buf[byte_idx];
        }

        if (calc_checksum == checksum) {
            return packet_hdr;
        }
        else {
            return NULL;
        }
    }
    else {
        return NULL;
    }
}
