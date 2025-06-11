 #ifndef growbies_h
#define growbies_h

#include "constants.h"
#include "protocol/command.h"
#include "protocol/network.h"

const int HX711_DAC_BITS = 24;

enum HX711SerialDelay {
    HX711_READY_TO_SCK_RISE_MICROSECONDS = 3,
    HX711_SCK_RISE_TO_DOUT_READY_MICROSECONDS = 3,
    HX711_POWER_OFF_DELAY = 64 * 2 // The specification says 64uS with SCK high will power down.
                                   // Double this to be sure.
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
        float scale = 1.0;

        byte* outbuf;
        MassDataPoint* mass_data_points;
        long* offset;

		float get_scale();
		void power_on();
		void power_off();
		bool read();
		void read_median_filter_avg(const byte times = default_times);
		void read_with_units(const byte times = default_times);
		void set_offset(long* offset);
		void set_scale(float scale);
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