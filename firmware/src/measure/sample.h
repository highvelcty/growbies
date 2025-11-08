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
        bool valid           : 1;  // sample is valid
        bool out_of_range    : 1;  // sensor exceeded measurable limits
        bool timeout         : 1;  // sensor read timeout
        bool reserved        : 5;  // reserved for expansion

        constexpr SampleFlags() : valid(true), out_of_range(false),
                                  timeout(false), reserved(false) {}
    };

    // Represents one raw measurement sample before filtering.
    struct Sample {
        float value;                 // raw or calibrated value (grams, °C, etc.)
        SensorType type;             // which sensor produced it
        SampleFlags flags;           // status flags

        explicit constexpr Sample(const float v = 0.0f,
                const SensorType t = SensorType::UNKNOWN,
                const SampleFlags f = SampleFlags{})
            : value(v), type(t), flags(f) {}
    };

}  // namespace growbies_hf
