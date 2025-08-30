#if ARDUINO_ARCH_AVR
#include <assert.h>
#include <EEPROM.h>
#elif ARDUINO_ARCH_ESP32
#include <Preferences.h>
#endif

#include "flags.h"
#include "persistent_store.h"

#if ARDUINO_ARCH_AVR
IdentifyStore* identify_store     = new IdentifyStore(PARTITION_A_OFFSET);
CalibrationStore* calibration_store = new CalibrationStore(PARTITION_B_OFFSET);
#elif ARDUINO_ARCH_ESP32
IdentifyStore* identify_store     = new IdentifyStore("mfg");
CalibrationStore* calibration_store = new CalibrationStore("cal");
#endif

void PersistentStore::begin() {
#if ARDUINO_ARCH_AVR
    assert(sizeof(Calibration) < EEPROM.length());
#elif ARDUINO_ARCH_ESP32
    this->prefs.begin(this->ns, false);
    this->prefs.end();
#endif
}
