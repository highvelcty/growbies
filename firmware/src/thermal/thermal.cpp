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
    pinMode(Pins::HEATER_ACTIVE, INPUT);
    pinMode(Pins::FAN_ACTIVE, INPUT);
    digitalWrite(Pins::ACTIVATE_BUTTON, LOW);
    pinMode(Pins::ACTIVATE_BUTTON, OUTPUT);
    digitalWrite(Pins::ACTIVATE_BUTTON, LOW);
    pinMode(Pins::GROUNDED_PIN, INPUT);
    pinMode(Pins::THERMISTOR_PIN_0, INPUT);

    _set_heater_off();
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
    int is_on = 0;
    for (auto ii = 0; ii < IS_HEATER_ON_SAMPLES; ++ii) {
        is_on += digitalRead(Pins::HEATER_ACTIVE);
        delay(IS_HEATER_ON_SAMPLE_INTERVAL);
    }
    return is_on > IS_HEATER_ON_SAMPLES / 2;
}

bool ThermalChamber::wait_for_heater_state(const bool on) {
    const auto start = millis();
    while (millis() - start < READ_STATE_MS) {
        if (is_heater_on() == on) {
            return true;
        }
    }
    return false;
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

bool ThermalChamber::_set_heater_state(const bool state) {
    if (is_heater_on() == state) {
        return true;
    }
    for (uint8_t attempt = 0; attempt < ACTIVATE_RETRIES; ++attempt) {

        // Pulse the activate button.
        digitalWrite(Pins::ACTIVATE_BUTTON, HIGH);
        delay(100);
        digitalWrite(Pins::ACTIVATE_BUTTON, LOW);

        if (wait_for_heater_state(state)) {
            return true;
        }
    }

    _state.error = ThermalError::TIMEOUT_ACTIVATING_DEACTIVATING_HEATER;
    return false;
}

void ThermalChamber::_set_heater_on() {
    _set_heater_state(true);
}

void ThermalChamber::_set_heater_off() {
    _set_heater_state(false);
}

