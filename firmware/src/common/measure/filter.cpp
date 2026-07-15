#include <Arduino.h>
#include "build_cfg.h"
#include "filter.h"

RTC_DATA_ATTR bool  aewma_mass_buffer_initialized = false;
RTC_DATA_ATTR float aewma_mass_buffer_last_value = 0.0f;
RTC_DATA_ATTR bool  aewma_temp_buffer_initialized[TEMPERATURE_SENSOR_COUNT] = {false};
RTC_DATA_ATTR float aewma_temp_buffer_last_value[TEMPERATURE_SENSOR_COUNT] = {0.0f};

// -----------------------------------------------------------------------------
// SlidingMedianFilter
// -----------------------------------------------------------------------------
SlidingMedianFilter::SlidingMedianFilter(const size_t window_size)
    : window_size_(window_size),
      buffer_(window_size, 0.0f),
      index_(0),
      count_(0)
{
    assert(window_size_ > 0);
}

float SlidingMedianFilter::update(const float value) {
    buffer_[index_] = value;
    index_ = (index_ + 1) % window_size_;
    if (count_ < window_size_) ++count_;

    // Copy only the valid portion
    temp_.assign(buffer_.begin(), buffer_.begin() + count_);

    const auto mid = temp_.begin() + count_ / 2;
    std::nth_element(temp_.begin(), mid, temp_.end());

    return *mid;
}

void SlidingMedianFilter::reset() {
    std::fill(buffer_.begin(), buffer_.end(), 0.0f);
    index_ = 0;
    count_ = 0;
}

// -----------------------------------------------------------------------------
// Base AEWMA
// -----------------------------------------------------------------------------
void AEWMABuffer::add(float value) {
    if (isnan(value)) return;

    if (!initialized) {
        last_value = value;
        initialized = true;
        return;
    }

    last_error = fabsf(value - last_value);
    const float alpha = compute_alpha(last_error);

    last_value = alpha * value + (1.0f - alpha) * last_value;
}

void AEWMABuffer::reset() {
    last_value = 0.0f;
    initialized = false;
}

float AEWMABuffer::error() const {
    return last_error;
}

float AEWMABuffer::value() const {
    return initialized ? last_value : 0.0f;
}
// -----------------------------------------------------------------------------
// LOGISTIC AEWMA
// -----------------------------------------------------------------------------
LogisticAEWMABuffer::LogisticAEWMABuffer(
    float alpha_min,
    float alpha_max,
    float midpoint,
    float steepness,
    bool initialized,
    float last_value
)
    : alpha_min(alpha_min),
      alpha_max(alpha_max),
      midpoint(midpoint),
      steepness(steepness)
{
    this->initialized = initialized;
    this->last_value = last_value;
}

float LogisticAEWMABuffer::compute_alpha(float error) const {
    if (error <= 0.0f || isnan(error)) {
        return alpha_min;
    }

    const float x = -steepness * (error - midpoint);
    const float denom = 1.0f + expf(x);

    float alpha = alpha_min +
        (alpha_max - alpha_min) / denom;

    if (alpha < alpha_min) return alpha_min;
    if (alpha > alpha_max) return alpha_max;

    return alpha;
}

// -----------------------------------------------------------------------------
// LINEAR AEWMA
// -----------------------------------------------------------------------------
LinearAEWMABuffer::LinearAEWMABuffer(
    float alpha_min,
    float alpha_max,
    float threshold,
    bool initialized,
    float last_value
)
    : alpha_min(alpha_min),
      alpha_max(alpha_max),
      threshold(threshold)
{
    this->initialized = initialized;
    this->last_value = last_value;
}

float LinearAEWMABuffer::compute_alpha(float error) const {
    if (error <= 0.0f || isnan(error)) {
        return alpha_min;
    }

    float alpha = error / threshold;

    if (alpha < alpha_min) return alpha_min;
    if (alpha > alpha_max) return alpha_max;

    return alpha;
}
