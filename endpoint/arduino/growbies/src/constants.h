#ifndef constants_h
#define constants_h

const int BITS_PER_BYTE = 8;

const int CHAN_SELECT_DELAY_MS = 1;
const int MAIN_POLLING_LOOP_INTERVAL_MS = 1;
const int WAIT_READY_RETRIES = 100;
const int WAIT_READY_RETRY_DELAY_MS = 10;

enum ArduinoDigitalPins : const int {
    ARDUINO_HX711_SCK = 2,
    ARDUINO_HX711_BASE_DOUT = 3,
};

inline int get_HX711_dout_pin(int sensor){
    return ARDUINO_HX711_BASE_DOUT + sensor;
}

enum Cmd: uint16_t {
    CMD_LOOPBACK = 0,
    CMD_READ_MEDIAN_FILTER_AVG = 1,
    CMD_SET_GAIN = 2,
    CMD_GET_VALUE = 3,
    CMD_GET_UNITS = 4,
    CMD_TARE = 5,
    CMD_SET_SCALE = 6,
    CMD_GET_SCALE = 7,
    CMD_SET_OFFSET = 8,
    CMD_GET_OFFSET = 9,
    CMD_POWER_DOWN = 10,
    CMD_POWER_UP = 11,
};

enum RespType: uint16_t {
    RESP_TYPE_VOID = 0,
    RESP_TYPE_BYTE = 1,
    RESP_TYPE_LONG = 2,
    RESP_TYPE_FLOAT = 3,
    RESP_TYPE_DOUBLE = 4,
    RESP_MASS_DATA_POINT = 5,
    RESP_TYPE_ERROR = 0xFFFF,
};

enum Error: long {
    ERROR_NONE = 0,
    ERROR_CMD_DESERIALIZATION_BUFFER_UNDERFLOW = 1,
    ERROR_UNRECOGNIZED_COMMAND = 2,
    ERROR_HX711_MIN = -0x800000,
    ERROR_HX711_MAX = 0x7FFFFF,
    ERROR_HX711_NOT_READY = ERROR_HX711_MAX + 1,
};

#endif /* constants_h */