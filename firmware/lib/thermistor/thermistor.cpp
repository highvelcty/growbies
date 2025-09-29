#include "math.h"

#include "constants.h"
#include "thermistor.h"

float beta(const float vout) {
    // Return is in Celsius
    float ret;

    const float thermistor_resistance = \
        (vout * THERMISTOR_SERIES_RESISTOR) / (THERMISTOR_SUPPLY_VOLTAGE - vout);

    ret = ((1/THERMISTOR_NOMINAL_TEMPERATURE)
            + (1/THERMISTOR_BETA_COEFF)
            * log(thermistor_resistance/THERMISTOR_NOMINAL_RESISTANCE));

    // Invert for kelvin, subtract for celsius
    return (1/ret) - 273.15;

}

float steinhart_hart(const float vout) {
    // Return is in Celsius
    float ret;

    const float thermistor_resistance = \
        (vout * THERMISTOR_SERIES_RESISTOR) / (THERMISTOR_SUPPLY_VOLTAGE - vout);

    ret = (STEINHART_HART_A
           + (STEINHART_HART_B*log(thermistor_resistance))
           + (STEINHART_HART_C*pow(log(thermistor_resistance), 3)));

    // Invert for kelvin, subtract for Celsius
    return (1/ret) - 273.15;
}

