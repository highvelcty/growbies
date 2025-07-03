#include <assert.h>
#include <EEPROM.h>
#include <float.h>
#include <new> // Required for placement new
#include <util/atomic.h>

#include "constants.h"
#include "flags.h"
#include "growbies.h"
#include "lib/eeprom.h"
#include "lib/display.h"
#include "utils/sort.h"

Growbies* growbies = new Growbies();

Growbies::Growbies() {
    assert(sizeof(EEPROMStruct) < EEPROM_BYTES);
}

void Growbies::begin(){
    pinMode(ARDUINO_HX711_SCK, OUTPUT);
    for(int sensor = 0; sensor < MASS_SENSOR_COUNT; ++sensor) {
        pinMode(get_HX711_dout_pin(sensor), INPUT_PULLUP);
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
    else if (packet_hdr->type == CMD_SET_PHASE) {
        CmdSetPhase* cmd = (CmdSetPhase*)slip_buf->buf;
        if (validate_packet(*cmd)) {
            new (this->outbuf) RespVoid;
            if (cmd->phase == PHASE_A) {
                this->set_phase_a();
            }
            else {
                this->set_phase_b();
            }
            send_packet(*this->outbuf, sizeof(RespVoid));
         }
    }
    else if (packet_hdr->type == CMD_GET_EEPROM) {
        CmdGetEEPROM* cmd = (CmdGetEEPROM*)slip_buf->buf;
        if(validate_packet(*cmd)) {
            RespGetEEPROM* resp = new (this->outbuf) RespGetEEPROM;
            this->get_eeprom(resp->eeprom);
            send_packet(*this->outbuf, sizeof(RespGetEEPROM));
        }
    }
    else if (packet_hdr->type == CDM_SET_EEPROM) {
        CmdSetEEPROM* cmd = (CmdSetEEPROM*)slip_buf->buf;
        if(validate_packet(*cmd)) {
            new (this->outbuf) RespVoid;
            this->set_eeprom(cmd->eeprom);
            send_packet(*this->outbuf, sizeof(RespVoid));
        }
    }
    else{
        RespError* resp = new (this->outbuf) RespError;
        resp->error = ERROR_UNRECOGNIZED_COMMAND;
        send_packet(resp, sizeof(RespError));
    }
}

void Growbies::set_phase_a() {
    digitalWrite(ARDUINO_EXCITATION_A, LOW);
    digitalWrite(ARDUINO_EXCITATION_B, HIGH);
    delay(SET_PHASE_DELAY_MS);
}

void Growbies::set_phase_b() {
    digitalWrite(ARDUINO_EXCITATION_A, HIGH);
    digitalWrite(ARDUINO_EXCITATION_B, LOW);
    delay(SET_PHASE_DELAY_MS);
}

void Growbies::get_eeprom(EEPROMStruct& eeprom) {
    EEPROM.get(0, eeprom);
}

void Growbies::set_eeprom(EEPROMStruct& eeprom) {
    EEPROM.put(0, eeprom);
}

void Growbies::set_gain(HX711Gain gain) {
    this->read_dac(this->data_points, 1, gain);
}

void Growbies::power_off() {
    digitalWrite(ARDUINO_HX711_SCK, HIGH);
    delayMicroseconds(HX711_POWER_DELAY);
}

void Growbies::power_on() {
    digitalWrite(ARDUINO_HX711_SCK, LOW);
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
    EEPROMStruct eeprom_struct;
    EEPROM.get(0, eeprom_struct);

#if TEMPERATURE_CHANNEL_B
    this->set_gain(HX711_GAIN_32);
    this->read_dac(this->data_points, times, HX711_GAIN_32);
    for (sensor_idx = 0; sensor_idx < MASS_SENSOR_COUNT; ++sensor_idx) {
        multi_data_points[sensor_idx].temperature.data = \
        this->data_points[sensor_idx].data;
    }
#endif

#if TEMPERATURE_ANALOG_INPUT
    for (sensor_idx = 0; sensor_idx < MASS_SENSOR_COUNT; ++sensor_idx) {
        multi_data_points[sensor_idx].temperature.data = analogRead(TEMPERATURE_ANALOG_PIN);
    }
#endif

#if TEMPERATURE_CHANNEL_B
    this->set_gain(HX711_GAIN_128);
#endif

    this->read_dac(this->data_points, times);
    for (sensor_idx = 0; sensor_idx < MASS_SENSOR_COUNT; ++sensor_idx) {
        multi_data_points[sensor_idx].mass.data = this->data_points[sensor_idx].data;
    }

    // Units
    if (units & UNIT_GRAMS) {
        for (sensor_idx = 0; sensor_idx < MASS_SENSOR_COUNT; ++sensor_idx) {
            multi_data_points[sensor_idx].mass.data = \
                (((multi_data_points[sensor_idx].mass.data
                   * eeprom_struct.mass_coefficient[sensor_idx][0])
                  + eeprom_struct.mass_coefficient[sensor_idx][1])
                 - eeprom_struct.tare[sensor_idx][this->tare_idx]);

        #if TEMPERATURE_ANALOG_INPUT
            multi_data_points[sensor_idx].temperature.data = \
                ((eeprom_struct.temperature_coefficient[sensor_idx][0]
                  * multi_data_points[sensor_idx].temperature.data)
                 + eeprom_struct.temperature_coefficient[sensor_idx][1]);
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
    uint8_t pinb;

    long long_data_points[MASS_SENSOR_COUNT] = {0};

    ATOMIC_BLOCK(ATOMIC_RESTORESTATE) {
        for (ii = 0; ii < HX711_DAC_BITS; ++ii) {
            delayMicroseconds(HX711_BIT_BANG_DELAY);
            // Read in a byte, most significant bit first
            digitalWrite(ARDUINO_HX711_SCK, HIGH);

            // This is a time critical block
            delayMicroseconds(HX711_BIT_BANG_DELAY);
            // Read pins 8-13
            pinb = PINB;
            digitalWrite(ARDUINO_HX711_SCK, LOW);

            // This time intensive task needs to happen after pulling SCK low so as to not perturb
            // time sensitive section when SCK is high.
            for (sensor = 0; sensor < MASS_SENSOR_COUNT; ++sensor) {
                a_bit = (bool)(pinb & get_HX711_dout_port_bit(sensor));
                long_data_points[sensor] |= (a_bit << (HX711_DAC_BITS - 1 - ii));
            }
        }

        // Set the gain. HX711 has two channels, "A" and "B".
        delayMicroseconds(HX711_BIT_BANG_DELAY);
        switch ( gain ) {
            case HX711_GAIN_32: // Channel "B"
                digitalWrite(ARDUINO_HX711_SCK, HIGH);
                delayMicroseconds(HX711_BIT_BANG_DELAY);
                digitalWrite(ARDUINO_HX711_SCK, LOW);
                delayMicroseconds(HX711_BIT_BANG_DELAY);
            case HX711_GAIN_64: // Channel "A"
                digitalWrite(ARDUINO_HX711_SCK, HIGH);
                delayMicroseconds(HX711_BIT_BANG_DELAY);
                digitalWrite(ARDUINO_HX711_SCK, LOW);
                delayMicroseconds(HX711_BIT_BANG_DELAY);
            case HX711_GAIN_128: // Channel "A"
                digitalWrite(ARDUINO_HX711_SCK, HIGH);
                delayMicroseconds(HX711_BIT_BANG_DELAY);
                digitalWrite(ARDUINO_HX711_SCK, LOW);
                delayMicroseconds(HX711_BIT_BANG_DELAY);
        }
    }

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
	byte pinb;
	int retry_count = 0;

	do {
        // Check for readiness from all sensors
        // Read pins 8-13
        pinb = PINB;
        all_ready = true;
	    for (sensor = 0; sensor < MASS_SENSOR_COUNT; ++sensor) {
	        // The sensor is ready when the data line is low.
	        ready = (bool)(pinb & get_HX711_dout_port_bit(sensor)) == LOW;
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
