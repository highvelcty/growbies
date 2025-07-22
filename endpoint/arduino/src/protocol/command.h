#ifndef command_h
#define command_h

#include "flags.h"
#include "lib/persistent_store.h"
#include "protocol/network.h"

#pragma pack(1)

enum Cmd: uint16_t {
    CMD_LOOPBACK = 0,
    CMD_GET_CALIBRATION = 1,
    CMD_SET_CALIBRATION = 2,
    CMD_READ_DAC = 3,
    CMD_READ_UNITS = 4,
    CMD_SET_PHASE = 5,
    CMD_POWER_ON_HX711 = 6,
    CMD_POWER_OFF_HX711 = 7,
    CMD_TEST = 0xFF
};

enum Response: uint16_t {
    RESP_VOID = 0,
    RESP_BYTE = 1,
    RESP_LONG = 2,
    RESP_FLOAT = 3,
    RESP_DOUBLE = 4,
    RESP_MULTI_DATA_POINT = 5,
    RESP_GET_CALIBRATION = 6,
    RESP_ERROR = 0xFFFF,
};

typedef enum Error: long {
    ERROR_NONE = 0,
    ERROR_CMD_DESERIALIZATION_BUFFER_UNDERFLOW = 1,
    ERROR_UNRECOGNIZED_COMMAND = 2,
} Error;

enum Phase: uint8_t {
    PHASE_A = 0,
    PHASE_B = 1
};

// --- Base Commands
struct BaseCmd : PacketHdr {};

struct BaseCmdWithTimesParam : BaseCmd {
    uint8_t times;
};

// --- Misc Structures
struct DataPoint {
    float data;
    byte error_count;
    byte ready : 1;
    byte  reserved : 7;
    byte reserved2[2];
};

struct MultiDataPoint {
    DataPoint mass;
    DataPoint temperature;
};


// --- Commands
struct CmdGetCalibration : BaseCmd {};
struct CmdSetCalibration : BaseCmd {
    CalibrationStruct calibration;
};
struct CmdPowerOnHx711 : BaseCmd {};
struct CmdPowerOffHx711 : BaseCmd {};
struct CmdReadDAC : BaseCmdWithTimesParam {};
struct CmdReadUnits : BaseCmdWithTimesParam {};
struct CmdSetPhase : BaseCmd {
    uint16_t phase;
};
// --- Base Responses
struct BaseResp : PacketHdr {
    BaseResp(Response resp_type) : PacketHdr(resp_type) {};
};

struct RespVoid : BaseResp {
    RespVoid(Response resp_type = RESP_VOID) : BaseResp(resp_type) {};
};

struct RespByte : BaseResp {
    uint8_t data;
    RespByte(Response resp_type = RESP_BYTE) : BaseResp(resp_type) {};
};

struct RespLong : BaseResp {
    long data;
    RespLong(Response resp_type = RESP_LONG) : BaseResp(resp_type) {};
};

struct RespFloat : BaseResp {
    float data;
    RespFloat(Response resp_type = RESP_FLOAT) : BaseResp(resp_type) {};
};

struct RespDouble : BaseResp {
    double data;
    RespDouble(Response resp_type = RESP_DOUBLE) : BaseResp(resp_type) {};
};

struct RespError : BaseResp {
    Error error;
    RespError(Response resp_type = RESP_ERROR) : BaseResp(resp_type) {};
};

// --- Responses
struct RespGetCalibration : BaseResp {
    CalibrationStruct calibration;
    RespGetCalibration(): BaseResp(RESP_GET_CALIBRATION) {};
};
static_assert(sizeof(RespGetCalibration) < SLIP_BUF_ALLOC_BYTES);

struct RespMultiDataPoint : BaseResp {
    RespMultiDataPoint() : BaseResp(RESP_MULTI_DATA_POINT) {};
};
// meyere, update this when the data point structure tree if fixed
static_assert(sizeof(RespMultiDataPoint) + (sizeof(MultiDataPoint) * MASS_SENSOR_COUNT));

#endif /* command_h */