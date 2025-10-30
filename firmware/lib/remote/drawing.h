#pragma once

#include <U8x8lib.h>
#include <cstdio>
#include <cstring>
#include <Arduino.h>

#include "nvm.h"


// -----------------------------------------------------------------------------
// Display constants
// -----------------------------------------------------------------------------
constexpr auto MAX_DISPLAY_COLUMNS = 16;
constexpr auto MAX_DISPLAY_ROWS     = 4;

constexpr auto ONE_BY_FONT         = u8x8_font_chroma48medium8_r;
constexpr auto TWO_BY_TWO_BY_FONT  = u8x8_font_px437wyse700a_2x2_r;
constexpr auto TWO_BY_THREE_FONT   = u8x8_font_courR18_2x3_r;

// -----------------------------------------------------------------------------
// Base class for all drawings
// -----------------------------------------------------------------------------
struct Drawing {
    bool selected{false};

    explicit Drawing(const bool _selected = false) : selected(_selected) {}

    virtual ~Drawing() = default;
    virtual void draw(U8X8& display, bool selected) const = 0;
};

// -----------------------------------------------------------------------------
// Simple text-based drawing (most menu pages, labels, etc.)
// -----------------------------------------------------------------------------
struct MenuDrawing : Drawing {
    const char* msg{nullptr};
    const int level{0};


    static constexpr char SELECTED_CHAR = '-';
    static constexpr char UNSELECTED_CHAR = '+';

    explicit MenuDrawing(const char* _msg, const int _level = 0, const bool _selected = false)
        : msg(_msg), level(_level) {
        selected = _selected;
    }

    void draw(U8X8& display, const bool selected) const override {
        if (level == 0) {
            display.setFont(ONE_BY_FONT);
        }

        if (!msg) return;
        char line_buf[MAX_DISPLAY_COLUMNS + 1];
        snprintf(line_buf, sizeof(line_buf), "%c %s", get_selected_char(selected), msg);
        display.drawString(level, level, line_buf);
    }

    virtual char get_selected_char(const bool selected) const {
        if (selected) {
            return SELECTED_CHAR;
        }
        return UNSELECTED_CHAR;
    }
};

struct SubMenuDrawing : MenuDrawing {
    explicit SubMenuDrawing(const char* _msg)
        : MenuDrawing(_msg, 1)
    {}
};

struct ItemDrawing : MenuDrawing {
    static constexpr char SELECTED_CHAR = '>';
    explicit ItemDrawing(const char* _msg) : MenuDrawing(_msg, 2, true) {}
    char get_selected_char(bool selected) const override { return SELECTED_CHAR; }
};

// -----------------------------------------------------------------------------
// Derived simple text pages (just assign message text)
// -----------------------------------------------------------------------------
struct ConfigurationDrawing final : MenuDrawing {
    ConfigurationDrawing() : MenuDrawing("Configuration") {}
};

struct MassUnitsMenuDrawing final : SubMenuDrawing {
    MassUnitsMenuDrawing() : SubMenuDrawing("Mass Units") {}
};
struct MassUnitsDrawing final : ItemDrawing {
    explicit MassUnitsDrawing(const MassUnits _units)
        : ItemDrawing(
              _units == MassUnits::GRAMS     ? "g: Grams" :
              _units == MassUnits::KILOGRAMS ? "kg: Kilog." :
              _units == MassUnits::OUNCES    ? "oz: Ounces" :
              "lb: Pounds"  // fallback for MassUnits::POUNDS
          ) {}
};

struct TemperatureUnitsMenuDrawing final : SubMenuDrawing {
    TemperatureUnitsMenuDrawing(): SubMenuDrawing("Temp. Units") {}
};
struct TemperatureUnitsDrawing final : ItemDrawing {
    explicit TemperatureUnitsDrawing(const TemperatureUnits _units)
        : ItemDrawing(_units == TemperatureUnits::CELSIUS ? "C: Celsius" : "F: Fahren.") {}
};

struct FlipMenuDrawing final : SubMenuDrawing {
    FlipMenuDrawing() : SubMenuDrawing("Flip") {}
};
// Only one class needed
struct FlipDrawing final : ItemDrawing {
    explicit FlipDrawing(const bool flip)
        : ItemDrawing(flip ? "True" : "False") {}
};

// -----------------------------------------------------------------------------
// TelemetryDrawing (base for mass, temperature, etc.)
// -----------------------------------------------------------------------------
struct TelemetryDrawing : Drawing {
    static constexpr auto VALUE_CHARS = 7;
    static constexpr auto UNITS_CHARS = 2;

    char title[MAX_DISPLAY_COLUMNS + 1]{};
    char value[VALUE_CHARS + 1]{};
    char units[UNITS_CHARS + 1]{};

    void draw(U8X8& display, const bool selected) const override {
        display.clear();

        display.setFont(ONE_BY_FONT);
        display.drawString(2, 0, title);

        display.setFont(TWO_BY_THREE_FONT);
        display.drawString(0, 1, value);

        display.setFont(ONE_BY_FONT);
        display.drawString(14, 3, units);
    }
};

// -----------------------------------------------------------------------------
// MassDrawing
// -----------------------------------------------------------------------------
struct MassDrawing final : TelemetryDrawing {
    explicit MassDrawing(const char* t, const float grams = 0.0f,
        const MassUnits requested_units = MassUnits::GRAMS) {
        strncpy(title, t, sizeof(title) - 1);
        title[sizeof(title) - 1] = '\0';

        constexpr float GRAMS_PER_KG = 1000.0f;
        constexpr float GRAMS_PER_OZ = 28.3495f;
        constexpr float OUNCES_PER_LB = 16.0f;

        float converted = grams;
        MassUnits units_to_use = requested_units;

        // Unit conversion
        switch (requested_units) {
            case MassUnits::GRAMS: break;
            case MassUnits::KILOGRAMS: converted /= GRAMS_PER_KG; break;
            case MassUnits::OUNCES: converted /= GRAMS_PER_OZ; break;
            case MassUnits::POUNDS: converted /= (GRAMS_PER_OZ * OUNCES_PER_LB); break;
        }

        // Adjust units if out of range
        if (units_to_use == MassUnits::GRAMS && (converted > 99999.9f || converted < -9999.9f)) {
            units_to_use = MassUnits::KILOGRAMS;
            converted /= GRAMS_PER_KG;
        }
        if (units_to_use == MassUnits::OUNCES && (converted > 9999.99f || converted < -999.99f)) {
            units_to_use = MassUnits::POUNDS;
            converted /= OUNCES_PER_LB;
        }

        // Clamp extreme
        if (converted > 999.999f) converted = 999.999f;
        if (converted < -99.999f) converted = -99.999f;

        // Precision by units
        int precision = 0;
        switch (units_to_use) {
            case MassUnits::GRAMS: precision = 1; break;
            case MassUnits::KILOGRAMS: precision = 3; break;
            case MassUnits::OUNCES: precision = 2; break;
            case MassUnits::POUNDS: precision = 3; break;
        }

        dtostrf(converted, VALUE_CHARS, precision, value);
        value[VALUE_CHARS] = '\0';

        switch (units_to_use) {
            case MassUnits::GRAMS: strncpy(units, "g", UNITS_CHARS); break;
            case MassUnits::KILOGRAMS: strncpy(units, "kg", UNITS_CHARS); break;
            case MassUnits::OUNCES: strncpy(units, "oz", UNITS_CHARS); break;
            case MassUnits::POUNDS: strncpy(units, "lb", UNITS_CHARS); break;
        }
        units[UNITS_CHARS] = '\0';
    }
};

// -----------------------------------------------------------------------------
// TemperatureDrawing
// -----------------------------------------------------------------------------
struct TemperatureDrawing final : TelemetryDrawing {
    TemperatureDrawing(const char* t, const float celsius, const TemperatureUnits requested_units) {
        strncpy(title, t, sizeof(title) - 1);
        title[sizeof(title) - 1] = '\0';

        float temp = celsius;
        if (requested_units == TemperatureUnits::FAHRENHEIT) {
            temp = (celsius * 9.0f / 5.0f) + 32.0f;
        }

        if (temp > 999.9f) temp = 999.9f;
        if (temp < -99.9f) temp = -99.9f;

        dtostrf(temp, VALUE_CHARS, 1, value);
        value[VALUE_CHARS] = '\0';

        switch (requested_units) {
            case TemperatureUnits::CELSIUS: strncpy(units, "C", UNITS_CHARS); break;
            case TemperatureUnits::FAHRENHEIT: strncpy(units, "F", UNITS_CHARS); break;
        }
        units[UNITS_CHARS] = '\0';
    }
};