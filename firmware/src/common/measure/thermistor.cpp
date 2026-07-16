#include "build_cfg.h"
#include "constants.h"
#include "thermistor.h"

// --- Thermistor ------------------------
void Thermistor::begin() const {
    pinMode(analog_pin_, INPUT);

    if (power_pin_ != NO_PIN) {
        pinMode(power_pin_, OUTPUT);
    }
}

void Thermistor::power_off() const {
    if (power_pin_ != NO_PIN) {
        digitalWrite(power_pin_, LOW);
    }
}

void Thermistor::power_on() const {
    if (power_pin_ != NO_PIN) {
        digitalWrite(power_pin_, HIGH);
    }
}

float Thermistor::read_voltage() const {
    const auto vout = static_cast<float>(analogReadMilliVolts(analog_pin_) / 1000.0);
    if (vout < 0.001f || vout > (THERMISTOR_SUPPLY_VOLTAGE - 0.001f)) {
        return NAN; // Safely bail out
    }
    return vout;
}

float Thermistor::sample() const {
    // Thermistor on the top of the resistor divider
    const float vout = read_voltage();
    return vout; // meyere
    if (isnan(vout)) {
        return DEFAULT_TEMPERATURE_CELSIUS;
    }
    const float r_therm =
        (THERMISTOR_R2_BOTTOM_RESISTOR * (THERMISTOR_SUPPLY_VOLTAGE - vout))
        / vout;

    const float inv_T = STEINHART_HART_A
                      + (STEINHART_HART_B * logf(r_therm))
                      + (STEINHART_HART_C * powf(logf(r_therm), 3));

    const float celsius = (1.0f / inv_T) - 273.15f;

    if (MIN_TEMPERATURE_CELSIUS < celsius and celsius < MAX_TEMPERATURE_CELSIUS) {
        return celsius;
    }
    return DEFAULT_TEMPERATURE_CELSIUS;
}

// --- MultiThermistor -------------------
void MultiThermistor::begin() {
    for (auto ii = 0; ii < TEMPERATURE_SENSOR_COUNT; ++ii) {
        add_device(new Thermistor(get_temperature_pin(ii), power_pin_));
    }

    for (const auto* device : devices_) {
        if (device) device->begin();
    }

#if POWER_CONTROL
    power_off();
#else
    power_on();
#endif
}

void MultiThermistor::power_off() const {
#if POWER_CONTROL
    for (const auto* device : devices_) {
        device->power_off();
    }
#endif
}

void MultiThermistor::power_on() const {
#if POWER_CONTROL
    for (const auto* device : devices_) {
        device->power_on();
    }
#endif
}

std::vector<float> MultiThermistor::sample() const {
    std::vector<float> readings;
    readings.reserve(devices_.size());
    for (const auto* therm : devices_) {
        readings.push_back(therm->sample());
    }
    return readings;
}

