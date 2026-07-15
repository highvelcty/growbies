#include "task.h"

void common::SerialPortInTask::run() {
    cmd_exec.exec();
}

void common::SerialPortOutTask::run() {
    cmd_exec.update_telemetry(true);
}
