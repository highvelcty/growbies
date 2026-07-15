#pragma once

#include "constants.h"
#include "hx711.h"
#include "common/measure/aggregate_temperature.h"
#include "common/measure/thermistor.h"
#include "scale/measure/aggregate_mass.h"

class MeasurementStack {
public:
    static MeasurementStack& get() {
        static MeasurementStack instance;
        return instance;
    }

    MeasurementStack(const MeasurementStack&) = delete;
    MeasurementStack& operator=(const MeasurementStack&) = delete;

    void begin();
    void reset() const;
    void update() const;

    void power_off() const { multi_hx711_.power_off(); }
    void power_on() const { multi_hx711_.power_on(); }

    AggregateMass& aggregate_mass() const noexcept { return *aggregate_mass_; }
    AggregateTemperature& aggregate_temp() const noexcept { return *aggregate_temp_; }

private:
    MeasurementStack() = default;

    MultiHX711 multi_hx711_{};
    MultiThermistor multi_thermistor_{SWITCHED_PWR_PIN};
    AggregateTemperature* aggregate_temp_ = nullptr;
    AggregateMass* aggregate_mass_ = nullptr;
};
