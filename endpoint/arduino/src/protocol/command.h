#ifndef command_h
#define command_h

#include "flags.h"
#include "protocol/network.h"

enum Cmd: uint16_t {
    CMD_LOOPBACK = 0,
    CMD_READ_DAC = 1,
    CMD_READ_UNITS = 2,
    CMD_GET_SCALE = 3,
    CMD_SET_SCALE = 4,
    CMD_GET_TARE = 5,
    CMD_SET_TARE = 6,
    CMD_SET_PHASE = 7,
    CMD_GET_TEMPERATURE_COEFFICIENT = 8,
    CMD_SET_TEMPERATURE_COEFFICIENT = 9,
};

enum RespType: uint16_t {
    RESP_TYPE_VOID = 0,
    RESP_TYPE_BYTE = 1,
    RESP_TYPE_LONG = 2,
    RESP_TYPE_FLOAT = 3,
    RESP_TYPE_DOUBLE = 4,
    RESP_MULTI_DATA_POINT = 5,
    RESP_GET_TARE = 6,
    RESP_GET_TEMPERATURE_COEFFICIENT = 7,
    RESP_TYPE_ERROR = 0xFFFF,
};

enum Error: long {
    ERROR_NONE = 0,
    ERROR_CMD_DESERIALIZATION_BUFFER_UNDERFLOW = 1,
    ERROR_UNRECOGNIZED_COMMAND = 2,
};

enum Phase: uint8_t {
    PHASE_A = 0,
    PHASE_B = 1
};


// --- Base Commands
struct BaseCmd : PacketHdr {};

struct BaseCmdWithTimesParam : BaseCmd {
    uint8_t times;
};

// --- Base Types
typedef float TemperatureCoefficient[TEMPERATURE_COEFFICIENT_COUNT];

// --- Commands
struct CmdReadDAC : BaseCmdWithTimesParam {};
struct CmdReadUnits : BaseCmdWithTimesParam {};
struct CmdSetPhase : BaseCmd {
    uint16_t phase;
};
struct CmdGetScale : BaseCmd {};
struct CmdSetScale : BaseCmd {
    float scale;
};
struct CmdGetTare: BaseCmd {};
struct CmdSetTare: BaseCmd {};
struct CmdGetTemperatureCoefficient: BaseCmd {};
struct CmdSetTemperatureCoefficient: BaseCmd {
    TemperatureCoefficient coefficient;
};
// --- Base Responses
struct BaseResp : PacketHdr {
    BaseResp(RespType resp_type) : PacketHdr(resp_type) {};
};

struct RespVoid : BaseResp {
    RespVoid(RespType resp_type = RESP_TYPE_VOID) : BaseResp(resp_type) {};
};

struct RespByte : BaseResp {
    uint8_t data;
    RespByte(RespType resp_type = RESP_TYPE_BYTE) : BaseResp(resp_type) {};
};

struct RespLong : BaseResp {
    long data;
    RespLong(RespType resp_type = RESP_TYPE_LONG) : BaseResp(resp_type) {};
};

struct RespFloat : BaseResp {
    float data;
    RespFloat(RespType resp_type = RESP_TYPE_FLOAT) : BaseResp(resp_type) {};
};

struct RespDouble : BaseResp {
    double data;
    RespDouble(RespType resp_type = RESP_TYPE_DOUBLE) : BaseResp(resp_type) {};
};

struct RespError : BaseResp {
    Error error;
    RespError(RespType resp_type = RESP_TYPE_ERROR) : BaseResp(resp_type) {};
};

// --- Cmd Responses
struct RespGetTare : BaseResp {
#if AC_EXCITATION
    float mass_a_offset[MAX_HX711_DEVICES];
    float mass_b_offset[MAX_HX711_DEVICES];
#else
    float mass_offset[MAX_HX711_DEVICES];
#endif
    RespGetTare(): BaseResp(RESP_GET_TARE) {};
};

struct RespGetTemperatureCoefficient: BaseResp {
    TemperatureCoefficient coefficient;
    RespGetTemperatureCoefficient(): BaseResp(RESP_GET_TEMPERATURE_COEFFICIENT) {};
};

struct DataPoint {
    float data;
    byte error_count;
    byte ready : 1;
    byte  reserved : 7;
    byte reserved2[2];
};

struct MultiDataPoint {
#if AC_EXCITATION
    DataPoint mass_a;
    DataPoint mass_b;
#endif
    DataPoint mass;
#if AC_EXCITATION
    DataPoint temperature_a;
    DataPoint temperature_b;
#endif
    DataPoint temperature;
};

struct RespMultiDataPoint : BaseResp {
    RespMultiDataPoint() : BaseResp(RESP_MULTI_DATA_POINT) {};
};

#endif /* command_h */