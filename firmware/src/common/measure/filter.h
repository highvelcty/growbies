#pragma once

#include <vector>

#include "build_cfg.h"

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
extern bool aewma_temp_buffer_initialized[TEMPERATURE_SENSOR_COUNT];
extern float aewma_temp_buffer_last_value[TEMPERATURE_SENSOR_COUNT];

// -----------------------------------------------------------------------------
// Base AEWMA Buffer (shared state + interface)
// -----------------------------------------------------------------------------
class AEWMABuffer {
public:
    virtual ~AEWMABuffer() = default;

    void add(float value);
    float error() const;
    void reset();
    float value() const;

protected:
    bool initialized = false;
    float last_value = 0.0f;
    float last_error = 0.0f;

private:
    virtual float compute_alpha(float error) const = 0;
};

// -----------------------------------------------------------------------------
// Linear AEWMA (proportional response)
// -----------------------------------------------------------------------------
class LinearAEWMABuffer : public AEWMABuffer {
public:
    LinearAEWMABuffer(float alpha_min,
                      float alpha_max,
                      float threshold,
                      bool initialized = false,
                      float last_value = 0.0f);

private:
    float alpha_min;
    float alpha_max;
    float threshold;

    float compute_alpha(float error) const override;
};

// -----------------------------------------------------------------------------
// Logistic AEWMA (S-curve response)
// -----------------------------------------------------------------------------
class LogisticAEWMABuffer : public AEWMABuffer {
public:
    LogisticAEWMABuffer(float alpha_min,
                        float alpha_max,
                        float midpoint,
                        float steepness,
                        bool initialized = false,
                        float last_value = 0.0f);

private:
    float alpha_min;
    float alpha_max;
    float midpoint;
    float steepness;

    float compute_alpha(float error) const override;
};
