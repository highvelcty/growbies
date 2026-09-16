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
        _per_sensor_measurement(
            num_sensors,
            Measurement{ 0.0f, ErrorCode::ERROR_NONE }),
        _mass(0.0f)
    {}

    MeasurementChannel& channel(const size_t idx) { return channels_[idx]; }
    const MeasurementChannel& channel(const size_t idx) const { return channels_[idx]; }

    void reset_channels() {
        for (auto& ch : channels_) {
            ch.reset();
        }

        for (auto& measurement : _per_sensor_measurement) {
            measurement = {
                0.0f,
                ErrorCode::ERROR_NONE,
            };
        }
        _mass = 0.0f;
        _error = ErrorCode::ERROR_NONE;
    }

    void reset() {
        aewma_buffer_.reset();
        reset_channels();
    }

    const std::vector<Measurement>& sensor_measurements() const {
        return _per_sensor_measurement;
    }

    size_t size() const {
        return channels_.size();
    }

    Measurement conditioned_total() const {
        return {
            aewma_buffer_.value(),
            _error,
        };
    }

    bool is_event_tripped() const {
        return aewma_buffer_.error() >= EVENT_THRESH_GRAMS;
    }

    void update() {
        _mass = 0.0f;
        _error = ErrorCode::ERROR_NONE;

        // ---- Load Calibration ----
        const auto* nvm_cal = calibration_store->payload();
        const auto& cal_hdr = nvm_cal->hdr;
        const auto& sensors = nvm_cal->sensor;
        const float Tref = cal_hdr.ref_temperature;
        const auto temperatures = temperature_.sensor_temperatures();

        for (size_t ii = 0; ii < channels_.size(); ++ii) {
            const auto& ch = channels_[ii];
            const Measurement measurement = ch.measurement();

            if (measurement.error != ErrorCode::ERROR_NONE) {
                _per_sensor_measurement[ii] = {
                    0.0f,
                    measurement.error,
                };
                _error = ErrorCode::ERROR_MEASUREMENT_DEGRADED;
                continue;
            }

            // Retrieve coefficients for this sensor
            const auto& coeffs = sensors[ii].coeffs;

            // Retrieve temperature for this sensor
            const Measurement temp_measurement = temperatures[ii];

            // --- Mass calibration ---
            const float calibrated_mass =
                coeffs.mass_offset
                + coeffs.mass_slope * measurement.value
                + coeffs.mass_quadratic * measurement.value
                  * measurement.value;

            // --- Temperature correction ---
            const float dT = temp_measurement.value - Tref;
            const float delta_M_temp =
                coeffs.temperature_offset
                + coeffs.temperature_slope * dT
                + coeffs.temperature_quadratic * dT * dT;

            const float mass = calibrated_mass - delta_M_temp;

            _per_sensor_measurement[ii] = {
                mass,
                measurement.error,
            };
        }

        // If every sensor was invalid, there is no valid aggregate.
        bool has_valid_sensor = false;
        for (const auto& ch : channels_) {
            if (ch.measurement().error == ErrorCode::ERROR_NONE) {
                has_valid_sensor = true;
                break;
            }
        }
        if (!has_valid_sensor) {
            _error = ErrorCode::ERROR_MEASUREMENT_FAILED;
            _mass = 0.0f;
            return;
        }

        // Estimate any invalid sensor measurements from the valid sensors.
        if (_error == ErrorCode::ERROR_MEASUREMENT_DEGRADED) {
            _estimate();
        }

        // Sum the calibrated and estimated sensor masses.
        for (const auto& measurement : _per_sensor_measurement) {
            _mass += measurement.value;
        }

        // Subtract global tare
        _mass -= tare_store->payload()->tares[TareIdx::GLOBAL].value;

        aewma_buffer_.add(_mass);
    }

private:
    void _estimate() {
        float valid_mass_sum = 0.0f;
        size_t valid_mass_count = 0;

        for (size_t ii = 0; ii < channels_.size(); ++ii) {
            if (_per_sensor_measurement[ii].error
                == ErrorCode::ERROR_NONE) {
                valid_mass_sum += _per_sensor_measurement[ii].value;
                ++valid_mass_count;
            }
        }

        if (valid_mass_count == 0) {
            return;
        }

        const float estimated_mass =
            valid_mass_sum / static_cast<float>(valid_mass_count);

        for (size_t ii = 0; ii < channels_.size(); ++ii) {
            if (_per_sensor_measurement[ii].error != ErrorCode::ERROR_NONE) {
                _per_sensor_measurement[ii] = {
                    estimated_mass,
                    ErrorCode::ERROR_MEASUREMENT_DEGRADED,
                };
                }
        }
    }

    LogisticAEWMABuffer aewma_buffer_;
    std::vector<MeasurementChannel> channels_;
    AggregateTemperature& temperature_;
    std::vector<Measurement> _per_sensor_measurement{};
    float _mass;
    ErrorCode _error = ErrorCode::ERROR_NONE;
};

