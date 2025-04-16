#include "growbies.h"
#include "utils/sort.h"

Growbies* growbies = new Growbies();

template <typename T>

bool check_and_respond_to_deserialization_underflow(const T& structure) {
    if (slip_buf->buf_len() >= sizeof(structure)) {
        return false;
    }
    else{
        RespError resp;
        resp.error = ERROR_CMD_DESERIALIZATION_BUFFER_UNDERFLOW;
        send_packet(resp);
        return true;
    }

}

void Growbies::begin(byte channel, byte gain){
    HX711::begin(get_HX711_dout_pin(this->channel), ARDUINO_HX711_SCK, gain);
}

void Growbies::execute(PacketHdr* packet_hdr) {
    if (packet_hdr->type == CMD_LOOPBACK) {
        send_slip(slip_buf->buf, slip_buf->buf_len());
        send_slip_end();
    }
    else if (packet_hdr->type == CMD_READ_MEDIAN_FILTER_AVG) {
        CmdReadMedianFilterAvg* cmd = (CmdReadMedianFilterAvg*)slip_buf->buf;
        if (!check_and_respond_to_deserialization_underflow(*cmd)){
            RespLong resp;
            resp.data = this->read_median_filter_avg(cmd->times);
            if (resp.data == ERROR_HX711_NOT_READY){
                RespError error_response;
                error_response.error = (Error)resp.data;
                send_packet(error_response);
            }
            else {
                send_packet(resp);
            }
         }
    }
    else if (packet_hdr->type == CMD_SET_GAIN) {
        CmdSetGain* cmd = (CmdSetGain*)slip_buf->buf;
        if (!check_and_respond_to_deserialization_underflow(*cmd)){
            RespVoid resp;
            this->set_gain(cmd->gain);
            // The first read after setting the gain applies the gain. The value returned looks
            // off from experimentation and is discarded.
            this->read();
            send_packet(resp);
         }
    }
    else if (packet_hdr->type == CMD_GET_UNITS) {
        CmdGetUnits* cmd = (CmdGetUnits*)slip_buf->buf;
        if (!check_and_respond_to_deserialization_underflow(*cmd)){
            RespLong resp;
            resp.data = this->get_units(cmd->times);
            if (resp.data == ERROR_HX711_NOT_READY){
                RespError error_response;
                error_response.error = (Error)resp.data;
                send_packet(error_response);
            }
            else {
                send_packet(resp);
            }
        }
    }
    else if (packet_hdr->type == CMD_TARE) {
        CmdTare* cmd = (CmdTare*)slip_buf->buf;
        if (!check_and_respond_to_deserialization_underflow(*cmd)){
            RespVoid resp;
            this->tare(cmd->times);
            send_packet(resp);
         }
    }
    else if (packet_hdr->type == CMD_SET_SCALE) {
        CmdSetScale* cmd = (CmdSetScale*)slip_buf->buf;
        if (!check_and_respond_to_deserialization_underflow(*cmd)){
            RespVoid resp;
            this->set_scale(cmd->scale);
            send_packet(resp);
         }
    }
    else if (packet_hdr->type == CMD_GET_SCALE) {
        CmdGetScale* cmd = (CmdGetScale*)slip_buf->buf;
        if (!check_and_respond_to_deserialization_underflow(*cmd)){
            RespFloat resp;
            resp.data = this->get_scale();
            send_packet(resp);
         }
    }
    else if (packet_hdr->type == CMD_POWER_UP) {
        RespVoid resp;
        this->power_up();
        send_packet(resp);
    }
    else if (packet_hdr->type == CMD_POWER_DOWN) {
        RespVoid resp;
        this->power_down();
        send_packet(resp);
    }
    else if (packet_hdr->type == CMD_SET_CHANNEL) {
        CmdSetChannel* cmd = (CmdSetChannel*)slip_buf->buf;
        if (!check_and_respond_to_deserialization_underflow(*cmd)){
            RespVoid resp;
            this->channel = cmd->channel;
            this->begin();
            send_packet(resp);
         }
    }
    else if (packet_hdr->type == CMD_GET_CHANNEL) {
        RespByte resp;
        resp.data = this->channel;
        send_packet(resp);
    }
    else{
        RespError resp;
        resp.error = ERROR_UNRECOGNIZED_COMMAND;
        send_packet(resp);
    }
}

long Growbies::read_median_filter_avg(byte times, int threshold) {
    // This method helps reduce serial bit errors likely caused by timing.
    long median;
    byte middle;
    long sample;
    long samples[times] = {0};
    long sum = 0;
    int sum_count = 0;

	// Read samples
	for (byte idx = 0; idx < times; ++idx) {
        samples[idx] = this->read();
	}

    // Sort
    insertion_sort(samples, times);

    // Find median
    middle = times / 2;
    if (times % 2) {
        // Odd - simply take the middle number
        median = samples[middle];
    }
    else {
        // Even - average the middle two numbers
        median = (samples[middle - 1] + samples[middle]) / 2;
    }

    // Average and return samples that fall within a threshold
    for (byte idx = 0; idx < times; ++idx) {
        sample = samples[idx];
        if (abs(median - sample) <= threshold) {
            sum += sample;
            ++sum_count;
        }
    }
    return sum / sum_count;
}