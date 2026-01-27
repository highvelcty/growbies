#include "task.h"
#include "measure/stack.h"
#include "nvm/nvm.h"
#include "protocol/cmd_exec.h"
#include "system_state.h"
#if FEATURE_DISPLAY
#include "remote/remote_high.h"
#endif

// ------------------- StaticTask -------------------

StaticTask::StaticTask(void (*fn)(), unsigned long interval)
    : fn_(fn)
{
    static_interval_ms = interval;
}

void StaticTask::run() {
    if (fn_) {
        fn_();
    }
}

// ------------------- TelemetryTask -------------------

void TelemetryTask::run() {
    CmdExec::get().update_telemetry(true);
}

uint32_t TelemetryTask::interval_ms() const {
    return identify_store->payload()->telemetry_interval_ms();
}

// ------------------- Task function implementations -------------------

void task_exec_cmd() {
    CmdExec::get().exec();
}

void task_remote_service() {
#if FEATURE_DISPLAY
    RemoteHigh::get().service();
#endif
}

void task_remote_update() {
#if FEATURE_DISPLAY
    auto& remote_high = RemoteHigh::get();
    auto& system_state = SystemState::get();

    if (system_state.is_active()) {
        const auto sleep_timeout_ms = identify_store->view()->payload.sleep_timeout_ms();
        if (sleep_timeout_ms && system_state.idle_time_ms(millis()) > sleep_timeout_ms) {
            remote_high.display_power_save(true);
            system_state.set_display_off();
        }
        else {
            RemoteHigh::get().update();
        }
    }
#endif
}

void task_telemetry_update() {
    CmdExec::get().update_telemetry(true);
}
