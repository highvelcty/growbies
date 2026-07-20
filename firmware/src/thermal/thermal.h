#pragma once

#include <vector>

#include "common/measure/aggregate_temperature.h"
#include "common/measure/thermistor.h"
#include "common/protocol/command.h"
#include "common/utils/pdm.h"
#include "common/utils/pi_controller.h"

#pragma pack(1)

constexpr int HEATER_STATE_TRANSITION_TIMEOUT_MS = 1000;
constexpr int IS_HEATER_ON_SAMPLES = 10;
constexpr int IS_HEATER_ON_SAMPLE_INTERVAL = 10;
constexpr int START_UP_DELAY_MS = 1000;


enum class ThermalDeviceErrorCode: uint32_t {
    ERROR_NONE                                  = 0,
    ERROR_HEATER_STATE_TRANSITION_TIMEOUT       = 1,
    ERROR_TEMPERATURE_TOO_HIGH                  = 2,
};

enum class ThermalDeviceMode : uint8_t {
    AUTO = 0,
    MANUAL = 1,
};

struct ThermalDeviceControl {
    bool active = false;
    ThermalDeviceMode mode = ThermalDeviceMode::AUTO;
    uint8_t reserved[2];
    float duty_cycle = 0.0f;
    float set_point = 0.0f;
};
static_assert(sizeof(ThermalDeviceControl) == 12, "incorrect structure size");

struct ThermalDeviceSense {
    bool heater_on = false;
    bool fan_on = false;
    uint8_t reserved[2];
    ThermalDeviceErrorCode error = ThermalDeviceErrorCode::ERROR_NONE;
    float temperature = NAN;
    float controller_proportional_term = 0.0f;
    float controller_integral_term = 0.0f;
};
static_assert(sizeof(ThermalDeviceSense) == 20, "incorrect structure size");

struct ThermalDeviceState {
    ThermalDeviceSense sense;
    ThermalDeviceControl control;

    static constexpr Version_t VERSION = 1;
};
static_assert(sizeof(ThermalDeviceState) == 32, "incorrect structure size");

class ThermalDevice
{
    static constexpr uint8_t ACTIVATE_RETRIES = 3;
    static constexpr int MAX_TEMP_C = 70;
    static constexpr float MIN_DUTY_CYCLE = 0.0f;
    static constexpr float MAX_DUTY_CYCLE = 100.0f;
    static constexpr float PI_KP = 3.0f;
    static constexpr float PI_KI = 0.02f;
public:
    static constexpr float UPDATE_INTERVAL_MS = 1000.0f;

    static ThermalDevice& get();

    void begin();

    ThermalDeviceState get_state();
    void set_controls(const ThermalDeviceControl &control);

    float get_temperature() const;
    std::vector<float> get_sensor_temperatures() const;

    void reset();
    void reset_controlling_memory();
    void reset_sensing_memory();
    void update();

    ThermalDevice(const ThermalDevice&) = delete;
    ThermalDevice& operator=(const ThermalDevice&) = delete;
    ThermalDevice(ThermalDevice&&) = delete;
    ThermalDevice& operator=(ThermalDevice&&) = delete;
    ThermalDevice() = default;
    ~ThermalDevice() = default;

private:
    unsigned long _last_update_ms = 0;
    ThermalDeviceState _state;
    MultiThermistor _multi_thermistor{SWITCHED_PWR_PIN};
    AggregateTemperature* _aggregate_temp = nullptr;
    PulseDensityModulator _pulse_density_modulator;
    PIController _pi_controller{PI_KP, PI_KI, MIN_DUTY_CYCLE, MAX_DUTY_CYCLE};

    static bool _is_fan_on();
    static bool _is_heater_on();
    bool _set_heater_state(bool state);
    void _set_heater_on();
    void _set_heater_off();
    static bool _wait_for_heater_state(bool on);
};

#pragma pack()
