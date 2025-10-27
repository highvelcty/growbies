#pragma once

#include <Arduino.h>
#include "nvm.h"

constexpr auto MAX_DISPLAY_COLUMNS = 16;
constexpr auto MAX_DISPLAY_ROWS = 4;

enum class DrawType: uint8_t {
    TEXT = 0,
    FLOAT = 1
};

struct Drawing {};

struct DrawingHdr {
    DrawType type;
    uint8_t x, y, width, height;
};

struct ConfigurationDrawing : Drawing {
    DrawingHdr hdr = {DrawType::TEXT, 1, 0, 1, 2};
    const char title[MAX_DISPLAY_COLUMNS + 1] = "Configuration:";
    static_assert(sizeof("Configuration:") <= MAX_DISPLAY_COLUMNS + 1, "insufficient buffer");
};

struct MassUnitsDrawing {
    DrawingHdr hdr = {DrawType::TEXT, 0, 0, 1, 1};
    const char* msg = "Mass Units:";
    DrawingHdr hdr2 = {DrawType::TEXT, 7, 1, 2, 2};
};
struct MassUnitsGramsDrawing: MassUnitsDrawing {
    const char* msg2 = "Grams (g)";
};
struct MassUnitsKilogramsDrawing: MassUnitsDrawing {
    const char* msg2 = "Kilograms (kg)";
};
struct MassUnitsPoundsDrawing: MassUnitsDrawing {
    const char* msg2 = "Pounds (lb)";
};
struct MassUnitsOuncesDrawing: MassUnitsDrawing {
    const char* msg2 = "Ounces (oz)";
};

struct TelemetryDrawing {
    DrawingHdr hdr = {DrawType::TEXT, 0, 0, 1, 1};
    char title[MAX_DISPLAY_COLUMNS + 1];
    DrawingHdr hdr2 = {DrawType::FLOAT, 1, 1, 2, 3};
    float grams;
    DrawingHdr hdr3 = {DrawType::TEXT, 15, 3, 1, 1};
    char units[MAX_DISPLAY_COLUMNS + 1];
    // Constructor

    TelemetryDrawing(const char* _title, const float _grams, const char* _units) // NOLINT(*-pro-type-member-init)
        : grams(_grams)
    {
        // Copy _title into title buffer safely
        std::size_t i = 0;
        for (; i < sizeof(title) - 1 && _title[i] != '\0'; ++i)
            title[i] = _title[i];
        title[i] = '\0';

        // Copy _units into units buffer safely
        i = 0;
        for (; i < sizeof(units) - 1 && _units[i] != '\0'; ++i)
            units[i] = _units[i];
        units[i] = '\0';
    }
};

struct TemperatureUnitsDrawing {
    DrawingHdr hdr = {DrawType::TEXT, 0, 0, 1, 1};
    const char* msg = "Temperature Units:";
    DrawingHdr hdr2 = {DrawType::TEXT, 7, 1, 2, 2};
};
struct TemperatureUnitsFDrawing {
    const char* msg = "Fahrenheit (*F)";
};
struct TemperatureUnitsCDrawing {
    const char* msg = "Celsius (*C)";
};

struct Flip {
    DrawingHdr hdr = {DrawType::TEXT, 0, 0, 1, 1};
    const char* msg = "Remote flip:";
    DrawingHdr hdr2 = {DrawType::TEXT, 7, 1, 2, 2};
};
struct FlipTrueDrawing {
    const char* msg = "True";
};
struct FlipFalseDrawing {
    const char* msg = "False";
};

struct TareDrawing {
    DrawingHdr hdr = {DrawType::TEXT, 0, 0, 1, 1};
    const char* msg = "Tare:";
    DrawingHdr hdr2 = {DrawType::FLOAT, 0, 0, 2, 2};
};

struct TareValueDrawing: TareDrawing {
    float value = 0.0;
};

struct AutoTareDrawing {
    DrawingHdr hdr = {DrawType::TEXT, 0, 0, 1, 1};
    const char* msg = "Auto Tare:";
    DrawingHdr hdr2 = {DrawType::FLOAT, 0, 0, 2, 2};
};
struct AutoTareValueDrawing: TareDrawing {
    float value = 0.0;
};

// Returns 7-character string + unit used
struct MassDisplay {
    static constexpr auto MASS_DISPLAY_CHARS = 7;
    char str[MASS_DISPLAY_CHARS + 1]; // 7 chars + null terminator
    MassUnits units;
};

MassDisplay format_mass(float grams, MassUnits requested_unit);