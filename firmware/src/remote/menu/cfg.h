#pragma once

#include <Arduino.h>
#include <cstdio>
#include <memory>
#include <U8x8lib.h>

#include "base.h"
#include "measure/measure_intf.h"
#include "nvm/nvm.h"

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

struct ConfigurationMenu final : BaseCfgMenu {
    explicit ConfigurationMenu(U8X8& display_)
        : BaseCfgMenu(
              display_,
              "Configuration",
              0,
              std::vector<std::shared_ptr<BaseMenu>>{
                  // std::make_shared<UnitsMenu>(display_),
                  std::make_shared<DisplayMenu>(display_),
              }) {}
};
