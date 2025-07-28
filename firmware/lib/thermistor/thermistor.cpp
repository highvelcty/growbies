#include <cmath>

#include "constants.h"
#include "thermistor.h"

float adc_to_vout(const int adc) {
    return (static_cast<float>(adc) / THERMISTOR_ADC_RESOLUTION) * THERMISTOR_V_REF;
}

float dac_to_celsius(const int adc) {
    return steinhart_hart(adc) - 273.15;
}

float dac_to_fahrenheit(const int adc) {
    return dac_to_celsius(adc) * (9.0/5.0) + 32.0;
}

float steinhart_hart(const int adc) {
    // Return is in kelvin
    float ret;

    const float vout = adc_to_vout(adc);
    const float thermistor_resistance = \
        (vout * THERMISTOR_SERIES_RESISTOR) / (THERMISTOR_V_REF - vout);

    ret = (STEINHART_HART_A
           + (STEINHART_HART_B * log(thermistor_resistance))
           + pow((STEINHART_HART_C * log(thermistor_resistance)), 3));

    return 1/ret;
}

