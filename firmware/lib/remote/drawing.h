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
// Simple text-based drawing (most menu pages, labels, etc.)
// -----------------------------------------------------------------------------

struct MenuDrawing {
    static constexpr char SELECTED_CHAR = '-';
    static constexpr char UNSELECTED_CHAR = '+';

    U8X8& display;
    const char* msg{nullptr};
    int level{0};
    std::vector<std::shared_ptr<MenuDrawing>> children;

    explicit MenuDrawing(
        U8X8& display_,                   // non-const reference
        const char* msg_ = nullptr,
        const int level_ = 0,
        std::vector<std::shared_ptr<MenuDrawing>> _children = {}
    )
        : display(display_),
          msg(msg_),
          level(level_),
          children(std::move(_children))
    {}

    virtual void draw(const bool selected) {}


    virtual char get_selected_char(const bool _selected) const {
        if (_selected) {
            return SELECTED_CHAR;
        }
        return UNSELECTED_CHAR;
    }
    virtual void on_down() {}
    virtual void on_up() {}
    virtual void on_select() {}
    virtual size_t on_descent() { return 0; }
    virtual void update() {}

    virtual ~MenuDrawing() = default;

};

struct CfgMenuDrawing : MenuDrawing {
    explicit CfgMenuDrawing(
        U8X8& display_,                   // non-const reference
        const char* msg_ = nullptr,
        const int level_ = 0,
        std::vector<std::shared_ptr<MenuDrawing>> _children = {}
    )
        : MenuDrawing(display_, msg_, level_, std::move(_children))
    {}

    void draw(const bool selected) override {
        if (level == 0) {
            display.setFont(ONE_BY_FONT);
        }

        if (!msg) return;
        char line_buf[MAX_DISPLAY_COLUMNS + 1];
        snprintf(line_buf, sizeof(line_buf), "%c %s", get_selected_char(selected), msg);
        display.drawString(level, level, line_buf);
    }
};

struct ItemDrawing : CfgMenuDrawing {
    static constexpr char SELECTED_CHAR = '>';
    explicit ItemDrawing(U8X8& display_, const char* msg_, const int level_) :
        CfgMenuDrawing(display_, msg_, level_) {}
    char get_selected_char(bool selected) const override { return SELECTED_CHAR; }
};

struct ValueDrawing : ItemDrawing {
    static constexpr char SELECTED_CHAR = '>';

    int value{0};

    explicit ValueDrawing(U8X8& display_ ,const int level_) :
        ItemDrawing(display_, nullptr, level_) {}

    void draw(const bool selected) override {
        char line_buf[MAX_DISPLAY_COLUMNS + 1];
        snprintf(line_buf, sizeof(line_buf), "%c %d", get_selected_char(selected), value);
        display.drawString(level, level, line_buf);
    }
};

// -----------------------------------------------------------------------------
// Concrete menu/item drawings
// -----------------------------------------------------------------------------
struct ContrastDrawing final : ValueDrawing {
    explicit ContrastDrawing(U8X8& display_) : ValueDrawing(display_, 3) {}

    void on_up() override {
        if (value == UINT8_MAX) {
            value = 0;
        }
        else if (value == 0) {
            value = 7;
        }
        else {
            value = min(value + 8, UINT8_MAX);
        }
        display.setContrast(value);
    }

    void on_down() override {
        if (value == 0) {
            value = UINT8_MAX;
        }
        else if (value == UINT8_MAX) {
            value = 248;
        }
        else {
            value = max(value - 8, 0);
        }
        display.setContrast(value);
    }

    void on_select() override {
        identify_store->edit().payload.contrast = value;
        identify_store->commit();
    }

    void update() override {
        value = identify_store->view()->payload.contrast;
        display.setContrast(value);
    }
};

struct ContrastMenuDrawing final : CfgMenuDrawing {
    explicit ContrastMenuDrawing(U8X8& display_)
        : CfgMenuDrawing(
              display_,
              "Contrast",
              2,
              std::vector<std::shared_ptr<MenuDrawing>>{
                  std::make_shared<ContrastDrawing>(display_),
              }) {}
};
struct FlipDrawing final : ItemDrawing {
    bool flip{false};

    explicit FlipDrawing(U8X8& display_, const bool flip_)
        : ItemDrawing(display_, flip_ ? "True" : "False", 3), flip(flip_) {}

    void on_select() override {
        display.setFlipMode(flip);
        identify_store->edit().payload.flip = flip;
        identify_store->commit();
    }
};

struct FlipMenuDrawing final : CfgMenuDrawing {
    explicit FlipMenuDrawing(U8X8& display_)
        : CfgMenuDrawing(
              display_,
              "Flip",
              2,
              std::vector<std::shared_ptr<MenuDrawing>>{
                  std::make_shared<FlipDrawing>(display_, false),
                  std::make_shared<FlipDrawing>(display_, true)
              }) {}

    size_t on_descent() override {
        if (identify_store->view()->payload.flip) {
            return 1;
        }
        return 0;
    }
};

struct DisplayMenuDrawing final : CfgMenuDrawing {
    explicit DisplayMenuDrawing(U8X8& display_)
        : CfgMenuDrawing(
            display_,
            "Display",
            1,
            std::vector<std::shared_ptr<MenuDrawing>>{
                std::make_shared<FlipMenuDrawing>(display_),
                std::make_shared<ContrastMenuDrawing>(display_),
            }) {}
};

struct MassUnitsDrawing final : ItemDrawing {
    MassUnits units;

    explicit MassUnitsDrawing(U8X8& display_, const MassUnits _units)
        : ItemDrawing(
              display_,
              _units == MassUnits::GRAMS     ? "g: Grams" :
              _units == MassUnits::KILOGRAMS ? "kg: Kilog." :
              _units == MassUnits::OUNCES    ? "oz: Ounces" :
              "lb: Pounds",  // fallback for MassUnits::POUNDS
              3), units(_units) {}

    void on_select() override {
        identify_store->edit().payload.mass_units = units;
        identify_store->commit();
    };
};

struct MassUnitsMenuDrawing final : CfgMenuDrawing {
    explicit MassUnitsMenuDrawing(U8X8& display_)
        : CfgMenuDrawing(
              display_,
              "Mass",
              2,
              std::vector<std::shared_ptr<MenuDrawing>>{
                  std::make_shared<MassUnitsDrawing>(display_, MassUnits::GRAMS),
                  std::make_shared<MassUnitsDrawing>(display_, MassUnits::KILOGRAMS),
                  std::make_shared<MassUnitsDrawing>(display_, MassUnits::OUNCES),
                  std::make_shared<MassUnitsDrawing>(display_, MassUnits::POUNDS)
              }) {}

    size_t on_descent() override {
        // Return an index based on the current MassUnits in the configuration.
        switch (identify_store->view()->payload.mass_units) {
            case MassUnits::GRAMS:      return 0;
            case MassUnits::KILOGRAMS:  return 1;
            case MassUnits::OUNCES:     return 2;
            case MassUnits::POUNDS:     return 3;
        }
        return 0; // fallback
    }

};


struct TemperatureUnitsDrawing final : ItemDrawing {
    TemperatureUnits units;

    explicit TemperatureUnitsDrawing(U8X8& display_, const TemperatureUnits _units)
        : ItemDrawing(
              display_,
              _units == TemperatureUnits::CELSIUS
                  ? "C: Celsius"
                  : "F: Fahren.",
              3), units(_units) {}

    void on_select() override {
        identify_store->edit().payload.temperature_units = units;
        identify_store->commit();
    }
};

struct TemperatureUnitsMenuDrawing final : CfgMenuDrawing {
    explicit TemperatureUnitsMenuDrawing(U8X8& display_)
        : CfgMenuDrawing(
              display_,
              "Temperature",
              2,
              std::vector<std::shared_ptr<MenuDrawing>>{
                  std::make_shared<TemperatureUnitsDrawing>(display_, TemperatureUnits::CELSIUS),
                  std::make_shared<TemperatureUnitsDrawing>(display_, TemperatureUnits::FAHRENHEIT)
              }) {}

    size_t on_descent() override {
        if (identify_store->view()->payload.temperature_units == TemperatureUnits::CELSIUS) {
            return 0;
        }
        return 1;
    }

};

struct UnitsMenuDrawing final : CfgMenuDrawing {
    explicit UnitsMenuDrawing(U8X8& display_)
        : CfgMenuDrawing(
              display_,
              "Units",
              1,
              std::vector<std::shared_ptr<MenuDrawing>>{
                  std::make_shared<MassUnitsMenuDrawing>(display_),
                  std::make_shared<TemperatureUnitsMenuDrawing>(display_),
              }) {}
};

struct ConfigurationDrawing final : CfgMenuDrawing {
    explicit ConfigurationDrawing(U8X8& display_)
        : CfgMenuDrawing(
              display_,
              "Configuration",
              0,
              std::vector<std::shared_ptr<MenuDrawing>>{
                  std::make_shared<UnitsMenuDrawing>(display_),
                  std::make_shared<DisplayMenuDrawing>(display_),
              }) {}
};


// -----------------------------------------------------------------------------
// TelemetryDrawing (base for mass, temperature, etc.)
// -----------------------------------------------------------------------------
struct TelemetryDrawing : MenuDrawing {
    static constexpr auto VALUE_CHARS = 7;
    static constexpr auto UNITS_CHARS = 2;

    char title[MAX_DISPLAY_COLUMNS + 1]{};
    char value[VALUE_CHARS + 1]{};
    char units[UNITS_CHARS + 1]{};

    explicit TelemetryDrawing(
        U8X8& display_,
        const char* msg_ = "",
        const int level_ = 0,
        std::vector<std::shared_ptr<MenuDrawing>> _children = {}
    )
        : MenuDrawing(display_, msg_, level_, std::move(_children)) {}

    void draw(const bool selected) override {
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
    explicit MassDrawing(U8X8& display_, const char* t, const float grams = 0.0f,
        const MassUnits requested_units = MassUnits::GRAMS) : TelemetryDrawing(display_) {

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
    TemperatureDrawing(U8X8& display_, const char* temperature, const float celsius,
        const TemperatureUnits requested_units) : TelemetryDrawing(display_) {
        strncpy(title, temperature, sizeof(title) - 1);
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

