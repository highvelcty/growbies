#pragma once

enum class PowerState : uint8_t {
    INITIAL,                    // Initial state following reset
    ACTIVE,                     // Display on, normal operation
    WAKEFUL_SLEEP,              // MCU in deep sleep, sensor input polling
    DEEP_SLEEP,                 // MCU in deep sleep
};


// -----------------------------------------------------------------------------
// System power / activity state
// -----------------------------------------------------------------------------
class SystemState {
public:
    // Singleton access
    static SystemState& get() {
        static SystemState instance;
        return instance;
    }

    // Non-copyable
    SystemState(const SystemState&) = delete;
    SystemState& operator=(const SystemState&) = delete;

    PowerState next_state() const {
        return next_state_;
    }

    PowerState state() const {
        return state_;
    }

    void set_state(const PowerState new_state) {
        state_ = new_state;
    }

    void set_next_state(const PowerState new_state) {
        next_state_ = new_state;
    }

    bool ready_for_tasks() const {
        return not transitioning() and state_ == PowerState::ACTIVE;
    }

    bool transitioning() const {
        return state_ != next_state_;
    }

    void notify_activity(const uint32_t now_ms) {
        last_activity_ms_ = now_ms;
    }

    uint32_t idle_time_ms(const uint32_t now_ms) const {
        return now_ms - last_activity_ms_;
    }

private:
    SystemState()
        : state_(PowerState::INITIAL),
          next_state_(PowerState::ACTIVE),
          last_activity_ms_(0)
    {}

    PowerState state_;
    PowerState next_state_;
    uint32_t last_activity_ms_;
};
