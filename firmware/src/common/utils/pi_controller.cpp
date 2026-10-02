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


void PIController::update(
    const float set_point,
    const float measurement,
    const unsigned long dt_milliseconds)
{
    const float dt_seconds = dt_milliseconds / 1000.0f; // NOLINT(*-narrowing-conversions)

    // Current error
    const float error = set_point - measurement;

    // Proportional term
    _proportional_duty_cycle = _kp * error;

    // Calculate what the integral state and output would be if we integrated
    // this error.
    const float candidate_integral_state =
        _integral_state + error * dt_seconds;

    const float candidate_duty_cycle =
        _proportional_duty_cycle +
        (_ki * candidate_integral_state);

    // Conditional integration prevents integral windup.
    //
    // If the candidate output is above the upper limit, only allow integration
    // if the error will reduce the output.
    //
    // If the candidate output is below the lower limit, only allow integration
    // if the error will increase the output.
    const bool saturated_high =
        candidate_duty_cycle > _output_max;

    const bool saturated_low =
        candidate_duty_cycle < _output_min;

    const bool integration_reduces_saturation =
        (saturated_high && error < 0.0f) ||
        (saturated_low && error > 0.0f);

    const bool output_not_saturated =
        !saturated_high && !saturated_low;

    if (output_not_saturated || integration_reduces_saturation) {
        _integral_state = candidate_integral_state;
    }

    _duty_cycle =
        _proportional_duty_cycle +
        (_ki * _integral_state);

    // Clamp the final output to the permitted range.
    if (_duty_cycle > _output_max) {
        _duty_cycle = _output_max;
    }
    else if (_duty_cycle < _output_min) {
        _duty_cycle = _output_min;
    }
}


float PIController::get_duty_cycle() const {
    return _duty_cycle;
}


float PIController::get_integral_duty_cycle() const {
    return _integral_state * _ki;
}


float PIController::get_proportional_duty_cycle() const {
    return _proportional_duty_cycle;
}


void PIController::reset()
{
    _duty_cycle = 0.0f;
    _integral_state = 0.0f;
    _proportional_duty_cycle = 0.0f;
}
