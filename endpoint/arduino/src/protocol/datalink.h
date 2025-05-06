#ifndef datalink_h
#define datalink_h

#include <Arduino.h>

#define SLIP_BUF_ALLOC_BYTES 64

enum Slip {
    SLIP_END = 0xC0,
    SLIP_ESC = 0xDB,
    SLIP_ESC_END = 0xDC,
    SLIP_ESC_ESC = 0xDD
};

class SlipBuf {
    public:
        uint8_t buf[SLIP_BUF_ALLOC_BYTES];
        uint8_t* buf_ptr = buf;
        bool within_escape = false;

        uint16_t buf_len();
        void reset();
};

bool recv_slip(byte a_byte);
void send_slip(byte* buf, unsigned int buf_len);
void send_slip_end();

extern SlipBuf* slip_buf;

#endif /* datalink_h */