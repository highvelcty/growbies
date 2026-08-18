#include "thermistor.h"
#include "build_cfg.h"
#include "flags.h"

// --- Thermistor ------------------------
void Thermistor::begin() const {
    pinMode(analog_pin_, INPUT);
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
    if (isnan(vout)) {
        return DEFAULT_TEMPERATURE_CELSIUS;
    }

    float r_therm;

    if (THERMISTOR_ON_TOP_OF_DIVIDER) {
        r_therm = (THERMISTOR_DIVIDER_RESISTOR * (THERMISTOR_SUPPLY_VOLTAGE - vout)) / vout;
    }
    else {
        r_therm = THERMISTOR_DIVIDER_RESISTOR * vout / (THERMISTOR_SUPPLY_VOLTAGE - vout);
    }

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
    if (SWITCHED_PWR_PIN != NO_PIN) {
        pinMode(SWITCHED_PWR_PIN, OUTPUT);
    }

    for (auto ii = 0; ii < TEMPERATURE_SENSOR_COUNT; ++ii) {
        add_device(new Thermistor(get_temperature_pin(ii)));
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

void MultiThermistor::power_off() {
    if (SWITCHED_PWR_PIN != NO_PIN) {
        if (INVERTED_SWITCHED_PWR_PIN) {
            digitalWrite(SWITCHED_PWR_PIN, HIGH);
        }
        else {
            digitalWrite(SWITCHED_PWR_PIN, LOW);
        }
    }
}

void MultiThermistor::power_on(){
    if (SWITCHED_PWR_PIN != NO_PIN) {
        if (INVERTED_SWITCHED_PWR_PIN) {
            digitalWrite(SWITCHED_PWR_PIN, LOW);
        }
        else {
            digitalWrite(SWITCHED_PWR_PIN, HIGH);
        }
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

