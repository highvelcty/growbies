#ifndef eeprom_h
#define eeprom_h

#include "constants.h"

struct EEPROMStruct {
    float scale;
    float mass_a_offset[MAX_HX711_DEVICES];
    float mass_b_offset[MAX_HX711_DEVICES];
    float temperature_offset[MAX_HX711_DEVICES];
};

float get_total_mass_offset(EEPROMStruct eeprom_struct) {
    return (eeprom_struct.mass_a_offset - eeprom_struct.mass_b_offset) / 2;
}

#endif /* eeprom_h */