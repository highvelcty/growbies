#include "Arduino.h"
#include "constants.h"
#include "thermal.h"

ThermalChamber& ThermalChamber::get()
{
    static ThermalChamber instance;
    static bool initialized = false;

    if (!initialized) {
        instance.begin();
        initialized = true;
    }

    return instance;
}

void ThermalChamber::begin()
{
    pinMode(Pins::HEATER_ACTIVE, INPUT_PULLDOWN);
    pinMode(Pins::FAN_ACTIVE, INPUT_PULLDOWN);

    pinMode(Pins::ACTIVATE_BUTTON, OUTPUT);
    digitalWrite(Pins::ACTIVATE_BUTTON, LOW);

    pinMode(Pins::GROUNDED_PIN, INPUT);

    pinMode(Pins::THERMISTOR_PIN_0, INPUT);

    _multi_thermistor.begin();
    _aggregate_temp = new AggregateTemperature(TEMPERATURE_SENSOR_COUNT);
}

bool ThermalChamber::is_on() const
{
    return _cfg.is_on;
}

void ThermalChamber::on()
{
    _cfg.is_on = true;
}

void ThermalChamber::off()
{
    _cfg.is_on = false;
}

bool ThermalChamber::is_fan_on() {
    return static_cast<bool>(digitalRead(Pins::FAN_ACTIVE));
}

bool ThermalChamber::is_heater_on() {
    return static_cast<bool>(digitalRead(Pins::HEATER_ACTIVE));
}

void ThermalChamber::update() const {
    _aggregate_temp->reset_channels();
    for (int ii = 0; ii < MEDIAN_FILTER_BUF_SIZE; ++ii) {
        std::vector<float> temp_vals = _multi_thermistor.sample();
        for (size_t i = 0; i < temp_vals.size() && i < _aggregate_temp->size(); ++i)
            _aggregate_temp->channel(i).update(temp_vals[i]);
    }
    _aggregate_temp->update();
}

float ThermalChamber::get_temperature() const {
    update();
    return _aggregate_temp->conditioned_total();
}

float ThermalChamber::get_duty_cycle() const
{
    return _state.duty_cycle;
}

void ThermalChamber::set_duty_cycle(const float duty_cycle)
{
    _state.duty_cycle = duty_cycle;
}

float ThermalChamber::get_set_point() const {
    return _cfg.set_point;
}
void ThermalChamber::set_set_point(const float set_point) {
    _cfg.set_point = set_point;
}

void ThermalChamber::_set_heater_on() {
    if (is_heater_on()) {
        return;
    }
    digitalWrite(Pins::ACTIVATE_BUTTON, HIGH);
    delay(100);
    digitalWrite(Pins::ACTIVATE_BUTTON, LOW);

    const uint32_t start = millis();

    while (!is_heater_on()) {
        if (millis() - start >= ACTIVATE_TRANSITION_TIMEOUT_MS) {
            _state.error = ThermalError::TIMEOUT_ACTIVATING_HEATER;
            return;
        }

        delay(10);
    }
}

void ThermalChamber::_set_heater_off() {
    if (!is_heater_on()) {
        return;
    }
    digitalWrite(Pins::ACTIVATE_BUTTON, LOW);
    delay(100);
    digitalWrite(Pins::ACTIVATE_BUTTON, HIGH);

    const uint32_t start = millis();

    while (is_heater_on()) {
        if (millis() - start >= ACTIVATE_TRANSITION_TIMEOUT_MS) {
            _state.error = ThermalError::TIMEOUT_ACTIVATING_HEATER;
            return;
        }

        delay(10);
    }
}

