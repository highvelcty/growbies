#ifndef CRC_H
#define CRC_H

#include <stdint.h>   // uint8_t, uint16_t, etc
#include <stddef.h>   // size_t

uint16_t crc_ccitt16(const uint8_t* data, size_t length, uint16_t crc = UINT16_MAX);

#endif // CRC_H