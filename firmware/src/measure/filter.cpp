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
RTC_DATA_ATTR bool  aewma_buffer_initialized = false;
RTC_DATA_ATTR float aewma_buffer_last_value = 0.0f;

AEWMABuffer::AEWMABuffer(const float alpha_threshold,
                         const float event_threshold)
    : alpha_threshold(alpha_threshold),
      event_threshold(event_threshold) {}

bool AEWMABuffer::add(const float value) const {
    if (isnan(value)) {
        return false;
    }

    if (!aewma_buffer_initialized) {
        aewma_buffer_last_value = value;
        aewma_buffer_initialized = true;
        return true;
    }

    const float error = fabsf(value - aewma_buffer_last_value);
    const float alpha = compute_alpha(error);
    aewma_buffer_last_value = alpha * value + (1.0f - alpha) * aewma_buffer_last_value;

    return error >= event_threshold;
}

// ReSharper disable once CppMemberFunctionMayBeStatic
float AEWMABuffer::value() { // NOLINT(*-convert-member-functions-to-static)
    return aewma_buffer_initialized ? aewma_buffer_last_value : 0.0f;
}

// ReSharper disable once CppMemberFunctionMayBeStatic
void AEWMABuffer::reset() { // NOLINT(*-convert-member-functions-to-static)
    aewma_buffer_last_value = 0.0f;
    aewma_buffer_initialized = false;
}

float AEWMABuffer::compute_alpha(const float error) const {
    if (error <= 0.0f or isnan(error)) {
        return ALPHA_MIN;
    }

    const float alpha = sqrtf(error / alpha_threshold);

    if (alpha < ALPHA_MIN) return ALPHA_MIN;
    if (alpha > ALPHA_MAX) return ALPHA_MAX;
    return alpha;
}

// -----------------------------------------------------------------------------
// Singleton
// -----------------------------------------------------------------------------
AEWMABuffer& mass_buffer() {
    static AEWMABuffer instance(
        EWMA_ALPHA_THRESH_GRAMS,
        STAY_AWAKE_THRESH_GRAMS
    );
    return instance;
}

}
