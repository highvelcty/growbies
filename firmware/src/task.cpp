#include "task.h"
#include "esp_sleep.h"
#include "nvm/nvm.h"

void PowerTransitionTask::run() {
    if (system_state.is_active()) {
        const auto sleep_timeout_ms = identify_store->view()->payload.sleep_timeout_ms();
        if (sleep_timeout_ms && system_state.idle_time_ms(millis()) > sleep_timeout_ms) {
            system_state.set_idle();
            RemoteHigh::get().display_power_save(true);
            if (not battery.is_charging()) {
                esp_deep_sleep_start();
            }
        }
    }
}

void RemoteInputTask::run() {
    remote_high.service();
}

void RemoteOutputTask::run() {
    remote_high.update();
}

void SerialPortInTask::run() {
    cmd_exec.exec();
}

void SerialPortOutTask::run() {
    cmd_exec.update_telemetry(true);
}

uint32_t SerialPortOutTask::interval_ms() const {
    return identify_store->payload()->telemetry_interval_ms();
}
