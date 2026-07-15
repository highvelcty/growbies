#include "constants.h"
#include "common/task/task.h"

void setup() {
    Serial.begin(DEFAULT_BAUD_RATE);
}

void loop() {
    static Task* tasks[] = {
        new SerialPortInTask(10),   // Every 10ms
    };

    for (const auto task : tasks) {
        task->tick(millis());
    }

    delay(SMALL_DELAY_MS);
}
