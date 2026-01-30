#pragma once
#include "measure.h"
#include "hx711.h"
#include "thermistor.h"

namespace growbies {

class MeasurementStack {
public:
    // HX711 filter needs to settle
    static MeasurementStack& get() {
        static MeasurementStack instance;
        return instance;
    }

    MeasurementStack(const MeasurementStack&) = delete;
    MeasurementStack& operator=(const MeasurementStack&) = delete;

    void begin();
    void update() const;

    void power_off() const { multi_hx711_.power_off(); }
    void power_on() const { multi_hx711_.power_on(); }

    const AggregateMass& aggregate_mass() const noexcept { return *aggregate_mass_; }
    const AggregateTemperature& aggregate_temp() const noexcept { return *aggregate_temp_; }

private:
    MeasurementStack() = default;

    MultiHX711 multi_hx711_{};
    MultiThermistor multi_thermistor_{};
    AggregateTemperature* aggregate_temp_ = nullptr;
    AggregateMass* aggregate_mass_ = nullptr;
};

}
