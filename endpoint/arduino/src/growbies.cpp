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

Growbies::Growbies(int sensor_count) : sensor_count(sensor_count){
    assert(sizeof(EEPROMStruct) < EEPROM_BYTES);
}

void Growbies::begin(){
    pinMode(ARDUINO_HX711_SCK, OUTPUT);
    for(int sensor = 0; sensor < this->sensor_count; ++sensor) {
        pinMode(get_HX711_dout_pin(sensor), INPUT_PULLUP);
    }
#if AC_EXCITATION
    this->set_phase_a();
#endif

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
                        sizeof(RespMultiDataPoint) + (sizeof(MultiDataPoint)*this->sensor_count));
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
                        sizeof(RespMultiDataPoint) + (sizeof(MultiDataPoint)*this->sensor_count));
         }
    }
    else if (packet_hdr->type == CMD_SET_PHASE) {
        CmdSetPhase* cmd = (CmdSetPhase*)slip_buf->buf;
        if (validate_packet(*cmd)) {
            new (this->outbuf) RespVoid;
            if (cmd->phase == 0) {
                this->set_phase_a();
            }
            else {
                this->set_phase_b();
            }
            send_packet(*this->outbuf, sizeof(RespVoid));
         }
    }
    else if (packet_hdr->type == CMD_GET_SCALE) {
        CmdGetScale* cmd = (CmdGetScale*)slip_buf->buf;
        if (validate_packet(*cmd)) {
            RespFloat* resp = new (this->outbuf) RespFloat;
            resp->data = this->get_scale();
            send_packet(*this->outbuf, sizeof(RespFloat));
         }
    }
    else if (packet_hdr->type == CMD_GET_TARE) {
        CmdGetTare* cmd = (CmdGetTare*)slip_buf->buf;
        if (validate_packet(*cmd)) {
            RespGetTare* resp = new (this->outbuf) RespGetTare;
            get_tare(resp);
            send_packet(*this->outbuf, (sizeof(RespGetTare)));
        }
    }
    else if (packet_hdr->type == CMD_SET_SCALE) {
        CmdSetScale* cmd = (CmdSetScale*)slip_buf->buf;
        if (validate_packet(*cmd)) {
            RespVoid resp;
            this->set_scale(cmd->scale);
            send_packet(resp);
         }
    }
    else if (packet_hdr->type == CMD_SET_TARE) {
        CmdSetTare* cmd = (CmdSetTare*)slip_buf->buf;
        if(validate_packet(*cmd)) {
            RespVoid resp;
            this->set_tare();
            send_packet(resp);
        }
    }
    else{
        RespError resp;
        resp.error = ERROR_UNRECOGNIZED_COMMAND;
        send_packet(resp);
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

float Growbies::get_scale() {
    EEPROMStruct eeprom_struct;
    EEPROM.get(0, eeprom_struct);
    return eeprom_struct.scale;
}

void Growbies::set_scale(float scale) {
    EEPROMStruct eeprom_struct;
    EEPROM.get(0, eeprom_struct);
    eeprom_struct.scale = scale;
    EEPROM.put(0, eeprom_struct);
}

void Growbies::get_tare(RespGetTare* resp_get_tare) {
    EEPROMStruct eeprom_struct;
    EEPROM.get(0, eeprom_struct);
    for (int sensor = 0; sensor < MAX_HX711_DEVICES; ++sensor){
        if (sensor < this->sensor_count) {
            resp_get_tare->mass_a_offset[sensor] = eeprom_struct.mass_a_offset[sensor];
            resp_get_tare->mass_b_offset[sensor] = eeprom_struct.mass_b_offset[sensor];
            resp_get_tare->temperature_offset[sensor] = eeprom_struct.temperature_offset[sensor];
        }
        else{
            resp_get_tare->mass_a_offset[sensor] = FLT_MAX;
            resp_get_tare->mass_b_offset[sensor] = FLT_MAX;
            resp_get_tare->temperature_offset[sensor] = FLT_MAX;
        }
    }
}

void Growbies::set_tare() {
    EEPROMStruct eeprom_struct;
    int sensor_idx = 0;
    int num_bytes = sizeof(MultiDataPoint) * this->sensor_count;
    MultiDataPoint* multi_data_points = (MultiDataPoint*)malloc(num_bytes);
    memset(multi_data_points, 0, num_bytes);

    EEPROM.get(0, eeprom_struct);

    this->read_units(multi_data_points, this->get_tare_times, UNIT_DAC);
    for (sensor_idx = 0; sensor_idx < this->sensor_count; ++sensor_idx) {
    #if AC_EXCITATION
        eeprom_struct.mass_a_offset[sensor_idx] = \
            multi_data_points[sensor_idx].mass_a.data;
        eeprom_struct.mass_b_offset[sensor_idx] = \
            multi_data_points[sensor_idx].mass_b.data;
    #else
        eeprom_struct.mass_a_offset[sensor_idx] = \
            multi_data_points[sensor_idx].mass.data;
    #endif
    }

    EEPROM.put(0, eeprom_struct);

    free(multi_data_points);
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

    float sensor_samples[this->sensor_count][times] = {0.0};

    // Initialize
    memset(data_points, 0, sizeof(DataPoint) * this->sensor_count);

	// Read samples
#if POWER_CONTROL
	this->power_on();
#endif
	for (sample_idx = 0; sample_idx < times; ++sample_idx) {
        this->sample(data_points, gain);
        for (sensor = 0; sensor < this->sensor_count; ++sensor){
            sensor_samples[sensor][sample_idx] = data_points[sensor].data;
        }
	}
#if POWER_CONTROL
	this->power_off();
#endif

    // Filter and average
    for (sensor = 0; sensor < this->sensor_count; ++sensor) {
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
    RespGetTare tare;

//    float total_mass = 0.0;
    get_tare(&tare);

#if CHANNEL_B_TEMPERATURE
    // Temperature
    this->set_gain(HX711_GAIN_32);
    this->read_dac(this->data_points, times);
    for (sensor_idx = 0; sensor_idx < this->sensor_count; ++sensor_idx) {
        multi_data_points[sensor_idx].temperature.data = \
        this->data_points[sensor_idx].data;
    }
#endif

    // Mass - Phase A
#if AC_EXCITATION
    set_phase_a();
#endif

#if CHANNEL_B_TEMPERATURE
    this->set_gain(HX711_GAIN_128);
#endif

    this->read_dac(this->data_points, times);
    for (sensor_idx = 0; sensor_idx < this->sensor_count; ++sensor_idx) {
    #if AC_EXCITATION
        multi_data_points[sensor_idx].mass_a.data = this->data_points[sensor_idx].data;
    #else
        multi_data_points[sensor_idx].mass.data = this->data_points[sensor_idx].data;
    #endif

    }

#if AC_EXCITATION
    // Mass - Phase B
    set_phase_b();
    this->read_dac(this->data_points, times);
    for (sensor_idx = 0; sensor_idx < this->sensor_count; ++sensor_idx) {
        multi_data_points[sensor_idx].mass_b.data = this->data_points[sensor_idx].data;
    }

    // Totals
    for (sensor_idx = 0; sensor_idx < this->sensor_count; ++sensor_idx) {
            multi_data_points[sensor_idx].mass.data = \
                ((multi_data_points[sensor_idx].mass_a.data
                - multi_data_points[sensor_idx].mass_b.data) / 2);
     }
#endif

    // Units
    if (units & UNIT_GRAMS) {
        for (sensor_idx = 0; sensor_idx < this->sensor_count; ++sensor_idx) {
        #if AC_EXCITATION
            multi_data_points[sensor_idx].mass_a.data = \
                (multi_data_points[sensor_idx].mass_a.data - tare.mass_a_offset[sensor_idx])
                / this->get_scale();

            multi_data_points[sensor_idx].mass_b.data = \
                (multi_data_points[sensor_idx].mass_b.data - tare.mass_b_offset[sensor_idx])
                / this->get_scale();

            multi_data_points[sensor_idx].mass.data = \
                (multi_data_points[sensor_idx].mass.data
                - get_total_mass_offset(tare, sensor_idx))
                / this->get_scale();
        #else
            multi_data_points[sensor_idx].mass.data = \
                (multi_data_points[sensor_idx].mass.data
                - tare.mass_a_offset[sensor_idx]) / this->get_scale();
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

    long long_data_points[this->sensor_count] = {0};

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
            for (sensor = 0; sensor < this->sensor_count; ++sensor) {
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

    for (sensor = 0; sensor < this->sensor_count; ++sensor) {
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
	    for (sensor = 0; sensor < this->sensor_count; ++sensor) {
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

float get_total_mass_offset(RespGetTare tare, int sensor_idx) {
    return (tare.mass_a_offset[sensor_idx] - tare.mass_b_offset[sensor_idx]) / 2;
}