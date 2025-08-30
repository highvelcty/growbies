#ifndef growbies_h
#define growbies_h

#include <Arduino.h>

#include "constants.h"
#include "flags.h"
#include "command.h"
#include "network.h"

constexpr int HX711_DAC_BITS = 24;

enum HX711SerialDelay {
    HX711_BIT_BANG_DELAY = 3,

    // The specification says 64uS with SCK high will power down. Double this to be sure.
    //
    // Additionally, this is used for power on delay to allow for settling of in rush current
    HX711_POWER_DELAY = 64 * 2
};

typedef enum HX711Gain {
    HX711_GAIN_128 = 128,
    HX711_GAIN_64 = 64,
    HX711_GAIN_32 = 32
} HX711Gain;

class Growbies {
    public:
        Growbies();
        void begin() const;

        void execute(const PacketHdr* packet_hdr);
#if BUTTERFLY
        void exec_read();
#endif

    private:
        uint8_t tare_idx = 0;
        byte outbuf[SLIP_BUF_ALLOC_BYTES] = {};

        static void power_off();

        static void power_on();

        static Error median_avg_filter(float **iteration_sensor_sample,
                                       int rows, int cols, float thresh, float* out);
        Error sample_mass(float** iteration_mass_samples, int times, HX711Gain gain);

        static Error sample_temperature(float** iteration_temp_samples, int times);
        void get_datapoint(RespDataPoint* resp, byte times, bool raw = false,
                        HX711Gain gain = HX711_GAIN_128);

        static void shift_all_in(float sensor_sample[MASS_SENSOR_COUNT], HX711Gain gain);

        static Error wait_hx711_ready(int retries, unsigned long delay_ms);
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
    return check_and_respond_to_deserialization_underflow(packet);
}

/**
 * Application global
 */
extern Growbies growbies;


#endif /* growbies_h */
