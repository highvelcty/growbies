#pragma once

#include "common/task/task.h"
#include "common/protocol/cmd_exec.h"
#include "scale/measure/battery.h"
#include "scale/remote/remote_out.h"
#include "common/system_state.h"

namespace scale {

class AutoWakeTask final : public common::Task {
public:
    void run() override;
    void run_on_wake();
    unsigned long interval_ms() const override;

protected:
    bool ready_to_run(const unsigned long now) const override{
        if (system_state.next_state() == PowerState::INITIAL) {
            return true;
        }
        return Task::ready_to_run(now);
    }

private:
    Battery battery;
    MeasurementStack& measurement_stack = MeasurementStack::get();
};

class PowerTransitionTask final : public common::Task {
public:
    using Task::Task;
    void run() override;

protected:
    bool ready_to_run(const unsigned long now) const override { return true; }

private:
    Battery battery;
    MeasurementStack& measurement_stack = MeasurementStack::get();
    RemoteOut& remote_out = RemoteOut::get();
};

class RemoteTask final : public common::Task {
public:
    using Task::Task;
    void run() override;
private:
    RemoteIn& remote_in = RemoteIn::get();
    RemoteOut& remote_out = RemoteOut::get();
};

class SerialPortOutTask final : public common::SerialPortOutTask {
public:
    void run() override;
    unsigned long interval_ms() const override;
private:
    Battery battery;
    CmdExec& cmd_exec = CmdExec::get();
};

}