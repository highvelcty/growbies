#ifndef growbies_h
#define growbies_h

#include "protocol/command.h"

const int HX711_DAC_BITS = 24;

enum HX711SerialDelay {
    HX711_BIT_BANG_DELAY = 3,

    // The specification says 64uS with SCK high will power down. Double this to be sure.
    //
    // Additionally, this is used for power on delay to allow for settling of in rush current
    HX711_POWER_DELAY = 64 * 2
};

class Growbies {
    public:
        const int sensor_count;

        Growbies(int sensor_count = 4);
        void begin();

        void execute(PacketHdr* packet_hdr);


    private:
        const int static default_threshold = 10000;
        const byte static default_times = 5;
        const byte static get_tare_times = 15;

        byte outbuf[512] = {};

		float get_scale();
		void set_scale(float scale);
		void get_tare(RespGetTare* resp_get_tare);
		void set_tare();
		void power_off();
		void power_on();
		void sample(MassDataPoint* mass_data_points);
		void read_dac(MassDataPoint* mass_data_points, const byte times = default_times);
		void read_grams(MassDataPoint* mass_data_points, const byte times = default_times);
		void shift_all_in(MassDataPoint* mass_data_points);
		bool wait_all_ready_retry(MassDataPoint* mass_data_points,
		    const int retries, const unsigned long delay_ms);
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
