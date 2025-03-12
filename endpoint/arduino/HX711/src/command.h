#ifndef command_h
#define command_h

#include "protocol/network.h"

#define WAIT_READY_RETRIES 5
#define WAIT_READY_RETRY_DELAY_MS 100

enum Cmd: uint16_t {
    CMD_LOOPBACK = 0,
    CMD_READ_AVERAGE = 1,
    CMD_SET_GAIN = 2,
    CMD_GET_VALUE = 3,
    CMD_GET_UNITS = 4,
    CMD_TARE = 5,
    CMD_SET_SCALE = 6,
    CMD_GET_SCALE = 7,
    CMD_SET_OFFSET = 8,
    CMD_GET_OFFSET = 9,
    CMD_POWER_DOWN = 10,
    CMD_POWER_UP = 11,
    CMD_SET_CHANNEL = 12,
    CMD_GET_CHANNEL = 13,
};

enum RespType: uint16_t {
    RESP_TYPE_VOID = 0,
    RESP_TYPE_BYTE = 1,
    RESP_TYPE_LONG = 2,
    RESP_TYPE_FLOAT = 3,
    RESP_TYPE_DOUBLE = 4,
    RESP_TYPE_ERROR = 0xFFFF,
};

enum Error: uint32_t {
    ERROR_NONE = 0,
    ERROR_CMD_DESERIALIZATION_BUFFER_UNDERFLOW = 1,
    ERROR_UNRECOGNIZED_COMMAND = 2,
    ERROR_HX711_NOT_READY = 3,
};

struct BaseCmd : PacketHdr {};
struct BaseResp : PacketHdr {
    BaseResp(RespType resp_type) : PacketHdr(resp_type) {};
};
struct BaseCmdWithTimesParam : BaseCmd {
    uint8_t times;
};

struct CmdReadAverage : BaseCmdWithTimesParam {};

struct CmdSetGain : BaseCmd {
    uint8_t gain;
};

struct CmdGetUnits : BaseCmdWithTimesParam {};

struct CmdTare : BaseCmdWithTimesParam {};

struct CmdSetScale : BaseCmd {
    float scale;
};

struct CmdGetScale : BaseCmd {};

struct CmdPowerUp : BaseCmd {};

struct CmdPowerDown : BaseCmd {};

struct CmdSetChannel : BaseCmd {
    uint8_t channel;
};

struct CmdGetChannel : BaseCmd {};

struct RespVoid : BaseResp {
    RespVoid() : BaseResp(RESP_TYPE_VOID) {};
};

struct RespByte : BaseResp {
    uint8_t data;
    RespByte() : BaseResp(RESP_TYPE_BYTE) {};
};

struct RespLong : BaseResp {
    int32_t data;
    RespLong() : BaseResp(RESP_TYPE_LONG) {};
};

struct RespFloat : BaseResp {
    float data;
    RespFloat() : BaseResp(RESP_TYPE_FLOAT) {};
};

struct RespDouble : BaseResp {
    double data;
    RespDouble() : BaseResp(RESP_TYPE_DOUBLE) {};
};

struct RespError : BaseResp {
    Error error;
    RespError() : BaseResp(RESP_TYPE_ERROR) {};
};

#endif /* command_h */