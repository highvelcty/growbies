#include <assert.h>
#include "pi_controller.h"


PIController::PIController(
    const float kp,
    const float ki,
    const float output_min,
    const float output_max
)
    :
    _kp(kp),
    _ki(ki),
    _output_min(output_min),
    _output_max(output_max)
{
    assert(_output_max > _output_min);
    assert(_kp >= 0.0f);
    assert(_ki >= 0.0f);
}


float PIController::update(
    const float set_point,
    const float measurement,
    const unsigned long dt_milliseconds)
{
    const float dt_seconds = dt_milliseconds / 1000.0f;

    // Current error
    const float error = set_point - measurement;

    // Proportional term
    _proportional = _kp * error;

    // Integral term
    _integral += error * dt_seconds;

    float output = _proportional + (_ki * _integral);

    // Anti-windup.
    // If output saturates, prevent integral from continuing to grow without bound.
    //
    // Here we are calculating the integral term that will result in the clamped output
    //
    // output = proportional + integral
    /// integral = output - proportional
    if (output > _output_max) {
        output = _output_max;
        _integral = (_output_max - _proportional) / _ki;
    }
    else if (output < _output_min) {
        output = _output_min;
        _integral = (_output_min - _proportional) / _ki;
    }

    return output;
}


float PIController::get_integral() const {
    return _integral;
}

float PIController::get_proportional() const {
    return _proportional;
}

void PIController::reset()
{
    _integral = 0.0f;
}