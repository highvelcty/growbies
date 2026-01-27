#pragma once
#include <Arduino.h>

namespace growbies_hf {

    /// Represents the type of sensor providing a measurement.
    /// Add new ones here as Growbies expands (light, humidity, etc.)
    enum class SensorType : uint8_t {
        MASS,
        TEMPERATURE,
        HUMIDITY,
        LIGHT,
        UNKNOWN,
    };

    // Flags for describing sample validity or acquisition errors
    struct SampleFlags {
        bool out_of_range    : 1;  // sensor exceeded load range
        bool timeout         : 1;  // sensor read timeout
        bool reserved        : 5;  // reserved for expansion

        constexpr SampleFlags() : out_of_range(false), timeout(false), reserved(false) {}
    };
}  // namespace growbies_hf
