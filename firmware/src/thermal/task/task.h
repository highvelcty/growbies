#pragma once

#include "common/task/task.h"

namespace thermal {

class ThermalDeviceTask final : public common::Task {
public:
    using Task::Task;
    void run() override;
};

}