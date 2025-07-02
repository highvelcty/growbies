#ifndef eeprom_h
#define eeprom_h

#include "constants.h"
#include "flags.h"

struct EEPROMStruct {
    float scale;
#if AC_EXCITATION
    float mass_a_offset[MAX_HX711_DEVICES];
    float mass_b_offset[MAX_HX711_DEVICES];
#else
    float mass_offset[MAX_HX711_DEVICES];
#endif
    float temperature_coefficient[TEMPERATURE_COEFFICIENT_COUNT];
};

#if AC_EXCITATION
float get_total_mass_offset(EEPROMStruct eeprom_struct) {
    return (eeprom_struct.mass_a_offset - eeprom_struct.mass_b_offset) / 2;
}
#endif

#endif /* eeprom_h */