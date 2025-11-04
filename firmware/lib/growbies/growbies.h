#ifndef growbies_h
#define growbies_h

#include "constants.h"
#include "command.h"
#include "datalink.h"
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
        void measure(uint8_t packet_hdr_id = 0, int times = DEFAULT_SAMPLES_PER_DATAPOINT,
                       bool raw = false);

    private:
        uint8_t tare_idx = 0;
        uint8_t outbuf[SLIP_OUT_BUF_ALLOC_BYTES] = {};
        PacketHdr* out_packet_hdr = reinterpret_cast<PacketHdr *>(outbuf);
        uint8_t* packet_buf = outbuf + sizeof(PacketHdr);

        static void power_off();

        static void power_on();

        static void median_avg_filter(float **iteration_sensor_sample,
                                       int times, EndpointType endpoint_type,
                                       float thresh, DataPoint* datapoint);
        static ErrorCode sample_mass(float** iteration_mass_samples, int times, HX711Gain gain);
        static void sample_temperature(float** iteration_temp_samples, int times);

        static ErrorCode get_datapoint(DataPoint* datapoint,
                                       int times, bool raw = false,
                                       HX711Gain gain = HX711_GAIN_128);

        static ErrorCode get_mass_datapoint(DataPoint* datapoint,
                                            int times,
                                            HX711Gain gain);
        static void get_tare_datapoint(DataPoint* datapoint);
        static void get_temperature_datapoint(DataPoint *datapoint, int times);
        static void shift_all_in(float* sensor_sample, HX711Gain gain);

        static ErrorCode wait_hx711_ready(int retries, unsigned long delay_ms);

    template <typename RespType>
    void send_payload(const RespType* resp, const size_t num_bytes) const {
        out_packet_hdr->resp    = RespType::TYPE;
        out_packet_hdr->version = RespType::VERSION;
        send_packet(out_packet_hdr, sizeof(*out_packet_hdr) + num_bytes);
    }
};

// Used to cast a payload structure after a packet header.
// Non-const base
template <typename T, typename U>
constexpr T* after(U* base) {
    return reinterpret_cast<T*>(
        reinterpret_cast<uint8_t*>(base) + sizeof(U)
    );
}
// Const base
template <typename T, typename U>
constexpr const T* after(const U* base) {
    return reinterpret_cast<const T*>(
        reinterpret_cast<const uint8_t*>(base) + sizeof(U)
    );
}

template <typename PacketType>
ErrorCode validate_packet([[maybe_unused]] const PacketHdr& packet_hdr,
                          [[maybe_unused]] const PacketType& packet) {
    if (slip_buf->buf_len() >= sizeof(packet_hdr) + sizeof(packet)) {
        return ERROR_NONE;
    }
    return ERROR_CMD_DESERIALIZATION_BUFFER_UNDERFLOW;
}

int get_temperature_sensor_idx(int mass_sensor_idx);
int get_temperature_pin(int mass_sensor_idx);


/**
 * Application global
 */
extern Growbies growbies;


#endif /* growbies_h */
