#include <new> // Required for placement new

// #include "esp_adc_cal.h"

#include "constants.h"
#include "flags.h"
#include <growbies.h>
#include <persistent_store.h>
#include <sort.h>
#include <thermistor.h>

#if ARDUINO_ARCH_AVR
#include <util/atomic.h>
#endif

// Growbies* growbies = new Growbies();

Growbies growbies;

Growbies::Growbies() = default;

void Growbies::begin() const {
    pinMode(HX711_SCK_PIN, OUTPUT);
    for(int sensor = 0; sensor < MASS_SENSOR_COUNT; ++sensor) {
    #if ARDUINO_ARCH_AVR
        pinMode(get_HX711_dout_pin(sensor), INPUT_PULLUP);
    #elif ARDUINO_ARCH_ESP32
        gpio_config_t io_conf;
        io_conf.intr_type = GPIO_INTR_DISABLE;
        io_conf.mode = GPIO_MODE_INPUT;
        io_conf.pull_down_en = GPIO_PULLDOWN_DISABLE;
        io_conf.pull_up_en = GPIO_PULLUP_ENABLE;
        io_conf.pin_bit_mask = (1ULL << DOUT_0_PIN);
        gpio_config(&io_conf);
    #endif
    }

#if POWER_CONTROL
    this->power_off();
#endif

    calibration_store->begin();
    identify_store->begin();
}

void Growbies::execute(const PacketHdr* packet_hdr) {
    if (packet_hdr->cmd == Cmd::LOOPBACK) {
        const auto resp = new (this->outbuf) RespVoid;
        resp->id = 1;
        send_packet(this->outbuf, sizeof(RespVoid));
    }
    else if (packet_hdr->cmd == Cmd::GET_DATAPOINT) {
        const auto* cmd = reinterpret_cast<CmdGetDatapoint *>(slip_buf->buf);
        if (validate_packet(*cmd)) {
            exec_read(packet_hdr);
         }
    }
    else if (packet_hdr->cmd == Cmd::GET_CALIBRATION) {
        const auto* cmd = reinterpret_cast<CmdGetCalibration *>(slip_buf->buf);
        if(validate_packet(*cmd)) {
            auto* resp = new (this->outbuf) RespGetCalibration;
            calibration_store->get(resp->calibration);
            send_packet(*this->outbuf, sizeof(*resp));
        }
    }
    else if (packet_hdr->cmd == Cmd::SET_CALIBRATION) {
        auto* cmd = reinterpret_cast<CmdSetCalibration *>(slip_buf->buf);
        if(validate_packet(*cmd)) {
            new (this->outbuf) RespVoid;
            calibration_store->put(cmd->calibration);
            send_packet(*this->outbuf, sizeof(RespVoid));
        }
    }
    else if (packet_hdr->cmd == Cmd::POWER_ON_HX711) {
        const auto cmd = reinterpret_cast<CmdPowerOnHx711 *>(slip_buf->buf);
        if(validate_packet(*cmd)) {
            this->power_on();
            new (this->outbuf) RespVoid;

            send_packet(*this->outbuf, sizeof(RespVoid));
        }
    }
    else if (packet_hdr->cmd == Cmd::POWER_OFF_HX711) {
        const auto cmd = reinterpret_cast<CmdPowerOffHx711 *>(slip_buf->buf);
        if(validate_packet(*cmd)) {
            this->power_off();
            new (this->outbuf) RespVoid;
            send_packet(*this->outbuf, sizeof(RespVoid));
        }
    }
    else if (packet_hdr->cmd == Cmd::GET_IDENTIFY) {
        const auto* cmd = reinterpret_cast<CmdGetIdentify *>(slip_buf->buf);
        if(validate_packet(*cmd)) {
            auto* resp = new (this->outbuf) RespGetIdentify;
            resp->id = packet_hdr->id;
            identify_store->get(resp->identify);
            send_packet(*this->outbuf, sizeof(*resp));
        }
    }
    else if (packet_hdr->cmd == Cmd::SET_IDENTIFY) {
        const auto* cmd = reinterpret_cast<CmdSetIdentify *>(slip_buf->buf);
        if(validate_packet(*cmd)) {
            auto* resp = new (this->outbuf) RespVoid;
            resp->id = packet_hdr->id;
            identify_store->put(cmd->identify);
            send_packet(*this->outbuf, sizeof(*resp));
        }
    }

    else{
        auto resp = new (this->outbuf) RespError;
        resp->error = ERROR_UNRECOGNIZED_COMMAND;
        resp->id = packet_hdr->id;
        send_packet(resp, sizeof(RespError));
    }
}

#if BUTTERFLY
void Growbies::exec_read(const PacketHdr* hdr) {
    auto* resp = new (this->outbuf) RespDataPoint;
    RespError resp_error;
    this->get_datapoint(resp, resp_error, BUTTERFLY_SAMPLES_PER_DATAPOINT);
    if (resp_error.error) {
        if (hdr != nullptr) {
            resp_error.id = hdr->id;
        }
        send_packet(resp_error, sizeof(resp_error));
    }
    else {
        send_packet(*this->outbuf, sizeof(*resp));
    }
}
#endif

void Growbies::power_off() {
    digitalWrite(HX711_SCK_PIN, HIGH);
    delayMicroseconds(HX711_POWER_DELAY);
}

void Growbies::power_on() {
    digitalWrite(HX711_SCK_PIN, LOW);
    delayMicroseconds(HX711_POWER_DELAY);
}

void Growbies::median_avg_filter(float **iteration_sensor_sample,
                                  const int iterations, const int sensors,
                                  const float thresh, float *out,
                                  RespError& resp_error) {
    int iteration;
    float median;

    float samples[iterations];

    // Filter and average
    for (int sensor_idx = 0; sensor_idx < sensors; ++sensor_idx) {
        for (iteration = 0; iteration < iterations; ++iteration) {
            samples[iteration] = iteration_sensor_sample[iteration][sensor_idx];
        }

        float sum = 0;
        int sum_count = 0;

        // Sort
        insertion_sort(samples, iterations);

        // Find median
        const int middle = iterations / 2;
        if (iterations % 2) {
            // Odd - simply take the middle number
            median = samples[middle];
        }
        else {
            // Even - average the middle two numbers
            median = (samples[middle - 1] + samples[middle]) / 2;
        }

        // Average samples that fall within a threshold
        int error_count = 0;
        for (iteration = 0; iteration < iterations; ++iteration) {
            const float sample = samples[iteration];
            if (abs(median - sample) <= thresh) {
                sum += sample;
                ++sum_count;
            }
            else {
                ++error_count;
            }
        }
        if (error_count >= min(2, iterations)) {
            resp_error.error = ERROR_OUT_OF_THRESHOLD_SAMPLE;
        }
        out[sensor_idx] = sum / sum_count;
    }
}


void Growbies::sample_mass(float** iteration_mass_samples,
                                const int times,
                                const HX711Gain gain,
                                RespError& resp_error) {
	for (int iteration = 0; iteration < times; ++iteration) {
        resp_error.error = wait_hx711_ready(WAIT_READY_RETRIES, WAIT_READY_RETRY_DELAY_MS);
	    if (resp_error.error) {
	        return;
	    }
        shift_all_in(iteration_mass_samples[iteration], gain);
    }
}

void Growbies::sample_temperature(float **iteration_temp_samples, const int times) {
    for (int iteration = 0; iteration < times; ++iteration) {
        for (int sensor_idx = 0; sensor_idx < TEMPERATURE_SENSOR_COUNT; ++sensor_idx) {
        #if ARDUINO_ARCH_AVR
            iteration_temp_samples[iteration][sensor_idx] = \
                (static_cast<float>(analogRead(get_temperature_pin(sensor_idx))) / ADC_RESOLUTION)
                * THERMISTOR_SUPPLY_VOLTAGE;

        #elif ARDUINO_ARCH_ESP32
            iteration_temp_samples[iteration][sensor_idx] = \
                static_cast<float>(analogReadMilliVolts(get_temperature_pin(sensor_idx))) / 1000.0;
        #endif

        }
    }
}

void Growbies::get_datapoint(RespDataPoint *resp, RespError& resp_error,
                             const byte times,
                             const bool raw, const HX711Gain gain) const {
    int iteration;
    int sensor_idx;
    Calibration calibration_struct{};
    calibration_store->get(calibration_struct);

    // Allocate 2D arrays
    const auto iteration_mass_samples = static_cast<float **>(malloc(times * sizeof(float *)));
    for (iteration = 0; iteration < times; ++iteration) {
        iteration_mass_samples[iteration] = \
            static_cast<float *>(malloc(MASS_SENSOR_COUNT * sizeof(float)));
    }
    const auto iteration_temp_samples = static_cast<float **>(malloc(times * sizeof(float *)));
    for (iteration = 0; iteration < times; ++iteration) {
        iteration_temp_samples[iteration] = \
            static_cast<float *>(malloc(TEMPERATURE_SENSOR_COUNT * sizeof(float)));
    }

#if POWER_CONTROL
	this->power_on();
#endif
    sample_mass(iteration_mass_samples, times, gain, resp_error);;
    if (resp_error.error) {
        return;
    }
#if TEMPERATURE_SENSOR_COUNT
    sample_temperature(iteration_temp_samples, times);
#endif
#if POWER_CONTROL
	this->power_off();
#endif

    median_avg_filter(iteration_mass_samples,
                      times,
                      MASS_SENSOR_COUNT,
                      INVALID_MASS_SAMPLE_THRESHOLD_DAC,
                      reinterpret_cast<float *>(&resp->mass_sensor),
                      resp_error);
    if (resp_error.error) {
        return;
    }

#if TEMPERATURE_SENSOR_COUNT
    median_avg_filter(iteration_temp_samples,
              times,
                      TEMPERATURE_SENSOR_COUNT,
                      INVALID_MASS_SAMPLE_THRESHOLD_DAC,
                      reinterpret_cast<float *>(&resp->temperature_sensor),
                      resp_error);
    if (resp_error.error) {
        return;
    }
#endif

    resp->mass = 0;
    resp->temperature = 0;

    for (sensor_idx = 0; sensor_idx < MASS_SENSOR_COUNT; ++sensor_idx) {
        if (!raw) {
            // mass/temperature compensation per sensor
            resp->mass_sensor[sensor_idx] -= (
                (calibration_struct.mass_temperature_coeff[sensor_idx][0]
                * resp->temperature_sensor[get_temperature_sensor_idx(sensor_idx)])
                + calibration_struct.mass_temperature_coeff[sensor_idx][1]);
        }

        // Sum  mass
        resp->mass += resp->mass_sensor[sensor_idx];
    }
    if (!raw) {
        // Mass calibration and tare
        resp->mass = ((resp->mass * calibration_struct.mass_coeff[0])
                      + calibration_struct.mass_coeff[1])
                     - calibration_struct.tare[this->tare_idx];
    }

    for (sensor_idx = 0; sensor_idx < TEMPERATURE_SENSOR_COUNT; ++sensor_idx) {
        if (!raw) {
            resp->temperature_sensor[sensor_idx] = \
                steinhart_hart(resp->temperature_sensor[sensor_idx]);
        }
        resp->temperature += resp->temperature_sensor[sensor_idx];
     }
    resp->temperature /= TEMPERATURE_SENSOR_COUNT;

    // Free 2D arrays
    for(iteration = 0; iteration < times; ++iteration) {
        free(iteration_mass_samples[iteration]);
    }
    free(iteration_mass_samples);
    for(iteration = 0; iteration < times; ++iteration) {
        free(iteration_temp_samples[iteration]);
    }
    free(iteration_temp_samples);
}

void Growbies::shift_all_in(float sensor_sample[MASS_SENSOR_COUNT], const HX711Gain gain) {
    uint32_t a_bit;
    uint8_t sensor;
#if ARDUINO_ARCH_AVR
    uint8_t gpio_in_reg;
#elif ARDUINO_ARCH_ESP32
    uint32_t gpio_in_reg = 0;
#endif

    long long_data_points[MASS_SENSOR_COUNT] = {0};

#if ARDUINO_ARCH_AVR
    ATOMIC_BLOCK(ATOMIC_RESTORESTATE) {
#elif ARDUINO_ARCH_ESP32
    noInterrupts();
#endif
        for (uint8_t ii = 0; ii < HX711_DAC_BITS; ++ii) {
            delayMicroseconds(HX711_BIT_BANG_DELAY);
            // Read in a byte, most significant bit first
            digitalWrite(HX711_SCK_PIN, HIGH);

            // This is a time critical block
            delayMicroseconds(HX711_BIT_BANG_DELAY);
        #if ARDUINO_ARCH_AVR
            // Read pins 8-13
            gpio_in_reg = PINB;
        #elif ARDUINO_ARCH_ESP32
            gpio_in_reg = REG_READ(GPIO_IN_REG);
        #endif
            digitalWrite(HX711_SCK_PIN, LOW);

            // This time intensive task needs to happen after pulling SCK low to not perturb time
            // sensitive section when SCK is high.
            for (sensor = 0; sensor < MASS_SENSOR_COUNT; ++sensor) {
                a_bit = static_cast<bool>(gpio_in_reg & get_HX711_dout_port_bit(sensor));
                long_data_points[sensor] |= (a_bit << (HX711_DAC_BITS - 1 - ii));
            }
        }

        // Set the gain. HX711 has two channels, "A" and "B".
        delayMicroseconds(HX711_BIT_BANG_DELAY);
        switch ( gain ) {
            case HX711_GAIN_32: // Channel "B"
                digitalWrite(HX711_SCK_PIN, HIGH);
                delayMicroseconds(HX711_BIT_BANG_DELAY);
                digitalWrite(HX711_SCK_PIN, LOW);
                delayMicroseconds(HX711_BIT_BANG_DELAY);
            case HX711_GAIN_64: // Channel "A"
                digitalWrite(HX711_SCK_PIN, HIGH);
                delayMicroseconds(HX711_BIT_BANG_DELAY);
                digitalWrite(HX711_SCK_PIN, LOW);
                delayMicroseconds(HX711_BIT_BANG_DELAY);
            case HX711_GAIN_128: // Channel "A"
                digitalWrite(HX711_SCK_PIN, HIGH);
                delayMicroseconds(HX711_BIT_BANG_DELAY);
                digitalWrite(HX711_SCK_PIN, LOW);
                delayMicroseconds(HX711_BIT_BANG_DELAY);
        }
#if ARDUINO_ARCH_AVR
    }
#elif ARDUINO_ARCH_ESP32
    interrupts();
#endif

    for (sensor = 0; sensor < MASS_SENSOR_COUNT; ++sensor) {
        if (long_data_points[sensor] & (1UL << (HX711_DAC_BITS - 1))) {
            long_data_points[sensor] |= (0xFFUL << HX711_DAC_BITS);
        }

        sensor_sample[sensor] = (float)long_data_points[sensor];
    }
}

ErrorCode Growbies::wait_hx711_ready(const int retries, const unsigned long delay_ms) {
	bool ready;
	int sensor;
#if ARDUINO_ARCH_AVR
	uint8_t gpio_in_reg;
#elif ARDUINO_ARCH_ESP32
    uint32_t gpio_in_reg;
#endif
    bool all_ready;
    ErrorCode error = ERROR_NONE;
	int retry_count = 0;

	do {
        // Check for readiness from all sensors
        // Read pins 8-13
    #if ARDUINO_ARCH_AVR
        gpio_in_reg = PINB;
    #elif ARDUINO_ARCH_ESP32
        gpio_in_reg = REG_READ(GPIO_IN_REG);
    #endif
        all_ready = true;
	    for (sensor = 0; sensor < MASS_SENSOR_COUNT; ++sensor) {
	        ready = static_cast<bool>(gpio_in_reg & get_HX711_dout_port_bit(sensor)) == LOW;
	        all_ready &= ready;
        }

        if (!all_ready){
            ++retry_count;
            delay(delay_ms);
        }

	} while ((retry_count <= retries) && (!all_ready));

	if (!all_ready){
	    error |= ERROR_HX711_NOT_READY;
	}

	return error;
}
