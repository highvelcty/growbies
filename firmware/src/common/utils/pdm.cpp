#include "Arduino.h"
#include "pdm.h"


bool PulseDensityModulator::update(float duty_cycle)
{
    if (duty_cycle < 0.0f)
        duty_cycle = 0.0f;

    if (duty_cycle > 100.0f)
        duty_cycle = 100.0f;


    // Special cases:
    // - 0% means definitely off immediately.
    // - 100% means turn on immediately.
    if (duty_cycle <= 0.0f) {
        reset();
        return _output;
    }
    if (duty_cycle >= 100.0f)
    {
        _output = true;
        _accumulator = 0.0f;
        return _output;
    }

    _accumulator += duty_cycle;

    if (_accumulator >= 100.0f) {
        _output = true;
        _accumulator -= 100.0f;
    }
    else {
        _output = false;
    }

    return _output;
}

void PulseDensityModulator::reset() {
    _accumulator = 0.0f;
    _output = false;
}

