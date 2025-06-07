 #ifndef growbies_h
#define growbies_h

#include "command.h"
#include "constants.h"
#include "protocol/network.h"

const int HX711_DAC_BITS = 24;

enum HX711SerialDelay {
    HX711_READY_TO_SCK_RISE_MICROSECONDS = 1,
    HX711_SCK_RISE_TO_DOUT_READY_MICROSECONDS = 1,
    HX711_SCK_HIGH_MICROSECONDS = 1,

    // 2025_04_22: From experimentation on the arduino mini 3v3, this is critical to reliable
    // transfer. PIND did not work well when set to 3 or less and digitalRread did not work well
    // when set to 6 or less.
    HX711_SCK_LOW_MICROSECONDS = 10
};

class Growbies {
    public:
        const int sensor_count;
        byte gain;


        Growbies(int sensor_count = 4, byte gain = 128);
        ~Growbies();

        void execute(PacketHdr* packet_hdr);
        void begin();

    private:
        // Output buffer and symbol mapping
        const int static outbuf_size = 512;
        const int static default_threshold = 10000;
        const byte static default_times = 3;

//        byte* outbuf;
        byte static outbuf[outbuf_size];
        MassDataPoint* mass_data_points;
        long* offset;
        float* scale;
		void power_on();
		void power_off();
		bool read();

		// Reads data from the chip the requested number of times. The median is found and then all
		// samples that are within the median +/- a DAC threshold are averaged and returned.
		void read_median_filter_avg(const byte times = default_times);
		void read_with_units(const byte times = default_times);
		void set_offset(long* offset);
		void set_scale(float* scale);
		void shift_all_in();
		void tare(const byte times = default_times);
		bool wait_all_ready_retry(const int retries, const unsigned long delay_ms);
};

template <typename PacketType>
bool check_and_respond_to_deserialization_underflow(const PacketType& packet) {
    if (slip_buf->buf_len() >= sizeof(packet)) {
        return true;
    }
    else{
        RespError resp;
        resp.error = ERROR_CMD_DESERIALIZATION_BUFFER_UNDERFLOW;
        send_packet(resp);
        return false;
    }
};

template <typename PacketType>
bool validate_packet(const PacketType& packet) {
    bool result;
    result = check_and_respond_to_deserialization_underflow(packet);
    return result;
}

extern Growbies* growbies;


#endif /* growbies_h */