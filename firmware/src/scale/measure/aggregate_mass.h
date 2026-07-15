#pragma once

#include <vector>
#include "common/measure/filter.h"
#include "common/measure/aggregate.h"
#include "common/measure/aggregate_temperature.h"
#include "scale/nvm/nvm.h"

// -------------------------------
// Aggregate MASS channels
// -------------------------------
constexpr float EVENT_THRESH_GRAMS = 50.0;
constexpr float EWMA_MASS_ALPHA_MIN = 0.1;
constexpr float EWMA_MASS_ALPHA_MAX = 0.7;
constexpr float EWMA_MASS_ALPHA_MID = 25;
constexpr float EWMA_MASS_STEEPNESS = 0.25;
class AggregateMass {
public:
    explicit AggregateMass(const size_t num_sensors, AggregateTemperature& temperature)
        :
          aewma_buffer_(EWMA_MASS_ALPHA_MIN, EWMA_MASS_ALPHA_MAX,
              EWMA_MASS_ALPHA_MID, EWMA_MASS_STEEPNESS,
              aewma_mass_buffer_initialized, aewma_mass_buffer_last_value),
        channels_(
            num_sensors,
            MeasurementChannel(SensorType::MASS, MEDIAN_FILTER_BUF_SIZE)),
        temperature_(temperature),
        per_sensor_mass_(num_sensors, 0.0f),
        total_mass_(0.0f)
    {}

    MeasurementChannel& channel(const size_t idx) { return channels_[idx]; }
    const MeasurementChannel& channel(const size_t idx) const { return channels_[idx]; }
    void reset_channels() {
        for (auto& ch : channels_) {
            ch.reset();
        }

        std::fill(per_sensor_mass_.begin(), per_sensor_mass_.end(), 0.0f);
        total_mass_ = 0.0f;
    }
    void reset() { aewma_buffer_.reset(); reset_channels(); }
    const std::vector<float>& sensor_masses() const { return per_sensor_mass_; }
    size_t size() const { return channels_.size(); }
    float conditioned_total() const { return aewma_buffer_.value(); }
    bool is_event_tripped() const { return aewma_buffer_.error() >= EVENT_THRESH_GRAMS; }

    void update() {
        total_mass_ = 0.0f;

        // ---- Load Calibration ----
        const auto* nvm_cal = calibration_store->payload();
        const auto& cal_hdr = nvm_cal->hdr;
        const auto& sensors = nvm_cal->sensor;
        const float Tref = cal_hdr.ref_temperature;

        for (size_t ii = 0; ii < channels_.size(); ++ii) {
            auto& ch = channels_[ii];
            float mass = ch.value();

            if (ii < cal_hdr.mass_sensor_count) {
                const auto& coeffs = sensors[ii].coeffs;


                // --- Per-sensor temperature if available ---
                float sensor_temp_value = 0.0f;
                if (ii < temperature_.size()) {
                    sensor_temp_value = temperature_.sensor_temperatures()[ii];
                }
                // Fallback to aggregate average
                else {
                    sensor_temp_value = temperature_.conditioned_total();
                }

                const float dT = sensor_temp_value - Tref;

                // --- Mass calibration ---
                const float calibrated_mass = coeffs.mass_offset
                                              + coeffs.mass_slope * mass
                                              + coeffs.mass_quadratic * mass * mass;


                // --- Temperature correction ---
                const float delta_M_temp = coeffs.temperature_offset
                                           + coeffs.temperature_slope * dT
                                           + coeffs.temperature_quadratic * dT * dT;

                // --- Total corrected mass ---
                mass = calibrated_mass - delta_M_temp;
            }

            per_sensor_mass_[ii] = mass;
            total_mass_ += mass;
        }

        // Subtract global tare
        total_mass_ -= tare_store->payload()->tares[TareIdx::GLOBAL].value;

        aewma_buffer_.add(total_mass_);
    }

private:
    LogisticAEWMABuffer aewma_buffer_;
    std::vector<MeasurementChannel> channels_;
    AggregateTemperature& temperature_;
    std::vector<float> per_sensor_mass_{};
    float total_mass_;
};
