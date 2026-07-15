#include "task.h"

void SerialPortInTask::run() {
    cmd_exec.exec();
}