#ifndef command_h
#define command_h

#include "flags.h"
#include "persistent_store.h"

#pragma pack(1)

enum class Cmd: uint16_t {
    LOOPBACK = 0,
    GET_CALIBRATION = 1,
    SET_CALIBRATION = 2,
    READ_UNITS = 3,
    POWER_ON_HX711 = 4,
    POWER_OFF_HX711 = 5,
};

enum class Resp: uint16_t {
    VOID = 0,
    BYTE = 1,
    LONG = 2,
    FLOAT = 3,
    DOUBLE = 4,
    READ_UNITS = 5,
    GET_CALIBRATION = 6,
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
inline Error operator|(Error lhs, Error rhs) {
    return static_cast<Error>(
        static_cast<uint32_t>(lhs) | static_cast<uint32_t>(rhs));
}

inline Error& operator|=(Error& lhs, Error rhs) {
    lhs = lhs | rhs;
    return lhs;
}

enum Phase: uint8_t {
    PHASE_A = 0,
    PHASE_B = 1
};

typedef enum Unit : uint16_t {
    // Bitfield
    UNIT_GRAMS       = 0x0001,
    UNIT_MASS_DAC    = 0x0002,
    UNIT_TEMP_DAC    = 0x0004,
    UNIT_CELSIUS     = 0x0008,
} Units;

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
struct BaseCmd : PacketHdr {};

struct BaseCmdWithTimesParam : BaseCmd {
    uint8_t times;
};

// --- Commands
struct CmdGetCalibration : BaseCmd {};
struct CmdSetCalibration : BaseCmd {
    CalibrationStruct calibration;
};
struct CmdPowerOnHx711 : BaseCmd {};
struct CmdPowerOffHx711 : BaseCmd {};
struct CmdReadUnits : BaseCmdWithTimesParam {
    Unit units;
};
// --- Base Responses
struct BaseResp : PacketHdr {
    Error error = ERROR_NONE;
    BaseResp(Resp resp_type) : PacketHdr(resp_type) {};
};

struct RespVoid : BaseResp {
    RespVoid(Resp resp_type = Resp::VOID) : BaseResp(resp_type) {};
};

struct RespByte : BaseResp {
    uint8_t data;
    RespByte(Resp resp_type = Resp::BYTE) : BaseResp(resp_type) {};
};

struct RespLong : BaseResp {
    long data;
    RespLong(Resp resp_type = Resp::LONG) : BaseResp(resp_type) {};
};

struct RespFloat : BaseResp {
    float data;
    RespFloat(Resp resp_type = Resp::FLOAT) : BaseResp(resp_type) {};
};

struct RespDouble : BaseResp {
    double data;
    RespDouble(Resp resp_type = Resp::DOUBLE) : BaseResp(resp_type) {};
};

struct RespError : BaseResp {
    Error error;
    RespError(Resp resp_type = Resp::ERROR) : BaseResp(resp_type) {};
};

// --- Responses
struct RespLoopback : BaseResp {
    RespLoopback(): BaseResp(Resp::VOID) {};
};

struct RespGetCalibration : BaseResp {
    CalibrationStruct calibration;
    RespGetCalibration(): BaseResp(Resp::GET_CALIBRATION) {};
};
static_assert(sizeof(RespGetCalibration) < MAX_SLIP_UNENCODED_PACKET_BYTES);

typedef float MassSensor[MASS_SENSOR_COUNT];
typedef float TemperatureSensor[TEMPERATURE_SENSOR_COUNT];
struct RespMultiDataPoint : BaseResp {
    MassSensor mass_sensor;
    float mass;
    TemperatureSensor temperature_sensor;
    float temperature;

    RespMultiDataPoint() : BaseResp(Resp::READ_UNITS) {};
};
static_assert(sizeof(RespMultiDataPoint) < MAX_SLIP_UNENCODED_PACKET_BYTES);

#endif /* command_h */