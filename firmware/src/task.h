#pragma once

#include "protocol/cmd_exec.h"
#include "measure/battery.h"
#include "remote/remote_high.h"
#include "system_state.h"

class Task {
public:
    explicit Task(const unsigned long interval = 0)
        : interval_ms_(interval)
    {}
    virtual ~Task() = default;
    virtual void run() = 0;
    virtual unsigned long interval_ms() const { return interval_ms_; }

    void tick(const unsigned long now) {
        if (ready_to_run(now)) {
            run();
            last_run = now;
        }
    }

protected:
    unsigned long interval_ms_{0};
    unsigned long last_run{0};

private:
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

class PowerTransitionTask final : public Task {
public:
    using Task::Task;
    void run() override;

private:
    Battery battery;
    SystemState& system_state = SystemState::get();

    bool ready_to_run(const unsigned long now) const override { return true; }
};

class SerialPortOutTask final : public Task {
public:
    void run() override;
    unsigned long interval_ms() const override;
private:
    CmdExec& cmd_exec = CmdExec::get();
};

class RemoteInputTask final : public Task {
public:
    using Task::Task;
    void run() override;
private:
    RemoteHigh& remote_high = RemoteHigh::get();
};

class RemoteOutputTask final : public Task {
public:
    using Task::Task;
    void run() override;
private:
    RemoteHigh& remote_high = RemoteHigh::get();
    SystemState& system_state = SystemState::get();
};

class SerialPortInTask final : public Task {
public:
    using Task::Task;
    void run() override;
private:
    CmdExec& cmd_exec = CmdExec::get();
};
