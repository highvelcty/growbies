#include "build_cfg.h"
#include "flags.h"
#include "stack.h"
#include "common/protocol/command.h"
#include "scale/remote/remote_in.h"

void MeasurementStack::begin() {
    multi_hx711_.begin();
    multi_thermistor_.begin();

    aggregate_temp_ = new AggregateTemperature(TEMPERATURE_SENSOR_COUNT);
    aggregate_mass_ = new AggregateMass(MASS_SENSOR_COUNT, *aggregate_temp_);
}

void MeasurementStack::reset() const {
    aggregate_temp_->reset();
    aggregate_mass_->reset();
}

void MeasurementStack::update() const {
    aggregate_temp_->reset_channels();
    aggregate_mass_->reset_channels();

#if POWER_CONTROL
     power_on();
#endif

    for (int ii = 0; ii < MEDIAN_FILTER_BUF_SIZE; ++ii) {
        const HX711ReadyMask ready_mask = multi_hx711_.wait_ready();

        // There is some settling with the thermistor, and it is typically longer than mass,
        // hence this ordering.
        std::vector<float> mass_vals = multi_hx711_.sample();
        std::vector<Measurement> temp_measurements = multi_thermistor_.sample();

        for (size_t i = 0; i < temp_measurements.size() && i < aggregate_temp_->size(); ++i)
            aggregate_temp_->channel(i).update(temp_measurements[i].value,
                temp_measurements[i].error);
        for (size_t i = 0; i < mass_vals.size() && i < aggregate_mass_->size(); ++i)
            if (ready_mask & (1 << i)) {
                aggregate_mass_->channel(i).update(mass_vals[i]);
            }
            else {
                aggregate_mass_->channel(i).update(0.0f, ErrorCode::ERROR_NOT_READY);
            }
    }
    // 2026_06_02 meyere: analogReadMillivolts has the side effect of disconnecting
    // interrupts.
    RemoteIn::attach_interrupts();
#if POWER_CONTROL
    power_off();
#endif

    // Temperature before mass because mass is a function of temperature.
    aggregate_temp_->update();
    aggregate_mass_->update();
}
