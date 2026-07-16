#pragma once

#include <vector>

#include "common/measure/aggregate_temperature.h"
#include "common/measure/thermistor.h"

constexpr int HEATER_STATE_TRANSITION_TIMEOUT_MS = 1000;
constexpr int IS_HEATER_ON_SAMPLES = 10;
constexpr int IS_HEATER_ON_SAMPLE_INTERVAL = 10;
constexpr int START_UP_DELAY_MS = 1000;

enum class ThermalError : uint32_t
{
    NO_ERROR = 0,
    HEATER_STATE_TRANSITION_TIMEOUT = 1,
};

struct ThermalDeviceState {
    bool active = false;
    bool heater_on = false;
    bool fan_on = false;
    uint8_t reserved;
    float temperature = 0.0f;
    float duty_cycle = 0.0f;
    float set_point = 0.0f;
    ThermalError error = ThermalError::NO_ERROR;


    static constexpr Version_t VERSION = 1;
};
static_assert(sizeof(ThermalDeviceState) == 20, "incorrect structure size");

class ThermalDevice
{
    static constexpr uint8_t ACTIVATE_RETRIES = 3;
public:

    static ThermalDevice& get();

    void begin();

    ThermalDeviceState get_state();
    void set_state(const ThermalDeviceState &state);

    float get_temperature() const;
    std::vector<float> get_sensor_temperatures() const;

    void reset_filters() const;
    void update() const;

    ThermalDevice(const ThermalDevice&) = delete;
    ThermalDevice& operator=(const ThermalDevice&) = delete;
    ThermalDevice(ThermalDevice&&) = delete;
    ThermalDevice& operator=(ThermalDevice&&) = delete;

private:
    ThermalDeviceState _state;
    MultiThermistor _multi_thermistor{SWITCHED_PWR_PIN};
    AggregateTemperature* _aggregate_temp = nullptr;

    static bool _is_fan_on();
    static bool _is_heater_on();
    bool _set_heater_state(bool state);
    void _set_heater_on();
    void _set_heater_off();
    static bool _wait_for_heater_state(bool on);

    ThermalDevice() = default;
    ~ThermalDevice() = default;
};
