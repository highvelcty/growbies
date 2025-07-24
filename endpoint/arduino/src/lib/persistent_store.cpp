#if ARDUINO_ARCH_AVR
#include <assert.h>
#include <EEPROM.h>
#elif ARDUINO_ARCH_ESP32
#include <Preferences.h>
#endif

#include "constants.h"
#include "flags.h"
#include "persistent_store.h"

CalibrationStore* calibration_store = new CalibrationStore();

void PersistentStore::begin() {
#if ARDUINO_ARCH_AVR
    assert(sizeof(CalibrationStruct) < EEPROM.length());
#elif ARDUINO_ARCH_ESP32
    this->prefs.begin(this->ns, false);
    this->prefs.end();
#endif
}

void CalibrationStore::begin() {
    PersistentStore::begin();
#if ARDUINO_ARCH_ESP32
    this->prefs.begin(this->ns, false);

    // Clear corrupted or crufty data. This is often due to structure changes in firmware.
    if (this->prefs.isKey(this->key_cal)) {
        if (this->prefs.getBytesLength(this->key_cal) != sizeof(CalibrationStruct)){
            this->prefs.remove(this->key_cal);
        }
    }

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

int CalibrationStore::get_temperature_sensor_idx(int mass_sensor_idx) {
    if (TEMPERATURE_SENSOR_COUNT == MASS_SENSOR_COUNT) {
        return mass_sensor_idx;
    }
    else {
        return 0;
    }
}