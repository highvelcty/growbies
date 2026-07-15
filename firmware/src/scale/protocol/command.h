#pragma once

#include "constants.h"
#include "common/protocol/command.h"
#include "scale/nvm/nvm.h"

#pragma pack(1)

// --- Commands
struct CmdGetCalibration : BaseCmd {};
struct CmdSetCalibration : BaseCmd {
    bool init = false;
    NvmCalibration calibration{};
};
struct CmdGetIdentify: BaseCmd {};
struct CmdSetIdentify : BaseCmd {
    bool init = false;
    NvmIdentify identify{};
};
struct CmdGetTare: BaseCmd {};
struct CmdSetTare : BaseCmd {
    bool init = false;
    NvmTare tare{};
};

struct CmdPowerOnHx711 : BaseCmd {};
struct CmdPowerOffHx711 : BaseCmd {};
struct CmdRead : BaseCmd {
    static constexpr auto VERSION = 2;
    bool reset = false;
};

struct RespGetCalibration : BaseResp {
    static constexpr auto VERSION = NvmCalibration::VERSION;
    static constexpr auto TYPE = Resp::CALIBRATION;

    NvmCalibration calibration{};

    explicit RespGetCalibration(const NvmCalibration& cal = NvmCalibration{})
        : calibration(cal) {}
};
static_assert(sizeof(RespGetCalibration) < MAX_SLIP_UNENCODED_PACKET_BYTES, "buffer overflow");
static_assert(156 == sizeof(RespGetCalibration), "unexpected structure size");

struct RespGetIdentify : BaseResp {
    static constexpr auto VERSION = NvmIdentify::VERSION;
    static constexpr auto TYPE = Resp::IDENTIFY;

    NvmIdentify identify{};

    explicit RespGetIdentify(const NvmIdentify& ident = NvmIdentify{})
        : identify(ident) {}
};
static_assert(sizeof(RespGetIdentify) < MAX_SLIP_UNENCODED_PACKET_BYTES, "buffer overflow");

struct RespGetTare : BaseResp {
    static constexpr auto VERSION = NvmTare::VERSION;
    static constexpr auto TYPE = Resp::TARE;

    NvmTare tare{};

    explicit RespGetTare(const NvmTare& tare_ = NvmTare{})
        : tare(tare_) {}
};
static_assert(sizeof(RespGetTare) < MAX_SLIP_UNENCODED_PACKET_BYTES, "buffer overflow");

#pragma pack()
