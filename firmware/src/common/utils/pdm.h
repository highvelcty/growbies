#pragma once

class PulseDensityModulator
{
public:
    static constexpr uint32_t PULSE_WIDTH_MS = 10000;

    PulseDensityModulator() = default;

    bool update(float duty_cycle);
    void reset();

private:
    float _accumulator = 0.0f;
    bool _output = false;
};
