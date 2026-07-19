#include "Arduino.h"
#include "thermal.h"

ThermalDevice& ThermalDevice::get()
{
    static ThermalDevice instance;
    static bool initialized = false;

    if (!initialized) {
        instance.begin();
        initialized = true;
    }

    return instance;
}

void ThermalDevice::begin()
{
    pinMode(Pins::HEATER_ACTIVE, INPUT);
    pinMode(Pins::FAN_ACTIVE, INPUT_PULLUP);
    digitalWrite(Pins::ACTIVATE_BUTTON, LOW);
    pinMode(Pins::ACTIVATE_BUTTON, OUTPUT);
    digitalWrite(Pins::ACTIVATE_BUTTON, LOW);
    pinMode(Pins::GROUNDED_PIN, INPUT);
    pinMode(Pins::THERMISTOR_PIN_0, INPUT);

    if (_wait_for_heater_state(true)) {
        _set_heater_off();
    }

    _multi_thermistor.begin();
    _aggregate_temp = new AggregateTemperature(TEMPERATURE_SENSOR_COUNT);
}

ThermalDeviceState ThermalDevice::get_state() {
    _aggregate_temp->reset_channels();
    for (int ii = 0; ii < MEDIAN_FILTER_BUF_SIZE; ++ii) {
        std::vector<float> temp_vals = _multi_thermistor.sample();
        for (size_t i = 0; i < temp_vals.size() && i < _aggregate_temp->size(); ++i)
            _aggregate_temp->channel(i).update(temp_vals[i]);
    }
    _aggregate_temp->update();

    _state.sense.temperature = _aggregate_temp->conditioned_total();
    _state.sense.heater_on = _is_heater_on();
    _state.sense.fan_on = _is_fan_on();

    if (_state.sense.temperature > MAX_TEMP_C) {
        _state.sense.error = ThermalDeviceErrorCode::ERROR_TEMPERATURE_TOO_HIGH;
    }

    return _state;
}

void ThermalDevice::set_controls(const ThermalDeviceControl &control)
{
    // Transition from inactive to active
    if (!_state.control.active and control.active) {
        reset();
    }
    _state.control = control;
}

void ThermalDevice::reset() {
    reset_sensing_memory();
    reset_controlling_memory();
}

void ThermalDevice::reset_controlling_memory() {
    _state.sense.error = ThermalDeviceErrorCode::ERROR_NONE;
    _last_update_ms = 0;
    _pulse_density_modulator.reset();
    _pi_controller.reset();
}

void ThermalDevice::reset_sensing_memory() {
    _aggregate_temp->reset();
    _state.sense.temperature = NAN;
}

void ThermalDevice::update() {
    const uint32_t now_ms = millis();

    get_state();

    if (_state.sense.error != ThermalDeviceErrorCode::ERROR_NONE or not _state.control.active) {
        _state.control.active = false;
        _set_heater_off();
        return;
    }

    if (_state.control.mode == ThermalDeviceMode::AUTO) {

        uint32_t delta_ms;
        if (!_last_update_ms) {
            delta_ms = 0;
        }
        else {
            delta_ms = now_ms - _last_update_ms;
        }

        _state.control.duty_cycle = _pi_controller.update(
            _state.control.set_point,
            _state.sense.temperature,
            delta_ms
        );
        _state.sense.controller_proportional_term = _pi_controller.get_proportional();
        _state.sense.controller_integral_term = _pi_controller.get_integral();

        _last_update_ms = now_ms;
    }

    if (_pulse_density_modulator.update(_state.control.duty_cycle)) {
        _set_heater_on();
    }
    else {
        _set_heater_off();
    }
}

float ThermalDevice::get_temperature() const {
    return _state.sense.temperature;
}

std::vector<float> ThermalDevice::get_sensor_temperatures() const
{
    std::vector<float> sensor_temperatures;

    for (auto sensor_temp : _aggregate_temp->sensor_temperatures()) {
        sensor_temperatures.push_back(sensor_temp);
    }

    return sensor_temperatures;
}

bool ThermalDevice::_is_fan_on()
{
    return digitalRead(Pins::FAN_ACTIVE);
}

bool ThermalDevice::_is_heater_on()
{
    return not digitalRead(Pins::HEATER_ACTIVE);
}

bool ThermalDevice::_set_heater_state(const bool state)
{
    if (_is_heater_on() == state) {
        return true;
    }

    for (uint8_t attempt = 0; attempt < ACTIVATE_RETRIES; ++attempt) {

        // Pulse the activate button.
        digitalWrite(Pins::ACTIVATE_BUTTON, HIGH);
        delay(100);
        digitalWrite(Pins::ACTIVATE_BUTTON, LOW);

        if (_wait_for_heater_state(state)) {
            return true;
        }
    }

    _state.sense.error = ThermalDeviceErrorCode::ERROR_HEATER_STATE_TRANSITION_TIMEOUT;
    return false;
}

void ThermalDevice::_set_heater_on()
{
    _set_heater_state(true);
}

void ThermalDevice::_set_heater_off()
{
    _set_heater_state(false);
}

bool ThermalDevice::_wait_for_heater_state(const bool on)
{
    const auto start = millis();
    while (_is_heater_on() != on) {
        if (millis() - start > HEATER_STATE_TRANSITION_TIMEOUT_MS) {
            return false;
        }
        delay(IS_HEATER_ON_SAMPLE_INTERVAL);
    }
    return true;
}
