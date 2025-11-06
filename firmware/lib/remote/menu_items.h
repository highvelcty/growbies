#pragma once

#include <U8x8lib.h>
#include <cstdio>
#include <cstring>
#include <Arduino.h>

#include "measure_intf.h"
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

struct BaseMenu {
    static constexpr char SELECTED_CHAR = '-';
    static constexpr char UNSELECTED_CHAR = '+';

    U8X8& display;
    const char* msg{nullptr};
    int level{0};
    std::vector<std::shared_ptr<BaseMenu>> children;

    bool cached_selected{false};

    explicit BaseMenu(
        U8X8& display_,                   // non-const reference
        const char* msg_ = nullptr,
        const int level_ = 0,
        std::vector<std::shared_ptr<BaseMenu>> _children = {}
    )
        : display(display_),
          msg(msg_),
          level(level_),
          children(std::move(_children))
    {}

    virtual void draw(const bool selected) {
        cached_selected = selected;
    }

    void draw() {
        draw(cached_selected);
    }


    virtual char get_selected_char(const bool _selected) const {
        if (_selected) {
            return SELECTED_CHAR;
        }
        return UNSELECTED_CHAR;
    }
    virtual void on_down() {}
    virtual void on_up() {}
    virtual void on_select() {}
    virtual void synchronize() {}
    virtual void update() {}

    virtual ~BaseMenu() = default;

};

struct BaseCfgMenu : BaseMenu {
    explicit BaseCfgMenu(
        U8X8& display_,                   // non-const reference
        const char* msg_ = nullptr,
        const int level_ = 0,
        std::vector<std::shared_ptr<BaseMenu>> _children = {}
    )
        : BaseMenu(display_, msg_, level_, std::move(_children))
    {}

    void draw(const bool selected) override {
        BaseMenu::draw(selected);

        if (level == 0) {
            display.setFont(ONE_BY_FONT);
        }

        if (!msg) return;
        char line_buf[MAX_DISPLAY_COLUMNS + 1];
        snprintf(line_buf, sizeof(line_buf), "%c %s", get_selected_char(selected), msg);
        display.drawString(level, level, line_buf);
    }
};

struct BaseStrMenuLeaf : BaseCfgMenu {
    static constexpr char SELECTED_CHAR = '>';
    explicit BaseStrMenuLeaf(U8X8& display_, const int level_) :
        BaseCfgMenu(display_, nullptr, level_) {}
    char get_selected_char(bool selected) const override { return SELECTED_CHAR; }
};

struct BaseIntMenuLeaf : BaseCfgMenu {
    static constexpr char SELECTED_CHAR = '>';

    int value{0};

    explicit BaseIntMenuLeaf(U8X8& display_ ,const int level_) :
        BaseCfgMenu(display_, nullptr, level_) {}

    char get_selected_char(bool selected) const override { return SELECTED_CHAR; }

    void draw(const bool selected) override {
        BaseCfgMenu::draw(selected);

        char line_buf[MAX_DISPLAY_COLUMNS + 1];
        snprintf(line_buf, sizeof(line_buf), "%c %d", get_selected_char(selected), value);
        display.drawString(level, level, line_buf);
    }
};

// -----------------------------------------------------------------------------
// Concrete menu/item drawings
// -----------------------------------------------------------------------------
struct ContrastMenuLeaf final : BaseIntMenuLeaf {
    static constexpr uint8_t INC = 15;
    explicit ContrastMenuLeaf(U8X8& display_) : BaseIntMenuLeaf(display_, 3) {}

    void on_up() override {
        if (value == UINT8_MAX) {
            value = 0;
        }
        else {
            value = min(value + INC, UINT8_MAX);
        }
        display.setContrast(value);
    }

    void on_down() override {

        if (value == 0) {
            value = UINT8_MAX;
        }
        else {
            value = max(value - INC, 0);
        }

        display.setContrast(value);
    }

    void on_select() override {
        identify_store->edit().payload.contrast = value;
        identify_store->commit();
    }

    void synchronize() override {
        value = identify_store->view()->payload.contrast;
        display.setContrast(value);
    }
};

struct ContrastMenu final : BaseCfgMenu {
    explicit ContrastMenu(U8X8& display_)
        : BaseCfgMenu(
              display_,
              "Contrast",
              2,
              std::vector<std::shared_ptr<BaseMenu>>{
                  std::make_shared<ContrastMenuLeaf>(display_),
              }) {}
};

struct FlipMenuLeaf final : BaseStrMenuLeaf {
    bool flip{false};

    explicit FlipMenuLeaf(U8X8& display_) : BaseStrMenuLeaf(display_, 3) {
        _set_msg();
    }

    void draw(const bool selected) override {
        BaseStrMenuLeaf::draw(selected);

        _set_msg();
        BaseStrMenuLeaf::draw(selected);
    }

    void on_up() override {
        flip = !flip;
    }

    void on_down() override {
        on_up();
    }

    void on_select() override {
        display.setFlipMode(flip);
        identify_store->edit().payload.flip = flip;
        identify_store->commit();
    }

    void synchronize() override {
        flip = identify_store->view()->payload.flip;
        display.setFlipMode(flip);
    }

    void _set_msg() {
        if (flip) {
            msg = "True";
        }
        else {
            msg = "False";
        }
    }
};

struct FlipMenu final : BaseCfgMenu {
    explicit FlipMenu(U8X8& display_)
        : BaseCfgMenu(
              display_,
              "Flip",
              2,
              std::vector<std::shared_ptr<BaseMenu>>{
                  std::make_shared<FlipMenuLeaf>(display_)
              }) {}
};

struct DisplayMenu final : BaseCfgMenu {
    explicit DisplayMenu(U8X8& display_)
        : BaseCfgMenu(
            display_,
            "Display",
            1,
            std::vector<std::shared_ptr<BaseMenu>>{
                std::make_shared<FlipMenu>(display_),
                std::make_shared<ContrastMenu>(display_),
            }) {}
};

struct MassUnitsMenuLeaf final : BaseStrMenuLeaf {
    MassUnits units{MassUnits::GRAMS};

    explicit  MassUnitsMenuLeaf(U8X8& display_) : BaseStrMenuLeaf(display_, 3) {
        _set_msg();
    }

    void on_down() override {
        // Convert to integer for cycling
        uint8_t next = static_cast<uint8_t>(units) + 1;

        // Wrap around if we exceed the last element
        if (next > static_cast<uint8_t>(MassUnits::POUNDS)) {
            next = static_cast<uint8_t>(MassUnits::GRAMS);
        }

        // Update the current unit
        units = static_cast<MassUnits>(next);
    }

    void on_up() override {
        // Convert to integer for cycling
        uint8_t next = static_cast<uint8_t>(units) - 1;

        // Wrap around if we exceed the first element - note the uint8 wraps to 255.
        if (next > static_cast<uint8_t>(MassUnits::POUNDS)) {
            next = static_cast<uint8_t>(MassUnits::POUNDS);
        }

        // Update the current unit
        units = static_cast<MassUnits>(next);
    }

    void on_select() override {
        identify_store->edit().payload.mass_units = units;
        identify_store->commit();
    }

    void synchronize() override {
        units = identify_store->view()->payload.mass_units;
    }

    void draw(const bool selected) override {
        BaseStrMenuLeaf::draw(selected);
        _set_msg();
        BaseStrMenuLeaf::draw(selected);
    }

    void _set_msg() {
        if (units == MassUnits::GRAMS) {
            msg = "g: grams";
        }
        else if (units == MassUnits::KILOGRAMS) {
            msg = "kg: kilog.";
        }
        else if (units == MassUnits::OUNCES) {
            msg = "oz: ounces";
        }
        else {
            msg = "lb: pounds";
        }
    }
};

struct MassUnitsMenu final : BaseCfgMenu {
    explicit MassUnitsMenu(U8X8& display_)
        : BaseCfgMenu(
              display_,
              "Mass",
              2,
              std::vector<std::shared_ptr<BaseMenu>>{
                  std::make_shared<MassUnitsMenuLeaf>(display_)
              }) {}
};

struct TemperatureUnitsMenuLeaf final : BaseStrMenuLeaf {
    TemperatureUnits units{TemperatureUnits::CELSIUS};

    explicit TemperatureUnitsMenuLeaf(U8X8& display_) : BaseStrMenuLeaf(display_, 3) {
        _set_msg();
    }

    void on_up() override {
        if (units == TemperatureUnits::CELSIUS) {
            units = TemperatureUnits::FAHRENHEIT;
        }
        else {
            units = TemperatureUnits::CELSIUS;
        }
    }

    void on_down() override {
        on_up();
    }

    void on_select() override {
        identify_store->edit().payload.temperature_units = units;
        identify_store->commit();
    }

    void synchronize() override {
        units = identify_store->view()->payload.temperature_units;
    }

    void draw(const bool selected) override {
        BaseStrMenuLeaf::draw(selected);
        _set_msg();
        BaseStrMenuLeaf::draw(selected);
    }

    void _set_msg() {
        if (units == TemperatureUnits::FAHRENHEIT) {
            msg = "F: Fahren.";
        }
        else {
            msg = "C: Celsius";
        }
    }
};

struct TemperatureUnitsMenu final : BaseCfgMenu {
    explicit TemperatureUnitsMenu(U8X8& display_)
        : BaseCfgMenu(
              display_,
              "Temperature",
              2,
              std::vector<std::shared_ptr<BaseMenu>>{
                  std::make_shared<TemperatureUnitsMenuLeaf>(display_),
              }) {}
};

struct UnitsMenu final : BaseCfgMenu {
    explicit UnitsMenu(U8X8& display_)
        : BaseCfgMenu(
              display_,
              "Units",
              1,
              std::vector<std::shared_ptr<BaseMenu>>{
                  std::make_shared<MassUnitsMenu>(display_),
                  std::make_shared<TemperatureUnitsMenu>(display_),
              }) {}
};

struct ConfigurationMenu final : BaseCfgMenu {
    explicit ConfigurationMenu(U8X8& display_)
        : BaseCfgMenu(
              display_,
              "Configuration",
              0,
              std::vector<std::shared_ptr<BaseMenu>>{
                  std::make_shared<UnitsMenu>(display_),
                  std::make_shared<DisplayMenu>(display_),
              }) {}
};


// -----------------------------------------------------------------------------
// TelemetryDrawing (base for mass, temperature, etc.)
// -----------------------------------------------------------------------------
struct TelemetryDrawing : BaseMenu {
    using BaseMenu::draw;

    static constexpr auto VALUE_CHARS = 7;
    static constexpr auto UNITS_CHARS = 2;

    char title[MAX_DISPLAY_COLUMNS + 1]{};
    float value{};
    char value_str[VALUE_CHARS + 1]{};
    MassUnits units{};
    char units_str[UNITS_CHARS + 1]{};

    explicit TelemetryDrawing(
        U8X8& display_,
        const char* msg_ = "",
        const int level_ = 0,
        std::vector<std::shared_ptr<BaseMenu>> _children = {}
    )
        : BaseMenu(display_, msg_, level_, std::move(_children)) {}

    void draw(const bool selected) override {
        BaseMenu::draw(selected);

        display.setFont(ONE_BY_FONT);
        display.drawString(2, 0, title);

        display.setFont(ONE_BY_FONT);
        display.drawString(14, 3, units_str);

        display.setFont(TWO_BY_THREE_FONT);
        draw_value();
    }

    void draw_value() const {
        display.drawString(0, 1, value_str);
    }
};


// -----------------------------------------------------------------------------
// MassDrawing
// -----------------------------------------------------------------------------
struct MassDrawing final : TelemetryDrawing {
    explicit MassDrawing(U8X8& display_, const char* title_, const float grams_ = 0.0f,
        const MassUnits requested_units_ = MassUnits::GRAMS) : TelemetryDrawing(display_) {

        strncpy(title, title_, sizeof(title) - 1);
        title[sizeof(title) - 1] = '\0';

        _convert_units(grams_, requested_units_);
    }

    bool _convert_units(const float grams, const MassUnits new_units) {
        value = grams;

        float converted_mass = grams;
        MassUnits converted_units = new_units;

        constexpr float GRAMS_PER_KG = 1000.0f;
        constexpr float GRAMS_PER_OZ = 28.3495f;
        constexpr float OUNCES_PER_LB = 16.0f;

        // ReSharper disable CppTooWideScope
        constexpr float MAX_ZERO_PRECISION   = 9999999;
        constexpr float MIN_ZERO_PRECISION   = -999999;
        constexpr float MAX_SINGLE_PRECISION = 99999.9;
        constexpr float MIN_SINGLE_PRECISION = -9999.9;
        constexpr float MAX_DOUBLE_PRECISION = 9999.99;
        constexpr float MIN_DOUBLE_PRECISION = -999.99;
        constexpr float MAX_TRIPLE_PRECISION = 99999.9;
        constexpr float MIN_TRIPLE_PRECISION = -9999.9;
        // ReSharper restore CppTooWideScope

        // Unit conversion
        switch (converted_units) {
            case MassUnits::GRAMS: break;
            case MassUnits::KILOGRAMS: converted_mass /= GRAMS_PER_KG; break;
            case MassUnits::OUNCES: converted_mass /= GRAMS_PER_OZ; break;
            case MassUnits::POUNDS: converted_mass /= (GRAMS_PER_OZ * OUNCES_PER_LB); break;
        }

        // Precision by units
        int precision = 0;
        switch (converted_units) {
            case MassUnits::GRAMS: {
                precision = 1;
                if (converted_mass > MAX_SINGLE_PRECISION ||
                    converted_mass < MIN_SINGLE_PRECISION) {
                    converted_units = MassUnits::KILOGRAMS;
                    converted_mass /= GRAMS_PER_KG;
                }
                else {
                    break;
                }
            }
            case MassUnits::OUNCES: {
                precision = 2;
                if (converted_mass > MAX_DOUBLE_PRECISION ||
                    converted_mass < MIN_DOUBLE_PRECISION) {
                    converted_units = MassUnits::POUNDS;
                    converted_mass /= OUNCES_PER_LB;
                }
                else {
                    break;
                }
            }
            case MassUnits::POUNDS:
            case MassUnits::KILOGRAMS: {
                precision = 3;
                if (converted_mass > MAX_TRIPLE_PRECISION ||
                    converted_mass < MIN_TRIPLE_PRECISION) {
                    precision = 2;
                }
                else if (converted_mass > MAX_DOUBLE_PRECISION ||
                         converted_mass < MIN_DOUBLE_PRECISION) {
                    precision = 1;
                }
                else if (converted_mass > MAX_SINGLE_PRECISION ||
                         converted_mass < MIN_SINGLE_PRECISION) {
                    precision = 0;
                    if (converted_mass > MAX_ZERO_PRECISION) {
                        converted_mass = MAX_ZERO_PRECISION;
                    }
                    else if (converted_mass < MIN_ZERO_PRECISION) {
                        converted_mass = MIN_ZERO_PRECISION;
                    }
                }
                break;
            }
        }

        dtostrf(converted_mass, VALUE_CHARS, precision, value_str);
        value_str[VALUE_CHARS] = '\0';

        switch (converted_units) {
            case MassUnits::GRAMS: strncpy(units_str, "g", UNITS_CHARS); break;
            case MassUnits::KILOGRAMS: strncpy(units_str, "kg", UNITS_CHARS); break;
            case MassUnits::OUNCES: strncpy(units_str, "oz", UNITS_CHARS); break;
            case MassUnits::POUNDS: strncpy(units_str, "lb", UNITS_CHARS); break;
        }
        units_str[UNITS_CHARS] = '\0';

        bool redraw = false;
        if (units != converted_units) {
            redraw = true;
            units = converted_units;
        }

        return redraw;
    }

    void update() override {
        const auto& stack = growbies_hf::MeasurementStack::get();
        const auto& new_value = stack.aggregate_mass().total_mass();
        const auto new_units = identify_store->view()->payload.mass_units;
        if (_convert_units(new_value, new_units)) {
            draw();
        }
        else {
            draw_value();
        }
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

        dtostrf(temp, VALUE_CHARS, 1, value_str);
        value_str[VALUE_CHARS] = '\0';

        switch (requested_units) {
            case TemperatureUnits::CELSIUS: strncpy(units_str, "C", UNITS_CHARS); break;
            case TemperatureUnits::FAHRENHEIT: strncpy(units_str, "F", UNITS_CHARS); break;
        }
        units_str[UNITS_CHARS] = '\0';
    }
};

