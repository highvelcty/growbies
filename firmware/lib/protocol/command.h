#ifndef command_h
#define command_h

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
    GET_TARE = 8,
    SET_TARE = 9,
};

enum class Resp: uint16_t {
    VOID = 0,
    DATAPOINT = 1,
    CALIBRATION = 2,
    IDENTIFY = 3,
    TARE = 4,
    ERROR = 0xFFFF,
};

typedef enum ErrorCode: uint32_t {
    // bitfield
    ERROR_NONE                                  = 0x00000000,
    ERROR_CMD_DESERIALIZATION_BUFFER_UNDERFLOW  = 0x00000001,
    ERROR_UNRECOGNIZED_COMMAND                  = 0x00000002,
    ERROR_OUT_OF_THRESHOLD_SAMPLE               = 0x00000004,
    ERROR_HX711_NOT_READY                       = 0x00000008,
    ERROR_INTERNAL                              = 0x00000010,
} ErrorCode;

typedef enum EndpointType: uint8_t {
    EP_MASS = 0,
    EP_TEMPERATURE = 1,
    EP_TARE_CRC = 2,
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
constexpr int MAX_RESP_BYTES = MAX_SLIP_UNENCODED_PACKET_BYTES - sizeof(PacketHdr);

// --- Base Commands
struct BaseCmd {};

struct BaseCmdWithTimesParam : BaseCmd {
    uint8_t times{0};
    explicit BaseCmdWithTimesParam(const uint8_t times_ = 0) : times(times_) {}
};

// --- Commands
struct CmdGetCalibration : BaseCmd {};
struct CmdSetCalibration : BaseCmd {
    bool init = false;
    Calibration calibration{};
};
struct CmdGetIdentify: BaseCmd {};
struct CmdSetIdentify : BaseCmd {
    bool init = false;
    Identify1 identify{};
};
struct CmdGetTare: BaseCmd {};
struct CmdSetTare : BaseCmd {
    bool init = false;
    Tare tare{};
};

struct CmdLoopback : BaseCmd {};
struct CmdPowerOnHx711 : BaseCmd {};
struct CmdPowerOffHx711 : BaseCmd {};
struct CmdGetDatapoint : BaseCmdWithTimesParam {
    bool raw{};
};
// --- Base Responses
struct BaseResp {};

// --- Responses
struct RespVoid : BaseResp {
    static constexpr auto VERSION = 0;
    static constexpr auto TYPE = Resp::VOID;
};

struct RespError : BaseResp {
    static constexpr auto VERSION = 0;
    static constexpr auto TYPE = Resp::ERROR;

    ErrorCode error = ErrorCode::ERROR_NONE;

    explicit RespError(const ErrorCode ec = ErrorCode::ERROR_NONE)
        : error(ec) {}
};

struct RespGetCalibration : BaseResp {
    static constexpr auto VERSION = 0;
    static constexpr auto TYPE = Resp::CALIBRATION;

    Calibration calibration{};

    explicit RespGetCalibration(const Calibration& cal = Calibration{})
        : calibration(cal) {}
};
static_assert(sizeof(RespGetCalibration) < MAX_SLIP_UNENCODED_PACKET_BYTES);

struct RespGetIdentify : BaseResp {
    static constexpr auto VERSION = 1;
    static constexpr auto TYPE = Resp::IDENTIFY;

    Identify1 identify{};

    explicit RespGetIdentify(const Identify1& ident = Identify1{})
        : identify(ident) {}
};
static_assert(sizeof(RespGetIdentify) < MAX_SLIP_UNENCODED_PACKET_BYTES);

struct RespGetTare : BaseResp {
    static constexpr auto VERSION = 0;
    static constexpr auto TYPE = Resp::TARE;

    Tare tare{};

    explicit RespGetTare(const Tare& tare_ = Tare{})
        : tare(tare_) {}
};
static_assert(sizeof(RespGetTare) < MAX_SLIP_UNENCODED_PACKET_BYTES);

struct TLVHdr {
    EndpointType type;
    uint8_t length; // number of values

    explicit TLVHdr(const EndpointType t = EndpointType::EP_MASS, const uint8_t len = 0)
        : type(t), length(len) {}
};

template <typename T>
struct TLV : TLVHdr {
    T* value; // pointer to array of T (can be single value too)

    TLV(const EndpointType t, const uint8_t len, T* val)
        : TLVHdr(t, len), value(val) {}

    T& operator[](size_t i) { return value[i]; }
    const T& operator[](size_t i) const { return value[i]; }
};

// --- Serialized ABI structure ---
struct DataPointRaw {
    uint32_t timestamp = 0;
};

// --- Wrapper class for bookkeeping ---
class DataPoint {
public:
    static constexpr auto VERSION = 0;
    static constexpr auto TYPE = Resp::DATAPOINT;

    explicit DataPoint(uint32_t ts = 0)
        : offset(sizeof(raw.timestamp)), last_tlv(nullptr) {
        raw.timestamp = ts;
    }

    template <typename T>
    bool add(const EndpointType type, const T& value) {
        // Check if we need a new TLV header
        const bool new_header = (last_tlv == nullptr) || (last_tlv->type != type);

        const size_t required = sizeof(T) + (new_header ? sizeof(TLVHdr) : 0);
        if (offset + required > MAX_RESP_BYTES) return false;

        uint8_t* dst = reinterpret_cast<uint8_t*>(&raw) + offset;

        if (new_header) {
            last_tlv = reinterpret_cast<TLVHdr*>(dst);
            last_tlv->type = type;
            last_tlv->length = 1;
            offset += sizeof(TLVHdr);
            dst += sizeof(TLVHdr);
        } else {
            last_tlv->length += 1;
        }

        memcpy(dst, &value, sizeof(T));
        offset += sizeof(T);
        return true;
    }

    template <typename T>
    T* find_value(EndpointType type) {
        size_t pos = sizeof(DataPointRaw);
        while (pos + sizeof(TLVHdr) <= offset) {
            auto* hdr = reinterpret_cast<TLVHdr*>(reinterpret_cast<uint8_t*>(&raw) + pos);
            if (hdr->type == type && hdr->length * sizeof(T) + sizeof(TLVHdr) <= offset - pos) {
                return reinterpret_cast<T*>(hdr + 1); // value follows header
            }
            pos += sizeof(TLVHdr) + hdr->length * sizeof(T);
        }
        return nullptr;
    }

    size_t get_size() const { return offset; }

    const DataPointRaw* view() const { return &raw; }
    DataPointRaw* view() { return &raw; }

private:
    DataPointRaw raw;
    size_t offset;    // per-instance tracking
    TLVHdr* last_tlv; // per-instance tracking
};

#endif /* command_h */


