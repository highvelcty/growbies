#pragma once

#include <U8x8lib.h>
#include <cstdio>
#include <Arduino.h>
#include "measure/stack.h"

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
    virtual void synchronize() {}
    virtual void update() {}

    virtual ~BaseMenu() = default;

};

struct BaseCfgMenu : BaseMenu {
    using BaseMenu::BaseMenu;
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

struct BaseTelemetryDrawing : BaseCfgMenu {
    using BaseCfgMenu::redraw;

    static constexpr auto VALUE_CHARS = 7;
    static constexpr auto UNITS_CHARS = 2;

    char title[MAX_DISPLAY_COLUMNS + 1]{};
    char value_str[VALUE_CHARS + 1]{};
    char units_str[UNITS_CHARS + 1]{};

    explicit BaseTelemetryDrawing(
        U8X8& display_,
        const char* msg_ = "",
        std::vector<std::shared_ptr<BaseMenu>> _children = {}
    )
        : BaseCfgMenu(display_, msg_, 0, std::move(_children)) {}

    void draw(const bool selected) override {
        BaseCfgMenu::draw(selected);

        if (!selected) {
            display.setFont(ONE_BY_FONT);
            display.drawString(14, 3, units_str);

            display.setFont(TWO_BY_THREE_FONT);
            draw_value();
        }
    }

    void draw_value() const {
        if (!cached_selected) {
            display.drawString(0, 1, value_str);
        }
    }
};
