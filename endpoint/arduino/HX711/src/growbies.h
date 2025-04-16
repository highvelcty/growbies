#ifndef growbies_h
#define growbies_h

#include "HX711.h"
#include "command.h"
#include "constants.h"
#include "protocol/network.h"

class Growbies : protected HX711 {
    public:
        void execute(PacketHdr* packet_hdr);
        void begin(byte channel = 0, byte gain = 128);
    private:
        byte channel = 0;

		// Reads data from the chip the requested number of times. The median is found and then all
		// samples that are within the median +/- a 24 DAC threshold are averaged and returned.
		long read_median_filter_avg(byte times = 3, int threshold = 10000);

};

extern Growbies* growbies;


#endif /* growbies_h */