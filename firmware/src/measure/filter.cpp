#include <Arduino.h>
#include "filter.h"

namespace growbies {

// -----------------------------------------------------------------------------
// SlidingMedianFilter implementation
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
// AEWMABuffer implementation
// -----------------------------------------------------------------------------
RTC_DATA_ATTR bool  aewma_mass_buffer_initialized = false;
RTC_DATA_ATTR float aewma_mass_buffer_last_value = 0.0f;

AEWMABuffer::AEWMABuffer(const float alpha_min, const float alpha_max, const float alpha_threshold,
                         const bool initialized, const float last_value)
    : alpha_min(alpha_min), alpha_max(alpha_max), alpha_threshold(alpha_threshold),
      initialized(initialized),
      last_value(last_value) {}

void AEWMABuffer::add(const float value) {
    if (isnan(value)) {
        return;
    }

    if (!initialized) {
        last_value = value;
        initialized = true;
        return;
    }

    last_error = fabsf(value - last_value);
    const float alpha = compute_alpha(last_error);
    last_value = alpha * value + (1.0f - alpha) * last_value;
}

float AEWMABuffer::compute_alpha(const float error) const {
    if (error <= 0.0f or isnan(error)) {
        return alpha_min;
    }

    // Scaling factor for how aggressive the smoothing is. An alpha of 1 (or maximum) is less
    // smoothing than a small value for alpha. alpha_threshold is the "knee point" between
    // smoothing and tracking modes.
    const float alpha = sqrtf(error / alpha_threshold);

    if (alpha < alpha_min) return alpha_min;
    if (alpha > alpha_max) return alpha_max;
    return alpha;
}

float AEWMABuffer::error() const {
    return last_error;
}

// ReSharper disable once CppMemberFunctionMayBeStatic
void AEWMABuffer::reset() { // NOLINT(*-convert-member-functions-to-static)
    last_value = 0.0f;
    initialized = false;
}

// ReSharper disable once CppMemberFunctionMayBeStatic
float AEWMABuffer::value() const { // NOLINT(*-convert-member-functions-to-static)
    return initialized ? last_value : 0.0f;
}

}
