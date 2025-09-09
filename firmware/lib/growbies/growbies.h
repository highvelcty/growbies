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

        static void begin();

        void execute(const PacketHdr* in_packet_hdr);
#if BUTTERFLY
        void exec_read(int packet_id = 0);
#endif

    private:
        uint8_t tare_idx = 0;
        uint8_t outbuf[SLIP_BUF_ALLOC_BYTES] = {};
        PacketHdr* out_packet_hdr = reinterpret_cast<PacketHdr *>(outbuf);
        uint8_t* packet_buf = outbuf + sizeof(PacketHdr);

        static void power_off();

        static void power_on();

        static ErrorCode median_avg_filter(float **iteration_sensor_sample,
                                       int iterations, EndpointType endpoint_type,
                                       float thresh, DataPoint* data_point);
        static ErrorCode sample_mass(float** iteration_mass_samples, int times, HX711Gain gain);
        static ErrorCode sample_temperature(float** iteration_temp_samples, int times);
        ErrorCode get_datapoint(DataPoint* resp,
                           byte times, bool raw = false,
                           HX711Gain gain = HX711_GAIN_128) const;

        static void shift_all_in(float sensor_sample[MASS_SENSOR_COUNT], HX711Gain gain);

        static ErrorCode wait_hx711_ready(int retries, unsigned long delay_ms);

        void send_payload(size_t num_bytes);
};

// Used to cast a payload structure after a packet header.
template <typename T, typename U>
constexpr T* after(U* base) {
    return reinterpret_cast<T*>(
        reinterpret_cast<uint8_t*>(base) + sizeof(U)
    );
}

template <typename PacketType>
ErrorCode validate_packet(const PacketHdr& packet_hdr, const PacketType& packet) {
    if (slip_buf->buf_len() >= sizeof(packet_hdr) + sizeof(packet)) {
        return ErrorCode::ERROR_NONE;
    }
    return ErrorCode::ERROR_CMD_DESERIALIZATION_BUFFER_UNDERFLOW;
}

/**
 * Application global
 */
extern Growbies growbies;


#endif /* growbies_h */
