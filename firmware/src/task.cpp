#include "task.h"
#include "utils/sleep.h"

void AutoWakeTask::run() {
    if (not system_state.ready_for_tasks()) {
        measurement_stack.update();
        if (mass_buffer().add(measurement_stack.aggregate_mass().total_mass())) {
            system_state.set_next_state(PowerState::ACTIVE);
        }
        else {
            if (system_state.state() == PowerState::INITIAL) {
                system_state.set_next_state(PowerState::WAKEFUL_SLEEP);
            }
        }
    }
}

void AutoWakeTask::run_on_wake() const {
    if (esp_sleep_get_wakeup_cause() == ESP_SLEEP_WAKEUP_TIMER) {
        const auto& measure_stack = MeasurementStack::get();
        measure_stack.update();
        if (!mass_buffer().add(measurement_stack.aggregate_mass().total_mass())) {
            go_to_wakeful_sleep();
        }
    }
}

unsigned long AutoWakeTask::interval_ms() const {
    return identify_store->payload()->auto_wake_interval_ms();
}

void PowerTransitionTask::run() {
    if (system_state.transitioning()) {
        system_state.set_state(system_state.next_state());
        if (system_state.next_state() == PowerState::ACTIVE) {
            system_state.notify_activity(millis());
            remote_out.display_power_save(false);
        }
        else if (system_state.next_state() == PowerState::WAKEFUL_SLEEP) {
            remote_out.display_power_save(true);
            if (not battery.is_charging()) {
                const auto auto_wake_interval = identify_store->payload()->auto_wake_interval_ms();
                if (auto_wake_interval == 0) {
                    go_to_deep_sleep();
                }
                go_to_wakeful_sleep();
            }
        }
        else if (system_state.next_state() == PowerState::DEEP_SLEEP) {
            go_to_deep_sleep();
        }
    }

    const auto sleep_timeout_ms = identify_store->payload()->sleep_timeout_ms();
    if (sleep_timeout_ms != 0 and system_state.idle_time_ms(millis()) >= sleep_timeout_ms) {
        system_state.set_next_state(PowerState::WAKEFUL_SLEEP);
    }
}

void RemoteTask::run() {
    remote_out.service(remote_in.service());
    if (system_state.ready_for_tasks()) {
        remote_out.update();
    }
}

void SerialPortInTask::run() {
    if (battery.is_charging()) {
        cmd_exec.exec();
    }
}

void SerialPortOutTask::run() {
    if (battery.is_charging()) {
        cmd_exec.update_telemetry(true);
    }
}

uint32_t SerialPortOutTask::interval_ms() const {
    return identify_store->payload()->telemetry_interval_ms();
}
