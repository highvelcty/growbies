#pragma once

#include "aggregate.h"

constexpr float EWMA_TEMPERATURE_ALPHA_MIN = 0.05;
constexpr float EWMA_TEMPERATURE_ALPHA_MAX = 0.7;
constexpr float EWMA_TEMPERATURE_ALPHA_THRESH_CELSIUS = 2;
class AggregateTemperature {

public:
    explicit AggregateTemperature(const size_t num_sensors) {
        aewma_.reserve(num_sensors);
        channels_.reserve(num_sensors);

        for (size_t ii = 0; ii < num_sensors; ++ii) {
            aewma_.emplace_back(EWMA_TEMPERATURE_ALPHA_MIN, EWMA_TEMPERATURE_ALPHA_MAX,
                EWMA_TEMPERATURE_ALPHA_THRESH_CELSIUS,
                aewma_temp_buffer_initialized[ii], aewma_temp_buffer_last_value[ii]);

            channels_.emplace_back(SensorType::TEMPERATURE, MEDIAN_FILTER_BUF_SIZE);
        }
    }

    MeasurementChannel& channel(const size_t idx) { return channels_[idx]; }
    const MeasurementChannel& channel(const size_t idx) const { return channels_[idx]; }
    size_t size() const { return channels_.size(); }

    ErrorCode error_code() const noexcept {
        return error_code_;
    }

    float conditioned_total() const {
        const auto temps = sensor_temperatures();
        if (temps.empty()) return 0.0f;

        float sum = 0.0f;
        for (const float t : temps) sum += t;
        return sum / static_cast<float>(temps.size());

    }

    static float _get_thermistor_offset(size_t idx);

    void update() {
        error_code_ = ErrorCode::ERROR_NONE;

        size_t valid_sensor_count = 0;

        for (size_t ii = 0; ii < channels_.size(); ++ii) {
            const auto& ch = channels_[ii];
            const Measurement measurement = ch.measurement();

            if (measurement.error_code != ErrorCode::ERROR_NONE) {
                error_code_ = ErrorCode::ERROR_MEASUREMENT_DEGRADED;
                continue;
            }

            const float raw_temp = measurement.value + _get_thermistor_offset(ii);
            aewma_[ii].add(raw_temp);
            ++valid_sensor_count;
        }

        // If every sensor was invalid, there is no valid aggregate.
        if (valid_sensor_count == 0) {
            error_code_ = ErrorCode::ERROR_MEASUREMENT_FAILED;
        }
    }

    void reset_channels() {
        for (auto& ch : channels_) {
            ch.reset();
        }

        error_code_ = ErrorCode::ERROR_NONE;
    }
    void reset() {

        for (auto& buf : aewma_) {
            buf.reset();
        }

        reset_channels();
    }

    std::vector<float> sensor_temperatures() const {
        std::vector<float> temps;
        temps.reserve(channels_.size());

        float valid_temperature_sum = 0.0f;
        size_t valid_temperature_count = 0;

        for (size_t ii = 0; ii < channels_.size(); ++ii) {
            if (channels_[ii].measurement().error_code == ErrorCode::ERROR_NONE) {
                valid_temperature_sum += aewma_[ii].value();
                ++valid_temperature_count;
            }
        }

        if (valid_temperature_count == 0)
            return temps;

        const float estimated_temperature =
            valid_temperature_sum
            / static_cast<float>(valid_temperature_count);

        for (size_t ii = 0; ii < channels_.size(); ++ii) {
            if (channels_[ii].measurement().error_code == ErrorCode::ERROR_NONE) {
                temps.push_back(aewma_[ii].value());
            }
            else {
                temps.push_back(estimated_temperature);
            }
        }

        return temps;
    }

private:
    std::vector<LinearAEWMABuffer> aewma_;
    std::vector<MeasurementChannel> channels_;
    ErrorCode error_code_ = ErrorCode::ERROR_NONE;
};
