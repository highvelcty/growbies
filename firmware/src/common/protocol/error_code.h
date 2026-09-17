#pragma once

#include <cstdint>

enum class ErrorCode: uint32_t {
    ERROR_NONE                                  = 0,
    ERROR_CMD_DESERIALIZATION_BUFFER_UNDERFLOW  = 1,
    ERROR_UNRECOGNIZED_COMMAND                  = 2,
    ERROR_INCOMPLETE_SLIP_FRAME                 = 3,
    ERROR_INVALID_SLIP_CRC                      = 4,
    ERROR_CMD_HDR_DESERIALIZATION_UNDERFLOW     = 5,
    ERROR_NOT_READY                             = 6,
    ERROR_MEASUREMENT_DEGRADED                  = 7,
    ERROR_MEASUREMENT_FAILED                    = 8,
    ERROR_READ_VOLTAGE                          = 9,
    ERROR_UNDER_TEMPERATURE                     = 10,
    ERROR_OVER_TEMPERATURE                      = 11,
};

inline const char* error_code_str(const ErrorCode code) {
    switch (code) {
        case ErrorCode::ERROR_NONE:
            return "no error";

        case ErrorCode::ERROR_CMD_DESERIALIZATION_BUFFER_UNDERFLOW:
            return "buf underflow";

        case ErrorCode::ERROR_UNRECOGNIZED_COMMAND:
            return "unknown cmd";

        case ErrorCode::ERROR_INCOMPLETE_SLIP_FRAME:
            return "partial SLIP";

        case ErrorCode::ERROR_INVALID_SLIP_CRC:
            return "bad SLIP CRC";

        case ErrorCode::ERROR_CMD_HDR_DESERIALIZATION_UNDERFLOW:
            return "cmd hdr underflow";

        case ErrorCode::ERROR_NOT_READY:
            return "not ready";

        case ErrorCode::ERROR_MEASUREMENT_DEGRADED:
            return "degraded";

        case ErrorCode::ERROR_MEASUREMENT_FAILED:
            return "failed";

        case ErrorCode::ERROR_READ_VOLTAGE:
            return "read volts";

        case ErrorCode::ERROR_UNDER_TEMPERATURE:
            return "under temp.";

        case ErrorCode::ERROR_OVER_TEMPERATURE:
            return "over temp.";
    }

    return "unknown err";
}