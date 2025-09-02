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
    GET_IDENTIFY = 6,
    SET_IDENTIFY = 7,
};

enum class Resp: uint16_t {
    VOID = 0,
    DATAPOINT = 1,
    CALIBRATION = 2,
    IDENTIFY = 3,
    ERROR = 0xFFFF,
};

typedef enum ErrorCode: uint32_t {
    // bitfield
    ERROR_NONE                                  = 0x00000000,
    ERROR_CMD_DESERIALIZATION_BUFFER_UNDERFLOW  = 0x00000001,
    ERROR_UNRECOGNIZED_COMMAND                  = 0x00000002,
    ERROR_OUT_OF_THRESHOLD_SAMPLE               = 0x00000004,
    ERROR_HX711_NOT_READY                       = 0x00000008,
} ErrorCode;

// Bitwise operators for Error
inline ErrorCode operator|(const ErrorCode lhs, const ErrorCode rhs) {
    return static_cast<ErrorCode>(
        static_cast<uint32_t>(lhs) | static_cast<uint32_t>(rhs));
}

inline ErrorCode& operator|=(ErrorCode& lhs, const ErrorCode rhs) {
    lhs = lhs | rhs;
    return lhs;
}

// --- Base Commands
struct PacketHdr {
    union {
        uint16_t type;
        Resp resp;
        Cmd cmd;
    };
    uint16_t id = 0;  // Default is zero

    // Constructors
    explicit PacketHdr(const uint16_t id_, const Resp r) : resp(r), id(id_) {}
    explicit PacketHdr(const uint16_t id_, const Cmd c)  : cmd(c), id(id_) {}
    explicit PacketHdr(const Cmd c) : PacketHdr(0, c) {}
    explicit PacketHdr(const Resp r) : PacketHdr(0, r) {}
};

// Verify size at compile time
static_assert(sizeof(PacketHdr) == 4, "PacketHdr must be exactly 4 bytes");


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
    Calibration calibration{};
};
struct CmdGetIdentify: BaseCmd {};
struct CmdSetIdentify : BaseCmd {
    Identify1 identify{};
};

struct CmdPowerOnHx711 : BaseCmd {};
struct CmdPowerOffHx711 : BaseCmd {};
struct CmdGetDatapoint : BaseCmdWithTimesParam {
    bool raw{};
};
// --- Base Responses
struct BaseResp : PacketHdr {
    explicit BaseResp(const Resp resp_type) : PacketHdr(resp_type) {}
};

struct RespVoid : BaseResp {
    explicit RespVoid(const Resp resp_type = Resp::VOID) : BaseResp(resp_type) {}
};

struct RespError : BaseResp {
    ErrorCode error{};
    explicit RespError(const Resp resp_type = Resp::ERROR) : BaseResp(resp_type) {}
};

// --- Responses
struct RespLoopback : BaseResp {
    RespLoopback(): BaseResp(Resp::VOID) {}
};

struct RespGetCalibration : BaseResp {
    Calibration calibration{};
    RespGetCalibration(): BaseResp(Resp::CALIBRATION) {}
};
static_assert(sizeof(RespGetCalibration) < MAX_SLIP_UNENCODED_PACKET_BYTES);

struct RespGetIdentify : BaseResp {
    Identify1 identify{};
    RespGetIdentify(): BaseResp(Resp::IDENTIFY) {}
};
static_assert(sizeof(RespGetIdentify) < MAX_SLIP_UNENCODED_PACKET_BYTES);

typedef float MassSensor[MASS_SENSOR_COUNT];
typedef float TemperatureSensor[TEMPERATURE_SENSOR_COUNT];
struct RespDataPoint : BaseResp {
    MassSensor mass_sensor{};
    float mass{};
    TemperatureSensor temperature_sensor{};
    float temperature{};

    RespDataPoint() : BaseResp(Resp::DATAPOINT) {}
};
static_assert(sizeof(RespDataPoint) < MAX_SLIP_UNENCODED_PACKET_BYTES);

#endif /* command_h */


