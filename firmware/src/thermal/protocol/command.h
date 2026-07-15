#pragma once

#include "common/protocol/command.h"

#pragma pack(1)

struct CmdRead : BaseCmd {
    static constexpr auto VERSION = 1;
};

#pragma pack()