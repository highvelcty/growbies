#pragma once

#include <Arduino.h>
#include <vector>

namespace growbies_hf {

// Select thermistor hardware version
#define THERMISTOR_HW_0 true
#define THERMISTOR_HW_1 false
    static_assert(!THERMISTOR_HW_0 != !THERMISTOR_HW_1, "Select exactly one thermistor hardware version.");

#if THERMISTOR_HW_0
    // Eaton NRNE105H4100B1H configuration (THERMISTOR_HW_0)
    constexpr float THERMISTOR_SERIES_RESISTOR = 100000.0f;
    constexpr float THERMISTOR_NOMINAL_RESISTANCE = 100000.0f;
    constexpr float THERMISTOR_NOMINAL_TEMPERATURE = 298.15f;  // Kelvin (25°C)
    constexpr float THERMISTOR_SUPPLY_VOLTAGE = 2.7f;
    constexpr float THERMISTOR_BETA_COEFF = 4100.0f;
    constexpr float STEINHART_HART_A = 1.003702421E-3f;
    constexpr float STEINHART_HART_B = 1.811901925E-4f;
    constexpr float STEINHART_HART_C = 1.731869483E-7f;
#endif

    class Thermistor {
    public:
        explicit Thermistor(const uint8_t analog_pin) : analog_pin_(analog_pin) {}

        // Initialize ADC pin
        void begin() const;

        // Measure temperature in °C (default Steinhart-Hart)
        float sample() const;

        // Optionally measure using Beta method
        float sample_beta() const;

    private:
        // Convert raw ADC value to output voltage
        float read_voltage() const;

        uint8_t analog_pin_;
    };

    // Multiple thermistors, analogous to MultiHX711
    class MultiThermistor {
    public:
        explicit MultiThermistor() = default;

        // Initialize all thermistors
        void begin();

        // Add a thermistor to the collection
        void add_device(Thermistor* therm) {
            if (therm) devices_.push_back(therm);
        }

        // Sample all thermistors (Steinhart–Hart method)
        std::vector<float> sample() const;

        // Sample all thermistors (Beta method)
        std::vector<float> sample_beta() const;

    private:
        std::vector<Thermistor*> devices_;
    };


}  // namespace growbies_hf
