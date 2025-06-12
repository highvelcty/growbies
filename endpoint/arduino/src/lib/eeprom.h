#ifndef eeprom_h
#define eeprom_h

#include "constants.h"

struct EEPROMStruct {
    float scale;
    int32_t offset[MAX_NUMBER_OF_MASS_SENSORS];
};

#endif /* eeprom_h */