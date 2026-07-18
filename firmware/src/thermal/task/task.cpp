#include "task.h"
#include "thermal/thermal.h"

void thermal::ThermalDeviceTask::run() {
    ThermalDevice::get().update();
}