#include "persistent_store.h"

#if ARDUINO_ARCH_AVR
IdentifyStore* identify_store       = new IdentifyStore(PARTITION_A_OFFSET);
CalibrationStore* calibration_store = new CalibrationStore(PARTITION_B_OFFSET);
#elif ARDUINO_ARCH_ESP32
IdentifyStore* identify_store       = new IdentifyStore("mfg");
CalibrationStore* calibration_store = new CalibrationStore("cal");
#endif
