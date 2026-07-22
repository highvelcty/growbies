#pragma once

class PIController
{
public:
    PIController(
        float kp,
        float ki,
        float output_min = 0.0f,
        float output_max = 100.0f
    );
    float update(
        float set_point,
        float measurement,
        unsigned long dt_milliseconds
    );

    float get_integral_state() const;
    float get_proportional_state() const;
    void reset();

private:
    float _kp;
    float _ki;

    float _output_min;
    float _output_max;

    float _integral_state = 0.0f;
    float _proportional_state = 0.0f;
};

