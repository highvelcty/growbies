#pragma once

#include "constants.h"
#include "measure.h"       // MeasurementChannels, MeasurementChannel
#include "hx711.h"         // HX711, MultiHX711
#include "thermistor2.h"   // Thermistor, MultiThermistor

namespace growbies_hf {

    // Aggregates heterogeneous measurement channels and low-level drivers.
    class MeasurementStack {
    public:
        // Initialize all channels and low-level drivers
        void begin() const;

        // Sample all low-level sensors and update MeasurementChannels
        void update() const;

    private:
        MeasurementChannels channels_;
        MultiHX711 multi_hx711_;
        MultiThermistor multi_thermistor_;
    };

}  // namespace growbies_hf
