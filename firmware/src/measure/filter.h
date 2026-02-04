#pragma once

#include <algorithm>
#include <cstddef>
#include <vector>

namespace growbies {

// -----------------------------------------------------------------------------
// Sliding median filter
// -----------------------------------------------------------------------------
class SlidingMedianFilter {
public:
    explicit SlidingMedianFilter(size_t window_size);

    float update(float value);

    void reset();

private:
    size_t window_size_;
    std::vector<float> buffer_;
    std::vector<float> temp_;
    size_t index_;
    int count_;
};

// -----------------------------------------------------------------------------
// Adaptive exponentially weighted moving average buffer
//
// RTC-retained state - persists through deep sleep
// -----------------------------------------------------------------------------

// RTC variables (defined in .cpp per requirement)
extern bool  aewma_buffer_initialized;
extern float aewma_buffer_last_value;

class AEWMABuffer {
public:
    explicit AEWMABuffer(float alpha_threshold, float event_threshold);

    bool add(float value);

    static float value();

    void reset();

private:
    float error = 0.0f;

    // Threshold at which the buffer is purely responsive with weighting
    float alpha_threshold = 0.0f;
    float event_threshold = 0.0f;

    static constexpr float ALPHA_MIN = 0.01f;   // very stable
    static constexpr float ALPHA_MAX = 0.6f;    // very responsive

    float compute_alpha() const;
};

// Mass Buffer Lazy-initialized Global Singleton
constexpr float STAY_AWAKE_THRESH_GRAMS = 5.0;
constexpr float EWMA_ALPHA_THRESH_GRAMS = 25.0;
AEWMABuffer& mass_buffer();

}
