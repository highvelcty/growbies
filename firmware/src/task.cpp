#include "task.h"
#include "measure/stack.h"
#include "protocol/cmd_exec.h"
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

void task_measure() {
    const auto& measurement_stack = growbies_hf::MeasurementStack::get();
    measurement_stack.update();
}

void task_remote_service() {
#if FEATURE_DISPLAY
    RemoteHigh::get().service();
#endif
}

void task_remote_update() {
#if FEATURE_DISPLAY
    RemoteHigh::get().update();
#endif
}

void task_telemetry_update() {
    CmdExec::get().update_telemetry(true);
}
