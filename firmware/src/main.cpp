#include "constants.h"
#include "task.h"
#include "measure/stack.h"
#include "nvm/nvm.h"
#include "remote/remote_high.h"

void setup() {
    calibration_store->begin();
    identify_store->begin();
    tare_store->begin();

    // 2025_04_01: Observed skipped characters at 115200 with mini pro 3v3. Suspect this is due
    //   to the 8MHz clock providing nearest baudrates of 115942 or 114285, whereas the closest
    //   baudrates for 8MHz for 57600 baud is 57554 or 57971.
    Serial.begin(57600);

    RemoteHigh::get().begin();

    MeasurementStack::get().begin();
}

void loop() {
    static Task* tasks[] = {
        new SerialPortInTask(10),   // Every 10ms
        new RemoteInputTask(50),    // Every 50ms
        new RemoteOutputTask(200),  // Every 200ms
        new SerialPortOutTask(),    // Execution timing dependent upon NVM config
        new PowerTransitionTask()   // Executed each loop
    };

    for (const auto task : tasks) {
        task->tick(millis());
    }

    delay(SMALL_DELAY_MS);
}
