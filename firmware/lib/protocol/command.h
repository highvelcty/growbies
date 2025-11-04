#pragma once

#include "constants.h"
#include "nvm.h"

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
    READ = 10
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
    ERROR_INVALID_PARAMETER                     = 0x00000020,
} ErrorCode;

typedef enum EndpointType: uint8_t {
    EP_MASS_SENSOR = 0,
    EP_MASS = 1,
    EP_MASS_ERRORS = 2,
    EP_TEMPERATURE_SENSORS = 3,
    EP_TEMPERATURE = 4,
    EP_TEMPERATURE_ERRORS = 5,
    EP_TARE = 6,
    EP_UNKNOWN = 0xFF
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

struct CmdLoopback : BaseCmd {};
struct CmdPowerOnHx711 : BaseCmd {};
struct CmdPowerOffHx711 : BaseCmd {};
struct CmdRead : BaseCmd {
    uint8_t times{0};
    bool raw{};
};

// --- Base Responses
struct BaseResp {};

// --- Responses
struct RespVoid : BaseResp {
    static constexpr auto VERSION = 1;
    static constexpr auto TYPE = Resp::VOID;
};

struct RespError : BaseResp {
    static constexpr auto VERSION = 1;
    static constexpr auto TYPE = Resp::ERROR;

    ErrorCode error = ERROR_NONE;

    explicit RespError(const ErrorCode ec = ERROR_NONE)
        : error(ec) {}
};

struct RespGetCalibration : BaseResp {
    static constexpr auto VERSION = 1;
    static constexpr auto TYPE = Resp::CALIBRATION;

    NvmCalibration calibration{};

    explicit RespGetCalibration(const NvmCalibration& cal = NvmCalibration{})
        : calibration(cal) {}
};
static_assert(sizeof(RespGetCalibration) < MAX_SLIP_UNENCODED_PACKET_BYTES, "buffer overlfow");

struct RespGetIdentify : BaseResp {
    static constexpr auto VERSION = NvmIdentify::VERSION;
    static constexpr auto TYPE = Resp::IDENTIFY;

    NvmIdentify identify{};

    explicit RespGetIdentify(const NvmIdentify& ident = NvmIdentify{})
        : identify(ident) {}
};
static_assert(sizeof(RespGetIdentify) < MAX_SLIP_UNENCODED_PACKET_BYTES, "buffer overflow");

struct RespGetTare : BaseResp {
    static constexpr auto VERSION = 1;
    static constexpr auto TYPE = Resp::TARE;

    NvmTare tare{};

    explicit RespGetTare(const NvmTare& tare_ = NvmTare{})
        : tare(tare_) {}
};
static_assert(sizeof(RespGetTare) < MAX_SLIP_UNENCODED_PACKET_BYTES);

struct TLVHdr {
    EndpointType type;
    uint8_t length; // number of bytes

    explicit TLVHdr(const EndpointType t = EndpointType::EP_MASS_SENSOR, const uint8_t len = 0)
        : type(t), length(len) {}
};

class DataPoint {
public:
    static constexpr auto VERSION = 1;
    static constexpr auto TYPE = Resp::DATAPOINT;

    explicit DataPoint(uint8_t* buf, const size_t buf_size)
        : buffer(buf), capacity(buf_size), offset(0), last_tlv(nullptr) {}

    template <typename T>
    bool add(const EndpointType type, const T& value) {
        const bool new_header = (last_tlv == nullptr) || (last_tlv->type != type);
        const size_t required = sizeof(T) + (new_header ? sizeof(TLVHdr) : 0);

        if (offset + required > capacity) return false;

        uint8_t* dst = buffer + offset;

        if (new_header) {
            last_tlv = reinterpret_cast<TLVHdr*>(dst);
            last_tlv->type = type;
            last_tlv->length = sizeof(T);
            offset += sizeof(TLVHdr);
            dst += sizeof(TLVHdr);
        } else {
            last_tlv->length += sizeof(T);
        }

        memcpy(dst, &value, sizeof(T));
        offset += sizeof(T);
        return true;
    }

    template <typename T>
    T* find_value(const EndpointType type) {
        size_t pos = 0;
        while (pos + sizeof(TLVHdr) <= offset) {
            auto* hdr = reinterpret_cast<TLVHdr*>(buffer + pos);
            const size_t tlv_size = sizeof(TLVHdr) + hdr->length;

            if (hdr->type == type && pos + tlv_size <= offset) {
                return reinterpret_cast<T*>(hdr + 1); // values follow header
            }

            pos += tlv_size;
        }
        return nullptr;
    }

    size_t get_size() const { return offset; }
    const uint8_t* view() const { return buffer; }
    uint8_t* view() { return buffer; }

private:
    uint8_t* buffer;
    size_t capacity;
    size_t offset;
    TLVHdr* last_tlv;
};

#pragma pack()
