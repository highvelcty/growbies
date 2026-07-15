#pragma once

#include "common/measure/aggregate_temperature.h"
#include "common/measure/thermistor.h"

enum class ThermalError : uint32_t
{
    NO_ERROR = 0,
    TIMEOUT_ACTIVATING_HEATER = 1,
    TIMEOUT_DEACTIVATING_HEATER = 2,
};

struct ThermalChamberCfg {
    bool is_on = false;
    uint8_t reserved[3] = {};
    float set_point = 0.0f;
};
static_assert(sizeof(ThermalChamberCfg) == 8, "ThermalChamberCfg must be exactly 8 bytes");

struct ThermalChamberState {
    float duty_cycle = 0.0f;
    ThermalError error = ThermalError::NO_ERROR;
};
static_assert(sizeof(ThermalChamberState) == 8, "ThermalChamberCfg must be exactly 8 bytes");

constexpr int ACTIVATE_TRANSITION_TIMEOUT_MS = 3000;

class ThermalChamber
{
public:

    static ThermalChamber& get();

    void begin();

    bool is_on() const;
    void on();
    void off();

    float get_temperature() const;

    float get_duty_cycle() const;
    void set_duty_cycle(float duty_cycle);

    float get_set_point() const;
    void set_set_point(float set_point);

    static bool is_fan_on();
    static bool is_heater_on();

    void update() const;

    AggregateTemperature& aggregate_temp() const noexcept { return *_aggregate_temp; }

    ThermalChamber(const ThermalChamber&) = delete;
    ThermalChamber& operator=(const ThermalChamber&) = delete;
    ThermalChamber(ThermalChamber&&) = delete;
    ThermalChamber& operator=(ThermalChamber&&) = delete;

private:
    ThermalChamberCfg _cfg;
    ThermalChamberState _state;
    MultiThermistor _multi_thermistor{SWITCHED_PWR_PIN};
    AggregateTemperature* _aggregate_temp = nullptr;

    void _set_heater_on();
    void _set_heater_off();

    ThermalChamber() = default;
    ~ThermalChamber() = default;
};
