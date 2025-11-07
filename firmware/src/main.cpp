#include "constants.h"
#include "flags.h"
#include <growbies.h>
#include <measure_intf.h>
#include <network.h>
#include <nvm.h>

#if FEATURE_DISPLAY
#include <remote_high.h>
#endif

#include <command.h>

// Simple cooperative task structure
struct Task {
    void (*fn)();
    unsigned long interval_ms;
    unsigned long last_run;
};

void task_serial() {
    while (Serial.available()) {
        if (recv_slip(Serial.read())) {
            const PacketHdr *packet_hdr = recv_packet();
            if (packet_hdr) {
                growbies.execute(packet_hdr);
            }
            slip_buf->reset();
        }
    }
}

void task_measure() {
    // growbies.measure();
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

    slip_buf->reset();
    // 2025_04_01: Observed skipped characters at 115200 with mini pro 3v3. Suspect this is due
    //   to the 8MHz clock providing nearest baudrates of 115942 or 114285, whereas the closest
    //   baudrates for 8MHz for 57600 baud is 57554 or 57971.
    Serial.begin(57600);
    Growbies::begin();
#if FEATURE_DISPLAY
    RemoteHigh::get().begin();
#endif

    auto& measurement_stack = growbies_hf::MeasurementStack::get();
    measurement_stack.begin();
}

void loop() {
    static Task tasks[] = {
        {task_serial,               10, 0},
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
