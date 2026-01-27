#pragma once
#include <algorithm>
#include <array>
#include <cstddef>

namespace growbies_hf {
    class SlidingMedianFilter {
    public:
        explicit SlidingMedianFilter(const size_t window_size)
            : window_size_(window_size),
              buffer_(window_size, 0.0f),
              index_(0),
              count_(0)
        {
            assert(window_size_ > 0);
        }
        float update(const float value) {
            buffer_[index_] = value;
            index_ = (index_ + 1) % window_size_;
            if (count_ < window_size_) ++count_;

            // Copy only the valid portion
            temp_.assign(buffer_.begin(), buffer_.begin() + count_);

            const auto mid = temp_.begin() + count_ / 2;
            std::nth_element(temp_.begin(), mid, temp_.end());

            return *mid;
        }

        void reset() {
            std::fill(buffer_.begin(), buffer_.end(), 0.0f);
            index_ = 0;
            count_ = 0;
        }

    private:
        size_t window_size_;
        std::vector<float> buffer_;
        std::vector<float> temp_;
        size_t index_;
        int count_;

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
