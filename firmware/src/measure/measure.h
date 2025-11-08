#pragma once

#include <vector>
#include <array>

#include "sample.h"
#include "filter.h"
#include "hx711.h"

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

        // New overload for integer input
        Sample update(const int32_t raw_value) {
            float float_value;
            // Convert to float for MASS channels
            if (raw_value & (1UL << (HX711_DAC_BITS - 1))) {
                float_value = static_cast<float>(raw_value | (0xFFUL << HX711_DAC_BITS));
            }
            else {
                float_value = static_cast<float>(raw_value);
            }
            return update(float_value);
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
    // Aggregates mass channels
    // -------------------------------
    struct TempComp {
        float slope{0.0f};         // Linear coefficient a
        float offset{0.0f};        // Linear coefficient b
        float reference_temp{25.0f}; // Reference temperature at calibration
    };

    class AggregateMass {
    public:
        explicit AggregateMass(const std::vector<MeasurementChannel*>& mass_channels,
                               const std::vector<MeasurementChannel*>& temp_channels = {},
                               const std::vector<TempComp>& temp_comp = {})
            : channels_(mass_channels), temps_(temp_channels), comp_params_(temp_comp),
              rate_index_(0), rate_count_(0), last_mass_(0.0f), last_rate_(0.0f)
        {
            mass_buffer_.fill(0.0f);
            timestamp_buffer_.fill(0);
        }

        void update() {
            float total = 0.0f;

            // Apply temperature compensation per load cell
            for (size_t i = 0; i < channels_.size(); ++i) {
                const auto* ch = channels_[i];
                if (!ch || ch->type() != SensorType::MASS) continue;

                float mass = ch->value();

                // Apply temp compensation if parameters exist
                if (i < comp_params_.size()) {
                    float Tcell = 0.0f;
                    bool apply_temp_comp = false;

                    // If there is a temperature channel for this cell, use it
                    if (i < temps_.size() && temps_[i] && temps_[i]->type()
                        == SensorType::TEMPERATURE) {
                        Tcell = temps_[i]->value();
                        apply_temp_comp = true;
                    }
                    // Else if there is at least one shared temperature sensor, use the first
                    else if (!temps_.empty() && temps_[0] && temps_[0]->type()
                        == SensorType::TEMPERATURE) {
                        Tcell = temps_[0]->value();
                        apply_temp_comp = true;
                    }


                    // Apply compensation only if temperature reading is valid
                    if (apply_temp_comp) {
                        const auto& params = comp_params_[i];
                        mass += params.slope * (Tcell - params.reference_temp) + params.offset;
                    }
                }

                total += mass;
            }

            // Update circular buffer for rate calculation
            const uint32_t now = millis();
            mass_buffer_[rate_index_] = total;
            timestamp_buffer_[rate_index_] = now;

            rate_index_ = (rate_index_ + 1) % RATE_WINDOW_SIZE;
            if (rate_count_ < RATE_WINDOW_SIZE) ++rate_count_;

            // Calculate mass rate
            if (rate_count_ > 1) {
                const size_t oldest_index =
                    (rate_index_ + RATE_WINDOW_SIZE - rate_count_) % RATE_WINDOW_SIZE;
                const float delta_mass = total - mass_buffer_[oldest_index];
                const uint32_t delta_time_ms = now - timestamp_buffer_[oldest_index];
                last_rate_ = (delta_time_ms > 0) ?
                    (delta_mass / (static_cast<float>(delta_time_ms) / 1000.0f)) : 0.0f;
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
        std::vector<MeasurementChannel*> temps_;         // TEMPERATURE channels
        std::vector<TempComp> comp_params_;        // Temperature compensation params per channel

        std::array<float, RATE_WINDOW_SIZE> mass_buffer_{};
        std::array<uint32_t, RATE_WINDOW_SIZE> timestamp_buffer_{};
        size_t rate_index_;
        size_t rate_count_;
        float last_mass_;
        float last_rate_;
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

}  // namespace growbies_hf
