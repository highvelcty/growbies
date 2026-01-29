#pragma once

#include "constants.h"

class Battery {
public:
    // Voltage divider resistors
    static constexpr float R1 = 1e6f; // 1 MΩ
    static constexpr float R2 = 2e6f; // 2 MΩ
    static constexpr float CHARGING_VOLTAGE_THRESHOLD = 2.5;
    static constexpr float MIN_VOLTAGE = 3.0;
    static constexpr float MAX_VOLTAGE = 4.2;
    static constexpr float NINETY_PERCENT_VOLTAGE = 4.0;
    static constexpr float SEVENTY_PERCENT_VOLTAGE = 3.8;
    static constexpr float FORTY_PERCENT_VOLTAGE = 3.6;

    bool initialized = false;

    // Get the measured battery voltage
    float voltage() {
        initialize();
        // Read raw ADC value (assuming 12-bit ADC on ESP32, 0-4095)
        const auto adc_voltage =
            static_cast<float>(analogReadMilliVolts(BATTERY_SENSE_PIN) / 1000.0);

        // voltage divider: Vbat = Vadc * (R1 + R2) / R2
        return adc_voltage * (R1 + R2) / R2;
    }

    // Get battery percentage (0–100%)
    int percentage() {
        const float volts = voltage();

        // Clip voltage
        if (volts <= MIN_VOLTAGE) return 0;
        if (volts >= MAX_VOLTAGE) return 100;

        // Piecewise approximation based on typical LiPo discharge
        //
        // 90–100%
        if (volts >= NINETY_PERCENT_VOLTAGE) {
            return 90
                   + static_cast<int>((volts - NINETY_PERCENT_VOLTAGE)
                   / (MAX_VOLTAGE - NINETY_PERCENT_VOLTAGE) * 10);
        }
        // 70–90%
        if (volts >= SEVENTY_PERCENT_VOLTAGE) {
            return 70
                   + static_cast<int>((volts - SEVENTY_PERCENT_VOLTAGE)
                   / (NINETY_PERCENT_VOLTAGE - SEVENTY_PERCENT_VOLTAGE) * 20);
        }
        // 40–70%
        if (volts >= FORTY_PERCENT_VOLTAGE) {
            return 40
                   + static_cast<int>((volts - FORTY_PERCENT_VOLTAGE)
                   / (SEVENTY_PERCENT_VOLTAGE - FORTY_PERCENT_VOLTAGE) * 30);
        }

        // 0-40%%
        return static_cast<int>((volts - MIN_VOLTAGE)
               / (FORTY_PERCENT_VOLTAGE - MIN_VOLTAGE) * 40);
    }

    bool is_charging() {
        return voltage() <= CHARGING_VOLTAGE_THRESHOLD;
    }

private:
    void initialize() {
        if (initialized) {
            return;
        }
        pinMode(BATTERY_SENSE_PIN, INPUT);
        initialized = true;
    }
};