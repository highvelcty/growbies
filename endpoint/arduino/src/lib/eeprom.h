#ifndef eeprom_h
#define eeprom_h

#include "constants.h"
#include "flags.h"

typedef float MassCoefficient[MASS_SENSOR_COUNT][COEFFICIENT_COUNT];
typedef float TemperatureCoefficient[TEMPERATURE_SENSOR_COUNT][COEFFICIENT_COUNT];
typedef float Tare[MASS_SENSOR_COUNT][TARE_COUNT];

struct EEPROMStruct {
    MassCoefficient mass_coefficient;
    TemperatureCoefficient temperature_coefficient;
    Tare tare;
};

#endif /* eeprom_h */