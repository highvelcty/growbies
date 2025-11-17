#pragma once

#include <vector>
#include <array>

#include "filter.h"
#include "hx711.h"
#include "nvm/nvm.h"
#include "sample.h"


namespace growbies_hf {

    // Represents a single sensor measurement channel.
    class MeasurementChannel {
    public:
        explicit MeasurementChannel(const SensorType type,
                                    const float gross_min = -1e6f,
                                    const float gross_max = 1e6f,
                                    const float alpha = 0.2f)
            : type_(type),
              gross_filter_(gross_min, gross_max),
              smoother_(alpha),
              last_smoothed_(0.0f)
        {}

        Sample update(const float raw_value) {
            // 1. Gross threshold filter
            const auto filtered = gross_filter_.update(raw_value);
            if (!filtered.valid) {
                flags_.valid = false;
                flags_.out_of_range = true;
                return Sample(raw_value, type_, flags_);
            }
            flags_.valid = true;
            flags_.out_of_range = false;

            // 2. Median filter
            const float median_value = median_filter_.update(filtered.value);

            // 3. IIR smoothing
            const float smooth_value = smoother_.update(median_value);
            last_smoothed_ = smooth_value;

            return Sample(smooth_value, type_, flags_);
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
    // Multiple measurement channels
    // -------------------------------
    class MeasurementChannels {
    public:
        MeasurementChannels() = default;

        void add_channel(SensorType type,
                         float min = -1e6f,
                         float max = 1e6f,
                         float alpha = 0.2f) {
            channels_.emplace_back(type, min, max, alpha);
        }

        MeasurementChannel* get_by_idx(const size_t index) {
            if (index < channels_.size()) return &channels_[index];
            return nullptr;
        }

        // Return a vector of pointers to channels of a specific type
        std::vector<MeasurementChannel*> get_by_type(const SensorType type) {
            std::vector<MeasurementChannel*> result;
            for (auto& ch : channels_) {
                if (ch.type() == type) {
                    result.push_back(&ch);
                }
            }
            return result;
        }


        void update_all(const std::vector<float>& values) {
            for (size_t i = 0; i < channels_.size() && i < values.size(); ++i) {
                channels_[i].update(values[i]);
            }
        }

        size_t num_channels() const noexcept { return channels_.size(); }

        const std::vector<MeasurementChannel>& channels() const noexcept { return channels_; }

    private:
        std::vector<MeasurementChannel> channels_;
    };

// -------------------------------
// Aggregates TEMPERATURE channels
// -------------------------------
class AggregateTemperature {
public:
    explicit AggregateTemperature(const std::vector<MeasurementChannel*>& temp_channels)
        : channels_(temp_channels) {}

    float average_temperature() const {
        float sum = 0.0f;
        size_t count = 0;
        for (const auto* ch : channels_) {
            if (ch && ch->type() == SensorType::TEMPERATURE) {
                sum += ch->value();
                ++count;
            }
        }
        return (count > 0) ? (sum / static_cast<float>(count)) : 0.0f;
    }

private:
    std::vector<MeasurementChannel*> channels_;
};

class AggregateMass {
public:
    explicit AggregateMass(const std::vector<MeasurementChannel*>& mass_channels,
                           AggregateTemperature* temperature)
        : channels_(mass_channels),
          temperature_(temperature),
          rate_index_(0),
          rate_count_(0),
          last_mass_(0.0f),
          last_rate_(0.0f)
    {
        mass_buffer_.fill(0.0f);
        timestamp_buffer_.fill(0);
    }

    void update() {
        float total = 0.0f;

        // ---- Load Calibration ----
        const auto* nvm_cal = calibration_store->payload();
        const auto& cal_hdr = nvm_cal->hdr;
        const auto& sensors = nvm_cal->sensor;

        const uint8_t sensor_count = cal_hdr.mass_sensor_count;
        const float Tref = cal_hdr.ref_temperature;

        // ---- Aggregate Temperature (via AggregateTemperature) ----
        const float T = (temperature_ != nullptr) ? temperature_->average_temperature() : 0.0f;
        const float dT = T - Tref;

        // ---- Per-sensor Mass Processing ----
        for (size_t ii = 0; ii < channels_.size(); ++ii) {
            const auto* ch = channels_[ii];
            if (!ch || ch->type() != SensorType::MASS) continue;

            float mass = ch->value();

            // Apply calibration only if sensor index is valid
            if (ii < sensor_count) {
                const auto& coeffs = sensors[ii].coeffs;

                // Full supported model:
                // M = c0 + c1*M + c2*dT + c3*(M*dT) + c4*(dT²) + c5*(M²)
                float corrected = coeffs.mass_offset;
                corrected += coeffs.mass_slope * mass;
                corrected += coeffs.temperature_slope * dT;
                corrected += coeffs.mass_cross_temperature * (mass * dT);
                corrected += coeffs.quadratic_temperature * (dT * dT);
                corrected += coeffs.quadratic_mass * (mass * mass);

                mass = corrected;
            }

            total += mass;
        }

        // --- Rate calculation section ---
        const uint32_t now = millis();
        mass_buffer_[rate_index_] = total;
        timestamp_buffer_[rate_index_] = now;

        rate_index_ = (rate_index_ + 1) % RATE_WINDOW_SIZE;
        if (rate_count_ < RATE_WINDOW_SIZE) ++rate_count_;

        if (rate_count_ > 1) {
            const size_t oldest_index =
                (rate_index_ + RATE_WINDOW_SIZE - rate_count_) % RATE_WINDOW_SIZE;
            const float delta_mass = total - mass_buffer_[oldest_index];
            const uint32_t delta_time_ms = now - timestamp_buffer_[oldest_index];
            last_rate_ = (delta_time_ms > 0)
                ? (delta_mass / (static_cast<float>(delta_time_ms) / 1000.0f))
                : 0.0f;
        } else {
            last_rate_ = 0.0f;
        }

        last_mass_ = total;
    }

        float total_mass() const { return last_mass_; }
        float mass_rate() const { return last_rate_; }

        void reset() {
            mass_buffer_.fill(0.0f);
            timestamp_buffer_.fill(0);
            rate_index_ = rate_count_ = 0;
            last_mass_ = last_rate_ = 0.0f;
        }

    private:
        static constexpr size_t RATE_WINDOW_SIZE = 5;

        std::vector<MeasurementChannel*> channels_;      // MASS channels
        AggregateTemperature* temperature_;

        std::array<float, RATE_WINDOW_SIZE> mass_buffer_{};
        std::array<uint32_t, RATE_WINDOW_SIZE> timestamp_buffer_{};
        size_t rate_index_;
        size_t rate_count_;
        float last_mass_;
        float last_rate_;
    };

}  // namespace growbies_hf
