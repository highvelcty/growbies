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
        case TareIdx::USER_0: return "User 0";
        case TareIdx::USER_1: return "User 1";
        case TareIdx::USER_2: return "User 2";
        case TareIdx::AUTO_0: return "User 3";
        case TareIdx::AUTO_1: return "Auto 4";
        case TareIdx::AUTO_2: return "Auto 5";
    }
    return "Unknown";
}
