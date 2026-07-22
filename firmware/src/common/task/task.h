#pragma once

#include "common/protocol/cmd_exec.h"
#include "common/system_state.h"

namespace common {

class Task {
public:
    explicit Task(const unsigned long interval = 0)
        : interval_ms_(interval)
    {}
    virtual ~Task() = default;
    virtual void run() = 0;
    virtual unsigned long interval_ms() const { return interval_ms_; }

    virtual void tick(const unsigned long now) {
        if (ready_to_run(now)) {
            run();
            last_run = now;
        }
    }

protected:
    unsigned long interval_ms_{0};
    unsigned long last_run{0};
    SystemState& system_state = SystemState::get();

    virtual bool ready_to_run(const unsigned long now) const {
        if (interval_ms() == 0) {
            return false;
        }
        if (now - last_run >= interval_ms()) {
            return true;
        }
        return false;
    };
};

class SerialPortInTask final : public Task {
public:
    using Task::Task;
    void run() override;
private:
    CmdExec& cmd_exec = CmdExec::get();
};

class TelemetryTask : public Task {
public:
    using Task::Task;
    void run() override;
private:
    CmdExec& cmd_exec = CmdExec::get();
};

}