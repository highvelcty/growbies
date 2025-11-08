#include "constants.h"
#include "flags.h"
#include "measure/measure_intf.h"
#include "nvm/nvm.h"
#include "protocol/cmd_exec.h"

#if FEATURE_DISPLAY
#include "remote/remote_high.h"
#endif

// Simple cooperative task structure
struct Task {
    void (*fn)();
    unsigned long interval_ms;
    unsigned long last_run;
};

void task_exec_cmd() {
    CmdExec::get().exec();
}

void task_measure() {
    auto& measurement_stack = growbies_hf::MeasurementStack::get();
    measurement_stack.update();
}

void task_remote_service() {
#if FEATURE_DISPLAY
    RemoteHigh& remote = RemoteHigh::get();
    remote.service();
#endif
}

void task_remote_update() {
#if FEATURE_DISPLAY
    const RemoteHigh& remote = RemoteHigh::get();
    remote.update();
#endif
}

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
    static Task tasks[] = {
        {task_exec_cmd,             10, 0},
        {task_measure,              25, 0},
        {task_remote_service,       50, 0},
        {task_remote_update,        100, 0}
    };

    const unsigned long now = millis();

    for (auto & task : tasks) {
        if (now - task.last_run >= task.interval_ms) {
            task.fn();
            task.last_run = now;
        }
    }

    delay(SMALL_DELAY_MS);
}
