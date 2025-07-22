#ifndef growbies_h
#define growbies_h

#include "defines.h"
#include "flags.h"
#include "protocol/command.h"

const int HX711_DAC_BITS = 24;

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

typedef enum Unit : uint16_t {
    // Bitfield
    UNIT_GRAMS       = 0x0001,
    UNIT_DAC         = 0x0002,
    UNIT_FAHRENHEIT  = 0x0004,
    UNIT_CELSIUS     = 0x0008,
} Units;


class Growbies {
    public:
        Growbies();
        void begin();

        void execute(PacketHdr* packet_hdr);

    private:
        const int static default_threshold = 10000;
        const byte static default_times = 5;
        const byte static default_tare_times = 15;
        uint8_t tare_idx = 0;

        byte outbuf[512] = {};
        DataPoint data_points[MASS_SENSOR_COUNT];

        void power_off();
		void power_on();
        void sample(DataPoint* data_points, const HX711Gain gain = HX711_GAIN_128);
		void read_dac(DataPoint* data_points, const byte times = default_times,
            const HX711Gain gain = HX711_GAIN_128);
		void read_units(MultiDataPoint* data_points, const byte times = default_times,
            Unit units = (Unit)(UNIT_GRAMS | UNIT_FAHRENHEIT));
        void set_gain(HX711Gain gain);
		void shift_all_in(DataPoint* data_points, const HX711Gain gain = HX711_GAIN_128);
		bool wait_all_ready_retry(DataPoint* data_points, const int retries,
            const unsigned long delay_ms);
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
