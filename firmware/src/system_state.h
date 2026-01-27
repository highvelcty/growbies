#pragma once

// -----------------------------------------------------------------------------
// System power / activity state
// -----------------------------------------------------------------------------
class SystemState {
public:
    enum class PowerState : uint8_t {
        ACTIVE,        // Display on, normal operation
        DISPLAY_OFF,   // Display powered down, MCU awake
        DEEP_SLEEP     // MCU in deep sleep
    };

    // Singleton access
    static SystemState& get() {
        static SystemState instance;
        return instance;
    }

    // Non-copyable
    SystemState(const SystemState&) = delete;
    SystemState& operator=(const SystemState&) = delete;

    // -------------------------------------------------------------------------
    // State queries
    // -------------------------------------------------------------------------
    PowerState power_state() const {
        return state_;
    }

    bool is_active() const {
        return state_ == PowerState::ACTIVE;
    }

    bool is_display_off() const {
        return state_ == PowerState::DISPLAY_OFF;
    }

    bool is_deep_sleep() const {
        return state_ == PowerState::DEEP_SLEEP;
    }

    // -------------------------------------------------------------------------
    // Activity / timing
    // -------------------------------------------------------------------------
    void notify_activity(const uint32_t now_ms) {
        last_activity_ms_ = now_ms;
    }

    uint32_t idle_time_ms(const uint32_t now_ms) const {
        if (last_activity_ms_ == 0) {
            return now_ms;
        }
        return now_ms - last_activity_ms_;
    }

    // -------------------------------------------------------------------------
    // State transitions (called by sleep task / policy code)
    // -------------------------------------------------------------------------
    void set_display_off() {
        state_ = PowerState::DISPLAY_OFF;
    }

    void set_deep_sleep() {
        state_ = PowerState::DEEP_SLEEP;
    }

    void set_active() {
        state_ = PowerState::ACTIVE;
    }

private:
    SystemState()
        : state_(PowerState::ACTIVE),
          last_activity_ms_(0)
    {}

    PowerState state_;
    uint32_t last_activity_ms_;
};
