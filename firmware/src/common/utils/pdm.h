#pragma once

class PulseDensityModulator
{
public:
    PulseDensityModulator() = default;

    bool update(float duty_cycle);
    void reset();

private:
    float _accumulator = 0.0f;
};
