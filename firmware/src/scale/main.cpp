#include "constants.h"
#include "common/task/task.h"
#include "scale/measure/stack.h"
#include "scale/nvm/nvm.h"
#include "scale/remote/remote_out.h"
#include "scale/task/task.h"

void setup() {
    calibration_store->begin();
    identify_store->begin();
    tare_store->begin();

    MeasurementStack::get().begin();
    scale::AutoWakeTask().run_on_wake();

    // 2025_04_01: Observed skipped characters at 115200 with mini pro 3v3. Suspect this is due
    // to the 8MHz clock providing nearest baudrates of 115942 or 114285, whereas the closest
    // baudrates for 8MHz for 57600 baud is 57554 or 57971.
    Serial.begin(DEFAULT_BAUD_RATE);

    RemoteOut::get().begin();
}


void loop() {
    static common::Task* tasks[] = {
        new scale::AutoWakeTask(),         // Execution timing dependent upon NVM config and logic
        new scale::PowerTransitionTask(),  // Executed each loop
        new common::SerialPortInTask(10),   // Every 10ms
        new scale::SerialPortOutTask(),    // Execution timing dependent upon NVM config
        new scale::RemoteTask(50),        // Every 50ms
    };

    for (const auto task : tasks) {
        task->tick(millis());
    }

    delay(SMALL_DELAY_MS);
}
