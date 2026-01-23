#include "constants.h"
#include "flags.h"
#include "task.h"
#include "measure/stack.h"
#include "nvm/nvm.h"

#if FEATURE_DISPLAY
#include "remote/remote_high.h"
#endif

void setup() {
    calibration_store->begin();
    identify_store->begin();
    tare_store->begin();

    // 2025_04_01: Observed skipped characters at 115200 with mini pro 3v3. Suspect this is due
    //   to the 8MHz clock providing nearest baudrates of 115942 or 114285, whereas the closest
    //   baudrates for 8MHz for 57600 baud is 57554 or 57971.
    Serial.begin(57600);

#if FEATURE_DISPLAY
    RemoteHigh::get().begin();
#endif

    growbies_hf::MeasurementStack::get().begin();
}

void loop() {
    static Task* tasks[] = {
        new StaticTask(task_exec_cmd,       10),
        new StaticTask(task_measure,        25),
        new StaticTask(task_remote_service, 50),
        new StaticTask(task_remote_update,  100),
        new TelemetryTask()
    };

    const unsigned long now = millis();

    for (const auto task : tasks) {
        // skip telemetry if disabled
        if (task->interval_ms() == 0) {
            continue;
        }
        task->tick(now);
    }

    delay(SMALL_DELAY_MS);
}
