#ifndef command_h
#define command_h

#include "constants.h"
#include "protocol/network.h"

// --- Base Commands
struct BaseCmd : PacketHdr {};

struct BaseCmdWithTimesParam : BaseCmd {
    uint8_t times;
};


// --- Commands
struct CmdReadMedianFilterAvg : BaseCmdWithTimesParam {};

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
struct MassDataPoint {
    long mass;
    byte error_count;
    byte ready : 1;
    byte  reserved : 7;
    byte reserved2[2];
};

struct RespMassDataPoint : BaseResp {
    RespMassDataPoint() : BaseResp(RESP_MASS_DATA_POINT) {};
};

#endif /* command_h */