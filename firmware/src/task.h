#pragma once

// Base cooperative task
struct Task {
    virtual ~Task() = default;
    virtual void run() = 0;
    virtual unsigned long interval_ms() const { return static_interval_ms; }

    void tick(const unsigned long now) {
        if (now - last_run >= interval_ms()) {
            run();
            last_run = now;
        }
    }

protected:
    unsigned long static_interval_ms{0};
    unsigned long last_run{0};
};

// Standard static-interval task
struct StaticTask final : Task {
    StaticTask(void (*fn)(), unsigned long interval);

    void run() override;

private:
    void (*fn_)() = nullptr;
};

// Telemetry task with dynamic interval
struct TelemetryTask final : Task {
    void run() override;
    unsigned long interval_ms() const override;
};

// Declarations of task functions
void task_exec_cmd();
void task_remote_service();
void task_remote_update();
void task_telemetry_update();
