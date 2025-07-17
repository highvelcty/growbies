#if ARDUINO_ARCH_AVR
#include <assert.h>
#include <EEPROM.h>
#elif ARDUINO_ARCH_ESP32
#include <Preferences.h>
#endif

#include "persistent_store.h"

CalibrationStore* calibration_store = new CalibrationStore();

void PersistentStore::begin() {
#if ARDUINO_ARCH_AVR
    assert(sizeof(CalibrationStruct) < EEPROM_BYTES);
#elif ARDUINO_ARCH_ESP32
    this->prefs.begin(this->ns, false);
    this->prefs.end();
#endif
}

void CalibrationStore::begin() {
    PersistentStore::begin();
#if ARDUINO_ARCH_ESP32
    this->prefs.begin(this->ns, false);
    if (!this->prefs.isKey(this->key_cal)){
        CalibrationStruct calibration;
        memset(&calibration, 0, sizeof(calibration));
        this->prefs.putBytes(this->key_cal, &calibration, sizeof(calibration));
    }
    this->prefs.end();
#endif
}

void CalibrationStore::get(CalibrationStruct& calibration) {
#if ARDUINO_ARCH_AVR
    EEPROM.get(0, calibration);
#elif ARDUINO_ARCH_ESP32
    this->prefs.begin(this->ns, true);
    this->prefs.getBytes(this->key_cal, &calibration, sizeof(calibration));
    this->prefs.end();
#endif
}

void CalibrationStore::put(CalibrationStruct& calibration) {
#if ARDUINO_ARCH_AVR
    EEPROM.put(0, calibration);
#elif ARDUINO_ARCH_ESP32
    this->prefs.begin(this->ns, false);
    this->prefs.putBytes(this->key_cal, &calibration, sizeof(calibration));
    this->prefs.end();
#endif
}
