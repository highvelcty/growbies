#include "constants.h"
#include "flags.h"
#include <growbies.h>
#include <network.h>
#include <nvm.h>

#if FEATURE_DISPLAY
#include <menu.h>
#endif

#if ARDUINO_ARCH_ESP32
#include "esp_sleep.h"
#endif
#include <command.h>

#if FEATURE_LED
#include "lib/led.h"
#endif

// ---------------------------------------------------------------------------
// Global inactivity tracker
// ---------------------------------------------------------------------------
unsigned long last_activity_ms = 0;

// Simple cooperative task structure
struct Task {
    void (*fn)();
    unsigned long interval_ms;
    unsigned long last_run;
};

void mark_activity() {
    last_activity_ms = millis();
}

void task_serial() {
    if (Serial.available()) {
        mark_activity();
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
    growbies.measure();
}

void task_remote() {
#if FEATURE_DISPLAY
    Menu& menu = Menu::get();
    if (menu.service()) {
        mark_activity();
    }
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
    last_activity_ms = millis();
#if FEATURE_DISPLAY
    Menu::get().begin();
#endif
}

void loop() {
    static Task tasks[] = {
        {task_serial,       10, 0},
        {task_remote,       50, 0},
        {task_measure,      1000, 0},
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
