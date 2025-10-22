#include <new> // Required for placement new

#include "constants.h"
#include "flags.h"
#include <growbies.h>
#include <remote.h>
#include <math.h>
#include <nvm.h>
#include <sort.h>
#include <thermistor.h>

#if ARDUINO_ARCH_AVR
#include <util/atomic.h>
#endif

Growbies growbies;

Growbies::Growbies() = default;

void Growbies::begin() {
    pinMode(HX711_SCK_PIN, OUTPUT);
    for(SensorIdx_t sensor = 0; sensor < identify_store->payload()->mass_sensor_count; ++sensor) {
    #if ARDUINO_ARCH_AVR
        pinMode(get_HX711_dout_pin(sensor), INPUT_PULLUP);
    #elif ARDUINO_ARCH_ESP32
        gpio_config_t io_conf;
        io_conf.intr_type = GPIO_INTR_DISABLE;
        io_conf.mode = GPIO_MODE_INPUT;
        io_conf.pull_down_en = GPIO_PULLDOWN_DISABLE;
        io_conf.pull_up_en = GPIO_PULLUP_ENABLE;
        io_conf.pin_bit_mask = (1ULL << get_HX711_dout_pin(sensor));
        gpio_config(&io_conf);
    #endif
    }

#if POWER_CONTROL
    power_off();
#endif
}

void Growbies::execute(const PacketHdr* in_packet_hdr) {
    out_packet_hdr->id = in_packet_hdr->id;
    ErrorCode error = ERROR_NONE;

    if (in_packet_hdr->cmd == Cmd::LOOPBACK) {
        [[maybe_unused]] const auto resp = new (this->packet_buf) RespVoid;
        send_payload(resp, sizeof(*resp));
    }
    else if (in_packet_hdr->cmd == Cmd::GET_CALIBRATION) {
        auto* cmd = after<CmdGetCalibration>(in_packet_hdr);
        error = validate_packet(*in_packet_hdr, *cmd);
        if(!error) {
            auto* resp = new (this->packet_buf) RespGetCalibration();
            memcpy(&resp->calibration, calibration_store->view(), sizeof(resp->calibration));
            send_payload(resp, sizeof(*resp));
        }
    }
    else if (in_packet_hdr->cmd == Cmd::SET_CALIBRATION) {
        auto* cmd = after<CmdSetCalibration>(in_packet_hdr);
        error = validate_packet(*in_packet_hdr, *cmd);
        if (!error) {
            [[maybe_unused]] const auto resp = new (this->packet_buf) RespVoid;
            if (cmd->init) {
                calibration_store->init();
            }
            else {
                calibration_store->put(cmd->calibration);
            }

            send_payload(resp, sizeof(*resp));
        }
    }
    else if (in_packet_hdr->cmd == Cmd::GET_IDENTIFY) {
        auto* cmd = after<CmdGetIdentify>(in_packet_hdr);
        error = validate_packet(*in_packet_hdr, *cmd);
        if (!error) {
            auto* resp = new (this->packet_buf) RespGetIdentify;
            memcpy(&resp->identify, identify_store->view(), sizeof(resp->identify));
            send_payload(resp, sizeof(*resp));
        }
    }
    else if (in_packet_hdr->cmd == Cmd::SET_IDENTIFY) {
        auto* cmd = after<CmdSetIdentify>(in_packet_hdr);
        error = validate_packet(*in_packet_hdr, *cmd);
        if (!error) {
            [[maybe_unused]] const auto* resp = new (this->packet_buf) RespVoid;
            if (cmd->init) {
                identify_store->init();
            }
            else {
                bool do_flip = false;
                if (identify_store->payload()->flip != cmd->identify.payload.flip) {
                    Remote& remote = Remote::get();
                    remote.set_flip(cmd->identify.payload.flip);
                }
                identify_store->put(cmd->identify);
            }
            send_payload(resp, sizeof(*resp));
        }
    }
    else if (in_packet_hdr->cmd == Cmd::POWER_ON_HX711) {
        const auto* cmd = after<CmdPowerOnHx711>(in_packet_hdr);
        error = validate_packet(*in_packet_hdr, *cmd);
        if (!error) {
            power_on();
            [[maybe_unused]] const auto* resp = new (this->packet_buf) RespVoid;

            send_payload(resp, sizeof(*resp));
        }
    }
    else if (in_packet_hdr->cmd == Cmd::POWER_OFF_HX711) {
        const auto* cmd = after<CmdPowerOffHx711>(in_packet_hdr);
        error = validate_packet(*in_packet_hdr, *cmd);
        if (!error) {
            power_off();
            [[maybe_unused]] const auto* resp = new (this->packet_buf) RespVoid;
            send_payload(resp, sizeof(*resp));
        }
    }
    else if (in_packet_hdr->cmd == Cmd::READ) {
        auto* cmd = after<CmdRead>(in_packet_hdr);
        error = validate_packet(*in_packet_hdr, *cmd);
        if (!error) {
            measure(in_packet_hdr->id, cmd->times, cmd->raw);
        }
    }
    else if (in_packet_hdr->cmd == Cmd::GET_TARE) {
        auto* cmd = after<CmdGetTare>(in_packet_hdr);
        error = validate_packet(*in_packet_hdr, *cmd);
        if (!error) {
            auto* resp = new (this->packet_buf) RespGetTare;
            memcpy(&resp->tare, tare_store->view(), sizeof(resp->tare));
            send_payload(resp, sizeof(*resp));
        }
    }
    else if (in_packet_hdr->cmd == Cmd::SET_TARE) {
        auto* cmd = after<CmdSetTare>(in_packet_hdr);
        error = validate_packet(*in_packet_hdr, *cmd);
        if (!error) {
            [[maybe_unused]] const auto* resp = new (this->packet_buf) RespVoid;
            if (cmd->init) {
                tare_store->init();
            }
            else {
                tare_store->put(cmd->tare);
            }
            send_payload(resp, sizeof(*resp));
        }
    }
    else{
        error = ERROR_UNRECOGNIZED_COMMAND;
    }

    if (error) {
        [[maybe_unused]] auto* resp = new (this->packet_buf) RespError;
        resp->error = error;
        send_payload(resp, sizeof(*resp));
    }
}

void Growbies::measure(const uint8_t packet_hdr_id, const int times, const bool raw) {
    ErrorCode error = ERROR_NONE;
    auto resp = DataPoint(this->packet_buf, MAX_RESP_BYTES);
    this->out_packet_hdr->id = packet_hdr_id;

    if (!times) {
        error = ERROR_INVALID_PARAMETER;
    }
    if (!error) {
        error = Growbies::get_datapoint(&resp, times, raw);
    }
    if (error) {
        auto* resp_error = new (this->packet_buf) RespError;
        resp_error->error = error;
        send_payload(resp_error, sizeof(*resp_error));
    }
    else {
        send_payload(&resp, resp.get_size());
    }
}

void Growbies::power_off() {
    digitalWrite(HX711_SCK_PIN, HIGH);
    delayMicroseconds(HX711_POWER_DELAY);
}

void Growbies::power_on() {
    digitalWrite(HX711_SCK_PIN, LOW);
    delayMicroseconds(HX711_POWER_DELAY);
}

void Growbies::median_avg_filter(float **iteration_sensor_sample,
                                      const int times, const EndpointType endpoint_type,
                                      const float thresh, DataPoint* datapoint) {
    int sample_idx;
    float median;
    float samples[times];
    SensorIdx_t sensor_count;
    const Identify1* ident = identify_store->payload();

    if (endpoint_type == EP_MASS_SENSOR) {
        sensor_count = ident->mass_sensor_count;
    }
    else if (endpoint_type == EP_TEMPERATURE_SENSORS) {
        sensor_count = ident->temperature_sensor_count;
    }
    else {
        assert(0 && "Invalid endpoint type");
    }

    int error_counts[sensor_count];
    memset(error_counts, 0, sizeof(error_counts));

    // Filter and average
    for (SensorIdx_t sensor_idx = 0; sensor_idx < sensor_count; ++sensor_idx) {

        for (sample_idx = 0; sample_idx < times; ++sample_idx) {
            samples[sample_idx] = iteration_sensor_sample[sample_idx][sensor_idx];
        }

        float sum = 0;
        int sum_count = 0;

        // Sort
        insertion_sort(samples, times);

        // Find median
        const int middle = times / 2;
        if (times % 2) {
            // Odd - simply take the middle number
            median = samples[middle];
        }
        else {
            // Even - average the middle two numbers
            median = (samples[middle - 1] + samples[middle]) / 2;
        }

        // Average samples that fall within a threshold
        for (sample_idx = 0; sample_idx < times; ++sample_idx) {
            const float sample = samples[sample_idx];
            if (abs(median - sample) <= thresh) {
                sum += sample;
                ++sum_count;
            }
            else {
                ++error_counts[sensor_idx];
            }
        }
        if (sum_count) {
            datapoint->add<float>(endpoint_type, sum / static_cast<float>(sum_count));
        }
    }

    // Zero fill until the last non-zero error count.
    const EndpointType filtered_samples_type =
        (endpoint_type == EP_MASS_SENSOR) ? EP_MASS_ERRORS
      : (endpoint_type == EP_TEMPERATURE_SENSORS) ? EP_TEMPERATURE_ERRORS
      : EP_UNKNOWN;  // default
    SensorIdx_t last_idx = 0;
    for (SensorIdx_t sensor_idx = 0; sensor_idx < sensor_count; ++sensor_idx) {
        if ( error_counts[sensor_idx] != 0) {
            last_idx = sensor_idx + 1;
        }
    }
    if (last_idx != 0) {
        for (SensorIdx_t sensor_idx = 0; sensor_idx < last_idx; ++sensor_idx) {
            datapoint->add<uint8_t>(filtered_samples_type, error_counts[sensor_idx]);
        }
    }
}

ErrorCode Growbies::sample_mass(float** iteration_mass_samples,
                                const int times,
                                const HX711Gain gain) {
    ErrorCode error = ERROR_NONE;
    for (int iteration = 0; iteration < times; ++iteration) {
        error = wait_hx711_ready(WAIT_READY_RETRIES, WAIT_READY_RETRY_DELAY_MS);
	    if (error) {
	        return error;
	    }
        shift_all_in(iteration_mass_samples[iteration], gain);
    }
    return error;
}

void Growbies::sample_temperature(float **iteration_temp_samples, const int times) {
    for (int iteration = 0; iteration < times; ++iteration) {
        for (uint16_t idx = 0; idx < identify_store->payload()->temperature_sensor_count; ++idx) {
        #if ARDUINO_ARCH_AVR
            iteration_temp_samples[iteration][idx] = \
                (static_cast<float>(analogRead(get_temperature_pin(idx))) / ADC_RESOLUTION)
                * THERMISTOR_SUPPLY_VOLTAGE;

        #elif ARDUINO_ARCH_ESP32
            iteration_temp_samples[iteration][idx] = \
                static_cast<float>(analogReadMilliVolts(get_temperature_pin(idx))) / 1000.0;
        #endif
        }
    }
}

ErrorCode Growbies::get_datapoint(DataPoint* datapoint,
                                  const int times, const bool raw,
                                  const HX711Gain gain) {
    SensorIdx_t sensor_idx;
    ErrorCode error = ERROR_NONE;
    const Calibration* cal = calibration_store->payload();
    const Identify1* ident = identify_store->payload();

    get_tare_datapoint(datapoint);

#if POWER_CONTROL
    power_on();
#endif
    error = get_mass_datapoint(datapoint, times, gain);
    if (error) {
        return error;
    }
    get_temperature_datapoint(datapoint, times);
#if POWER_CONTROL
    power_off();
#endif

     float mass = 0.0;
     float temperature = 0.0;

     auto* mass_ptr = datapoint->find_value<float>(EP_MASS_SENSOR);
     auto* temp_ptr = datapoint->find_value<float>(EP_TEMPERATURE_SENSORS);

    for (sensor_idx = 0; sensor_idx < ident->mass_sensor_count; ++sensor_idx) {
        if (!raw and temp_ptr != nullptr) {
            // mass/temperature compensation per sensor
            mass_ptr[sensor_idx] -= (
                (cal->mass_temperature_coeff[sensor_idx][0]
                * temp_ptr[get_temperature_sensor_idx(sensor_idx)])
                + cal->mass_temperature_coeff[sensor_idx][1]);
        }

        // Sum  mass
        mass += mass_ptr[sensor_idx];
    }
    if (!raw) {
        // Mass calibration and tare
        mass = ((mass * cal->mass_coeff[0]) + cal->mass_coeff[1]);
    }

    datapoint->add<float>(EP_MASS, mass);

    for (sensor_idx = 0; sensor_idx < ident->temperature_sensor_count; ++sensor_idx) {
        if (!raw) {
            temp_ptr[sensor_idx] = steinhart_hart(temp_ptr[sensor_idx]);
        }
        temperature += temp_ptr[sensor_idx];
    }
    temperature /= static_cast<float>(ident->temperature_sensor_count);
    datapoint->add<float>(EP_TEMPERATURE, temperature);

    return error;
}

ErrorCode Growbies::get_mass_datapoint(DataPoint* datapoint,
                                       const int times,
                                       const HX711Gain gain) {
    ErrorCode error = ERROR_NONE;

    // Allocate 2D arrays
    const auto iteration_mass_samples = static_cast<float **>(malloc(times * sizeof(float *)));
    for (int iteration = 0; iteration < times; ++iteration) {
        iteration_mass_samples[iteration] = \
            static_cast<float *>(malloc(identify_store->payload()->mass_sensor_count
                * sizeof(float)));
    }

    error = sample_mass(iteration_mass_samples, times, gain);;

    if (!error) {
        median_avg_filter(iteration_mass_samples,
                          times,
                          EP_MASS_SENSOR,
                          INVALID_MASS_SAMPLE_THRESHOLD_DAC,
                          datapoint);
    }

    for(int iteration = 0; iteration < times; ++iteration) {
        free(iteration_mass_samples[iteration]);
    }
    free(iteration_mass_samples);

    return error;
}

void Growbies::get_tare_datapoint(DataPoint* datapoint) {
    auto* values = tare_store->payload()->values;
    size_t last_idx = 0;

    // Find the index of the last non-NaN value
    for (size_t i = 0; i < TARE_COUNT; ++i) {
        if (!isnan(values[i])) {
            last_idx = i;
        }
    }

    // If all NaNs, last_idx will be 0 and isnan(values[0]) is true
    if (last_idx == 0 && isnan(values[0])) {
        return; // nothing to add
    }

    // Add all values up to last non-NaN
    for (size_t i = 0; i <= last_idx; ++i) {
        datapoint->add<float>(EP_TARE, values[i]);
    }
}

void Growbies::get_temperature_datapoint(DataPoint *datapoint,
                                         const int times) {
    const auto iteration_temp_samples = static_cast<float **>(malloc(times * sizeof(float *)));
    for (int iteration = 0; iteration < times; ++iteration) {
        iteration_temp_samples[iteration] = \
            static_cast<float *>(malloc(
                identify_store->payload()->temperature_sensor_count * sizeof(float)));
    }
    if (identify_store->payload()->temperature_sensor_count) {
        sample_temperature(iteration_temp_samples, times);
    }


    if (identify_store->payload()->temperature_sensor_count) {
        median_avg_filter(iteration_temp_samples,
                          times,
               EP_TEMPERATURE_SENSORS,
                    INVALID_TEMPERATURE_SAMPLE_THRESHOLD_DAC,
                          datapoint);
    }
    for(int iteration = 0; iteration < times; ++iteration) {
        free(iteration_temp_samples[iteration]);
    }
    free(iteration_temp_samples);
}

void Growbies::shift_all_in(float* sensor_sample, const HX711Gain gain) {
    uint32_t a_bit;
    SensorIdx_t sensor;
#if ARDUINO_ARCH_AVR
    uint8_t gpio_in_reg;
#elif ARDUINO_ARCH_ESP32
    uint32_t gpio_in_reg = 0;
#endif

    long long_data_points[identify_store->payload()->mass_sensor_count];
    memset(long_data_points, 0, sizeof(long_data_points));

#if ARDUINO_ARCH_AVR
    ATOMIC_BLOCK(ATOMIC_RESTORESTATE) {
#elif ARDUINO_ARCH_ESP32
    noInterrupts();
#endif
    // Read bit by bit in parallel. Most significant bit first.
    for (uint8_t ii = 0; ii < HX711_DAC_BITS; ++ii) {
            delayMicroseconds(HX711_BIT_BANG_DELAY);
            digitalWrite(HX711_SCK_PIN, HIGH);

        {
            // This is a time critical block
            delayMicroseconds(HX711_BIT_BANG_DELAY);
            #if ARDUINO_ARCH_AVR
                // Read pins 8-13
                gpio_in_reg = PINB;
            #elif ARDUINO_ARCH_ESP32
                gpio_in_reg = REG_READ(GPIO_IN_REG);
            #endif
                digitalWrite(HX711_SCK_PIN, LOW);
        }

            // This time intensive task needs to happen after pulling SCK low to not perturb time
            // sensitive section when SCK is high.
            for (sensor = 0; sensor < identify_store->payload()->mass_sensor_count; ++sensor) {
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

    for (sensor = 0; sensor < identify_store->payload()->mass_sensor_count; ++sensor) {
        if (long_data_points[sensor] & (1UL << (HX711_DAC_BITS - 1))) {
            long_data_points[sensor] |= (0xFFUL << HX711_DAC_BITS);
        }

        sensor_sample[sensor] = static_cast<float>(long_data_points[sensor]);
    }
}

ErrorCode Growbies::wait_hx711_ready(const int retries, const unsigned long delay_ms) {
	bool ready;
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
	    for (SensorIdx_t sensor = 0; sensor < identify_store->payload()->mass_sensor_count; ++sensor) {
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

int get_temperature_sensor_idx(const int mass_sensor_idx) {
    if (identify_store->payload()->temperature_sensor_count ==
        identify_store->payload()->mass_sensor_count) {
        return mass_sensor_idx;
    }
    return 0;
}

int get_temperature_pin(const int mass_sensor_idx) {
    if (identify_store->payload()->mass_sensor_count == 1) {
        return TEMPERATURE_PIN_0;
    }
#if HX711_PIN_CFG_0
    assert(false && "Unimplemented temperature pin mapping.");
#elif HX711_PIN_CFG_1
    switch (mass_sensor_idx) {
        case 0:
            return TEMPERATURE_PIN_0;
        case 1:
            return TEMPERATURE_PIN_1;
        case 2:
            return TEMPERATURE_PIN_2;
        default:
            assert(false && "Temperature pin out of range.");
    }
#endif
}