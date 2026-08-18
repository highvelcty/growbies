#pragma once

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

    static void power_off() { MultiHX711::power_off(); MultiThermistor::power_off(); }
    static void power_on() { MultiHX711::power_on(); MultiThermistor::power_on(); }

    AggregateMass& aggregate_mass() const noexcept { return *aggregate_mass_; }
    AggregateTemperature& aggregate_temp() const noexcept { return *aggregate_temp_; }

private:
    MeasurementStack() = default;

    MultiHX711 multi_hx711_{};
    MultiThermistor multi_thermistor_{};
    AggregateTemperature* aggregate_temp_ = nullptr;
    AggregateMass* aggregate_mass_ = nullptr;
};
