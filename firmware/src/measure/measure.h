#pragma once

#include <vector>
#include "filter.h"
#include "nvm/nvm.h"

namespace growbies {

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

// -------------------------------
// Aggregate TEMPERATURE channels
// -------------------------------
class AggregateTemperature {

public:
    explicit AggregateTemperature(const size_t num_sensors)
        : channels_(num_sensors,
            MeasurementChannel(SensorType::TEMPERATURE, MEDIAN_FILTER_BUF_SIZE))
    {}

    MeasurementChannel& channel(const size_t idx) { return channels_[idx]; }
    const MeasurementChannel& channel(const size_t idx) const { return channels_[idx]; }
    size_t size() const { return channels_.size(); }

    float average() const {
        const auto temps = sensor_temperatures();
        if (temps.empty()) return 0.0f;

        float sum = 0.0f;
        for (const float t : temps) sum += t;
        return sum / static_cast<float>(temps.size());
    }

    void reset() {
        for (auto& ch : channels_) {
            ch.reset();
        }
    }

    std::vector<float> sensor_temperatures() const {
        std::vector<float> temps;
        temps.reserve(channels_.size());
        const auto* nvm_cal = calibration_store->payload();
        const auto& sensors = nvm_cal->sensor;
        for (size_t ii = 0; ii < channels_.size(); ++ii) {
            auto& ch = channels_[ii];
            const auto& coeffs = sensors[ii].coeffs;
            temps.push_back(ch.value() - coeffs.thermistor_offset);
        }
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
    explicit AggregateMass(const size_t num_sensors, AggregateTemperature& temperature)
        : channels_(
              num_sensors,
              MeasurementChannel(SensorType::MASS, MEDIAN_FILTER_BUF_SIZE)),
          temperature_(temperature),
          per_sensor_mass_(num_sensors, 0.0f),
          total_mass_(0.0f)
    {}

    MeasurementChannel& channel(const size_t idx) { return channels_[idx]; }
    const MeasurementChannel& channel(const size_t idx) const { return channels_[idx]; }
    void reset() {
        for (auto& ch : channels_) {
            ch.reset();
        }

        std::fill(per_sensor_mass_.begin(), per_sensor_mass_.end(), 0.0f);
        total_mass_ = 0.0f;
    }
    const std::vector<float>& sensor_masses() const { return per_sensor_mass_; }
    size_t size() const { return channels_.size(); }
    float total_mass() const { return total_mass_; }

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
                    sensor_temp_value = temperature_.average();
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
                mass = calibrated_mass + delta_M_temp;
            }

            per_sensor_mass_[ii] = mass;
            total_mass_ += mass;
        }
    }

private:
    std::vector<MeasurementChannel> channels_;
    AggregateTemperature& temperature_;
    std::vector<float> per_sensor_mass_{};
    float total_mass_;
};

}
