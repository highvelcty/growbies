#include "datalink.h"

uint16_t SlipBuf::buf_len() const {
    return this->buf_ptr - this->buf;
}

void SlipBuf::reset() {
    this->buf_ptr = this->buf;
    this->within_escape = false;
}


bool recv_slip(const byte a_byte) {
    if (a_byte == SLIP_END){
        return true;
    }
    else if (a_byte == SLIP_ESC){
        slip_buf->within_escape = true;
    }
    else{
        if (slip_buf->within_escape){
            slip_buf->within_escape = false;
            if (a_byte == SLIP_ESC_END){
                *slip_buf->buf_ptr++ = SLIP_END;
            }
            else if (a_byte == SLIP_ESC_ESC){
                *slip_buf->buf_ptr++ = SLIP_ESC;
            }
        }
        else{
            *slip_buf->buf_ptr++ = a_byte;
        }
    }
    return false;
}


void send_slip(const byte* buf, unsigned int buf_len) {
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


void send_slip_end(){
    Serial.write(SLIP_END);
}

SlipBuf* slip_buf = new SlipBuf();
