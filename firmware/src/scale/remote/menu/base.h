#pragma once

#include <U8x8lib.h>
#include <cstdio>
#include <Arduino.h>
#include "scale/measure/stack.h"

// -----------------------------------------------------------------------------
// Display constants
// -----------------------------------------------------------------------------
constexpr auto MAX_DISPLAY_COLUMNS = 16;
constexpr auto MAX_DISPLAY_ROWS     = 4;

constexpr auto ONE_BY_FONT         = u8x8_font_chroma48medium8_r;
// constexpr auto TWO_BY_TWO_BY_FONT  = u8x8_font_px437wyse700a_2x2_r;
constexpr auto TWO_BY_TWO_FONT     = u8x8_font_px437wyse700b_2x2_n;
constexpr auto TWO_BY_THREE_FONT   = u8x8_font_courR18_2x3_r;

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

    virtual void redraw() {
        display.clear();
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
    virtual void set_msg() {}
    virtual void synchronize() {}
    virtual void update(const bool current) {}

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

        if (level == 0) {
            display.setFont(ONE_BY_FONT);
        }

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
    static constexpr auto VALUE_CHARS = 7;
    static constexpr auto VALUE_CHARS_TIGHT = 4;
    static constexpr auto UNITS_CHARS = 2;
    static constexpr auto ERROR_CHARS = MAX_DISPLAY_COLUMNS;

    char value_str[VALUE_CHARS + 1]{};
    char units_str[UNITS_CHARS + 1]{};
    char error_str[ERROR_CHARS + 1]{};

    ErrorCode error{ErrorCode::ERROR_NONE};
};

// -----------------------------------------------------------------------------
// Base telemetry drawing
//
// This owns the telemetry state, but does not impose a particular layout.
// Aggregate and sensor layouts are implemented by the derived drawing classes.
// -----------------------------------------------------------------------------

struct BaseTelemetryDrawing : BaseCfgMenu {
    static constexpr auto VALUE_CHARS =
        TelemetryDrawingState::VALUE_CHARS;

    static constexpr auto VALUE_CHARS_TIGHT =
        TelemetryDrawingState::VALUE_CHARS_TIGHT;

    static constexpr auto UNITS_CHARS =
        TelemetryDrawingState::UNITS_CHARS;

    static constexpr auto ERROR_CHARS =
        TelemetryDrawingState::ERROR_CHARS;

    TelemetryDrawingState telemetry;

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
};

// -----------------------------------------------------------------------------
// Aggregate telemetry drawing
//
// This remains a real BaseMenu-derived drawing because it represents a
// particular kind of menu page. Its rendering state is owned by
// BaseTelemetryDrawing.
// -----------------------------------------------------------------------------

struct BaseAggregateTelemetryDrawing : BaseTelemetryDrawing {
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
        BaseTelemetryDrawing::draw(selected);

        if (selected)
            return;

        display.setFont(ONE_BY_FONT);
        display.drawString(14, 3, telemetry.units_str);
        display.drawString(15, 2, telemetry.error_str);

        display.setFont(TWO_BY_THREE_FONT);
        draw_fast();
    }

    void draw_fast() const {
        display.drawString(0, 1, telemetry.value_str);
    }
};

// -----------------------------------------------------------------------------
// Sensor telemetry drawing
// -----------------------------------------------------------------------------

struct BaseSensorTelemetryDrawing : BaseTelemetryDrawing {
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

        display.setFont(ONE_BY_FONT);
        display.drawString(14, 2, telemetry.units_str);
        display.drawString(2, 2, telemetry.value_str);
        display.drawString(0, 3, telemetry.error_str);
    }
};

// -----------------------------------------------------------------------------
// Temperature formatting helper
//
// This is deliberately NOT a BaseMenu and does not inherit from
// BaseTelemetryDrawing. It is a formatting capability that operates on an
// existing BaseTelemetryDrawing.
//
// This avoids the diamond that would otherwise occur when TemperatureDrawing
// needs both aggregate telemetry rendering and temperature formatting.
// -----------------------------------------------------------------------------

struct BaseTemperatureDrawing {
    BaseTelemetryDrawing& telemetry_drawing;

    TemperatureUnits units{TemperatureUnits::CELSIUS};

    explicit BaseTemperatureDrawing(
        BaseTelemetryDrawing& telemetry_drawing_)
        : telemetry_drawing(telemetry_drawing_)
    {}

    void synchronize() {
        units = identify_store->view()->payload.temperature_units;
    }

    bool _set_state(const Measurement measurement) {
        const auto new_units =
            identify_store->view()->payload.temperature_units;

        float temp = measurement.value;

        if (new_units == TemperatureUnits::FAHRENHEIT) {
            temp = (measurement.value * 9.0f / 5.0f) + 32.0f;
        }

        if (temp > 999.9f)
            temp = 999.9f;

        if (temp < -99.9f)
            temp = -99.9f;

        dtostrf(
            temp,
            TelemetryDrawingState::VALUE_CHARS,
            1,
            telemetry_drawing.telemetry.value_str);

        telemetry_drawing.telemetry.value_str[
            TelemetryDrawingState::VALUE_CHARS] = '\0';

        switch (new_units) {
            case TemperatureUnits::CELSIUS:
                strncpy(
                    telemetry_drawing.telemetry.units_str,
                    "*C",
                    TelemetryDrawingState::UNITS_CHARS);
                break;

            case TemperatureUnits::FAHRENHEIT:
                strncpy(
                    telemetry_drawing.telemetry.units_str,
                    "*F",
                    TelemetryDrawingState::UNITS_CHARS);
                break;
        }

        telemetry_drawing.telemetry.units_str[
            TelemetryDrawingState::UNITS_CHARS] = '\0';

        const bool redraw =
            (units != new_units) ||
            (telemetry_drawing.telemetry.error != measurement.error);

        units = new_units;
        telemetry_drawing.telemetry.error = measurement.error;

        return redraw;
    }
};

