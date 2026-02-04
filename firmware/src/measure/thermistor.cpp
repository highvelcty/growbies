#include "build_cfg.h"
#include "thermistor.h"

#include "constants.h"
#include "hx711.h"

namespace growbies {

// --- Thermistor ------------------------
void Thermistor::begin() const {
    pinMode(analog_pin_, INPUT);
}

float Thermistor::read_voltage() const {
#if defined(ARDUINO_ARCH_ESP32)
    const auto vout = static_cast<float>(analogReadMilliVolts(analog_pin_) / 1000.0);
    if (vout < 0.001f || vout > (THERMISTOR_SUPPLY_VOLTAGE - 0.001f)) {
        return NAN; // Safely bail out
    }
    return vout;
#else
    const float adc_max = 1023.0f;
    const int adc_raw = analogRead(analog_pin_);
    return (adc_raw / adc_max) * THERMISTOR_SUPPLY_VOLTAGE;
#endif

}

float Thermistor::sample() const {
    // Thermistor on the top of the resistor divider
    const float vout = read_voltage();
    if (isnan(vout)) {
        return DEFAULT_TEMPERATURE_CELSIUS;
    }
    const float r_therm =
        (THERMISTOR_SERIES_RESISTOR * (THERMISTOR_SUPPLY_VOLTAGE - vout))
        / vout;

    const float inv_T = STEINHART_HART_A
                      + (STEINHART_HART_B * logf(r_therm))
                      + (STEINHART_HART_C * powf(logf(r_therm), 3));

    return (1.0f / inv_T) - 273.15f;  // Celsius
}


float Thermistor::sample_beta() const {
    // Thermistor on the top of the resistor divider
    const float vout = read_voltage();
    if (isnan(vout)) {
        return DEFAULT_TEMPERATURE_CELSIUS;
    }
    const float r_therm =
        (THERMISTOR_SERIES_RESISTOR * (THERMISTOR_SUPPLY_VOLTAGE - vout))
        / vout;

    const float inv_T = (1.0f / THERMISTOR_NOMINAL_TEMPERATURE)
                      + (1.0f / THERMISTOR_BETA_COEFF)
                      * logf(r_therm / THERMISTOR_NOMINAL_RESISTANCE);

    return (1.0f / inv_T) - 273.15f;  // Celsius
}

// --- MultiThermistor -------------------
    void MultiThermistor::begin() {
    for (auto ii = 0; ii < TEMPERATURE_SENSOR_COUNT; ++ii) {
        add_device(new Thermistor(get_temperature_pin(ii)));
    }

    for (const auto* device : devices_) {
        if (device) device->begin();
    }
}

std::vector<float> MultiThermistor::sample() const {
    std::vector<float> readings;
    readings.reserve(devices_.size());
    for (const auto* therm : devices_) {
        readings.push_back(therm->sample());
    }
    return readings;
}

}

