#ifndef command_h
#define command_h

#include "flags.h"
#include "persistent_store.h"

#pragma pack(1)

enum class Cmd: uint16_t {
    LOOPBACK = 0,
    GET_CALIBRATION = 1,
    SET_CALIBRATION = 2,
    GET_DATAPOINT = 3,
    POWER_ON_HX711 = 4,
    POWER_OFF_HX711 = 5,
};

enum class Resp: uint16_t {
    VOID = 0,
    DATAPOINT = 1,
    CALIBRATION = 2,
    ERROR = 0xFFFF,
};

typedef enum Error: uint32_t {
    // bitfield
    ERROR_NONE                                  = 0x00000000,
    ERROR_CMD_DESERIALIZATION_BUFFER_UNDERFLOW  = 0x00000001,
    ERROR_UNRECOGNIZED_COMMAND                  = 0x00000002,
    ERROR_OUT_OF_THRESHOLD_SAMPLE               = 0x00000004,
    ERROR_HX711_NOT_READY                       = 0x00000008,
} Error;

// Bitwise operators for Error
inline Error operator|(const Error lhs, const Error rhs) {
    return static_cast<Error>(
        static_cast<uint32_t>(lhs) | static_cast<uint32_t>(rhs));
}

inline Error& operator|=(Error& lhs, const Error rhs) {
    lhs = lhs | rhs;
    return lhs;
}

// --- Base Commands
struct PacketHdr {
    union {
        Resp resp;
        Cmd cmd;
    } type{};

    explicit PacketHdr(const Resp type_) {
        this->type.resp = type_;
    };

    explicit PacketHdr(const Cmd type_) {
        this->type.cmd = type_;
    }
};
struct BaseCmd : PacketHdr {
    explicit BaseCmd(const Cmd type_ = Cmd::LOOPBACK) : PacketHdr(type_) {};
};

struct BaseCmdWithTimesParam : BaseCmd {
    explicit BaseCmdWithTimesParam(const Cmd type_ = Cmd::LOOPBACK, const uint8_t times = 0)
        : BaseCmd(type_),
          times(times) {
    }

    uint8_t times;
};

// --- Commands
struct CmdGetCalibration : BaseCmd {};
struct CmdSetCalibration : BaseCmd {
    CalibrationStruct calibration{};
};
struct CmdPowerOnHx711 : BaseCmd {};
struct CmdPowerOffHx711 : BaseCmd {};
struct CmdGetDatapoint : BaseCmdWithTimesParam {
    bool raw{};
};
// --- Base Responses
struct BaseResp : PacketHdr {
    Error error = ERROR_NONE;
    explicit BaseResp(const Resp resp_type) : PacketHdr(resp_type) {};
};

struct RespVoid : BaseResp {
    explicit RespVoid(const Resp resp_type = Resp::VOID) : BaseResp(resp_type) {};
};

struct RespError : BaseResp {
    Error error;
    explicit RespError(const Resp resp_type = Resp::ERROR) : BaseResp(resp_type), error() {
    };
};

// --- Responses
struct RespLoopback : BaseResp {
    RespLoopback(): BaseResp(Resp::VOID) {};
};

struct RespGetCalibration : BaseResp {
    CalibrationStruct calibration;
    RespGetCalibration(): BaseResp(Resp::CALIBRATION), calibration() {
    };
};
static_assert(sizeof(RespGetCalibration) < MAX_SLIP_UNENCODED_PACKET_BYTES);

typedef float MassSensor[MASS_SENSOR_COUNT];
typedef float TemperatureSensor[TEMPERATURE_SENSOR_COUNT];
struct RespDataPoint : BaseResp {
    MassSensor mass_sensor;
    float mass;
    TemperatureSensor temperature_sensor;
    float temperature;

    RespDataPoint() : BaseResp(Resp::DATAPOINT), mass_sensor{}, mass(0), temperature_sensor{},
                      temperature(0) {
    };
};
static_assert(sizeof(RespDataPoint) < MAX_SLIP_UNENCODED_PACKET_BYTES);

#endif /* command_h */