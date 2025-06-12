#include <assert.h>
#include <EEPROM.h>
#include <new> // Required for placement new
#include <util/atomic.h>

#include "constants.h"
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
    digitalWrite(ARDUINO_HX711_SCK, LOW);
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
            new (this->outbuf) RespMassDataPoint;
            MassDataPoint* mass_data_points = \
                new (this->outbuf + sizeof(RespMassDataPoint)) MassDataPoint;
            this->read_dac(mass_data_points, cmd->times);
            send_packet(*this->outbuf,
                        sizeof(RespMassDataPoint) + (sizeof(MassDataPoint)*this->sensor_count));
         }
    }
    else if (packet_hdr->type == CMD_READ_GRAMS) {
        CmdReadGrams* cmd = (CmdReadGrams*)slip_buf->buf;
        if (validate_packet(*cmd)) {
            // This constructs at location
            new (this->outbuf) RespMassDataPoint;
            MassDataPoint* mass_data_points = \
                new (this->outbuf + sizeof(RespMassDataPoint)) MassDataPoint;
            this->read_grams(mass_data_points, cmd->times);
            send_packet(*this->outbuf,
                        sizeof(RespMassDataPoint) + (sizeof(MassDataPoint)*this->sensor_count));
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
    for (int sensor = 0; sensor < MAX_NUMBER_OF_MASS_SENSORS; ++sensor){
        if (sensor < this->sensor_count) {
            resp_get_tare->offset[sensor] = eeprom_struct.offset[sensor];
        }
        else{
            resp_get_tare->offset[sensor] = INT32_MAX;
        }
    }
}

void Growbies::set_tare() {
    EEPROMStruct eeprom_struct;
    MassDataPoint* mass_data_points = \
        (MassDataPoint*)malloc(sizeof(MassDataPoint) * this->sensor_count);

    EEPROM.get(0, eeprom_struct);
    for (int sensor = 0; sensor < this->sensor_count; ++sensor){
        eeprom_struct.offset[sensor] = 0;
    }
    EEPROM.put(0, eeprom_struct);

    this->read_dac(mass_data_points, this->get_tare_times);

    for (int sensor = 0; sensor < this->sensor_count; ++sensor){
        eeprom_struct.offset[sensor] = mass_data_points[sensor].mass;
    }
    EEPROM.put(0, eeprom_struct);

    free(mass_data_points);
}

void Growbies::power_off() {
    digitalWrite(ARDUINO_HX711_SCK, HIGH);
    delayMicroseconds(HX711_POWER_OFF_DELAY);
}

void Growbies::power_on() {
    digitalWrite(ARDUINO_HX711_SCK, LOW);
}

void Growbies::sample(MassDataPoint* mass_data_points){
    this->power_on();
    this->wait_all_ready_retry(mass_data_points, WAIT_READY_RETRIES, WAIT_READY_RETRY_DELAY_MS);
    this->shift_all_in(mass_data_points);
    this->power_off();
}

void Growbies::read_dac(MassDataPoint* mass_data_points, const byte times) {
    // Reads data from the chip the requested number of times. The median is found and then all
    // samples that are within the median +/- a DAC threshold are averaged and returned.

    long median;
    byte middle;
    long sample;
    int sensor;
    byte sensor_sample;
    long sum;
    int sum_count;

    long sensor_samples[this->sensor_count][times] = {0};

    // Initialize
    memset(mass_data_points, 0, sizeof(MassDataPoint) * this->sensor_count);

	// Read samples
	for (sample = 0; sample < times; ++sample) {
        this->sample(mass_data_points);
        for (sensor = 0; sensor < this->sensor_count; ++sensor){
            sensor_samples[sensor][sample] = mass_data_points[sensor].mass;
        }
	}

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
                ++mass_data_points[sensor].error_count;
            }
        }
        mass_data_points[sensor].mass = sum / sum_count;
    }
}

void Growbies::read_grams(MassDataPoint* mass_data_points, const byte times){
    float total_mass = 0.0;
    RespGetTare tare;
    get_tare(&tare);

    this->read_dac(mass_data_points, times);
    for (int sensor = 0; sensor < this->sensor_count; ++sensor) {
        mass_data_points[sensor].mass = \
            (mass_data_points[sensor].mass - tare.offset[sensor]) / get_scale();
        total_mass += mass_data_points[sensor].mass;
    }
    display->print_mass(total_mass);
}

void Growbies::shift_all_in(MassDataPoint* mass_data_points) {
    uint32_t a_bit;
    uint8_t ii;
    uint8_t sensor;
    uint8_t pinb;

    ATOMIC_BLOCK(ATOMIC_RESTORESTATE) {
        delayMicroseconds(HX711_READY_TO_SCK_RISE_MICROSECONDS);
        for (ii = 0; ii < HX711_DAC_BITS; ++ii) {
            // Read in a byte, most significant bit first
            digitalWrite(ARDUINO_HX711_SCK, HIGH);

            // This is a time critical block
            delayMicroseconds(HX711_SCK_RISE_TO_DOUT_READY_MICROSECONDS);
            // Read pins 8-13
            pinb = PINB;
            digitalWrite(ARDUINO_HX711_SCK, LOW);

            // This time intensive task needs to happen after pulling SCK low so as to not perturb
            // time sensitive section when SCK is high.
            for (sensor = 0; sensor < this->sensor_count; ++sensor) {
                a_bit = (bool)(pinb & get_HX711_dout_port_bit(sensor));
                mass_data_points[sensor].mass |= (a_bit << (HX711_DAC_BITS - 1 - ii));
            }
        }
    }

    for (sensor = 0; sensor < this->sensor_count; ++sensor) {
        if (mass_data_points[sensor].mass & (1UL << (HX711_DAC_BITS - 1))) {
            mass_data_points[sensor].mass |= (0xFFUL << HX711_DAC_BITS);
        }
    }
}

bool Growbies::wait_all_ready_retry(MassDataPoint* mass_data_points,
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
	        mass_data_points[sensor].ready = ready;
	        all_ready &= ready;
        }

        if (!all_ready){
            ++retry_count;
            delay(delay_ms);
        }

	} while ((retry_count <= retries) && (!all_ready));

	return all_ready;
}