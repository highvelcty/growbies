#include "task.h"
#include "thermal/thermal.h"

void thermal::ThermalDeviceTask::run() {
    ThermalDevice::get().update();
}

void thermal::TelemetryTask::run() {
    if (ThermalDevice::get().get_state().control.active) {
        // Only send telemetry if active, otherwise the thermal device thermistor reads stale air
        // due to the fans not running.
        common::TelemetryTask::run();
    }
}