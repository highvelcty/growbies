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

    float conditioned_total() const {
        const auto temps = sensor_temperatures();
        if (temps.empty()) return 0.0f;

        float sum = 0.0f;
        for (const float t : temps) sum += t;
        return sum / static_cast<float>(temps.size());

    }

    static float _get_thermistor_offset(size_t idx);

    void update() {
        for (size_t ii = 0; ii < channels_.size(); ++ii) {
            const auto& ch = channels_[ii];
            const float raw_temp = ch.value() + _get_thermistor_offset(ii);
            aewma_[ii].add(raw_temp);
        }
    }

    void reset_channels() {
        for (auto& ch : channels_) {
            ch.reset();
        }
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

        for (size_t ii = 0; ii < channels_.size(); ++ii) {
            temps.push_back(aewma_[ii].value());
        }

        return temps;
    }

private:
    std::vector<LinearAEWMABuffer> aewma_;
    std::vector<MeasurementChannel> channels_;
};

