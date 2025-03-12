#ifndef constants_h
#define constants_h

const int CHAN_SELECT_DELAY_MS = 1;
const int MAIN_POLLING_LOOP_INTERVAL_MS = 1;

enum ArduinoDigitalPins : const int {
    ARDUINO_HX711_SCK = 2,
};

inline int get_HX711_dout_pin(int channel){
    return ARDUINO_HX711_SCK + channel + 1;
}


#endif /* constants_h */