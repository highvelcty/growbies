#pragma once

#include "protocol/cmd_exec.h"
#include "measure/battery.h"
#include "remote/remote_out.h"
#include "system_state.h"

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

class AutoWakeTask final : public Task {
public:
    void run() override;
    void run_on_wake() const;
    unsigned long interval_ms() const override;

protected:
    bool ready_to_run(const unsigned long now) const override{
        if (system_state.next_state() == PowerState::INITIAL) {
            return true;
        }
        return Task::ready_to_run(now);
    }

private:
    MeasurementStack& measurement_stack = MeasurementStack::get();
};

class PowerTransitionTask final : public Task {
public:
    using Task::Task;
    void run() override;

protected:
    bool ready_to_run(const unsigned long now) const override { return true; }

private:
    Battery battery;
    RemoteOut& remote_out = RemoteOut::get();
};

class SerialPortOutTask final : public Task {
public:
    void run() override;
    unsigned long interval_ms() const override;
private:
    Battery battery;
    CmdExec& cmd_exec = CmdExec::get();
};

class RemoteServiceTask final : public Task {
public:
    using Task::Task;
    void run() override;
private:
    RemoteIn& remote_in = RemoteIn::get();
    RemoteOut& remote_out = RemoteOut::get();
};

class RemoteUpdateTask final : public Task {
public:
    using Task::Task;
    void run() override;
private:
    RemoteOut& remote_out = RemoteOut::get();
};

class SerialPortInTask final : public Task {
public:
    using Task::Task;
    void run() override;
private:
    Battery battery;
    CmdExec& cmd_exec = CmdExec::get();
};
