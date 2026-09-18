#pragma once

#include <Arduino.h>
#include <cstdio>
#include <U8x8lib.h>

#include "common/utils/font.h"
#include "scale/measure/stack.h"

// -----------------------------------------------------------------------------
// Display constants
// -----------------------------------------------------------------------------
constexpr auto MAX_DISPLAY_COLUMNS = 16;
constexpr auto MAX_DISPLAY_ROWS     = 4;
constexpr auto LINE_PREFIX_CHARS    = 2;

constexpr auto ONE_BY_ONE_FONT     = u8x8_font_chroma48medium8_r;
constexpr auto ONE_BY_TWO_FONT     = u8x8_font_8x13B_1x2_f;
constexpr auto TWO_BY_TWO_FONT     = u8x8_font_px437wyse700b_2x2_n;
constexpr auto TWO_BY_THREE_FONT   = growbies_font_courR18_2x3_r;

// -----------------------------------------------------------------------------
// Simple text-based drawing (most menu pages, labels, etc.)
// -----------------------------------------------------------------------------
struct BaseMenu {
    static constexpr char SELECTED_CHAR = '-';
    static constexpr char UNSELECTED_CHAR = '+';
    static constexpr char LEAF_CHAR = '>';
    static constexpr char ERROR_CHAR = '!';

    U8X8& display;
    const char* msg{nullptr};
    int level{0};
    std::vector<std::shared_ptr<BaseMenu>> children;

    bool cached_selected{false};

    explicit BaseMenu(
        U8X8& display_,
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

    virtual void initialize() {}

    virtual char get_selected_char(const bool _selected) const {
        if (_selected) {
            return SELECTED_CHAR;
        }
        return UNSELECTED_CHAR;
    }

    virtual void on_down() {}
    virtual void on_up() {}
    virtual void on_select() {}
    virtual void set_msg() {}
    virtual void synchronize() {}
    virtual void update() {}

    virtual ~BaseMenu() = default;
};

struct BaseCfgMenu : BaseMenu {
    using BaseMenu::BaseMenu;

    explicit BaseCfgMenu(
        U8X8& display_,
        const char* msg_ = nullptr,
        const int level_ = 0,
        std::vector<std::shared_ptr<BaseMenu>> _children = {}
    )
        : BaseMenu(display_, msg_, level_, std::move(_children))
    {}

    void draw(const bool selected) override {
        BaseMenu::draw(selected);

        display.setFont(ONE_BY_ONE_FONT);

        if (!msg) return;

        char line_buf[MAX_DISPLAY_COLUMNS + 1];
        snprintf(
            line_buf,
            sizeof(line_buf),
            "%c %s",
            get_selected_char(selected),
            msg);

        display.drawString(0, level, line_buf);
    }
};

struct BaseStrMenuLeaf : BaseCfgMenu {
    constexpr static size_t MSG_BUF_LEN = 16;
    char msg_buf[MSG_BUF_LEN]{};

    explicit BaseStrMenuLeaf(U8X8& display_, const int level_) :
        BaseCfgMenu(display_, nullptr, level_)
    {
        msg = msg_buf;
    }

    char get_selected_char(bool selected) const override {
        return LEAF_CHAR;
    }
};

struct BaseIntMenuLeaf : BaseCfgMenu {
    int value{0};

    explicit BaseIntMenuLeaf(U8X8& display_, const int level_) :
        BaseCfgMenu(display_, nullptr, level_)
    {}

    char get_selected_char(bool selected) const override {
        return LEAF_CHAR;
    }

    void draw(const bool selected) override {
        BaseCfgMenu::draw(selected);

        char line_buf[MAX_DISPLAY_COLUMNS + 1];
        snprintf(
            line_buf,
            sizeof(line_buf),
            "%c %d",
            get_selected_char(selected),
            value);

        display.drawString(0, level, line_buf);
    }
};

// -----------------------------------------------------------------------------
// Telemetry drawing state
// -----------------------------------------------------------------------------
struct TelemetryDrawingState {
    static constexpr auto UNITS_CHARS = 2;

    char error_str[MAX_DISPLAY_COLUMNS + 1]{};
    char units_str[UNITS_CHARS + 1]{};
    char value_str[MAX_DISPLAY_COLUMNS + 1]{};

    float value{NAN};
    int precision{1};

    UnitsType units_type{UnitsType::MASS};
    uint8_t units{static_cast<uint8_t>(MassUnits::GRAMS)};
    ErrorCode error{ErrorCode::ERROR_NONE};

    bool needs_full_redraw{true};
};

// -----------------------------------------------------------------------------
// Base telemetry drawing
//
// This owns the telemetry state, but does not impose a particular layout.
// Aggregate and sensor layouts are implemented by the derived drawing classes.
// -----------------------------------------------------------------------------
struct BaseTelemetryDrawing : BaseCfgMenu {
    TelemetryDrawingState state{};

    explicit BaseTelemetryDrawing(
        U8X8& display_,
        const char* msg_,
        const int level_ = 0,
        std::vector<std::shared_ptr<BaseMenu>> _children = {}
    )
        : BaseCfgMenu(
            display_,
            msg_,
            level_,
            std::move(_children))
    {}

    const char* _units_str() const {
        if (state.units_type == UnitsType::MASS) {
            switch (static_cast<MassUnits>(state.units)) {
                case MassUnits::GRAMS:
                    return "g";

                case MassUnits::KILOGRAMS:
                    return "kg";

                case MassUnits::OUNCES:
                    return "oz";

                case MassUnits::POUNDS:
                    return "lb";
            }
            return "";
        }

        return (static_cast<TemperatureUnits>(state.units)
            == TemperatureUnits::CELSIUS ? "*C" : "*F");
    }

    void _set_units_str() {
        snprintf(
            state.units_str,
            sizeof(state.units_str),
            "%2s",
            _units_str());
    }
};

// -------------------------------------------------------------------------------------------------
// Aggregate telemetry drawing
//
// This BaseMenu-derived drawing implements the drawing format for an aggregate telemetry output.
// -------------------------------------------------------------------------------------------------
struct BaseAggregateTelemetryDrawing : BaseTelemetryDrawing {
    static constexpr auto VALUE_CHARS = 7;

    explicit BaseAggregateTelemetryDrawing(
        U8X8& display_,
        const char* msg_,
        const int level_ = 0,
        std::vector<std::shared_ptr<BaseMenu>> _children = {}
    )
        : BaseTelemetryDrawing(
            display_,
            msg_,
            level_,
            std::move(_children))
    {}

    void draw(const bool selected) override {
        if (state.needs_full_redraw) {
            BaseTelemetryDrawing::draw(selected);
            _set_units_str();
            _set_error_str();

            display.setFont(ONE_BY_ONE_FONT);
            display.drawString(14, 3, state.units_str);

            display.setFont(ONE_BY_TWO_FONT);
            display.drawString(15, 1, state.error_str);

            state.needs_full_redraw = false;

            display.setFont(TWO_BY_THREE_FONT);
        }

        draw_fast();
    }

    void draw_fast() {
        _set_value_str();
        display.drawString(0, 1, state.value_str);
    }

    void initialize() override {
        BaseTelemetryDrawing::initialize();
        state.needs_full_redraw = true;
    }

    void _set_error_str() {
        state.error_str[0] =
            state.error == ErrorCode::ERROR_NONE
                ? ' '
                : ERROR_CHAR;

        state.error_str[1] = '\0';
    }

    void _set_value_str() {
        dtostrf(
            state.value,
            VALUE_CHARS,
            state.precision,
            state.value_str);

        state.value_str[VALUE_CHARS] = '\0';
    }
};

// -----------------------------------------------------------------------------
// Sensor telemetry drawing
//
// This implements the drawing format for per sensor (not aggregate) telemetry.
// -----------------------------------------------------------------------------
struct BaseSensorTelemetryDrawing : BaseTelemetryDrawing {
    static constexpr auto VALUE_CHARS = 4;

    explicit BaseSensorTelemetryDrawing(
        U8X8& display_,
        const char* msg_,
        const int level_ = 0,
        std::vector<std::shared_ptr<BaseMenu>> _children = {}
    )
        : BaseTelemetryDrawing(
            display_,
            msg_,
            level_,
            std::move(_children))
    {}

    void draw(const bool selected) override {
        BaseTelemetryDrawing::draw(selected);

        _set_value_str();
        _set_error_str();

        display.setFont(ONE_BY_ONE_FONT);
        display.drawString(2, 2, state.value_str);
        display.drawString(0, 3, state.error_str);
    }

    void _set_error_str() {
        snprintf(
            state.error_str,
            sizeof(state.error_str),
            "%lu: %s",
            static_cast<unsigned long>(state.error),
            error_code_str(state.error));

        for (size_t i = strlen(state.error_str); i < MAX_DISPLAY_COLUMNS; ++i) {
            state.error_str[i] = ' ';
        }

        state.error_str[MAX_DISPLAY_COLUMNS] = '\0';
    }

    void _set_value_str() {
        constexpr auto pad_count = MAX_DISPLAY_COLUMNS - LINE_PREFIX_CHARS;
        snprintf(
            state.value_str,
            sizeof(state.value_str),
            "%*.*f %s",
            VALUE_CHARS,
            state.precision,
            state.value,
            _units_str());

        const size_t len = strlen(state.value_str);

        for (size_t i = len; i < pad_count; ++i) {
            state.value_str[i] = ' ';
        }

        state.value_str[pad_count] = '\0';
    }
};

// -----------------------------------------------------------------------------
// Aggregate Error drawing
//
// This implements the drawing format for per sensor (not aggregate) telemetry.
// -----------------------------------------------------------------------------
struct BaseErrorDrawing : BaseTelemetryDrawing {
    BaseErrorDrawing(
        U8X8& display_,
        const char* msg_)
        : BaseTelemetryDrawing(
            display_,
            msg_,
            2,
            std::vector<std::shared_ptr<BaseMenu>>{})
    {}

    void update() override {
        const auto& measurement_stack = MeasurementStack::get();
        measurement_stack.update();

        state.error = get_measurement(measurement_stack).error;
    }

    void draw(const bool selected) override {
        display.setFont(ONE_BY_ONE_FONT);

        snprintf(
            state.error_str,
            sizeof(state.error_str),
            "%lu: %s",
            static_cast<unsigned long>(state.error),
            error_code_str(state.error));

        display.drawString(
            0,
            2,
            state.error_str);
    }

    char get_selected_char(bool selected) const override {
        return LEAF_CHAR;
    }

    virtual Measurement get_measurement(
        const MeasurementStack& measurement_stack) const = 0;
};

