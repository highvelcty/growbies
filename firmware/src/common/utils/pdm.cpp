#include "Arduino.h"
#include "pdm.h"


bool PulseDensityModulator::update(const float duty_cycle)
{
    if (duty_cycle <= 0.0f) {
        reset();
        return false;
    }

    if (duty_cycle >= 100.0f) {
        reset();
        return true;
    }

    if (isnan(duty_cycle)) {
        reset();
        return false;
    }

    _accumulator += duty_cycle;

    const auto output = (_accumulator >= 100.0f);

    if (output) {
        _accumulator = fmodf(_accumulator, 100.0f);
    }

    return output;
}

void PulseDensityModulator::reset() {
    _accumulator = 0.0f;
}

