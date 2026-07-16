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
    pinMode(Pins::FAN_ACTIVE, INPUT);
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
    _state.temperature = get_temperature();
    _state.heater_on = _is_heater_on();
    _state.fan_on = _is_fan_on();

    return _state;
}

void ThermalDevice::set_state(const ThermalDeviceState &state) {
    _state = state;
}

void ThermalDevice::reset_filters() const {
    _aggregate_temp->reset();
}


void ThermalDevice::update() const
{
    _aggregate_temp->reset_channels();
    for (int ii = 0; ii < MEDIAN_FILTER_BUF_SIZE; ++ii) {
        std::vector<float> temp_vals = _multi_thermistor.sample();
        for (size_t i = 0; i < temp_vals.size() && i < _aggregate_temp->size(); ++i)
            _aggregate_temp->channel(i).update(temp_vals[i]);
    }
    _aggregate_temp->update();
}

float ThermalDevice::get_temperature() const
{
    update();
    return _aggregate_temp->conditioned_total();
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
    return static_cast<bool>(digitalRead(Pins::FAN_ACTIVE));
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

    _state.error = ErrorCode::ERROR_HEATER_STATE_TRANSITION_TIMEOUT;
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