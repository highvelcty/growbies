#include <assert.h>
#include <EEPROM.h>
#include <new> // Required for placement new
#include <util/atomic.h>

#include "constants.h"
#include "eeprom.h"
#include "growbies.h"
#include "utils/sort.h"


Growbies* growbies = new Growbies();

Growbies::Growbies(int sensor_count, byte gain) : sensor_count(sensor_count), gain(gain){
    assert(sizeof(EEPROMStruct) < EEPROM_BYTES);

    this->outbuf = new byte[this->outbuf_size];
    memset(this->outbuf, 0, this->outbuf_size);
    this->mass_data_points = (MassDataPoint*)&outbuf[sizeof(PacketHdr)];

    this->offset = new long[this->sensor_count];
}

Growbies::~Growbies() {
    delete[] this->outbuf;
    delete[] this->offset;
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
    else if (packet_hdr->type == CMD_READ_MEDIAN_FILTER_AVG) {
        CmdReadMedianFilterAvg* cmd = (CmdReadMedianFilterAvg*)slip_buf->buf;
        if (validate_packet(*cmd)) {
            // This constructs at location
            new (this->outbuf) RespMassDataPoint;
            this->read_median_filter_avg(cmd->times);
            send_packet(*this->outbuf,
                        sizeof(RespMassDataPoint) + (sizeof(MassDataPoint)*this->sensor_count));
         }
    }

//    else if (packet_hdr->type == CMD_SET_GAIN) {
//        CmdSetGain* cmd = (CmdSetGain*)slip_buf->buf;
//        if (validate_packet(*cmd)) {
//            RespVoid resp;
//            this->set_gain(cmd->gain);
//            // The first read after setting the gain applies the gain. The value returned looks
//            // off from experimentation and is discarded.
//            this->read();
//            send_packet(resp);
//         }
//    }
//    else if (packet_hdr->type == CMD_GET_UNITS) {
//        CmdGetUnits* cmd = (CmdGetUnits*)slip_buf->buf;
//        if (validate_packet(*cmd)) {
//            RespLong resp;
//            resp.data = this->get_units(cmd->times);
//            if (resp.data == ERROR_HX711_NOT_READY){
//                RespError error_response;
//                error_response.error = (Error)resp.data;
//                send_packet(error_response);
//            }
//            else {
//                send_packet(resp);
//            }
//        }
//    }
    else if (packet_hdr->type == CMD_TARE) {
        CmdTare* cmd = (CmdTare*)slip_buf->buf;
        if (validate_packet(*cmd)) {
            RespVoid resp;
            this->tare(cmd->times);
            send_packet(resp);
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
    else if (packet_hdr->type == CMD_GET_SCALE) {
        CmdGetScale* cmd = (CmdGetScale*)slip_buf->buf;
        if (validate_packet(*cmd)) {
            RespFloat* resp = new (this->outbuf) RespFloat;
            resp->data = this->get_scale();
            send_packet(*this->outbuf, sizeof(RespFloat));
         }
    }
//    else if (packet_hdr->type == CMD_POWER_UP) {
//        CmdPowerUp* cmd = (CmdPowerUp*)slip_buf->buf;
//        if (validate_packet(*cmd)) {
//            RespVoid resp;
//            this->power_up();
//            send_packet(resp);
//        }
//    }
//    else if (packet_hdr->type == CMD_POWER_DOWN) {
//        CmdPowerDown* cmd = (CmdPowerDown*)slip_buf->buf;
//        if (validate_packet(*cmd)) {
//            RespVoid resp;
//            this->power_down();
//            send_packet(resp);
//        }
//    }
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

void Growbies::power_on() {
    digitalWrite(ARDUINO_HX711_SCK, LOW);
}
void Growbies::power_off() {
    digitalWrite(ARDUINO_HX711_SCK, HIGH);
    delayMicroseconds(HX711_POWER_OFF_DELAY);
}

bool Growbies::read(){
    this->power_on();
    if (!this->wait_all_ready_retry(WAIT_READY_RETRIES, WAIT_READY_RETRY_DELAY_MS)){
        ; // MEYERE
//        return false;
    }

    this->shift_all_in();
    this->power_off();
    return true;
}

void Growbies::read_median_filter_avg(const byte times) {
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
    memset(this->mass_data_points, 0, sizeof(MassDataPoint) * this->sensor_count);

	// Read samples
	for (sample = 0; sample < times; ++sample) {
        if (!this->read()){
            return;
        }
        for (sensor = 0; sensor < this->sensor_count; ++sensor){
            sensor_samples[sensor][sample] = this->mass_data_points[sensor].mass;
        }
	}

    // Filter and average
    for (sensor = 0; sensor < this->sensor_count; ++sensor){
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
                ++this->mass_data_points[sensor].error_count;
            }
        }
        this->mass_data_points[sensor].mass = sum / sum_count;
    }
}

void Growbies::read_with_units(const byte times) {
    this->read_median_filter_avg(times);
    for (int sensor = 0; sensor < this->sensor_count; ++sensor) {
        this->mass_data_points[sensor].mass = \
            (this->mass_data_points[sensor].mass - this->offset[sensor]) / this->scale;
    }
}

void Growbies::set_offset(long* offset) {
    for (int sensor = 0; sensor < this->sensor_count; ++sensor) {
        this->offset[sensor] = offset[sensor];
    }
}

void Growbies::set_scale(float scale) {
    EEPROMStruct eeprom_struct;
    EEPROM.get(0, eeprom_struct);
    eeprom_struct.scale = scale;
    EEPROM.put(0, eeprom_struct);
}

void Growbies::shift_all_in() {
    uint32_t a_bit;
    uint8_t ii;
    uint8_t sensor;
    uint8_t pinb;

    for (sensor = 0; sensor < this->sensor_count; ++sensor) {
        this->mass_data_points[sensor].mass = 0;
    }

    ATOMIC_BLOCK(ATOMIC_RESTORESTATE) {
        delayMicroseconds(HX711_READY_TO_SCK_RISE_MICROSECONDS);
        for (ii = 0; ii < HX711_DAC_BITS; ++ii) {
            // Read in a byte,   most significant bit first
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
                this->mass_data_points[sensor].mass |= (a_bit << (HX711_DAC_BITS - 1 - ii));
            }
        }
    }

    for (sensor = 0; sensor < this->sensor_count; ++sensor) {
        if (this->mass_data_points[sensor].mass & (1UL << (HX711_DAC_BITS - 1))) {
            this->mass_data_points[sensor].mass |= (0xFFUL << HX711_DAC_BITS);
        }
    }
}

void Growbies::tare(const byte times) {
    read_median_filter_avg(times);
    long offset[this->sensor_count];
    for (int sensor = 0; sensor < this->sensor_count; ++sensor) {
        offset[sensor] = this->mass_data_points[sensor].mass;
    }

    this->set_offset(offset);
}


bool Growbies::wait_all_ready_retry(const int retries, const unsigned long delay_ms)
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
	        this->mass_data_points[sensor].ready = ready;
	        all_ready &= ready;
        }

        if (!all_ready){
            ++retry_count;
            delay(delay_ms);
        }

	} while ((retry_count <= retries) && (!all_ready));

	return all_ready;
}