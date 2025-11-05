#pragma once

#include <vector>
#include "measure.h"       // MeasurementChannels, MeasurementChannel
#include "hx711.h"         // HX711, MultiHX711
#include "thermistor2.h"   // Thermistor, MultiThermistor

namespace growbies_hf {

    /// Aggregates heterogeneous measurement channels and low-level drivers.
    class MeasurementStack {
    public:
        MeasurementStack() = default;

        // Add a collection of measurement channels (plural)
        void add_channels(MeasurementChannels* channels);

        // Set low-level drivers
        void set_hx711_driver(MultiHX711* hx);
        void set_thermistor_driver(MultiThermistor* thermistors);

        // Initialize all channels and low-level drivers
        void begin() const;

        // Sample all low-level sensors and update MeasurementChannels
        void update() const;

        // Access all channel collections
        const std::vector<MeasurementChannels*>& channels() const { return channels_; }

        // Convenience: get all mass or temperature channels across all collections
        std::vector<MeasurementChannel*> get_mass_channels() const;
        std::vector<MeasurementChannel*> get_temperature_channels() const;

    private:
        std::vector<MeasurementChannels*> channels_;
        MultiHX711* multi_hx711_ = nullptr;
        MultiThermistor* multi_thermistor_ = nullptr;
    };

}  // namespace growbies_hf
