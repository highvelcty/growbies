#ifndef persistent_store_h
#define persistent_store_h

#if ARDUINO_ARCH_ESP32
#include <Preferences.h>
#endif

#include "constants.h"

typedef float MassTemperatureCoeff[MASS_SENSOR_COUNT][COEFF_COUNT];
typedef float MassCoeff[COEFF_COUNT];
typedef float Tare[TARE_COUNT];

#pragma pack(1)
struct CalibrationStruct {
    MassTemperatureCoeff mass_temperature_coeff;
    MassCoeff mass_coeff;
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
};

class CalibrationStore : public PersistentStore {
    public:
        void begin();
        void get(CalibrationStruct& calibration);
        void put(CalibrationStruct& calibration);
        int get_temperature_sensor_idx(int mass_sensor_idx);

    private:
    #if ARDUINO_ARCH_ESP32
        const char* key_cal = "cal";
    #endif
};

extern CalibrationStore* calibration_store;

#endif /* persistent_store_h */