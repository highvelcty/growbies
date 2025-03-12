#ifndef growbies_h
#define growbies_h

#include "HX711.h"
#include "protocol/network.h"

class Growbies : protected HX711 {
    public:
        void execute(PacketHdr* packet_hdr);
        void begin(byte channel = 0, byte gain = 128);
    protected:
        bool wait_and_get_units(uint8_t times, long& data);
        bool wait_and_read_average(uint8_t times, long& data);
    private:
        byte channel = 0;
};

extern Growbies* growbies;


#endif /* growbies_h */