#pragma once

enum class ThermalError : int
{
    NO_ERROR = 0,
    TIMEOUT_ACTIVATING_HEATER = 1,
    TIMEOUT_DEACTIVATING_HEATER = 2,
};

constexpr int ACTIVATE_TRANSITION_TIMEOUT_MS = 3000;

class ThermalChamber
{
public:
    static ThermalChamber& get();

    void begin();

    bool is_on() const;
    void on();
    void off();

    static float get_temperature();

    float get_duty_cycle() const;
    void set_duty_cycle(float duty_cycle);

    float get_set_point() const;
    void set_set_point(float set_point);

    static bool is_fan_on();
    static bool is_heater_on();

    ThermalChamber(const ThermalChamber&) = delete;
    ThermalChamber& operator=(const ThermalChamber&) = delete;
    ThermalChamber(ThermalChamber&&) = delete;
    ThermalChamber& operator=(ThermalChamber&&) = delete;

private:
    ThermalChamber() = default;
    ~ThermalChamber() = default;

    bool _is_on = false;
    float _set_point = 0.0f;
    float _duty_cycle = 0.0f;
    ThermalError _error = ThermalError::NO_ERROR;

    void _set_heater_on();
    void _set_heater_off();
};
