#include "build_cfg.h"
#include "measure_intf.h"

namespace growbies_hf {

void MeasurementStack::begin() {
    multi_hx711_.begin();
    multi_thermistor_.begin();

    // Register channels to match hardware configuration
    // (replace the counts/types with actual numbers)
    for (size_t ii = 0; ii < MASS_SENSOR_COUNT; ++ii) {
        channels_.add_channel(SensorType::MASS);
    }

    for (size_t ii = 0; ii < TEMPERATURE_SENSOR_COUNT; ++ii) {
        channels_.add_channel(SensorType::TEMPERATURE);
    }

    // Build aggregation references
    const auto mass_channels = channels_.get_by_type(SensorType::MASS);
    const auto temp_channels = channels_.get_by_type(SensorType::TEMPERATURE);

    aggregate_mass_ = AggregateMass(mass_channels, temp_channels);
    aggregate_temp_ = AggregateTemperature(temp_channels);
}

void MeasurementStack::update() {
    std::vector<float> mass_values;
    std::vector<float> temp_values;

    multi_hx711_.power_on();
    const bool ready = multi_hx711_.wait_ready();
    if (ready) {
        mass_values = multi_hx711_.sample();
        temp_values  = multi_thermistor_.sample();
    }
    multi_hx711_.power_off();

    if (ready) {
        // Update MASS channels
        const auto mass_channels = channels_.get_by_type(SensorType::MASS);
        for (size_t ii = 0; ii < mass_channels.size() && ii < mass_values.size(); ++ii) {
            mass_channels[ii]->update(mass_values[ii]);
        }
        aggregate_mass_.update();

        // Update TEMPERATURE channels
        const auto temp_channels = channels_.get_by_type(SensorType::TEMPERATURE);
        for (size_t ii = 0; ii < temp_channels.size() && ii < temp_values.size(); ++ii) {
            temp_channels[ii]->update(temp_values[ii]);
        }
    }
}

}  // namespace growbies_hf
