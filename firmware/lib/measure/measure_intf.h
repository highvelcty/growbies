#pragma once

#include "measure.h"
#include "hx711.h"
#include "thermistor2.h"

namespace growbies_hf {

    // Aggregates heterogeneous measurement channels and low-level drivers.
    class MeasurementStack {
    public:
        // Return the application-global singleton
        static MeasurementStack& get() {
            static MeasurementStack instance;
            return instance;
        }

        // Delete copy/move constructors and assignment for singleton
        MeasurementStack(const MeasurementStack&) = delete;
        MeasurementStack& operator=(const MeasurementStack&) = delete;
        MeasurementStack(MeasurementStack&&) = delete;
        MeasurementStack& operator=(MeasurementStack&&) = delete;

        // Initialize all channels and low-level drivers
        void begin();

        void power_off() const { multi_hx711_.power_off(); }

        // Power on all devices
        void power_on() const { multi_hx711_.power_on(); }

        // Sample all low-level sensors and update MeasurementChannels
        void update();

        // Accessors for aggregates
        const AggregateMass& aggregate_mass() const noexcept { return aggregate_mass_; }
        const AggregateTemperature& aggregate_temp() const noexcept { return aggregate_temp_; }

        // Optional direct access if other modules need per-channel data
        const MeasurementChannels& channels() const noexcept { return channels_; }

    private:
        // Private constructor for singleton
        MeasurementStack() = default;

        MeasurementChannels channels_{};
        MultiHX711 multi_hx711_{};
        MultiThermistor multi_thermistor_{};
        AggregateMass aggregate_mass_{{}};
        AggregateTemperature aggregate_temp_{{}};
    };

}  // namespace growbies_hf
