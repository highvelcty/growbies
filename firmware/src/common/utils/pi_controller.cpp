#include <cassert>
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
    assert(_kp > 0.0f);
    assert(_ki > 0.0f);
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
    _proportional_state = _kp * error;

    // Integral term - only accumulate if less than the specified range in grams. This prevents
    // too much accumulation when very below the setpoint. i.e. only accumulate into the integral
    // state if within a small number of degrees (positive) of the setpoint and everything above
    // the setpoint (negative).
    if (error < INTEGRAL_ACCUMULATE_RANGE_GRAMS) {
        _integral_state += error * dt_seconds;
    }

    float output = _proportional_state + (_ki * _integral_state);

    // Anti-windup.
    // If output saturates, prevent integral from continuing to grow without bound.
    //
    // Here we are calculating the integral term that will result in the clamped output
    //
    // output = proportional + integral
    /// integral = output - proportional
    if (output > _output_max) {
        output = _output_max;
        _integral_state = (_output_max - _proportional_state) / _ki;
    }
    else if (output < _output_min) {
        output = _output_min;
        _integral_state = (_output_min - _proportional_state) / _ki;
    }

    return output;
}


float PIController::get_integral_state() const {
    return _integral_state;
}

float PIController::get_proportional_state() const {
    return _proportional_state;
}

void PIController::reset()
{
    _integral_state = 0.0f;
}