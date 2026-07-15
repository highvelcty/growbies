#include "nvm.h"

#if ARDUINO_ARCH_AVR
IdentifyStore* identify_store       = new IdentifyStore(PARTITION_A_OFFSET);
CalibrationStore* calibration_store = new CalibrationStore(PARTITION_B_OFFSET);
TareStore* tare_store = new TareStore(PARTITION_D_OFFSET);
#elif ARDUINO_ARCH_ESP32
IdentifyStore* identify_store       = new IdentifyStore("mfg");
CalibrationStore* calibration_store = new CalibrationStore("cal");
TareStore* tare_store = new TareStore("tare");
#endif

const char* get_tare_name(const TareIdx idx) {
    switch (idx) {
        case TareIdx::TARE_0: return "Tare A";
        case TareIdx::TARE_1: return "Tare B";
        case TareIdx::TARE_2: return "Tare C";
        default: return "Unknown";
    }
}
