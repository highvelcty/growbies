#include "build_cfg.h"
#include "stack.h"

namespace growbies_hf {

    void MeasurementStack::begin() {
        multi_hx711_.begin();
        multi_thermistor_.begin();

        aggregate_temp_ = new AggregateTemperature(TEMPERATURE_SENSOR_COUNT);
        aggregate_mass_ = new AggregateMass(MASS_SENSOR_COUNT, *aggregate_temp_);
    }

    void MeasurementStack::update() const {
        multi_hx711_.power_on();
        const bool ready = multi_hx711_.wait_ready();

        std::vector<float> mass_vals, temp_vals;
        if (ready) {
            // Sample mass before temperature to give thermistors settling time
            mass_vals = multi_hx711_.sample();
            temp_vals = multi_thermistor_.sample();
        }
        multi_hx711_.power_off();

        if (!ready) return;

        // Update temperature before mass as mass is a function of temperature.
        for (size_t i = 0; i < temp_vals.size() && i < aggregate_temp_->size(); ++i)
            aggregate_temp_->channel(i).update(temp_vals[i]);

        for (size_t i = 0; i < mass_vals.size() && i < aggregate_mass_->size(); ++i)
            aggregate_mass_->channel(i).update(mass_vals[i]);
        aggregate_mass_->update();
    }

}  // namespace growbies_hf
