#include <Arduino.h>

#include "drawing.h"

MassDisplay format_mass(const float grams, const MassUnits requested_unit) {
    MassDisplay result{};
    result.units = requested_unit;

    float converted_mass = grams;

    // Conversion constants
    constexpr float GRAMS_PER_KG = 1000.0f;
    constexpr float GRAMS_PER_OZ = 28.3495f;
    constexpr float OUNCES_PER_LB = 16.0f;

    // Convert to requested unit
    switch (requested_unit) {
        case MassUnits::GRAMS: break; // already in grams
        case MassUnits::KILOGRAMS: converted_mass /= GRAMS_PER_KG; break;
        case MassUnits::OUNCES: converted_mass /= GRAMS_PER_OZ; break;
        case MassUnits::POUNDS: converted_mass /= (GRAMS_PER_OZ * OUNCES_PER_LB); break;
    }

    if (result.units == MassUnits::GRAMS and
        (converted_mass > 99999.9 or converted_mass < -9999.9)) {
        result.units = MassUnits::KILOGRAMS;
        converted_mass /= GRAMS_PER_KG;
    }

    if (result.units == MassUnits::KILOGRAMS and
        (converted_mass > 999.999 or converted_mass < -99.999)) {
        converted_mass = (converted_mass > 0) ? 999.999f : -99.9f;
    }

    if (result.units == MassUnits::OUNCES and
        (converted_mass > 9999.99 or converted_mass < -999.99)) {
        result.units = MassUnits::POUNDS;
        converted_mass /= OUNCES_PER_LB;
    }

    if (result.units == MassUnits::POUNDS and
        (converted_mass > 999.999 or converted_mass < -99.999)) {
        converted_mass = (converted_mass > 0) ? 999.999f : -99.9f;
    }

    // Determine precision based on unit
    int precision = 0;
    switch (result.units) {
        case MassUnits::GRAMS:      precision = 1; break;
        case MassUnits::KILOGRAMS:  precision = 3; break;
        case MassUnits::OUNCES:     precision = 2; break;
        case MassUnits::POUNDS:     precision = 3; break;
    }

    dtostrf(converted_mass, MassDisplay::MASS_DISPLAY_CHARS, precision, result.str);
    result.str[MassDisplay::MASS_DISPLAY_CHARS] = '\0';

    return result;
}
