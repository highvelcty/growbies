#ifndef persistent_store_h
#define persistent_store_h

#if ARDUINO_ARCH_ESP32
#include <Preferences.h>
#endif

#include "constants.h"

typedef float MassCoefficient[MASS_SENSOR_COUNT][COEFFICIENT_COUNT];
typedef float TemperatureCoefficient[TEMPERATURE_SENSOR_COUNT][COEFFICIENT_COUNT];
typedef float Tare[MASS_SENSOR_COUNT][TARE_COUNT];

#pragma pack(1)
struct CalibrationStruct {
    MassCoefficient mass_coefficient;
    TemperatureCoefficient temperature_coefficient;
    Tare tare;
};

class PersistentStore {
    public:
        void begin();

    protected:
    #if ARDUINO_ARCH_ESP32
        Preferences prefs;
        const char* ns = "growbies";
    #endif

    private:
    #if ARDUINO_ARCH_AVR
        const unsigned int EEPROM_BYTES = 1024;
    #endif
};

class CalibrationStore : public PersistentStore {
    public:
        void begin();
        void get(CalibrationStruct& calibration);
        void put(CalibrationStruct& calibration);

    private:
    #if ARDUINO_ARCH_ESP32
        const char* key_cal = "cal";
    #endif
};

extern CalibrationStore* calibration_store;

#endif /* persistent_store_h */