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
extern bool  aewma_mass_buffer_initialized;
extern float aewma_mass_buffer_last_value;

// Adaptive Exponentially Weighted Moving Average (AEWMA) Buffer
class AEWMABuffer {

    public:
        explicit AEWMABuffer(
            float alpha_min, float alpha_max, float alpha_threshold,
            bool initialized = false, float last_value = 0.0f);

        void add(float value);
        float error() const;
        void reset();
        float value() const;

    private:
        float alpha_min = 0.0f;
        float alpha_max = 0.0f;
        // Threshold at which the buffer is purely responsive with weighting
        float alpha_threshold = 0.0f;
        bool initialized = false;
        float last_error = 0.0f;
        float last_value = 0.0f;


    static constexpr float ALPHA_MIN = 0.02f;   // very stable
    static constexpr float ALPHA_MAX = 0.7f;    // very responsive

        float compute_alpha(float error) const;
    };
}
