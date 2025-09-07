#ifndef command_h
#define command_h

#include "flags.h"
#include "constants.h"
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

typedef enum EndpointType: uint8_t {
    MASS = 0,
    TEMPERATURE = 1,
    MASS_0 = 2,
    MASS_1 = 3,
    MASS_2 = 4,
    MASS_3 = 5,
    MASS_4 = 6,
    MASS_5 = 7,
    MASS_6 = 8,
    MASS_7 = 9,
    TEMPERATURE_0 = 7,
    TEMPERATURE_1 = 8,
    TEMPERATURE_2 = 9,
    TEMPERATURE_3 = 10,
    TEMPERATURE_4 = 11,
    TEMPERATURE_5 = 12,
    TEMPERATURE_6 = 13,
    TEMPERATURE_7 = 14,
    TARE_CRC = 15,
} EndpointType;

// Bitwise operators for Error
inline ErrorCode operator|(const ErrorCode lhs, const ErrorCode rhs) {
    return static_cast<ErrorCode>(
        static_cast<uint32_t>(lhs) | static_cast<uint32_t>(rhs));
}

inline ErrorCode& operator|=(ErrorCode& lhs, const ErrorCode rhs) {
    lhs = lhs | rhs;
    return lhs;
}

// Headers/
struct PacketHdr {
    union {
        uint16_t type;
        Resp resp;
        Cmd cmd;
    };
    uint8_t id = 0;
    uint8_t version = 0;

    // Constructors
    explicit PacketHdr(const Resp r,
                       const uint8_t id_,
                       const uint8_t version_)
        : resp(r), id(id_), version(version_) {}

    explicit PacketHdr(const Cmd c,
                       const uint8_t id_,
                       const uint8_t version_)
        : cmd(c), id(id_), version(version_) {}

    explicit PacketHdr(const Cmd c, const uint8_t version_ = 0)
        : PacketHdr(c, 0, version_) {}

    explicit PacketHdr(const Resp r, const uint8_t version_ = 0)
        : PacketHdr(r, 0, version_) {}
};

// Verify size at compile time
static_assert(sizeof(PacketHdr) == 4, "PacketHdr must be exactly 4 bytes");

// --- Base Commands
struct BaseCmd {};

struct BaseCmdWithTimesParam : BaseCmd {
    uint8_t times{0};
    explicit BaseCmdWithTimesParam(const uint8_t times_) : times(times_) {}
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
struct BaseResp {};

// --- Responses
struct RespVoid : BaseResp {};

struct RespError : BaseResp {
    ErrorCode error = ErrorCode::ERROR_NONE;

    explicit RespError(const ErrorCode ec = ErrorCode::ERROR_NONE)
        : error(ec) {}
};

struct RespLoopback : BaseResp {};

struct RespGetCalibration : BaseResp {
    Calibration calibration{};

    explicit RespGetCalibration(const Calibration& cal = Calibration{})
        : calibration(cal) {}
};
static_assert(sizeof(RespGetCalibration) < MAX_SLIP_UNENCODED_PACKET_BYTES);

struct RespGetIdentify : BaseResp {
    Identify1 identify{};

    explicit RespGetIdentify(const Identify1& ident = Identify1{})
        : identify(ident) {}
};
static_assert(sizeof(RespGetIdentify) < MAX_SLIP_UNENCODED_PACKET_BYTES);

struct TLVHdr {
    EndpointType type;
    uint8_t length; // number of values

    explicit TLVHdr(const EndpointType t = EndpointType::MASS, const uint8_t len = 0)
        : type(t), length(len) {}
};

template <typename T>
struct TLV : TLVHdr {
    T* value;         // pointer to array of T (can be single value too)

    TLV(const EndpointType t, const uint8_t len, T* val)
        : TLVHdr(t, len), value(val) {}

    T& operator[](size_t i) { return value[i]; }
    const T& operator[](size_t i) const { return value[i]; }
};

// Concrete TLV types
using FloatTLV = TLV<float>;
using Uint16TLV = TLV<uint16_t>;

template <size_t MAX_DATAPOINT_SIZE>
struct DataPoint {
    uint32_t timestamp = 0;
private:
    size_t offset = sizeof(timestamp);  // relative offset into the buffer for adding data
    TLVHdr* last_tlv = nullptr;         // pointer to last TLV header if any

public:
    explicit DataPoint(const uint32_t ts = 0) : timestamp(ts) {}

    template <typename T>
    bool add(const EndpointType type, const T& value) {
        // Check if we need a new TLV header
        const bool new_header = (last_tlv == nullptr) || (last_tlv->type != type);

        const size_t required = sizeof(T) + (new_header ? sizeof(TLVHdr) : 0);
        if (offset + required > MAX_DATAPOINT_SIZE) return false;

        uint8_t* dst = reinterpret_cast<uint8_t*>(this) + offset;

        if (new_header) {
            last_tlv = reinterpret_cast<TLVHdr*>(dst);
            last_tlv->type = type;
            last_tlv->length = 1;
            offset += sizeof(TLVHdr);
            dst += sizeof(TLVHdr);
        } else {
            last_tlv->length += 1;
        }

        // Copy value
        memcpy(dst, &value, sizeof(T));
        offset += sizeof(T);
        return true;
    }
    size_t getSize() const { return offset; }
};



// typedef float MassSensor[MASS_SENSOR_COUNT];
// typedef float TemperatureSensor[TEMPERATURE_SENSOR_COUNT];
// struct RespDataPoint : BaseResp {
//     MassSensor mass_sensor{};
//     float mass{};
//     TemperatureSensor temperature_sensor{};
//     float temperature{};
//
//     RespDataPoint() : BaseResp(Resp::DATAPOINT) {}
// };
static_assert(sizeof(RespDataPoint) < MAX_SLIP_UNENCODED_PACKET_BYTES);

#endif /* command_h */


