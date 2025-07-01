#ifndef constants_h
#define constants_h

const int MAX_HX711_DEVICES = 5;
const int MAIN_POLLING_LOOP_INTERVAL_MS = 1;
const int WAIT_READY_RETRIES = 100;
const int WAIT_READY_RETRY_DELAY_MS = 10;
const int SET_PHASE_DELAY_MS = 10;
const int EEPROM_BYTES = 1024;

enum ArduinoDigitalPins : const int {
    ARDUINO_EXCITATION_A = 5,
    ARDUINO_EXCITATION_B = 6,
    ARDUINO_PORT_B_BASE_PIN = 8,
    ARDUINO_HX711_SCK = 12,
    ARDUINO_HX711_BASE_DOUT = ARDUINO_PORT_B_BASE_PIN,
};

enum ArduinoAnalogPins : const int {
    A4_HW_I2C_SDA = 0xA4,
    A5_HW_I2C_SCL = 0xA5,
};

enum SensorHw : const int {
    TEMPERATURE_SENSOR = 0,
    MASS_SENSOR = 1
};

inline int get_HX711_dout_pin(int sensor){
    return ARDUINO_HX711_BASE_DOUT + sensor;
}

inline int get_HX711_dout_port_bit(int sensor){
    return (1 << (get_HX711_dout_pin(sensor) - ARDUINO_PORT_B_BASE_PIN));
}

#endif /* constants_h */