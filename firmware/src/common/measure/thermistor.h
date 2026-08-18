#pragma once

#include <vector>
#include "constants.h"
#include "build_cfg.h"

// Select thermistor hardware version
#define THERMISTOR_HW_0 false
#define THERMISTOR_HW_1 true
#if !(THERMISTOR_HW_0 ^ THERMISTOR_HW_1)
#error "Select exactly one thermistor hardware."
#endif

constexpr float MIN_TEMPERATURE_CELSIUS = -20.0f;
constexpr float MAX_TEMPERATURE_CELSIUS = 70.0f;

constexpr float THERMISTOR_NOMINAL_TEMPERATURE = 298.15f;  // Kelvin (25°C)

#if THERMISTOR_HW == 0
// Eaton NRNE105H4100B1H
constexpr bool THERMISTOR_ON_TOP = true;
constexpr float THERMISTOR_DIVIDER_RESISTOR = 100000.0f;
constexpr float THERMISTOR_SUPPLY_VOLTAGE = 2.7f;
constexpr float STEINHART_HART_A = 1.003702421E-3f;
constexpr float STEINHART_HART_B = 1.811901925E-4f;
constexpr float STEINHART_HART_C = 1.731869483E-7f;
#elif THERMISTOR_HW == 1
// Eaton NRNE105H4100B1H
constexpr bool THERMISTOR_ON_TOP_OF_DIVIDER = true;
constexpr float THERMISTOR_DIVIDER_RESISTOR = 15000.0f;
constexpr float THERMISTOR_SUPPLY_VOLTAGE = 3.3f;
constexpr float STEINHART_HART_A = 1.003702421E-3f;
constexpr float STEINHART_HART_B = 1.811901925E-4f;
constexpr float STEINHART_HART_C = 1.731869483E-7f;
#elif THERMISTOR_HW == 2
// Unknown - found in Creality HM-01 chamber heater
constexpr bool THERMISTOR_ON_TOP_OF_DIVIDER = false;
constexpr float THERMISTOR_DIVIDER_RESISTOR = 50000.0f;
constexpr float THERMISTOR_SUPPLY_VOLTAGE = 5.0f;

constexpr float STEINHART_HART_A = 1.17745599E-2f;
constexpr float STEINHART_HART_B = -1.55698289E-3f;
constexpr float STEINHART_HART_C = 7.41006996E-6f;
#endif


class Thermistor {
    static constexpr float DEFAULT_TEMPERATURE_CELSIUS = 22.0;
public:

    explicit Thermistor(
        const uint8_t analog_pin)
        : analog_pin_(analog_pin) {}

    // Initialize ADC pin
    void begin() const;

    // Measure temperature in °C (default Steinhart-Hart)
    float sample() const;

private:
    // Convert raw ADC value to output voltage
    float read_voltage() const;

    uint8_t analog_pin_;
};

// Multiple thermistors, analogous to MultiHX711
class MultiThermistor {
public:
    // Initialize all thermistors
    void begin();

    // Add a thermistor to the collection
    void add_device(Thermistor* therm) {
        if (therm) devices_.push_back(therm);
    }

    static void power_off();
    static void power_on();

    // Sample all thermistors (Steinhart–Hart method)
    std::vector<float> sample() const;

private:
    std::vector<Thermistor*> devices_;
};
