#pragma once

#include "protocol/command.h"

namespace transport {

constexpr int SLIP_BUF_ALLOC_BYTES = 512;
constexpr int PACKET_CRC_BYTES = 2;
constexpr int PACKET_MIN_BYTES = sizeof(PacketHdr) + PACKET_CRC_BYTES;
//                                                 escape                     END PAD
constexpr int MAX_RESP_BYTES = (SLIP_BUF_ALLOC_BYTES / 2) - PACKET_CRC_BYTES - 1 - 2 \
                                - sizeof(PacketHdr);

enum Slip {
    SLIP_END = 0xC0,
    SLIP_ESC = 0xDB,
    SLIP_ESC_END = 0xDC,
    SLIP_ESC_ESC = 0xDD
};

class SlipBuf {
public:
    uint8_t buf[SLIP_BUF_ALLOC_BYTES]{};
    uint8_t* ptr = buf;
    bool within_escape = false;
    uint16_t len() const;
    void reset();
};

class UsbDatalink {
public:
    SlipBuf& get_in_buf() { return in_buf; }
    uint8_t* get_out_buf() { return out_buf; }

    ErrorCode recv_slip();
    static void send_slip(const uint8_t* buf, unsigned int buf_len);
    static void send_slip_end();
    void reset() { in_buf.reset(); };

private:
    SlipBuf in_buf;
    uint8_t out_buf[SLIP_BUF_ALLOC_BYTES] = {};

};

class UsbNetwork {
public:
    SlipBuf& get_in_buf() { return datalink.get_in_buf(); }
    uint8_t* get_out_buf() { return datalink.get_out_buf(); }

    ErrorCode recv_packet();

    static void send_packet(const void* ptr, size_t packet_size);
    void reset() {  datalink.reset(); }

private:
    UsbDatalink datalink;
};

class UsbTransport {
public:

    PacketHdr* get_cmd_hdr() const { return cmd_hdr; }
    uint8_t* get_cmd_buf() const { return cmd_buf; }
    uint8_t* get_resp_buf() const { return resp_buf; }

    // This technique allows introspection of output packet size without passing the
    // type explicitly. The template and the unused parameter allow this to happen.
    template <typename RespType>
    void send_resp(const RespType* _, const size_t num_bytes,
        const bool async = false) const {
        if (async) {
            resp_hdr->id = 0;
        }
        else {
            resp_hdr->id = cmd_hdr->id;
        }
        resp_hdr->resp    = RespType::TYPE;
        resp_hdr->version = RespType::VERSION;
        UsbNetwork::send_packet(resp_hdr, sizeof(*resp_hdr) + num_bytes);
    }

    ErrorCode recv_cmd();
    void reset() { network.reset(); }
    ErrorCode validate_cmd(int exp_num_bytes);

private:
    UsbNetwork network;

    PacketHdr* cmd_hdr = reinterpret_cast<PacketHdr *>(network.get_in_buf().buf);
    uint8_t* cmd_buf = network.get_in_buf().buf + sizeof(PacketHdr);
    PacketHdr* resp_hdr = reinterpret_cast<PacketHdr *>(network.get_out_buf());
    uint8_t* resp_buf = network.get_out_buf() + sizeof(PacketHdr);
};

} // transport