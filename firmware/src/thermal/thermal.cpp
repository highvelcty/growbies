#include "Arduino.h"
#include "constants.h"
#include "thermal.h"

ThermalChamber& ThermalChamber::get()
{
    static ThermalChamber instance;
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

    _duty_cycle = 0.0f;
    _set_point = 0.0f;
    _error = ThermalError::NO_ERROR;
}

bool ThermalChamber::is_on() const
{
    return _is_on;
}

void ThermalChamber::on()
{
    _is_on = true;
}

void ThermalChamber::off()
{
    _is_on = false;
}

bool ThermalChamber::is_fan_on() {
    return static_cast<bool>(digitalRead(Pins::FAN_ACTIVE));
}

bool ThermalChamber::is_heater_on() {
    return static_cast<bool>(digitalRead(Pins::HEATER_ACTIVE));
}

float ThermalChamber::get_temperature() {
    return static_cast<float>(analogReadMilliVolts(Pins::THERMISTOR_PIN_0) / 1000.0);
}

float ThermalChamber::get_duty_cycle() const
{
    return _duty_cycle;
}

void ThermalChamber::set_duty_cycle(const float duty_cycle)
{
    this->_duty_cycle = duty_cycle;
}

float ThermalChamber::get_set_point() const {
    return _set_point;
}
void ThermalChamber::set_set_point(const float set_point) {
    this->_set_point = set_point;
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
            _error = ThermalError::TIMEOUT_ACTIVATING_HEATER;
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
            _error = ThermalError::TIMEOUT_ACTIVATING_HEATER;
            return;
        }

        delay(10);
    }
}

