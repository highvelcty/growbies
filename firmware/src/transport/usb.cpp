#include <Arduino.h>
#include <cstring>
#include "usb.h"
#include "utils/crc.h"

namespace transport {

uint16_t SlipBuf::len() const {
    return this->ptr - this->buf;
}

void SlipBuf::reset() {
    this->ptr = this->buf;
    this->within_escape = false;
}

ErrorCode UsbDatalink::recv_slip() {
    while (Serial.available()) {
        const uint8_t a_byte = Serial.read();
        if (a_byte == SLIP_END){
            return ERROR_NONE;
        }
        else if (a_byte == SLIP_ESC){
            in_buf.within_escape = true;
        }
        else{
            if (in_buf.within_escape){
                in_buf.within_escape = false;
                if (a_byte == SLIP_ESC_END){
                    *in_buf.ptr++ = SLIP_END;
                }
                else if (a_byte == SLIP_ESC_ESC){
                    *in_buf.ptr++ = SLIP_ESC;
                }
            }
            else{
                *in_buf.ptr++ = a_byte;
            }
        }
    }
    return ERROR_INCOMPLETE_SLIP_FRAME;
}


void UsbDatalink::send_slip(const byte* buf, const unsigned int buf_len) {
    for (unsigned int idx = 0; idx < buf_len; ++idx){
        if (buf[idx] == SLIP_END){
            Serial.write(SLIP_ESC);
            Serial.write(SLIP_ESC_END);
        }
        else if (buf[idx] == SLIP_ESC){
            Serial.write(SLIP_ESC);
            Serial.write(SLIP_ESC_ESC);
        }
        else {
            Serial.write(buf[idx]);
        }
    }
}


void UsbDatalink::send_slip_end(){
    Serial.write(SLIP_END);
}


    ErrorCode UsbNetwork::recv_packet() {
    auto error = datalink.recv_slip();

    if (!error) {
        auto& in_buf = datalink.get_in_buf();
        const uint16_t buf_len = in_buf.len();

        if (buf_len >= PACKET_MIN_BYTES) {
            uint16_t crc = 0;
            std::memcpy(&crc, &in_buf.buf[buf_len - PACKET_CRC_BYTES], sizeof(crc));

            const uint16_t calc_crc = crc_ccitt16(in_buf.buf, buf_len - PACKET_CRC_BYTES);

            if (calc_crc == crc) {
                error = ERROR_NONE;
            } else {
                error = ERROR_INVALID_SLIP_CRC;
            }
        } else {
            error = ERROR_CMD_HDR_DESERIALIZATION_UNDERFLOW;
        }
    }

    return error;
}


void UsbNetwork::send_packet(const void* ptr, const size_t packet_size) {
    const auto byte_ptr = static_cast<const uint8_t*>(ptr);
    uint16_t crc = crc_ccitt16(byte_ptr, packet_size);
    UsbDatalink::send_slip(byte_ptr, packet_size);
    UsbDatalink::send_slip(reinterpret_cast<byte *>(&crc), sizeof(crc));
    UsbDatalink::send_slip_end();
    // This is crucial for asynchronous communication. Without this, garbage is found on the serial
    // port at host connection time.
    Serial.flush();
}


ErrorCode UsbTransport::recv_cmd() {
    auto error = network.recv_packet();

    if (!error) {
        // Execute command
        error = ERROR_NONE;
    }

    if (error != ERROR_INCOMPLETE_SLIP_FRAME) {
        reset();
    }

    return error;
}

ErrorCode UsbTransport::validate_cmd(const int exp_num_bytes) {
    if (exp_num_bytes > network.get_in_buf().len() - sizeof(PacketHdr)) {
        return ERROR_CMD_DESERIALIZATION_BUFFER_UNDERFLOW;
    }
    return ERROR_NONE;
    }

} // transport