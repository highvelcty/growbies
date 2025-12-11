#pragma once

#include <vector>
#include <array>
#include "filter.h"
#include "hx711.h"
#include "nvm/nvm.h"
#include "sample.h"

namespace growbies_hf {

// -------------------------------
// Single measurement channel
// -------------------------------
    class MeasurementChannel {
    public:
        explicit MeasurementChannel(const SensorType type,
                                    const float gross_min = -1e6f,
                                    const float gross_max = 1e6f,
                                    const float alpha = 0.2f)
            : type_(type),
              gross_filter_(gross_min, gross_max),
              smoother_(alpha),
              last_smoothed_(0.0f) {}

    Sample update(const float raw_value) {
        // Gross threshold filter
        const auto filtered = gross_filter_.update(raw_value);
        if (!filtered.valid) {
            flags_.valid = false;
            flags_.out_of_range = true;
            return Sample(raw_value, type_, flags_);
        }

        flags_.valid = true;
        flags_.out_of_range = false;

        // Median filter
        const float median_value = median_filter_.update(filtered.value);

        // IIR smoothing
        last_smoothed_ = smoother_.update(median_value);

        return Sample(last_smoothed_, type_, flags_);
    }

    float value() const noexcept { return last_smoothed_; }
    float last_valid() const noexcept { return gross_filter_.last_valid(); }
    void reset() {
        gross_filter_.reset();
        median_filter_.reset();
        smoother_.reset();
        last_smoothed_ = 0.0f;
    }

    SensorType type() const noexcept { return type_; }

private:
    SensorType type_;
    SampleFlags flags_{};
    GrossThresholdFilter gross_filter_;
    SlidingMedianFilter median_filter_;
    IIRSmoother smoother_;
    float last_smoothed_;
};

// -------------------------------
// Aggregate TEMPERATURE channels
// -------------------------------
class AggregateTemperature {
public:
    explicit AggregateTemperature(const size_t num_sensors)
        : channels_(num_sensors, MeasurementChannel(SensorType::TEMPERATURE)) {}

    MeasurementChannel& channel(const size_t idx) { return channels_[idx]; }
    const MeasurementChannel& channel(const size_t idx) const { return channels_[idx]; }
    size_t size() const { return channels_.size(); }

    float average() const {
        float sum = 0.0f;
        for (const auto& ch : channels_) sum += ch.value();
        return channels_.empty() ? 0.0f : sum / static_cast<float>(channels_.size());
    }

    std::vector<float> sensor_temperatures() const {
        std::vector<float> temps;
        temps.reserve(channels_.size());
        for (const auto& ch : channels_) temps.push_back(ch.value());
        return temps;
    }


private:
    std::vector<MeasurementChannel> channels_;
};

// -------------------------------
// Aggregate MASS channels
// -------------------------------
class AggregateMass {
public:
    explicit AggregateMass(const size_t num_sensors, AggregateTemperature* temperature)
        : channels_(num_sensors, MeasurementChannel(SensorType::MASS)),
          temperature_(temperature),
          per_sensor_mass_(num_sensors, 0.0f),
          rate_index_(0),
          rate_count_(0),
          last_mass_(0.0f),
          last_rate_(0.0f)
    {
        mass_buffer_.fill(0.0f);
        timestamp_buffer_.fill(0);
    }

    MeasurementChannel& channel(const size_t idx) { return channels_[idx]; }
    const MeasurementChannel& channel(const size_t idx) const { return channels_[idx]; }
    size_t size() const { return channels_.size(); }

    void update() {
        float total = 0.0f;

        // ---- Load Calibration ----
        const auto* nvm_cal = calibration_store->payload();
        const auto& cal_hdr = nvm_cal->hdr;
        const auto& sensors = nvm_cal->sensor;
        const float Tref = cal_hdr.ref_temperature;
        const float dT = (temperature_ ? temperature_->average() : 0.0f) - Tref;

        for (size_t ii = 0; ii < channels_.size(); ++ii) {
            auto& ch = channels_[ii];
            float mass = ch.value();

            if (ii < cal_hdr.mass_sensor_count) {
                const auto& coeffs = sensors[ii].coeffs;
                // M = c0 + c1*M + c2*dT + c3*(M*dT) + c4*(dT²) + c5*(M²)
                mass = coeffs.mass_offset
                     + coeffs.mass_slope * mass
                     + coeffs.temperature_slope * dT
                     + coeffs.mass_cross_temperature * (mass * dT)
                     + coeffs.quadratic_temperature * (dT * dT)
                     + coeffs.quadratic_mass * (mass * mass);
            }

            per_sensor_mass_[ii] = mass;
            total += mass;
        }

        // --- Rate calculation ---
        const uint32_t now = millis();
        mass_buffer_[rate_index_] = total;
        timestamp_buffer_[rate_index_] = now;

        rate_index_ = (rate_index_ + 1) % RATE_WINDOW_SIZE;
        if (rate_count_ < RATE_WINDOW_SIZE) ++rate_count_;

        if (rate_count_ > 1) {
            const size_t oldest = (rate_index_ + RATE_WINDOW_SIZE - rate_count_) % RATE_WINDOW_SIZE;
            const float delta_mass = total - mass_buffer_[oldest];
            const auto delta_time = static_cast<float>(now - timestamp_buffer_[oldest]);
            last_rate_ = (delta_time > 0) ? (delta_mass / (delta_time / 1000.0f)) : 0.0f;
        } else {
            last_rate_ = 0.0f;
        }

        last_mass_ = total;
    }

    float mass_rate() const { return last_rate_; }
    const std::vector<float>& sensor_masses() const { return per_sensor_mass_; }
    float total_mass() const { return last_mass_; }


private:
    static constexpr size_t RATE_WINDOW_SIZE = 5;
    std::vector<MeasurementChannel> channels_;
    AggregateTemperature* temperature_;

    std::array<float, RATE_WINDOW_SIZE> mass_buffer_{};
    std::array<uint32_t, RATE_WINDOW_SIZE> timestamp_buffer_{};
    std::vector<float> per_sensor_mass_{};
    size_t rate_index_;
    size_t rate_count_;
    float last_mass_;
    float last_rate_;
};

}  // namespace growbies_hf
