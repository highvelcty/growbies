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
};