#pragma once

#include <cstdint>
#include <vector>
#include "common/measure/filter.h"

static constexpr size_t MEDIAN_FILTER_BUF_SIZE = 3;

enum class SensorType : uint8_t {
    MASS,
    TEMPERATURE,
    HUMIDITY,
    LIGHT,
    UNKNOWN,
};

// -------------------------------
// Single measurement channel
// -------------------------------
class MeasurementChannel {
public:
    explicit MeasurementChannel(
        const SensorType type,
        const size_t median_window_size)
        : type_(type),
          median_filter_(median_window_size),
          value_(0.0f)
    {}


    void reset() {
        median_filter_.reset();
        value_ = 0.0f;
    }

    SensorType type() const noexcept { return type_; }

    void update(const float raw_value) {
        value_ = median_filter_.update(raw_value);
    }

    float value() const noexcept { return value_; }

private:
    SensorType type_;
    SlidingMedianFilter median_filter_;
    float value_;
};


class AggregateMeasurement {
public:
    explicit AggregateMeasurement(
        const size_t num_sensors,
        SensorType sensor_type)
    {
        channels_.reserve(num_sensors);
        per_sensor_values_.reserve(num_sensors);

        for (size_t ii = 0; ii < num_sensors; ++ii) {
            channels_.emplace_back(
                sensor_type,
                MEDIAN_FILTER_BUF_SIZE);

            per_sensor_values_.push_back(0.0f);
        }
    }

    virtual ~AggregateMeasurement() = default;

    MeasurementChannel& channel(const size_t idx) {
        return channels_[idx];
    }

    const MeasurementChannel& channel(const size_t idx) const {
        return channels_[idx];
    }

    size_t size() const {
        return channels_.size();
    }

    const std::vector<float>& sensor_values() const {
        return per_sensor_values_;
    }

    virtual void update() = 0;

    virtual void reset() {
        reset_channels();

        for (auto& value : per_sensor_values_) {
            value = 0.0f;
        }
    }

protected:
    void reset_channels() {
        for (auto& ch : channels_) {
            ch.reset();
        }
    }

    std::vector<MeasurementChannel> channels_;
    std::vector<float> per_sensor_values_;
};