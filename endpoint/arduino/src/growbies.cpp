#include <float.h>
#include <new> // Required for placement new

#include "constants.h"
#include "flags.h"
#include "growbies.h"
#include "lib/display.h"
#include "lib/persistent_store.h"
#include "utils/sort.h"

//#if HAS_ATOMIC_BLOCK
#if ARDUINO_ARCH_AVR
#include <util/atomic.h>
#endif

Growbies* growbies = new Growbies();

Growbies::Growbies() {}

void Growbies::begin(){
    pinMode(HX711_SCK_PIN, OUTPUT);
    for(int sensor = 0; sensor < MASS_SENSOR_COUNT; ++sensor) {
    #if ARDUINO_ARCH_AVR
        pinMode(get_HX711_dout_pin(sensor), INPUT_PULLUP);
    #elif ARDUINO_ARCH_ESP32
        gpio_config_t io_conf;
        io_conf.intr_type = GPIO_INTR_DISABLE; // Disable interrupts
        io_conf.mode = GPIO_MODE_INPUT; // Set mode to input
        io_conf.pull_down_en = GPIO_PULLDOWN_DISABLE; // Disable pull-down resistors
        io_conf.pull_up_en = GPIO_PULLUP_ENABLE; // Enable pull-up resistors (optional, depending on your circuit)
        io_conf.pin_bit_mask = (1ULL << DOUT_0_PIN);
        gpio_config(&io_conf);
    #endif
    }

#if POWER_CONTROL
    this->power_off();
#endif
}

void Growbies::execute(PacketHdr* packet_hdr) {
    if (packet_hdr->type == CMD_LOOPBACK) {
        send_slip(slip_buf->buf, slip_buf->buf_len());
        send_slip_end();
    }
    else if (packet_hdr->type == CMD_READ_DAC) {
        CmdReadDAC* cmd = (CmdReadDAC*)slip_buf->buf;
        if (validate_packet(*cmd)) {
            // This constructs at location
            new (this->outbuf) RespMultiDataPoint;
            MultiDataPoint* multi_data_points = \
                new (this->outbuf + sizeof(RespMultiDataPoint)) MultiDataPoint;
            this->read_units(multi_data_points, cmd->times, UNIT_DAC);
            send_packet(*this->outbuf,
                        sizeof(RespMultiDataPoint) + (sizeof(MultiDataPoint)*MASS_SENSOR_COUNT));
         }
    }
    else if (packet_hdr->type == CMD_READ_UNITS) {
        CmdReadUnits* cmd = (CmdReadUnits*)slip_buf->buf;
        if (validate_packet(*cmd)) {
            // This constructs at location
            new (this->outbuf) RespMultiDataPoint;
            MultiDataPoint* multi_data_points = \
                new (this->outbuf + sizeof(RespMultiDataPoint)) MultiDataPoint;
            this->read_units(multi_data_points, cmd->times);
            send_packet(*this->outbuf,
                        sizeof(RespMultiDataPoint) + (sizeof(MultiDataPoint)*MASS_SENSOR_COUNT));
         }
    }
    else if (packet_hdr->type == CMD_GET_CALIBRATION) {
        CmdGetCalibration* cmd = (CmdGetCalibration*)slip_buf->buf;
        if(validate_packet(*cmd)) {
            RespGetCalibration* resp = new (this->outbuf) RespGetCalibration;
            calibration_store->get(resp->calibration);
            send_packet(*this->outbuf, sizeof(RespGetCalibration));
        }
    }
    else if (packet_hdr->type == CMD_SET_CALIBRATION) {
        CmdSetCalibration* cmd = (CmdSetCalibration*)slip_buf->buf;
        if(validate_packet(*cmd)) {
            new (this->outbuf) RespVoid;
            calibration_store->put(cmd->calibration);
            send_packet(*this->outbuf, sizeof(RespVoid));
        }
    }
    else if (packet_hdr->type == CMD_POWER_ON_HX711) {
        CmdPowerOnHx711* cmd = (CmdPowerOnHx711*)slip_buf->buf;
        if(validate_packet(*cmd)) {
            this->power_on();
            new (this->outbuf) RespVoid;

            send_packet(*this->outbuf, sizeof(RespVoid));
        }
    }
    else if (packet_hdr->type == CMD_POWER_OFF_HX711) {
        CmdPowerOffHx711* cmd = (CmdPowerOffHx711*)slip_buf->buf;
        if(validate_packet(*cmd)) {
            this->power_off();
            new (this->outbuf) RespVoid;
            send_packet(*this->outbuf, sizeof(RespVoid));
        }
    }
    else if (packet_hdr->type == CMD_TEST) {
        BaseCmd* cmd = (BaseCmd*)slip_buf->buf;
        if(validate_packet(*cmd)) {
            RespLong* resp = new (this->outbuf) RespLong;
            resp->data = 0;
            send_packet(*this->outbuf, sizeof(RespLong));
        }
    }
    else{
        RespError* resp = new (this->outbuf) RespError;
        resp->error = ERROR_UNRECOGNIZED_COMMAND;
        send_packet(resp, sizeof(RespError));
    }
}

void Growbies::set_gain(HX711Gain gain) {
    this->read_dac(this->data_points, 1, gain);
}

void Growbies::power_off() {
    digitalWrite(HX711_SCK_PIN, HIGH);
    delayMicroseconds(HX711_POWER_DELAY);
}

void Growbies::power_on() {
    digitalWrite(HX711_SCK_PIN, LOW);
    delayMicroseconds(HX711_POWER_DELAY);
}

void Growbies::sample(DataPoint* data_points, const HX711Gain gain) {
    this->wait_all_ready_retry(data_points, WAIT_READY_RETRIES, WAIT_READY_RETRY_DELAY_MS);
    this->shift_all_in(data_points, gain);
}

void Growbies::read_dac(DataPoint* data_points, const byte times, const HX711Gain gain) {
    // Reads data from the chip the requested number of times. The median is found and then all
    // samples that are within the median +/- a DAC threshold are averaged and returned.

    float median;
    byte middle;
    float sample;
    int sample_idx;
    int sensor;
    byte sensor_sample;
    float sum;
    int sum_count;

    float sensor_samples[MASS_SENSOR_COUNT][times] = {0.0};

    // Initialize
    memset(data_points, 0, sizeof(DataPoint) * MASS_SENSOR_COUNT);

	// Read samples
#if POWER_CONTROL
	this->power_on();
#endif
	for (sample_idx = 0; sample_idx < times; ++sample_idx) {
        this->sample(data_points, gain);
        for (sensor = 0; sensor < MASS_SENSOR_COUNT; ++sensor){
            sensor_samples[sensor][sample_idx] = data_points[sensor].data;
        }
	}
#if POWER_CONTROL
	this->power_off();
#endif

    // Filter and average
    for (sensor = 0; sensor < MASS_SENSOR_COUNT; ++sensor) {
        sum = 0;
        sum_count = 0;

        // Sort
        insertion_sort(sensor_samples[sensor], times);

        // Find median
        middle = times / 2;
        if (times % 2) {
            // Odd - simply take the middle number
            median = sensor_samples[sensor][middle];
        }
        else {
            // Even - average the middle two numbers
            median = (sensor_samples[sensor][middle - 1] + sensor_samples[sensor][middle]) / 2;
        }

        // Average samples that fall within a threshold
        for (sensor_sample = 0; sensor_sample < times; ++sensor_sample) {
            sample = sensor_samples[sensor][sensor_sample];
            if (abs(median - sample) <= this->default_threshold) {
                sum += sample;
                ++sum_count;
            }
            else {
                ++data_points[sensor].error_count;
            }
        }
        data_points[sensor].data = sum / sum_count;
    }
}

void Growbies::read_units(MultiDataPoint* multi_data_points, const byte times, const Unit units){
    int sensor_idx;
    CalibrationStruct calibration_struct;
    calibration_store->get(calibration_struct);

#if TEMPERATURE_LOAD_CELL
    for (sensor_idx = 0; sensor_idx < MASS_SENSOR_COUNT; ++sensor_idx) {
        multi_data_points[sensor_idx].temperature.data = analogRead(TEMPERATURE_ANALOG_PIN);
    }
#endif

    this->read_dac(this->data_points, times);
    for (sensor_idx = 0; sensor_idx < MASS_SENSOR_COUNT; ++sensor_idx) {
        // meyere: this copy could be eliminated
        multi_data_points[sensor_idx].mass.data = this->data_points[sensor_idx].data;
        multi_data_points[sensor_idx].mass.error_count = this->data_points[sensor_idx].error_count;
        multi_data_points[sensor_idx].mass.ready = this->data_points[sensor_idx].ready;
    }

    // Units
    if (units & UNIT_GRAMS) {
        for (sensor_idx = 0; sensor_idx < MASS_SENSOR_COUNT; ++sensor_idx) {
            multi_data_points[sensor_idx].mass.data = \
                (((multi_data_points[sensor_idx].mass.data
                   * calibration_struct.mass_coefficient[sensor_idx][0])
                  + calibration_struct.mass_coefficient[sensor_idx][1])
                 - calibration_struct.tare[sensor_idx][this->tare_idx]);

        #if TEMPERATURE_LOAD_CELL
            multi_data_points[sensor_idx].temperature.data = \
                ((calibration_struct.temperature_coefficient[sensor_idx][0]
                  * multi_data_points[sensor_idx].temperature.data)
                 + calibration_struct.temperature_coefficient[sensor_idx][1]);
        #endif
        }
    }

//    display->print_mass(total_mass);
}


void Growbies::shift_all_in(DataPoint* data_points, const HX711Gain gain) {
    //
    //
    uint32_t a_bit;
    uint8_t ii;
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
        for (ii = 0; ii < HX711_DAC_BITS; ++ii) {
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

            // This time intensive task needs to happen after pulling SCK low so as to not perturb
            // time sensitive section when SCK is high.
            for (sensor = 0; sensor < MASS_SENSOR_COUNT; ++sensor) {
                a_bit = (bool)(gpio_in_reg & get_HX711_dout_port_bit(sensor));
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

        data_points[sensor].data = (float)long_data_points[sensor];
    }
}

bool Growbies::wait_all_ready_retry(DataPoint* data_points,
    const int retries, const unsigned long delay_ms)
{
	bool all_ready = true;
	bool ready;
	int sensor;
#if ARDUINO_ARCH_AVR
	uint8_t gpio_in_reg;
#elif ARDUINO_ARCH_ESP32
    uint32_t gpio_in_reg;
#endif
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
	        ready = (bool)(gpio_in_reg & get_HX711_dout_port_bit(sensor)) == LOW;
	        data_points[sensor].ready = ready;
	        all_ready &= ready;
        }

        if (!all_ready){
            ++retry_count;
            delay(delay_ms);
        }

	} while ((retry_count <= retries) && (!all_ready));

	return all_ready;
}
