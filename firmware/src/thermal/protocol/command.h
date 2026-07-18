#pragma once

#include "common/protocol/command.h"
#include "thermal/thermal.h"

#pragma pack(1)

// Commands
struct CmdGetThermalState : BaseCmd {};
struct CmdSetThermalState : BaseCmd {
    ThermalDeviceControl control;
};

// Responses
struct RespGetThermalState : BaseResp, ThermalDeviceState {

    static constexpr auto VERSION = ThermalDeviceState::VERSION;
    static constexpr auto TYPE = Resp::THERMAL_STATE;
};

#pragma pack()