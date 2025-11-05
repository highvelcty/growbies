#include "stack.h"

namespace growbies_hf {

void MeasurementStack::add_channels(MeasurementChannels* channels) {
    if (channels) channels_.push_back(channels);
}

void MeasurementStack::set_hx711_driver(MultiHX711* hx) {
    multi_hx711_ = hx;
}

void MeasurementStack::set_thermistor_driver(MultiThermistor* thermistors) {
    multi_thermistor_ = thermistors;
}

void MeasurementStack::begin() const {
    // Initialize low-level drivers first
    if (multi_hx711_) multi_hx711_->begin();
    if (multi_thermistor_) multi_thermistor_->begin();

    // Initialize all channel collections (no-op in current design, placeholder)
    for (const auto* ch : channels_) {
        // Could add per-channel initialization if needed
        (void)ch;
    }
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

std::vector<MeasurementChannel*> MeasurementStack::get_mass_channels() const {
    std::vector<MeasurementChannel*> result;
    for (auto* ch_collection : channels_) {
        if (!ch_collection) continue;
        auto chs = ch_collection->get_channels_by_type(SensorType::MASS);
        result.insert(result.end(), chs.begin(), chs.end());
    }
    return result;
}

std::vector<MeasurementChannel*> MeasurementStack::get_temperature_channels() const {
    std::vector<MeasurementChannel*> result;
    for (auto* ch_collection : channels_) {
        if (!ch_collection) continue;
        auto chs = ch_collection->get_channels_by_type(SensorType::TEMPERATURE);
        result.insert(result.end(), chs.begin(), chs.end());
    }
    return result;
}

}  // namespace growbies_hf
