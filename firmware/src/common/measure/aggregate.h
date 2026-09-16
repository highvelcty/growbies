#pragma once

#include <vector>
#include "common/protocol/error_code.h"
#include "common/measure/filter.h"

static constexpr size_t MEDIAN_FILTER_BUF_SIZE = 3;

enum class SensorType : uint8_t {
    MASS,
    TEMPERATURE,
    HUMIDITY,
    LIGHT,
    UNKNOWN,
};

struct Measurement {
    float value;
    ErrorCode error;
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
          value_(0.0f),
          error_code_(ErrorCode::ERROR_NONE)
    {}


    void reset() {
        median_filter_.reset();
        value_ = 0.0f;
        error_code_ = ErrorCode::ERROR_NONE;
    }

    SensorType type() const noexcept { return type_; }

    void update(
        const float raw_value,
        const ErrorCode error_code = ErrorCode::ERROR_NONE)
    {
        error_code_ = error_code;

        if (error_code_ == ErrorCode::ERROR_NONE)
            value_ = median_filter_.update(raw_value);
    }

    Measurement measurement() const noexcept {
        return { value_, error_code_, };
    }

    ErrorCode error_code() const noexcept { return error_code_; }

private:
    SensorType type_;
    SlidingMedianFilter median_filter_;
    float value_;
    ErrorCode error_code_;
};


class AggregateMeasurement {
public:
    explicit AggregateMeasurement(
        const size_t num_sensors,
        SensorType sensor_type)
        : error_code_(ErrorCode::ERROR_NONE)
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

    ErrorCode error_code() const noexcept {
        return error_code_;
    }

    virtual void update() = 0;

    virtual void reset() {
        reset_channels();

        for (auto& value : per_sensor_values_) {
            value = 0.0f;
        }

        error_code_ = ErrorCode::ERROR_NONE;
    }

protected:
    void reset_channels() {
        for (auto& ch : channels_) {
            ch.reset();
        }
    }

    std::vector<MeasurementChannel> channels_;
    std::vector<float> per_sensor_values_;
    ErrorCode error_code_;
};

