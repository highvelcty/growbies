#pragma once

#include "common/task/task.h"

namespace thermal {

class ThermalDeviceTask final : public common::Task {
public:
    using Task::Task;
    void run() override;
};

class TelemetryTask final : public common::TelemetryTask {
public:
    void run() override;
private:
    CmdExec& cmd_exec = CmdExec::get();
};

}