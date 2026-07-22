#include "task.h"

void common::SerialPortInTask::run() {
    cmd_exec.exec();
}

void common::TelemetryTask::run() {
    cmd_exec.update_telemetry(true);
}
