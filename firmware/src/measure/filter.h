#pragma once
#include <algorithm>
#include <array>
#include <cstddef>

namespace growbies_hf {

    constexpr auto MEDIAN_FILTER_BUFFER_SIZE  = 5;

    struct OptionalFloat {
        bool valid;
        float value;
        OptionalFloat() : valid(false), value(0.0f) {}
        explicit OptionalFloat(const float v) : valid(true), value(v) {}
    };

    class SlidingMedianFilter {
    public:
        static constexpr size_t WINDOW_SIZE = 5;

        SlidingMedianFilter() : buffer_{}, index_(0), count_(0) {}

        float update(const float value) {
            buffer_[index_] = value;
            index_ = (index_ + 1) % WINDOW_SIZE;
            if (count_ < WINDOW_SIZE) ++count_;

            std::array<float, WINDOW_SIZE> temp{};
            std::copy_n(buffer_.begin(), count_, temp.begin());

            const auto mid = temp.begin() + count_ / 2;
            std::nth_element(temp.begin(), mid, temp.begin() + count_);

            return *mid;
        }

        void reset() {
            buffer_.fill(0.0f);
            index_ = 0;
            count_ = 0;
        }

    private:
        std::array<float, WINDOW_SIZE> buffer_;
        size_t index_;
        size_t count_;
    };


    // Simple single-pole IIR smoother
    class IIRSmoother {
    public:
        static constexpr auto ALPHA = 0.2f;
        explicit IIRSmoother(const float alpha = ALPHA)
            : alpha_(alpha), initialized_(false), state_(0.0f) {}

        float update(const float value) {
            if (!initialized_) {
                state_ = value;
                initialized_ = true;
            } else {
                state_ = alpha_ * value + (1.0f - alpha_) * state_;
            }
            return state_;
        }

        void reset() {
            initialized_ = false;
            state_ = 0.0f;
        }

    private:
        float alpha_;
        bool initialized_;
        float state_;
    };

}  // namespace growbies_hf
