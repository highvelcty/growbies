#pragma once

class PIController
{
    static constexpr float INTEGRAL_ACCUMULATE_RANGE_GRAMS = 3.0f;
public:
    PIController(
        float kp,
        float ki,
        float output_min = 0.0f,
        float output_max = 100.0f
    );
    void update(
        float set_point,
        float measurement,
        unsigned long dt_milliseconds
    );

    float get_duty_cycle() const;
    float get_integral_duty_cycle() const;
    float get_proportional_duty_cycle() const;
    void reset();

private:
    float _kp;
    float _ki;

    float _output_min;
    float _output_max;

    float _duty_cycle = 0.0f;
    float _integral_state = 0.0f;
    float _proportional_duty_cycle = 0.0f;
};

