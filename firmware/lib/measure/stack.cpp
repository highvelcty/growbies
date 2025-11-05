#include "stack.h"

namespace growbies_hf {


void MeasurementStack::begin() const {

}

void MeasurementStack::update() const {
    // Sample low-level sensors
    std::vector<int32_t> mass_values;
    std::vector<float> temp_values;

    if (multi_hx711_) mass_values = multi_hx711_->sample();
    if (multi_thermistor_) temp_values = multi_thermistor_->sample();

    // Update MeasurementChannels
    for (auto* ch_collection : channels_) {
        if (!ch_collection) continue;

        // Mass channels
        auto mass_ch = ch_collection->get_channels_by_type(SensorType::MASS);
        for (size_t i = 0; i < mass_ch.size() && i < mass_values.size(); ++i) {
            mass_ch[i]->update(static_cast<float>(mass_values[i]));
        }

        // Temperature channels
        auto temp_ch = ch_collection->get_channels_by_type(SensorType::TEMPERATURE);
        for (size_t i = 0; i < temp_ch.size() && i < temp_values.size(); ++i) {
            temp_ch[i]->update(temp_values[i]);
        }
    }
}


}  // namespace growbies_hf
