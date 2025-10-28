#pragma once

#include <U8x8lib.h>

#include "nvm.h"


constexpr auto MAX_DISPLAY_COLUMNS = 16;
constexpr auto MAX_DISPLAY_ROWS = 4;
constexpr auto ONE_BY_FONT = u8x8_font_chroma48medium8_r;
constexpr auto TWO_BY_TWO_BY_FONT = u8x8_font_px437wyse700a_2x2_r;
constexpr auto TWO_BY_THREE_FONT = u8x8_font_courR18_2x3_r;


enum class DrawType: uint8_t {
    TEXT = 0,
};

template <typename Derived>
struct Drawing {
    void draw(U8X8& display) const {
        display.clear();
        static_cast<const Derived*>(this)->draw(display);
    }
};

struct SimpleDrawing : Drawing<SimpleDrawing> {
    const char* msg{nullptr};

    void draw(U8X8& display) const {
        display.setFont(ONE_BY_FONT);
        display.draw1x2String(0, 1, msg);
    }
};

struct ConfigurationDrawing : SimpleDrawing {
    ConfigurationDrawing() {msg = "Configuration:";}
};

struct MassUnitsDrawing : SimpleDrawing {
    MassUnitsDrawing() {msg = "Mass Units:";}
};

struct MassUnitsGramsDrawing: SimpleDrawing {
    MassUnitsGramsDrawing() {msg = "Grams (g)";}
};

struct MassUnitsKilogramsDrawing: SimpleDrawing {
    MassUnitsKilogramsDrawing() {msg = "Kilograms (kg)";}
};

struct MassUnitsPoundsDrawing: SimpleDrawing {
    MassUnitsPoundsDrawing() {msg = "Pounds (lb)";}
};
struct MassUnitsOuncesDrawing: SimpleDrawing {
    MassUnitsOuncesDrawing() {msg = "Ounces (oz)";}
};

struct TelemetryDrawing : Drawing<TelemetryDrawing> {
    static constexpr auto VALUE_CHARS = 7;
    static constexpr auto UNITS_CHARS = 2;

    char title[MAX_DISPLAY_COLUMNS + 1]{};
    char value[VALUE_CHARS + 1]{};
    char units[UNITS_CHARS + 1]{};

    void draw(U8X8& display) const {
        display.setFont(ONE_BY_FONT);
        display.drawString(0, 0, title);

        display.setFont(TWO_BY_THREE_FONT);
        display.drawString(0, 1, value);

        display.setFont(ONE_BY_FONT);
        display.drawString(14, 3, units);
    }
};

struct MassDrawing : TelemetryDrawing {
    MassDrawing(const char* t, const float grams, const MassUnits requested_units) {
        // Copy title safely
        strncpy(title, t, sizeof(title) - 1);
        title[sizeof(title) - 1] = '\0';

        // Conversion constants
        constexpr float GRAMS_PER_KG = 1000.0f;
        constexpr float GRAMS_PER_OZ = 28.3495f;
        constexpr float OUNCES_PER_LB = 16.0f;

        float converted_mass = grams;
        MassUnits units_to_use = requested_units;

        // Convert to requested units
        switch (requested_units) {
            case MassUnits::GRAMS: break;
            case MassUnits::KILOGRAMS: converted_mass /= GRAMS_PER_KG; break;
            case MassUnits::OUNCES: converted_mass /= GRAMS_PER_OZ; break;
            case MassUnits::POUNDS: converted_mass /= (GRAMS_PER_OZ * OUNCES_PER_LB); break;
        }

        // Auto-adjust units for display limits
        if (units_to_use == MassUnits::GRAMS &&
            (converted_mass > 99999.9f || converted_mass < -9999.9f)) {
            units_to_use = MassUnits::KILOGRAMS;
            converted_mass /= GRAMS_PER_KG;
        }

        if (units_to_use == MassUnits::KILOGRAMS &&
            (converted_mass > 999.999f || converted_mass < -99.999f)) {
            converted_mass = (converted_mass > 0) ? 999.999f : -99.9f;
        }

        if (units_to_use == MassUnits::OUNCES &&
            (converted_mass > 9999.99f || converted_mass < -999.99f)) {
            units_to_use = MassUnits::POUNDS;
            converted_mass /= OUNCES_PER_LB;
        }

        if (units_to_use == MassUnits::POUNDS &&
            (converted_mass > 999.999f || converted_mass < -99.999f)) {
            converted_mass = (converted_mass > 0) ? 999.999f : -99.9f;
        }

        // Determine precision based on units
        int precision = 0;
        switch (units_to_use) {
            case MassUnits::GRAMS:      precision = 1; break;
            case MassUnits::KILOGRAMS:  precision = 3; break;
            case MassUnits::OUNCES:     precision = 2; break;
            case MassUnits::POUNDS:     precision = 3; break;
        }

        // Convert float to string
        dtostrf(converted_mass, VALUE_CHARS, precision, value);
        value[VALUE_CHARS] = '\0';

        // Set units string
        switch (units_to_use) {
            case MassUnits::GRAMS:      strncpy(units, "g", UNITS_CHARS); break;
            case MassUnits::KILOGRAMS:  strncpy(units, "kg", UNITS_CHARS); break;
            case MassUnits::OUNCES:     strncpy(units, "oz", UNITS_CHARS); break;
            case MassUnits::POUNDS:     strncpy(units, "lb", UNITS_CHARS); break;
        }
        units[UNITS_CHARS] = '\0';
    }
};

struct TemperatureDrawing : TelemetryDrawing {
    TemperatureDrawing(const char* t, const float celsius, const TemperatureUnits requested_units) {
        // Copy title safely
        strncpy(title, t, sizeof(title) - 1);
        title[sizeof(title) - 1] = '\0';

        float temp = celsius;
        const TemperatureUnits units_to_use = requested_units;

        // Convert to requested units
        if (requested_units == TemperatureUnits::FAHRENHEIT) {
            temp = (celsius * 9.0f / 5.0f) + 32.0f;
        }

        // Optionally, clamp to display limits (similar to MassDrawing)
        if (temp > 999.9f || temp < -999.9f) {
            temp = (temp > 0) ? 999.9f : -99.9f;
        }

        // Convert float to string with precision one
        dtostrf(temp, VALUE_CHARS, 1, value);
        value[VALUE_CHARS] = '\0';

        // Set units string
        switch (units_to_use) {
            case TemperatureUnits::CELSIUS:      strncpy(units, "C", UNITS_CHARS); break;
            case TemperatureUnits::FAHRENHEIT:   strncpy(units, "F", UNITS_CHARS); break;
        }
        units[UNITS_CHARS] = '\0';
    }
};


struct TemperatureUnitsDrawing: SimpleDrawing {
    TemperatureUnitsDrawing() {msg = "Temp. Units:";}
};
struct TemperatureUnitsFDrawing: SimpleDrawing {
    TemperatureUnitsFDrawing() {msg = "Fahrenheit (F)";}
};
struct TemperatureUnitsCDrawing: SimpleDrawing {
    TemperatureUnitsCDrawing() {msg = "Celsius (C)";}
};

struct FlipDrawing: SimpleDrawing {
    FlipDrawing() {msg = "Flip:";}
};

// struct Flip {
//     DrawingHdr hdr = {DrawType::TEXT, 0, 0, 1, 1};
//     const char* msg = "Remote flip:";
//     DrawingHdr hdr2 = {DrawType::TEXT, 7, 1, 2, 2};
// };
struct FlipTrueDrawing {
    const char* msg = "True";
};
struct FlipFalseDrawing {
    const char* msg = "False";
};

// struct TareDrawing {
//     DrawingHdr hdr = {DrawType::TEXT, 0, 0, 1, 1};
//     const char* msg = "Tare:";
//     DrawingHdr hdr2 = {DrawType::FLOAT, 0, 0, 2, 2};
// };
//
// struct TareValueDrawing: TareDrawing {
//     float value = 0.0;
// };
//
// struct AutoTareDrawing {
//     DrawingHdr hdr = {DrawType::TEXT, 0, 0, 1, 1};
//     const char* msg = "Auto Tare:";
//     DrawingHdr hdr2 = {DrawType::FLOAT, 0, 0, 2, 2};
// };
// struct AutoTareValueDrawing: TareDrawing {
//     float value = 0.0;
// };