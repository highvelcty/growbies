#include "constants.h"
#include "common/task/task.h"
#include "thermal/task/task.h"
#include "thermal/thermal.h"

void setup() {
    Serial.begin(DEFAULT_BAUD_RATE);
}

void loop() {
    static common::Task* tasks[] = {
        new common::SerialPortInTask(10),   // Every 10ms
        new thermal::ThermalDeviceTask(ThermalDevice::UPDATE_INTERVAL_MS),
        new common::TelemetryTask(10000), // Every 10 seconds
    };

    for (const auto task : tasks) {
        task->tick(millis());
    }

    delay(SMALL_DELAY_MS);
}
