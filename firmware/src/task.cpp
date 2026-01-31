#include "esp_sleep.h"

#include "task.h"
#include "nvm/nvm.h"

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
            esp_deep_sleep_enable_gpio_wakeup(1ULL << digitalPinToGPIONumber(BUTTON_0_PIN) |
                                      1ULL << digitalPinToGPIONumber(BUTTON_1_PIN),
                                      ESP_GPIO_WAKEUP_GPIO_HIGH);
            esp_sleep_enable_timer_wakeup(1000 * 1000ULL);
            esp_deep_sleep_start();
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
                    // meyere - 2026_01_30: I did not find disabling the wakeup by timer source only to
                    // be effective.
                    //
                    // esp_sleep_disable_wakeup_source(ESP_SLEEP_WAKEUP_TIMER);
                    esp_sleep_disable_wakeup_source(ESP_SLEEP_WAKEUP_ALL);
                    delay(100);
                    esp_deep_sleep_enable_gpio_wakeup(1ULL << digitalPinToGPIONumber(BUTTON_0_PIN) |
                                              1ULL << digitalPinToGPIONumber(BUTTON_1_PIN),
                                              ESP_GPIO_WAKEUP_GPIO_HIGH);
                    esp_deep_sleep_start();
                }
                esp_sleep_enable_timer_wakeup(auto_wake_interval * 1000ULL);
                esp_deep_sleep_start();
            }
        }
        else if (system_state.next_state() == PowerState::DEEP_SLEEP) {
            remote_out.display_power_save(true);

            // meyere - 2026_01_30: I did not find disabling the wakeup by timer source only to
            // be effective.
            //
            // esp_sleep_disable_wakeup_source(ESP_SLEEP_WAKEUP_TIMER);
            esp_sleep_disable_wakeup_source(ESP_SLEEP_WAKEUP_ALL);
            delay(100); // meyere: Why is this needed again? debouncing?
            esp_deep_sleep_enable_gpio_wakeup(1ULL << digitalPinToGPIONumber(BUTTON_0_PIN) |
                                      1ULL << digitalPinToGPIONumber(BUTTON_1_PIN),
                                      ESP_GPIO_WAKEUP_GPIO_HIGH);

            esp_deep_sleep_start();
        }
    }

    const auto sleep_timeout_ms = identify_store->payload()->sleep_timeout_ms();
    if (sleep_timeout_ms != 0 and system_state.idle_time_ms(millis()) >= sleep_timeout_ms) {
        system_state.set_next_state(PowerState::WAKEFUL_SLEEP);
    }
}

void RemoteServiceTask::run() {
    remote_out.service(remote_in.service());
}

void RemoteUpdateTask::run() {
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
