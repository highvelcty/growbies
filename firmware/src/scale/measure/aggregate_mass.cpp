#include "common/measure/aggregate_temperature.h"
#include "scale/nvm/nvm.h"

float AggregateTemperature::_get_thermistor_offset(const size_t idx) {
    const auto* nvm_cal = calibration_store->payload();
    const auto& sensors = nvm_cal->sensor;
    const auto& coeffs = sensors[idx].coeffs;
    return coeffs.thermistor_offset;
}

